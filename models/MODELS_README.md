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