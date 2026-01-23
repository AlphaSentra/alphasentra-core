"""
Monte Carlo Simulation Module

This module provides two main functions for Monte Carlo simulation of trading strategies:

1. _run_simulation_for_optimization() - A lightweight, performance-optimized version
   - Use this function for the default session_id as the optimized model
   - Designed specifically for automated parameter optimization
   - Rapidly tests numerous target price and stop-loss combinations
   - Returns only Expected Value (EV) and Win Probability for quick evaluation
   - Ideal for finding statistically optimal trading parameters

2. run_monte_carlo_simulation() - The full, comprehensive simulation
   - Use this function when providing custom take-profit (TP), stop-loss (SL), or personalized metrics
   - Executes complete simulation with user-specified parameters
   - Stores full results in the database including all price paths and percentiles
   - Generates professional commentary and trading advice
   - Returns comprehensive metrics including risk of ruin, maximum drawdown, etc.
   - Ideal for custom strategy analysis and decision-making

The optimize_and_run_monte_carlo() function combines both approaches:
- First uses _run_simulation_for_optimization() to find optimal parameters
- Then uses run_monte_carlo_simulation() with those parameters for final analysis
"""

import numpy as np
import os
import random
import pymongo
from helpers import DatabaseManager
from logging_utils import log_error, log_info, log_warning

def _run_simulation_for_optimization(
    initial_price: float,
    strategy_direction: str, # Renamed from strategy to strategy_direction
    target_price: float,
    stop_loss: float,
    volatility: float,
    drift: float,
    time_horizon: int,
    num_simulations: int
):
    """
    A lightweight and performance-optimized version of the Monte Carlo simulation, designed specifically for the optimization process.

    This function rapidly calculates the Expected Value (EV) and Win Probability for a given set of trading parameters.
    It is stripped of detailed analytics to allow for quick, iterative testing of numerous
    target and stop-loss combinations in the `optimize_and_run_monte_carlo` function.
    """
    strategy_direction = strategy_direction.lower()
    if strategy_direction not in {"long", "short"}:
        raise ValueError(f"Invalid strategy direction: {strategy_direction}")

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
    if strategy_direction == 'long':
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
    if strategy_direction == 'long':
        outcomes[is_win] = target_price - initial_price
        outcomes[is_loss] = stop_loss - initial_price
        outcomes[is_expired] = final_prices_expired - initial_price
    else:  # short
        outcomes[is_win] = initial_price - target_price
        outcomes[is_loss] = initial_price - stop_loss
        outcomes[is_expired] = initial_price - final_prices_expired

    # Calculate the summary metrics
    expected_value = np.mean(outcomes)
    win_probability = np.sum(is_win) / num_simulations

    # Scale expected_value by the initial bet size from config
    # The bet size represents a dollar amount, so we need to calculate how many shares it can buy
    from _config import MONTE_CARLO_MODEL_INITIAL_BET_SIZE
    shares_from_bet_size = MONTE_CARLO_MODEL_INITIAL_BET_SIZE / initial_price
    scaled_expected_value = expected_value * shares_from_bet_size

    return scaled_expected_value, win_probability


