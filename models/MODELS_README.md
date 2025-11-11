# Models Documentation

This document provides an overview of the Python modules in the `models` directory.

## hcb.py - High Conviction Backtest Model

### Overview
The `hcb.py` module provides functionality to fetch and analyze high conviction equity insights.

### Key Functions

#### `get_high_conviction_buys()`
- **Purpose**: Fetches insights from last week with positive sentiment and high conviction
- **Criteria**:
  - Created within last 7 days
  - Positive sentiment score
  - High conviction level (≥0.7)
- **Returns**: List of insight documents sorted by conviction (descending) then sentiment score
- **Database Operations**:
  - Updates importance level (3) for matching insights
  - Adds ">high conviction buy ↗" tag
  - Unflags pipeline task for subsequent runs

#### `unflag_hcb_pipeline_task()`
- **Purpose**: Unflags the HCB pipeline task_completed check in MongoDB
- **Behavior**:
  - Checks for pending ticker documents
  - Unflags pipeline task if pending documents exist
- **Error Handling**: Logs database errors but continues execution

### Configuration Parameters
```python
tag_string = ">high conviction buy ↗"
min_sentiment_score = 0
conviction_threshold = 0.7
importance_level = 3
```

---

## trending.py - Trending Instruments Analysis

### Overview
Identifies trending financial instruments using AI responses across three asset classes:
- EQ (Equities)
- CR (Cryptocurrencies)
- FX (Forex)

### Key Functions

#### Core Functions
- `get_trending_instruments(asset_class, ...)`
  - **Main entry point** for trending analysis
  - **Parameters**:
    - `asset_class`: "EQ", "CR", or "FX"
    - `model_strategy`: Gemini model strategy (default "Pro")
    - `batch_mode`: Batch processing flag (default True)
  - **Process**:
    1. Checks pending ticker documents
    2. Selects AI prompt based on asset class
    3. Gets AI response
    4. Processes JSON response
    5. Updates database with new tickers
    6. Manages pipeline tracking

#### Support Functions
- `unflag_trending_pipeline_task()`
  - Resets pipeline task completion flags
- `update_ticker_recurrence(instruments)`
  - Updates ticker documents' recurrence status
- `create_new_ticker_documents()`
  - Creates ticker docs for new trending instruments
- `update_insights_importance_for_trending()`
  - Sets importance=3 and adds ">trending ⇧" tag

### Asset Class Handlers
- `run_trending_analysis_equity()`
- `run_trending_analysis_crypto()`
- `run_trending_analysis_forex()`

### Configuration
Uses encrypted prompts from `_config.py`:
- `EQ_EQUITY_TRENDING_PROMPT`
- `CR_CRYPTO_TRENDING_PROMPT`
- `FX_FOREX_TRENDING_PROMPT`

---

## Dependencies
- MongoDB database connection via `DatabaseManager`
- Environment variables for configuration
- Helper functions from `helpers.py`
- AI integration through `genAI.ai_prompt`

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
  4. Processes equity-specific charts
  5. Updates database with analysis results
- **Output**: Returns dictionary with description and sector fields
- **Database Operations**:
  - Updates ticker document with:
    - Description and sector
    - Financial health grades (cashflow, profit, etc.)
    - Performance metrics
    - Interactive charts (growth, financial health, etc.)

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
  - `decimal_digits`: Precision for price calculations
  - `batch_mode`: Suppresses console output when True

#### Features
- Dynamic stop loss/target price calculation
- Sentiment score generation
- Region-specific analysis
- Simulation data processing

### Configuration
Uses encrypted prompts from `_config.py`:
- `FX_LONG_SHORT_PROMPT`
- `FX_FACTORS_PROMPT`
- `FACTOR_WEIGHTS`

---

## holistic.py - Holistic Market Model

### Overview
Provides comprehensive market analysis across multiple asset classes with integrated factor weighting and simulation capabilities.

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

#### Advanced Features
- JSON repair capabilities for AI responses
- Conviction scoring system
- Multi-factor weighting (geopolitical, macroeconomic, etc.)
- Batch processing support

### Configuration
Uses encrypted prompts from `_config.py`:
- `HOLISTIC_MARKET_PROMPT`
- `FACTOR_WEIGHTS`

---

## Dependencies
- MongoDB database connection via `DatabaseManager`
- Environment variables for configuration
- Helper functions from `helpers.py`
- AI integration through `genAI.ai_prompt`
- Data processing from `data.price`
- Simulation handling from `models.simulation`