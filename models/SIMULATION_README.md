# Market Simulation Documentation

This document details the agent-based market simulation system implemented in [`simulation.py`](models/simulation.py).

## Overview
The simulation system models financial markets through three key phases:
1. **Agent-Based Market Simulation**: Models investor behavior and price discovery
2. **Dynamic Correlation Adjustment**: Adapts investor relationships based on market volatility
3. **Stochastic Data Augmentation**: Adds realistic noise and synthetic data points

Key components:
- `Agent`: Represents individual investors with behavioral parameters
- `MarketSimulator`: Manages market dynamics and price formation
- `process_simulation_data()`: Main pipeline function coordinating all phases

## Core Functions

### `process_simulation_data(raw_simulation_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]`
Main pipeline function that processes raw investor data through:
1. Market simulation phase
2. Dynamic correlation adjustment
3. Stochastic augmentation phase

**Parameters:**
- `raw_simulation_data`: List of investor profiles with:
  - `profile`: Investor identifier
  - `conviction`: Rational assessment [-1.0, 1.0]
  - `sentiment`: Emotional bias [-1.0, 1.0]
  - `position`: Current market position (BULLISH/BEARISH/NEUTRAL)

**Returns:**
- Processed investor states with:
  - Updated conviction/sentiment from market dynamics
  - Unique profile identifiers
  - Enforced academic constraints
  - Stochastic variations for robustness testing
  - Dynamic correlation adjustments based on price volatility

**Note:** Current implementation uses example parameters for market simulation that should be parameterized in future versions.

## Core Functions

### `dynamic_correlation_strength(prices, min_strength=0.3, max_strength=0.8, window=20)`
Adjusts correlation strength between conviction and sentiment based on recent price volatility.

**Parameters:**
- `prices`: Historical price data for volatility calculation
- `min_strength`: Minimum correlation (independent behavior)
- `max_strength`: Maximum correlation (trend-driven behavior)
- `window`: Lookback period for volatility calculation

**Returns:** Correlation strength between min_strength and max_strength

### `apply_stochastic_noise(value: float, scale: float = 0.15) -> float`
Applies Gaussian noise to a value and clamps between -1.0 and 1.0.

**Parameters:**
- `value`: Base value to modify
- `scale`: Standard deviation of noise distribution (default: 0.15)

**Returns:** Noisy value clamped to [-1.0, 1.0]

### `update_simulation_with_stochastic()`
Applies controlled noise to simulation outputs while:
- Generating synthetic data points
- Preserving academic constraints
- Ensuring sentiment never exceeds conviction (rational agent principle)
- Incorporating dynamic correlation adjustments

**Key Parameters:**
- `simulation_data`: Simulation results from market phase
- `num_additional_points`: Synthetic points to generate (default: 1000)
- `prices`: Price history for dynamic correlation adjustment
- Noise scaling parameters for different processing stages

## Core Classes

### `Agent` Class
Represents an investor in the market simulation with reverse-engineered behavioral parameters.

**Key Attributes:**
- `conviction`: Rational assessment (-1.0 to 1.0)
- `sentiment`: Emotional bias (-1.0 to 1.0)
- `position`: Current market position (BULLISH/BEARISH/NEUTRAL)
- `risk_aversion`: (Reverse-engineered) Willingness to take risks (1.0 - |conviction|)
- `recency_bias`: (Reverse-engineered) Behavioral bias from conviction-sentiment gap

**Key Methods:**
- `calculate_pnl()`: Updates profit/loss based on price changes
- `calculate_new_conviction()`: Updates conviction using public info and macro shocks
- `calculate_new_sentiment()`: Updates sentiment based on P&L and herd effect
- `execute_trade()`: Determines new position based on conviction threshold
- `get_state()`: Returns current agent state

### `MarketSimulator` Class
Models market dynamics including:
- Price discovery through investor interactions
- Aggregate sentiment calculation
- Net order imbalance computation
- Price history tracking for volatility analysis

**Key Methods:**
- `run_time_step()`: Executes one market time step with:
  - Price correction based on order imbalance and noise
  - Agent conviction/sentiment updates
  - Trade execution
  - Price history recording

## Academic Constraints
1. Sentiment cannot exceed conviction (|S| ≤ |C|)
2. Price changes depend on net order imbalance (γ=0.5) plus random noise
3. Agent behavior follows ABM principles from financial literature:
   - Parameters reverse-engineered from initial C/S data
   - Conviction influenced by fundamental factors
   - Sentiment influenced by P&L and herd behavior
4. Stochastic noise follows Gaussian distributions
5. Dynamic correlation adjusts based on market volatility

## Example Parameters
Current market simulation uses:
- `public_info=0.6` (positive market signal)
- `macro_shock=-0.1` (negative macroeconomic event)
- `correlation_strength`: Dynamically adjusted between 0.3-0.8 based on volatility

These should be made configurable in future versions.