def _update_insight_with_optimal_levels(sessionID: str, ticker: str, target_price: float, stop_loss: float, trade_direction: str, simulation_results: dict):
    """
    Updates the latest insight document in the 'insights' collection, but only if the sessionID is 'default'.
    """
    if sessionID != "default":
        log_info(f"Insight update for ticker {ticker} skipped: sessionID is not 'default'.")
        print("\nInsight update skipped: sessionID is not 'default'.")
        return
         
    try:
        client = DatabaseManager().get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        db = client[db_name]
        insights_collection = db["insights"]

        # Find the most recent insight for the ticker to check if strategy direction has changed
        existing_insight = insights_collection.find_one(
            {"recommendations.0.ticker": ticker},
            sort=[("timestamp_gmt", pymongo.DESCENDING)]
        )

        # Prepare the update payload with only the specified fields at the root level.
        # Preserve original decimal precision for target_price and stop_loss
        
        # If we have an existing insight, preserve the decimal precision from the original values
        if existing_insight and "recommendations" in existing_insight and len(existing_insight["recommendations"]) > 0:
            existing_rec = existing_insight["recommendations"][0]
            # Preserve decimal precision by using the same number of decimal places as the original
            if "target_price" in existing_rec and existing_rec["target_price"] is not None:
                original_target_decimals = len(str(existing_rec["target_price"]).split('.')[1]) if '.' in str(existing_rec["target_price"]) else 0
                target_price_preserved = round(target_price, original_target_decimals)
            else:
                target_price_preserved = float(target_price)
                
            if "stop_loss" in existing_rec and existing_rec["stop_loss"] is not None:
                original_stop_decimals = len(str(existing_rec["stop_loss"]).split('.')[1]) if '.' in str(existing_rec["stop_loss"]) else 0
                stop_loss_preserved = round(stop_loss, original_stop_decimals)
            else:
                stop_loss_preserved = float(stop_loss)
        else:
            # No existing insight, use the values as-is
            target_price_preserved = float(target_price)
            stop_loss_preserved = float(stop_loss)

        update_payload = {
            "recommendations.0.target_price": target_price_preserved,
            "recommendations.0.stop_loss": stop_loss_preserved,
            "recommendations.0.trade_direction": trade_direction.upper(), # Added trade_direction in uppercase
            "win_probability": simulation_results.get("win_probability"),
            "risk_of_ruin": simulation_results.get("risk_of_ruin"),
            "avg_days_to_target": simulation_results.get("avg_days_to_target"),
            "expired_probability": simulation_results.get("expired_probability"),
            "maximum_drawdown": simulation_results.get("maximum_drawdown"),
            "expected_value": simulation_results.get("expected_value")
        }

        # Check if strategy direction has changed and update entry_price to match the "price" field
        if existing_insight and "recommendations" in existing_insight and len(existing_insight["recommendations"]) > 0:
            existing_direction = existing_insight["recommendations"][0].get("trade_direction", "")
            if existing_direction and existing_direction.lower() != trade_direction.lower():
                # Get the price from the existing insight and use it as entry_price
                if "price" in existing_insight:
                    update_payload["recommendations.0.entry_price"] = existing_insight["price"]
                    log_info(f"Strategy direction changed from {existing_direction} to {trade_direction.upper()} for {ticker}. Setting entry_price to price value: {existing_insight['price']}.")
                else:
                    log_warning(f"Strategy direction changed from {existing_direction} to {trade_direction.upper()} for {ticker}, but no 'price' field found in existing insight.")

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
    volatility: float,
    drift: float,
    num_simulations: int,
    min_rrr: float = 2.0,
    strategy: str = "long" # Added strategy parameter with default value
):
    """
    Automates the discovery of optimal trading parameters with a fallback mechanism.

    This function first attempts to find the strategy with the highest win probability
    that also has a positive Expected Value (EV).

    If no such strategy is found, it falls back to recommending the strategy with the
    highest EV overall, regardless of its win probability.
    """
    # Define search spaces
    vol_multiplier_range = np.arange(1.0, 5.1, 0.5)
    rrr_range = np.arange(min_rrr, 3.1, 0.5) # Cap RRR at 3:1

    # Use the configured time horizon from _config.py
    from _config import MONTE_CARLO_MODEL_TIME_HORIZON
    time_horizon = MONTE_CARLO_MODEL_TIME_HORIZON
    log_info(f"Using configured time horizon: {time_horizon} days for {ticker}")

    total_iterations = len(vol_multiplier_range) * len(rrr_range) * 2 # Multiply by 2 for long/short
    current_iteration = 0

    print("\nStarting optimization for max Expected Value...")
    print(f"Total iterations to perform: {total_iterations}")

    # Track best parameters for long and short strategies
    best_params_long_positive_ev = {
        'target_price': None, 'stop_loss': None, 'expected_value': -np.inf,
        'win_probability': 0, 'rrr': 0, 'strategy_direction': 'long'
    }
    best_params_long_overall = {
        'target_price': None, 'stop_loss': None, 'expected_value': -np.inf,
        'win_probability': 0, 'rrr': 0, 'strategy_direction': 'long'
    }
    best_params_short_positive_ev = {
        'target_price': None, 'stop_loss': None, 'expected_value': -np.inf,
        'win_probability': 0, 'rrr': 0, 'strategy_direction': 'short'
    }
    best_params_short_overall = {
        'target_price': None, 'stop_loss': None, 'expected_value': -np.inf,
        'win_probability': 0, 'rrr': 0, 'strategy_direction': 'short'
    }

    # Dynamic search space for stop-loss based on volatility
    daily_volatility = volatility / np.sqrt(252)
    
    for strategy_direction in ["long", "short"]:
        for vol_multiplier in vol_multiplier_range:
            stop_loss_distance = initial_price * daily_volatility * vol_multiplier
            
            if strategy_direction == 'long':
                stop_loss_price = initial_price - stop_loss_distance
            else: # short
                stop_loss_price = initial_price + stop_loss_distance

            for rrr in rrr_range:
                current_iteration += 1
                print(f"  > Optimizing ({strategy_direction})... {current_iteration}/{total_iterations} ({((current_iteration/total_iterations)*100):.1f}%)  ", end='\r')

                # Triple the distance parameters before calculating target and stop prices
                stop_loss_distance = stop_loss_distance * 3
                
                if strategy_direction == 'long':
                    stop_loss_price = initial_price - stop_loss_distance
                else: # short
                    stop_loss_price = initial_price + stop_loss_distance

                potential_risk = abs(initial_price - stop_loss_price)
                potential_reward = potential_risk * rrr

                if strategy_direction == 'long':
                    target_price = initial_price + potential_reward
                else: # short
                    target_price = initial_price - potential_reward

                expected_value, win_probability = _run_simulation_for_optimization(
                    initial_price=initial_price, strategy_direction=strategy_direction, target_price=target_price,
                    stop_loss=stop_loss_price, volatility=volatility, drift=drift,
                    time_horizon=time_horizon, num_simulations=num_simulations
                )

                if strategy_direction == 'long':
                    # Always track the best overall EV for long
                    if expected_value > best_params_long_overall['expected_value']:
                        best_params_long_overall = {'expected_value': expected_value, 'win_probability': win_probability,
                                                 'target_price': target_price, 'stop_loss': stop_loss_price, 'rrr': rrr, 'strategy_direction': 'long'}

                    # Track the best win probability for long that has positive expected value
                    if expected_value > 0 and win_probability > best_params_long_positive_ev['win_probability']:
                        best_params_long_positive_ev = {'expected_value': expected_value, 'win_probability': win_probability,
                                                     'target_price': target_price, 'stop_loss': stop_loss_price, 'rrr': rrr, 'strategy_direction': 'long'}
                else: # short
                    # Always track the best overall EV for short
                    if expected_value > best_params_short_overall['expected_value']:
                        best_params_short_overall = {'expected_value': expected_value, 'win_probability': win_probability,
                                                 'target_price': target_price, 'stop_loss': stop_loss_price, 'rrr': rrr, 'strategy_direction': 'short'}

                    # Track the best win probability for short that has positive expected value
                    if expected_value > 0 and win_probability > best_params_short_positive_ev['win_probability']:
                        best_params_short_positive_ev = {'expected_value': expected_value, 'win_probability': win_probability,
                                                     'target_price': target_price, 'stop_loss': stop_loss_price, 'rrr': rrr, 'strategy_direction': 'short'}
    
    print("\n\nOptimization finished.                                ")

    # Compare long and short strategies
    candidates = []
    if best_params_long_positive_ev['target_price'] is not None:
        candidates.append(best_params_long_positive_ev)
    if best_params_short_positive_ev['target_price'] is not None:
        candidates.append(best_params_short_positive_ev)

    if candidates:
        final_best_params = max(candidates, key=lambda x: x['win_probability'])
        print(f"\nFound optimal strategy ({final_best_params['strategy_direction']}) with best win probability and positive expected value.")
    else:
        # Fallback to the best overall EV if no strategy has positive expected value
        all_overall_bests = [best_params_long_overall, best_params_short_overall]
        final_best_params = max(all_overall_bests, key=lambda x: x['expected_value'])
        log_warning(f"Could not find any strategy with positive expected value for {ticker}. Falling back to highest EV strategy.", "OPTIMIZATION_FALLBACK")
        print(f"\nWarning: Could not find any strategy with positive expected value. Falling back to the highest EV ({final_best_params['strategy_direction']}) strategy found.")

    if final_best_params['target_price'] is None:
        log_error(f"Could not find any optimal parameters for {ticker}.", "OPTIMIZATION_FAILURE")
        print(f"Could not find any optimal parameters for {ticker}.")
        return

    print(f"\nBest parameters found for {ticker}:")
    print(f"  - Strategy: {final_best_params['strategy_direction'].capitalize()}")
    print(f"  - Target Price: {final_best_params['target_price']:.4f}")
    print(f"  - Stop Loss: {final_best_params['stop_loss']:.4f}")
    print(f"  - Expected Value: ${final_best_params['expected_value']:.4f}")
    print(f"  - Win Probability: {final_best_params.get('win_probability', 0):.2%}")
    print(f"  - Risk-Reward Ratio: {final_best_params['rrr']:.1f}\n")

    print("Running final simulation with optimal parameters...")
    
    simulation_results = run_monte_carlo_simulation(
        sessionID=sessionID, ticker=ticker, initial_price=initial_price, strategy=final_best_params['strategy_direction'],
        target_price=final_best_params['target_price'],
        stop_loss=final_best_params['stop_loss'],
        volatility=volatility, drift=drift, time_horizon=time_horizon, num_simulations=num_simulations
    )

    _update_insight_with_optimal_levels(
        sessionID=sessionID,
        ticker=ticker,
        target_price=final_best_params['target_price'],
        stop_loss=final_best_params['stop_loss'],
        trade_direction=final_best_params['strategy_direction'],
        simulation_results=simulation_results
    )

    print("Final simulation complete. Results saved to database and insight updated.")


