# Models Documentation

This document provides an overview of the Python modules in the `models` directory.

---

## analysis.py - Instrument Analysis Module

### Overview
The `analysis.py` module provides comprehensive instrument analysis capabilities including AI-generated descriptions, sector classification, financial health grades, and performance charts.

### Key Functions

#### `run_analysis(ticker, instrument_name, batch_mode=False)`
- **Purpose**: Performs end-to-end analysis of financial instruments
- **Process**:
  1. Decrypts and formats AI prompt
  2. Gets AI response with instrument details
  3. Parses JSON response with validation
  4. Processes equity-specific charts (only for EQ asset class)
  5. Updates database with analysis results
- **Output**: Returns dictionary with description and sector fields
- **Database Operations**:
  - Updates ticker document with:
    - Description and sector
    - Financial health grades (cashflow, profit, etc.)
    - Performance metrics
    - Interactive charts (growth, financial health, etc.) for equities
    - Dividend yield data

#### Support Functions
- `parse_ai_response(text)`: Extracts JSON from AI response
- `validate_grade(value)`: Ensures valid financial health grades (A-F)
- `process_equity_charts(ticker)`: Generates equity-specific visualizations

### Configuration
Uses encrypted prompt from `_config.py`:
- `INSTRUMENT_DESCRIPTION_PROMPT`

### Chart Types
1. Growth Profitability
2. Financial Health
3. Capital Structure
4. Dividend History

---

## fx_long_short.py - FX Long/Short Model

### Overview
Generates FX trading recommendations based on multi-factor analysis including geopolitical, macroeconomic, and technical factors.

### Key Functions

#### `run_fx_model(tickers, name, fx_regions, ...)`
- **Purpose**: Creates FX trading recommendations
- **Process**:
  1. Gets AI-generated factor weights
  2. Formats analysis prompt with market data
  3. Processes AI response into structured JSON
  4. Enhances recommendations with trading levels
  5. Saves analysis to database
- **Parameters**:
  - `fx_regions`: List of relevant regions (e.g., ['US', 'Eurozone'])
  - `decimal_digits`: Precision for price calculations (default: 4)
  - `batch_mode`: Suppresses console output when True

#### Features
- Dynamic stop loss/target price calculation
- Sentiment score generation
- Region-specific analysis
- Simulation data processing
- Automatic document saving with fallback handling

### Configuration
Uses encrypted prompts from `_config.py`:
- `FX_LONG_SHORT_PROMPT`
- `FX_FACTORS_PROMPT`
- `FACTOR_WEIGHTS`

---

## holistic.py - Holistic Market Model

### Overview
Provides comprehensive market analysis across multiple asset classes with integrated factor weighting.

### Key Functions

#### `run_holistic_market_model(tickers, name, ...)`
- **Purpose**: Generates cross-asset market analysis
- **Process**:
  1. Computes AI-optimized factor weights
  2. Formats holistic analysis prompt
  3. Processes and repairs JSON output
  4. Adds trading parameters and metadata
  5. Persists analysis to database
- **Parameters**:
  - `factors`: Custom factors prompt override
  - `region`: Focus region for analysis
  - `asset_class`: Target asset class filter
  - `tag`: Custom classification tag
  - `decimal_digits`: Precision for price calculations (default: 2)

#### Advanced Features
- JSON repair capabilities for AI responses
- Conviction scoring system
- Multi-factor weighting (geopolitical, macroeconomic, etc.)
- Batch processing support
- Automatic document saving with fallback handling

### Configuration
Uses encrypted prompts from `_config.py`:
- `HOLISTIC_MARKET_PROMPT`
- `FACTOR_WEIGHTS`

---

## montecarlo.py - Monte Carlo Simulation Module

### Overview
Provides Monte Carlo simulation capabilities for trading strategy analysis, offering both automated parameter optimization and custom parameter testing.

### Key Functions

#### `_run_simulation_for_optimization()`
- **Purpose**: Lightweight, performance-optimized simulation for parameter optimization
- **Use Case**: Used internally by `optimize_and_run_monte_carlo()` for rapid testing
- **Features**:
  - Tests numerous parameter combinations quickly
  - Returns only Expected Value (EV) and Win Probability
  - Ideal for finding statistically optimal trading parameters
- **When to Use**: For the default session_id as the optimized model

#### `run_monte_carlo_simulation()`
- **Purpose**: Full, comprehensive simulation with detailed analytics
- **Use Case**: Custom parameter analysis and strategy testing
- **Features**:
  - Executes complete simulation with user-specified parameters
  - Stores full results in database including price paths and percentiles
  - Generates professional commentary and trading advice
  - Returns comprehensive metrics (risk of ruin, maximum drawdown, etc.)
- **When to Use**: When providing custom take-profit (TP), stop-loss (SL), or personalized metrics

#### `optimize_and_run_monte_carlo()`
- **Purpose**: Combines optimization and full simulation
- **Process**:
  1. Uses `_run_simulation_for_optimization()` to find optimal parameters
  2. Executes `run_monte_carlo_simulation()` with optimal parameters
  3. Updates insights with optimal price levels
- **Parameters**:
  - `sessionID`, `ticker`, `initial_price`, `volatility`, `drift`
  - `num_simulations`, `min_rrr` (minimum risk-reward ratio)
  - `strategy` (long/short)

### Usage Guidelines

1. **For Automated Parameter Optimization**: Use `optimize_and_run_monte_carlo()` for default session_id to automatically find optimal trading parameters.

2. **For Custom Parameter Analysis**: Use `run_monte_carlo_simulation()` when you have specific take-profit, stop-loss, or other custom metrics to test.

### Database Output
- Stores simulation results in `trades` collection
- Updates `insights` collection with optimal price levels and simulation summary
- Includes comprehensive metrics, price paths, percentiles, and professional commentary

---

## Dependencies
- MongoDB database connection via `DatabaseManager`
- Environment variables for configuration
- Helper functions from `helpers.py`
- AI integration through `genAI.ai_prompt`
- Data processing from `data.price`
- Simulation handling from `models.simulation`
- Configuration from `_config.py` (MONTE_CARLO_MODEL_* parameters)