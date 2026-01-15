
import numpy as np
import os
import random
from helpers import DatabaseManager
from logging_utils import log_error, log_info

def run_monte_carlo_simulation(
    sessionID: str,
    ticker: str,
    initial_price: float,
    strategy: str,
    target_price: float,
    stop_loss: float,
    volatility: float,
    drift: float,
    time_horizon: int,
    num_simulations: int
):
    """
    Runs a Monte Carlo simulation for a trading strategy and stores the results in the database.

    Args:
        sessionID (str): The session ID for the trade.
        ticker (str): The ticker.
        initial_price (float): The current price of the instrument.
        strategy (str): The trading strategy, either 'long' or 'short'.
        target_price (float): The target price to sell at for a profit.
        stop_loss (float): The price at which to sell to limit losses.
        volatility (float): The volatility (annualized).
        drift (float): The drift (annualized).
        time_horizon (int): The number of trading days for the simulation.
        num_simulations (int): The number of simulations to run.
    """
    strategy = strategy.lower()
    if strategy not in {"long", "short"}:
        raise ValueError(f"Invalid strategy: {strategy}")
    # Daily drift and volatility
    daily_drift = drift / 252
    daily_volatility = volatility / np.sqrt(252)

    wins = 0
    losses = 0
    expired_trades = 0
    days_to_target = []
    max_drawdowns = []
    outcomes = []
    all_paths = []

    for _ in range(num_simulations):
        price_path = [initial_price]
        price = initial_price
        
        for day in range(1, time_horizon + 1):
            daily_return = np.exp(
                (daily_drift - 0.5 * daily_volatility**2) + 
                daily_volatility * np.random.normal(0, 1)
            )
            price *= daily_return
            price_path.append(price)

            if strategy == 'long':
                if target_price is not None and price >= target_price:
                    wins += 1
                    days_to_target.append(day)
                    outcomes.append(target_price - initial_price)
                    break
                elif stop_loss is not None and price <= stop_loss:
                    losses += 1
                    outcomes.append(stop_loss - initial_price)
                    break
            
            elif strategy == 'short':
                if target_price is not None and price <= target_price:
                    wins += 1
                    days_to_target.append(day)
                    outcomes.append(initial_price - target_price)
                    break
                elif stop_loss is not None and price >= stop_loss:
                    losses += 1
                    outcomes.append(initial_price - stop_loss)
                    break
        
        else: # Trade expired
            expired_trades += 1
            if strategy == 'long':
                outcomes.append(price - initial_price)
            else: # short
                outcomes.append(initial_price - price)
        
        all_paths.append(price_path)
        
        # Calculate maximum drawdown for the simulation
        sim_max_dd = 0
        peak = price_path[0]
        for p in price_path:
            if p > peak:
                peak = p
            drawdown = (peak - p) / peak
            if drawdown > sim_max_dd:
                sim_max_dd = drawdown
        max_drawdowns.append(sim_max_dd)

    # Calculate results
    win_probability = wins / num_simulations if num_simulations > 0 else 0.0
    risk_of_ruin = losses / num_simulations if num_simulations > 0 else 0.0
    expired_probability = expired_trades / num_simulations if num_simulations > 0 else 0.0
    
    if len(days_to_target) > 0:
        average_days_to_target = float(np.mean(days_to_target))
    else:
        average_days_to_target = 0.0
        
    maximum_drawdown = float(np.max(max_drawdowns)) if max_drawdowns else 0.0
    expected_value = float(np.mean(outcomes)) if outcomes else 0.0
    
    # Prepare chart data
    time_index = list(range(time_horizon + 1))
    
    # Ensure all paths have the same length for percentile calculation
    padded_paths = []
    for path in all_paths:
        padded_path = path + [path[-1]] * (time_horizon + 1 - len(path))
        padded_paths.append(padded_path)

    if padded_paths:
        p5 = np.percentile(padded_paths, 5, axis=0).tolist()
        p50 = np.percentile(padded_paths, 50, axis=0).tolist()
        p95 = np.percentile(padded_paths, 95, axis=0).tolist()
    else:
        p5, p50, p95 = [], [], []

    num_samples = min(100, num_simulations)
    sample_paths = random.sample(all_paths, num_samples) if num_simulations > 0 else []

    # Prepare data for database insertion
    trade_data = {
        "inputs": {
            "sessionID": sessionID,
            "ticker": ticker,
            "strategy": str(strategy) if strategy is not None else "",
            "inputs": {
                "entry_price": float(initial_price),
                "target_price": float(target_price) if target_price is not None else 0.0,
                "stop_loss": float(stop_loss) if stop_loss is not None else 0.0,
                "drift": float(drift),
                "volatility": float(volatility),
                "num_simulations": int(num_simulations),
            },
        },
        "results": {
            "win_probability": win_probability,
            "risk_of_ruin": risk_of_ruin,
            "avg_days_to_target": average_days_to_target,
            "expired_probability": expired_probability,
            "maximum_drawdown": maximum_drawdown,
            "expected_value": expected_value,
        },
        "chart_data": {
            "time_index": time_index,
            "percentiles": {
                "p5": p5,
                "p50": p50,
                "p95": p95,
            },
            "sample_paths": sample_paths,
        },
    }

    # Insert into database
    try:
        client = DatabaseManager().get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        db = client[db_name]
        trades_collection = db["trades"]
        trades_collection.insert_one(trade_data)
        log_info("Successfully inserted trade simulation into the database.")
    except Exception as e:
        log_error(f"Error inserting trade simulation into the database: {e}", "DATABASE_INSERTION", e)