def _generate_simulation_commentary(results: dict, num_simulations: int, strategy: str, ticker: str, sessionID: str = "default") -> str:
    """
    Generates a professional single-paragraph commentary based on the Monte Carlo simulation results,
    providing trading advice with a focus on risk management.
    """
    win_prob = results.get("win_probability", 0) * 100
    risk_of_ruin = results.get("risk_of_ruin", 0) * 100
    avg_days = results.get("avg_days_to_target", 0)
    expired_prob = results.get("expired_probability", 0) * 100
    max_dd = results.get("maximum_drawdown", 0) * 100
    ev = results.get("expected_value", 0)
    
    # Get the bet size from configuration
    from _config import MONTE_CARLO_MODEL_INITIAL_BET_SIZE
    bet_size = MONTE_CARLO_MODEL_INITIAL_BET_SIZE
    
    # Calculate profitability score (0-100)
    profitability_score = 0
    if ev > 0:
        profitability_score += 50  # Base score for positive EV
        if win_prob > 60:
            profitability_score += 30
        elif win_prob > 50:
            profitability_score += 20
        elif win_prob > 40:
            profitability_score += 10
            
        if risk_of_ruin < 30:
            profitability_score += 15
        elif risk_of_ruin < 40:
            profitability_score += 5
            
        if max_dd < 20:
            profitability_score += 5
    
    # Generate single paragraph commentary
    commentary = f"Based on {num_simulations:,} simulated trades for {ticker} using a {strategy} strategy with a ${bet_size:,} bet size, this analysis reveals the following: the strategy demonstrates a {win_prob:.1f}% win probability with an expected value of ${ev:.2f} per trade (based on the ${bet_size:,} bet amount), a {risk_of_ruin:.1f}% stop level, and a maximum drawdown of {max_dd:.1f}%. Approximately {expired_prob:.1f}% of trades are projected to expire without hitting targets, and winning trades typically reach their objectives in around {avg_days:.1f} days when successful. "
    
    # Add strategy selection rationale (only for default session)
    if win_prob < 50 and sessionID == "default":
        commentary += f"Although this strategy has a lower {win_prob:.1f}% win probability, it was selected because "
        if ev > 0:
            commentary += f"it maintains a positive expected value of ${ev:.2f}, indicating that the winning trades are sufficiently larger than losing trades to justify the approach. "
        else:
            commentary += f"it represents the best available option among the tested strategies, though both win probability and expected value suggest caution is warranted. "
        commentary += f"The {strategy} position was chosen based on the optimization algorithm's assessment that it provides the most favorable risk-reward profile given current market conditions and the {ticker} asset's historical behavior. "
    
    if ev > 0 and win_prob > 60:
        commentary += f"This represents a highly promising strategy with strong statistical advantages, as evidenced by the favorable combination of high win probability and positive expected value, resulting in a profitability score of {profitability_score}/100. The relatively low stop level suggests good risk-reward characteristics, making this a strategy worthy of serious consideration for traders seeking consistent profitability. However, prudent risk management remains essential, with position sizing to withstand the {max_dd:.1f}% maximum drawdown scenarios that may occur during normal market fluctuations."
    
    elif ev > 0 and win_prob > 50:
        commentary += f"This strategy shows solid potential with a profitability score of {profitability_score}/100, indicating statistical profitability over the long term, though the {risk_of_ruin:.1f}% stop level suggests disciplined execution is required. It is advised to approach this strategy with conservative position sizing be prepared for the {max_dd:.1f}% drawdowns that represent the worst-case scenarios. The positive expected value of ${ev:.2f} suggests this could be a viable strategy, but it requires consistent application and proper risk management to realize its potential over a large sample of trades."
    
    elif ev > 0 and win_prob <= 50:
        commentary += f"This strategy falls into the high-risk category with a profitability score of {profitability_score}/100, characterized by a positive expected value of ${ev:.2f} but a lower {win_prob:.1f}% win rate, meaning more losing trades than winners are expected. The {risk_of_ruin:.1f}% stop level is concerning and demands extremely cautious approach. This is a speculative trade and should be part of a diversified strategy portfolio, considering the risk of a {max_dd:.1f}% drawdowns."
    
    elif ev <= 0 and win_prob > 50:
        commentary += f"This strategy presents a dangerous combination with a profitability score of {profitability_score}/100, where a {win_prob:.1f}% win rate is offset by a negative expected value of ${ev:.2f}, indicating that losses are likely larger than wins. The {risk_of_ruin:.1f}% stop level confirms this is a risky proposition that will likely erode trading capital over time. Strong recommendation against trading this strategy in its current form; focus instead on developing strategies with both positive expected value and reasonable win rates. Consider adjusting risk-reward ratios, refining entry/exit criteria, or exploring alternative timeframes to improve the statistical profile."
    
    else: # ev <= 0 and win_prob <= 50
        commentary += f"Based on these results with a profitability score of {profitability_score}/100, this does not appear to be a viable trading strategy, as both the {win_prob:.1f}% win rate and negative expected value of ${ev:.2f} suggest the odds are stacked against success. The {risk_of_ruin:.1f}% stop level and {max_dd:.1f}% maximum drawdown confirm this strategy is likely to lose money over time. The current configuration shows no statistical edge and requires significant improvement."
    
    return commentary


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

    # Generate simulation commentary
    simulation_commentary = _generate_simulation_commentary(
        results={
            "win_probability": win_probability,
            "risk_of_ruin": risk_of_ruin,
            "avg_days_to_target": avg_days_to_target,
            "expired_probability": expired_probability,
            "maximum_drawdown": maximum_drawdown,
            "expected_value": expected_value,
        },
        num_simulations=num_simulations,
        strategy=strategy,
        ticker=ticker,
        sessionID=sessionID
    )

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
        "simulation_results": simulation_commentary,
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
        
        # Also update insights collection with simulation_summary if sessionID is "default"
        if sessionID == "default":
            insights_collection = db["insights"]
            # Find the most recent insight for this ticker and update it
            result = insights_collection.find_one_and_update(
                {"recommendations.0.ticker": ticker},
                {"$set": {"simulation_results": simulation_commentary}},
                sort=[("timestamp_gmt", pymongo.DESCENDING)]
            )
            if result is not None:
                log_info(f"Successfully updated insight for {ticker} with simulation summary.")
            else:
                log_warning(f"Could not find an insight document to update for ticker {ticker}.", "DATABASE_UPDATE")
                
    except Exception as e:
        log_error(f"Error inserting trade simulation into the database: {e}", "DATABASE_INSERTION", e)
        
    return trade_data["results"]