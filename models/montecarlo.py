# INSTRUCTIONS:
#
# To automatically find the optimal target price and stop loss, use the `optimize_and_run_monte_carlo` function.
# This function will find the best parameters for you and then run the simulation.
#
# If you want to specify your own target price and stop loss, use the `run_monte_carlo_simulation` function.

import numpy as np
import os
import random
from helpers import DatabaseManager
from logging_utils import log_error, log_info

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

    This function rapidly calculates the win probability for a given set of trading parameters. 
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

    # A win occurs if a target is hit, AND either no stop is hit or the target is hit first
    wins = np.sum(
        valid_target_hit &
        (~valid_stop_hit | (target_hit_days <= stop_hit_days))
    )

    return wins / num_simulations if num_simulations > 0 else 0.0

def optimize_and_run_monte_carlo(
    sessionID: str,
    ticker: str,
    initial_price: float,
    strategy: str,
    volatility: float,
    drift: float,
    time_horizon: int,
    num_simulations: int,
    min_rrr: float = 2.0
):
    """
    Automates the discovery of optimal trading parameters and executes a comprehensive Monte Carlo analysis.

    This function systematically searches for the best `target_price` and `stop_loss` combination by:
    1.  Defining a dynamic search space for the stop-loss based on the instrument's daily volatility.
        It iterates through different volatility multipliers to find an appropriate stop-loss distance.
    2.  Testing various risk-reward ratios (starting from `min_rrr`) for each stop-loss level.
    3.  Utilizing a lightweight simulation (`_run_simulation_for_optimization`) to quickly evaluate the win probability of each parameter set.

    The goal is to identify the combination that maximizes the probability of reaching the target price while respecting the minimum risk-reward ratio.

    Once the optimal parameters are found, it calls the `run_monte_carlo_simulation` function to perform a detailed analysis and store the results in the database.
    """
    # Ensure strategy is lowercase for consistent comparisons
    strategy = strategy.lower()
    if strategy not in {"long", "short"}:
        raise ValueError(f"Invalid strategy: {strategy}")

    best_params = {
        'target_price': None,
        'stop_loss': None,
        'win_probability': -1.0,
        'rrr': 0
    }

    # Dynamic search space for stop-loss based on volatility
    daily_volatility = volatility / np.sqrt(252)
    # The multipliers test stop-losses at different multiples of daily volatility, analogous to an ATR multiplier
    vol_multiplier_range = np.arange(1.0, 5.1, 0.5)
    
    # Search space for Risk-Reward Ratio
    rrr_range = np.arange(min_rrr, 5.1, 0.5)

    total_iterations = len(vol_multiplier_range) * len(rrr_range)
    current_iteration = 0

    print("\nStarting optimization with dynamic stop-loss...")
    print(f"Total iterations to perform: {total_iterations}")

    # Search space for stop_loss as a multiple of daily volatility
    for vol_multiplier in vol_multiplier_range:
        
        stop_loss_distance = initial_price * daily_volatility * vol_multiplier
        
        if strategy == 'long':
            stop_loss_price = initial_price - stop_loss_distance
        else: # short
            stop_loss_price = initial_price + stop_loss_distance

        # Search space for RRR from min_rrr up to 5.0
        for rrr in rrr_range:
            current_iteration += 1
            # Use carriage return to show progress on a single line
            print(f"  > Optimizing... {current_iteration}/{total_iterations} ({((current_iteration/total_iterations)*100):.1f}%)  ", end='\r')

            potential_risk = abs(initial_price - stop_loss_price)
            potential_reward = potential_risk * rrr

            if strategy == 'long':
                target_price = initial_price + potential_reward
            else: # short
                target_price = initial_price - potential_reward

            win_probability = _run_simulation_for_optimization(
                initial_price=initial_price,
                strategy=strategy,
                target_price=target_price,
                stop_loss=stop_loss_price,
                volatility=volatility,
                drift=drift,
                time_horizon=time_horizon,
                num_simulations=num_simulations
            )

            if win_probability > best_params['win_probability']:
                # Ensure the target is profitable for the given strategy
                if (strategy == 'long' and target_price > initial_price) or \
                   (strategy == 'short' and target_price < initial_price):
                    best_params['win_probability'] = win_probability
                    best_params['target_price'] = target_price
                    best_params['stop_loss'] = stop_loss_price
                    best_params['rrr'] = rrr
    
    # Print a newline to move on from the progress line
    print("\n\nOptimization finished.                                ")

    if best_params['target_price'] is None:
        log_error("Could not find optimal parameters.", "OPTIMIZATION_FAILURE")
        print("Could not find optimal parameters.")
        return

    print(f"\nBest parameters found:")
    print(f"  - Target Price: {best_params['target_price']:.2f}")
    print(f"  - Stop Loss: {best_params['stop_loss']:.2f}")
    print(f"  - Win Probability: {best_params['win_probability']:.2%}")
    print(f"  - Risk-Reward Ratio: {best_params['rrr']:.1f}\n")

    print("Running final simulation with optimal parameters...")
    
    # Run the full simulation with the best found parameters
    run_monte_carlo_simulation(
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
    print("Final simulation complete. Results saved to database.")

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
    trade_.data = {
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
