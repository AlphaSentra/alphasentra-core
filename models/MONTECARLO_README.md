# Monte Carlo Simulation for Trading Strategies

This module provides a set of tools to simulate the potential outcomes of trading strategies using the Monte Carlo method. It can either automatically discover the optimal take-profit and stop-loss levels or run simulations with manually provided parameters.

## Implementation

This module offers two primary functions for running simulations:

1.  **For Automated Parameter Optimization**:
    -   Call `optimize_and_run_monte_carlo()`.
    -   This is the recommended function for the default session_id as the optimized model.
    -   It uses `_run_simulation_for_optimization()` internally to rapidly test numerous parameter combinations.
    -   Automatically finds the best `target_price` and `stop_loss` that maximize win probability while enforcing a minimum risk-reward ratio (default is 2:1).
    -   Ideal for finding statistically optimal trading parameters.

2.  **For Custom Parameter Analysis**:
    -   Call `run_monte_carlo_simulation()`.
    -   Use this function when providing custom take-profit (TP), stop-loss (SL), or personalized metrics.
    -   Executes complete simulation with user-specified parameters.
    -   Provides comprehensive analysis including risk metrics and professional commentary.
    -   Ideal for testing specific trading strategies with predefined parameters.

---

## Core Functions

### `optimize_and_run_monte_carlo()`

Automates the discovery of optimal trading parameters and executes a comprehensive Monte Carlo analysis.

**Process:**

1.  **Iterates** through a predefined search space for stop-loss levels (1% to 20% of the initial price).
2.  **Tests** various risk-reward ratios (starting from a minimum of 2:1) for each stop-loss.
3.  **Evaluates** the win probability for each parameter set using a lightweight, performance-optimized simulation.
4.  **Identifies** the `target_price` and `stop_loss` combination that offers the highest win probability.
5.  **Executes** a full, detailed simulation using these optimal parameters and stores the results in the database.

**Parameters:**

-   `sessionID` (str): The session ID for the trade.
-   `ticker` (str): The financial instrument to simulate.
-   `initial_price` (float): The starting price of the instrument.
-   `strategy` (str): The trading strategy, either `'long'` or `'short'`.
-   `volatility` (float): The annualized volatility of the instrument.
-   `drift` (float): The annualized drift (expected return) of the instrument.
-   `time_horizon` (int): The number of trading days for the simulation.
-   `num_simulations` (int): The number of simulation paths to generate.
-   `min_rrr` (float): The minimum risk-reward ratio to enforce (default: `2.0`).

### `run_monte_carlo_simulation()`

Runs a Monte Carlo simulation with a specific, user-defined `target_price` and `stop_loss`.

**Parameters:**

-   All parameters from the optimization function, plus:
-   `target_price` (float): The price at which to take profit.
-   `stop_loss` (float): The price at which to cut losses.

---

## Database Output

The results of every simulation are stored as a document in the `trades` collection of the database. The document has the following structure:

```json
{
    "inputs": {
        "sessionID": "...",
        "ticker": "...",
        "strategy": "...",
        "inputs": {
            "entry_price": 100.0,
            "target_price": 120.0,
            "stop_loss": 90.0,
            "drift": 0.1,
            "volatility": 0.2,
            "num_simulations": 10000
        }
    },
    "results": {
        "win_probability": 0.65,
        "risk_of_ruin": 0.25,
        "avg_days_to_target": 15.5,
        "expired_probability": 0.10,
        "maximum_drawdown": 0.12,
        "expected_value": 8.5
    },
    "chart_data": {
        "time_index": [0, 1, 2, ...],
        "percentiles": {
            "p5": [...],  // 5th percentile price path
            "p50": [...], // 50th percentile (median) price path
            "p95": [...]  // 95th percentile price path
        },
        "sample_paths": [...] // A sample of individual simulation paths
    }
}
```
