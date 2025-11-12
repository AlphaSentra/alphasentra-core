# Market Simulation Documentation

This document details the agent-based market simulation system implemented in `simulation.py`.

## Overview
The simulation system models financial markets through two key phases:
1. **Agent-Based Market Simulation**: Models investor behavior and price discovery
2. **Stochastic Data Augmentation**: Adds realistic noise and synthetic data points

Key components:
- `Agent`: Represents individual investors with behavioral parameters
- `MarketSimulator`: Manages market dynamics and price formation
- `process_simulation_data()`: Main pipeline function coordinating both phases

## Core Functions

### `process_simulation_data(raw_simulation_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]`
Main pipeline function that processes raw investor data through:
1. Market simulation phase
2. Stochastic augmentation phase

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

**Note:** Current implementation uses example parameters for market simulation that should be parameterized in future versions.

## Core Functions

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

**Key Parameters:**
- `simulation_data`: Simulation results from market phase
- `num_additional_points`: Synthetic points to generate (default: 1000)
- Noise scaling parameters for different processing stages

## Core Classes

### `Agent` Class
Represents an investor in the market simulation.

**Key Attributes:**
- `conviction`: Rational assessment (-1.0 to 1.0)
- `sentiment`: Emotional bias (-1.0 to 1.0)
- `position`: Current market position (BULLISH/BEARISH/NEUTRAL)
- `risk_aversion`: Willingness to take risks
- `recency_bias`: Tendency to follow recent trends

**Key Methods:**
- `calculate_pnl()`: Updates profit/loss
- `execute_trade()`: Determines new position
- `get_state()`: Returns current agent state

### `MarketSimulator` Class
Models market dynamics including:
- Price discovery through investor interactions
- Aggregate sentiment calculation
- Net order imbalance computation

**Key Methods:**
- `run_time_step()`: Executes one market time step with:
  - Price correction based on order imbalance
  - Agent conviction/sentiment updates
  - Trade execution

## Academic Constraints
1. Sentiment cannot exceed conviction (|S| ≤ |C|)
2. Price changes depend on net order imbalance (γ=0.5 in current implementation)
3. Agent behavior follows ABM principles from financial literature
4. Stochastic noise follows Gaussian distributions

## Example Parameters
Current market simulation uses:
- `public_info=0.6` (positive market signal)
- `macro_shock=-0.1` (negative macroeconomic event)

These should be made configurable in future versions.

## Academic Constraints
1. Sentiment cannot exceed conviction (|S| ≤ |C|)
2. Price changes depend on net order imbalance
3. Agent behavior follows ABM principles from literature