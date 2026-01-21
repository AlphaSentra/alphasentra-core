# INSTRUCTIONS:
#
# To automatically find the optimal target price and stop loss, use the `optimize_and_run_monte_carlo` function.
# This function will find the best parameters for you and then run the simulation.
#
# If you want to specify your own target price and stop loss, use the `run_monte_carlo_simulation` function.

import numpy as np
import os
import random
import pymongo
from helpers import DatabaseManager
from logging_utils import log_error, log_info, log_warning

def _run_simulation_for_optimization(
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
    A lightweight and performance-optimized version of the Monte Carlo simulation, designed specifically for the optimization process.

    This function rapidly calculates the Expected Value (EV) for a given set of trading parameters.
    It is stripped of detailed analytics to allow for quick, iterative testing of numerous
    target and stop-loss combinations in the `optimize_and_run_monte_carlo` function.
    """
    strategy = strategy.lower()
    if strategy not in {"long", "short"}:
        raise ValueError(f"Invalid strategy: {strategy}")

    # Daily drift and volatility
    daily_drift = drift / 252
    daily_volatility = volatility / np.sqrt(252)

    # Generate all random daily returns at once using NumPy
    daily_returns = np.exp(
        (daily_drift - 0.5 * daily_volatility**2) +
        daily_volatility * np.random.normal(0, 1, (num_simulations, time_horizon))
    )

    # Calculate all price paths at once
    price_paths = initial_price * daily_returns.cumprod(axis=1)

    # Determine hits for target and stop-loss across all paths
    if strategy == 'long':
        target_hits = price_paths >= target_price
        stop_hits = price_paths <= stop_loss
    else:  # short
        target_hits = price_paths <= target_price
        stop_hits = price_paths >= stop_loss

    # Find the first day a target or stop is hit
    target_hit_days = np.argmax(target_hits, axis=1)
    stop_hit_days = np.argmax(stop_hits, axis=1)

    # A hit is only valid if it actually occurred (argmax returns 0 if no hit)
    valid_target_hit = np.any(target_hits, axis=1)
    valid_stop_hit = np.any(stop_hits, axis=1)

    # Create masks for each outcome type
    is_win = valid_target_hit & (~valid_stop_hit | (target_hit_days <= stop_hit_days))
    is_loss = valid_stop_hit & (~valid_target_hit | (stop_hit_days < target_hit_days))
    is_expired = ~(is_win | is_loss)

    # Initialize outcomes array
    outcomes = np.zeros(num_simulations)
    final_prices_expired = price_paths[is_expired, -1]

    # Calculate the outcome (profit/loss) for each simulation path
    if strategy == 'long':
        outcomes[is_win] = target_price - initial_price
        outcomes[is_loss] = stop_loss - initial_price
        outcomes[is_expired] = final_prices_expired - initial_price
    else:  # short
        outcomes[is_win] = initial_price - target_price
        outcomes[is_loss] = initial_price - stop_loss
        outcomes[is_expired] = initial_price - final_prices_expired

    # The expected value is the mean of all outcomes
    return np.mean(outcomes)

def _update_insight_with_optimal_levels(ticker: str, target_price: float, stop_loss: float, simulation_results: dict):
    """
    Updates the latest insight document in the 'insights' collection with optimized price levels and specific, consistent root-level simulation metrics.
    """
    try:
        client = DatabaseManager().get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        db = client[db_name]
        insights_collection = db["insights"]

        # Prepare the update payload with only the specified fields at the root level.
        update_payload = {
            "recommendations.0.target_price": target_price,
            "recommendations.0.stop_loss": stop_loss,
            "win_probability": simulation_results.get("win_probability"),
            "risk_of_ruin": simulation_results.get("risk_of_ruin"),
            "avg_days_to_target": simulation_results.get("avg_days_to_target"),
            "expired_probability": simulation_results.get("expired_probability"),
            "maximum_drawdown": simulation_results.get("maximum_drawdown"),
            "expected_value": simulation_results.get("expected_value")
        }

        # Find the most recent insight for the ticker and update it atomically.
        result = insights_collection.find_one_and_update(
            {"recommendations.0.ticker": ticker},
            {"$set": update_payload},
            sort=[("timestamp_gmt", pymongo.DESCENDING)]
        )

        if result is not None:
            log_info(f"Successfully updated insight for {ticker} with optimal price levels and root-level simulation summary.")
        else:
            # This is a warning, not an error, as some models might run stand-alone without a preceding insight.
            log_warning(f"Could not find an insight document to update for ticker {ticker}.", "DATABASE_UPDATE")

    except Exception as e:
        log_error(f"Error updating insight for {ticker}: {e}", "DATABASE_UPDATE", e)

def optimize_and_run_monte_carlo(
    sessionID: str,
    ticker: str,
    initial_price: float,
    strategy: str,
    volatility: float,
    drift: float,
    num_simulations: int,
    min_rrr: float = 2.0
):
    """
    Automates the discovery of optimal trading parameters by optimizing for the highest Expected Value (EV).

    This function systematically searches for the best `target_price` and `stop_loss` combination by:
    1.  Calculating a dynamic `time_horizon` based on volatility and risk-reward ratio.
    2.  Defining a dynamic search space for the stop-loss based on the instrument's daily volatility.
    3.  Testing various risk-reward ratios (from `min_rrr` up to 3:1) for each stop-loss level.
    4.  Utilizing a lightweight simulation (`_run_simulation_for_optimization`) to quickly evaluate the EV of each parameter set.

    Once the optimal parameters are found, it calls `run_monte_carlo_simulation` to perform a detailed analysis,
    saves the results to the `trades` collection, and updates the corresponding `insights` document with a full simulation summary.
    """
    # Ensure strategy is lowercase for consistent comparisons
    strategy = strategy.lower()
    if strategy not in {"long", "short"}:
        raise ValueError(f"Invalid strategy: {strategy}")

    best_params = {
        'target_price': None,
        'stop_loss': None,
        'expected_value': -np.inf,  # Optimize for the highest Expected Value
        'rrr': 0
    }

    # Define search spaces
    vol_multiplier_range = np.arange(1.0, 5.1, 0.5)
    rrr_range = np.arange(min_rrr, 3.1, 0.5) # Cap RRR at 3:1

    # Dynamically calculate time horizon
    median_vol_multiplier = np.median(vol_multiplier_range)
    median_rrr = np.median(rrr_range)
    # Heuristic: The time to reach a target is related to the square of the distance.
    # We use the median RRR and volatility multiplier to estimate a 'typical' trade's distance.
    calculated_horizon = int((median_rrr * median_vol_multiplier) ** 2)
    # Clamp the horizon to a practical range (e.g., 1 month to 1 year)
    time_horizon = np.clip(calculated_horizon, 21, 252).item()
    log_info(f"Using dynamically calculated time horizon: {time_horizon} days for {ticker}")

    total_iterations = len(vol_multiplier_range) * len(rrr_range)
    current_iteration = 0

    print("\nStarting optimization for max Expected Value (Max RRR: 3:1)...")
    print(f"Total iterations to perform: {total_iterations}")

    # Dynamic search space for stop-loss based on volatility
    daily_volatility = volatility / np.sqrt(252)
    
    for vol_multiplier in vol_multiplier_range:
        stop_loss_distance = initial_price * daily_volatility * vol_multiplier
        
        if strategy == 'long':
            stop_loss_price = initial_price - stop_loss_distance
        else: # short
            stop_loss_price = initial_price + stop_loss_distance

        for rrr in rrr_range:
            current_iteration += 1
            print(f"  > Optimizing... {current_iteration}/{total_iterations} ({((current_iteration/total_iterations)*100):.1f}%)  ", end='\r')

            potential_risk = abs(initial_price - stop_loss_price)
            potential_reward = potential_risk * rrr

            if strategy == 'long':
                target_price = initial_price + potential_reward
            else: # short
                target_price = initial_price - potential_reward

            expected_value = _run_simulation_for_optimization(
                initial_price=initial_price,
                strategy=strategy,
                target_price=target_price,
                stop_loss=stop_loss_price,
                volatility=volatility,
                drift=drift,
                time_horizon=time_horizon,
                num_simulations=num_simulations
            )

            if expected_value > best_params['expected_value']:
                if (strategy == 'long' and target_price > initial_price) or \
                   (strategy == 'short' and target_price < initial_price):
                    best_params['expected_value'] = expected_value
                    best_params['target_price'] = target_price
                    best_params['stop_loss'] = stop_loss_price
                    best_params['rrr'] = rrr
    
    print("\n\nOptimization finished.                                ")

    if best_params['target_price'] is None:
        log_error(f"Could not find optimal parameters for {ticker}.", "OPTIMIZATION_FAILURE")
        print(f"Could not find optimal parameters for {ticker}.")
        return

    print(f"\nBest parameters found for {ticker}:")
    print(f"  - Target Price: {best_params['target_price']:.4f}")
    print(f"  - Stop Loss: {best_params['stop_loss']:.4f}")
    print(f"  - Expected Value: ${best_params['expected_value']:.4f}")
    print(f"  - Risk-Reward Ratio: {best_params['rrr']:.1f}\n")

    print("Running final simulation with optimal parameters...")
    
    simulation_results = run_monte_carlo_simulation(
        sessionID=sessionID,
        ticker=ticker,
        initial_price=initial_price,
        strategy=strategy,
        target_price=best_params['target_price'],
        stop_loss=best_params['stop_loss'],
        volatility=volatility,
        drift=drift,
        time_horizon=time_horizon,
        num_simulations=num_simulations
    )

    _update_insight_with_optimal_levels(
        ticker=ticker,
        target_price=best_params['target_price'],
        stop_loss=best_params['stop_loss'],
        simulation_results=simulation_results
    )

    print("Final simulation complete. Results saved to database and insight updated.")

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
    Runs a Monte Carlo simulation for a trading strategy, stores the results in the database,
    and returns a summary of the simulation's performance metrics.
    """
    strategy = strategy.lower()
    if strategy not in {"long", "short"}:
        raise ValueError(f"Invalid strategy: {strategy}")
        
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
        
        sim_max_dd = 0
        peak = price_path[0]
        for p in price_path:
            if p > peak:
                peak = p
            drawdown = (peak - p) / peak
            if drawdown > sim_max_dd:
                sim_max_dd = drawdown
        max_drawdowns.append(sim_max_dd)

    win_probability = wins / num_simulations if num_simulations > 0 else 0.0
    risk_of_ruin = losses / num_simulations if num_simulations > 0 else 0.0
    expired_probability = expired_trades / num_simulations if num_simulations > 0 else 0.0
    
    avg_days_to_target = float(np.mean(days_to_target)) if days_to_target else 0.0
    maximum_drawdown = float(np.max(max_drawdowns)) if max_drawdowns else 0.0
    expected_value = float(np.mean(outcomes)) if outcomes else 0.0
    
    time_index = list(range(time_horizon + 1))
    
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
            "avg_days_to_target": avg_days_to_target,
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

    try:
        client = DatabaseManager().get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        db = client[db_name]
        trades_collection = db["trades"]
        trades_collection.insert_one(trade_data)
        log_info("Successfully inserted trade simulation into the database.")
    except Exception as e:
        log_error(f"Error inserting trade simulation into the database: {e}", "DATABASE_INSERTION", e)
        
    return trade_data["results"]
