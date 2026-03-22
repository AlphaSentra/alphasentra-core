# AlphaSentra
![screenshot](img/banner.png)

AlphaSentra is an agentic AI that leverages generative intelligence to convert market, economic, and sentiment data into insights, opinions, and recommendations. It autonomously tests, adapts, and executes strategies to capture patterns driven by collective sentiment.

## Install Packages
To run this script, you need to make sure of the requirements:

`pip install -r requirements.txt`


## Usage

Run the application interactively:
```bash
python main.py
```

Or run in batch processing mode directly:
```bash
python main.py -batch
```

Reset all datasets:
```bash
python main.py -reset
```

Enforce database size limit (optional MB value):
```bash
python main.py -dblimit [MB]
```

The `-batch` flag executes `run_batch_processing()` without showing the menu interface.
The `-reset` flag executes `reset_all()` to reset document statuses and clean up one-time records.
The `-dblimit` flag executes `purge_insights_collection()` to delete all documents in the insights collection.

## Environment Variables
Create a `.env` file in the root of the project. This file should include sensitive configuration such as database connections, API keys, and the encryption secret.

### Database Configuration
Add the following database settings to your `.env`:
If `USE_MONGODB_SRV` is `true` the connection string `MONGODB_SRV` will be used, otherwise `MONGODB_HOST`, `MONGO_PORT`, `MONGODB_DATABASE`, `MONGODB_USERNAME`, `MONGODB_PASSWORD`, and `MONGODB_AUTH_SOURCE` will be used.

<pre>
USE_MONGODB_SRV=true
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=alphasentra
MONGODB_USERNAME=username
MONGODB_PASSWORD=password
MONGODB_AUTH_SOURCE=admin
MONGODB_SRV='mongodb+srv://alphasentra_db_user:{db_password}@cluster0.9x59erc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
</pre>

### Google Gemini API
Include your Google Gemini API credentials and encryption secret:

<pre>
GEMINI_API_KEY='gemini_api_key_1, gemini_api_key_2'
GEMINI_DEFAULT=gemini-2.5-pro
GEMINI_FLASH_MODEL=gemini-2.5-flash
GEMINI_FLASH_LITE_MODEL=gemini-2.5-flash-lite
GEMINI_PRO_MODEL=gemini-2.5-pro
ENCRYPTION_SECRET=encryption-secret
</pre>

1. **Gemini API Key**: Provide your Gemini API key using the ```GEMINI_API_KEY``` constant from [Google AI Studio](https://aistudio.google.com). 
2. **Gemini Model**: You can select which Gemini model to use. By default, we are using gemini-2.5-pro: ```GEMINI_PRO_MODEL=gemini-2.5-pro```.
3. **Encryption**: The ```ENCRYPTION_SECRET``` constant is used as the key for encrypting and decrypting our proprietary prompt designs.

Note: To create your own prompt, use the `crypt.py` script to encrypt it with your `ENCRYPTION_SECRET`.

## AI Prompt Variables and Output

### Prompt input variables

**Model [prompt] contain some of the following variables:**

- Tickers: `{ticker_str}`,
- Instrument Name: `{instrument_name}`,
- Current date: `{current_date}`,
- Sector Region: `{sector_region_str}`,
- Regional Region: `{regional_region_str}`,
- FX Region: `{fx_regions_str}`,
- Geopolitical: `{geopolitical_weight}`,
- Macroeconomic: `{macroeconomic_weight}`,
- Technical/Sentiment: `{technical_sentiment_weight}`,
- Liquidity: `{liquidity_weight}`,
- Earnings: `{earnings_weight}`,
- Business Cycle: `{business_cycle_weight}`,
- Sentiment Surveys: `{sentiment_surveys_weight}`

Importance represents how we classify the significance of the information, where 1 is most important and 5 is least important:

1. Thematic market research coverage
2. Major economic data releases
3. Earnings reports and trending topics in the equity market
4. Daily coverage of popular instruments
5. Daily coverage of other or exotic instruments

We categorise asset classes as follows:

- **FX**: Forex
- **EQ**: Equities
- **ETF**: ETFs
- **IX**: Indices
- **CO**: Commodities
- **CR**: Crypto

## System Architecture

The following diagram illustrates the high-level architecture and data flow of AlphaSentra:

```mermaid
graph TD
    subgraph "User Interface"
        UI[main.py / menu.py]
    end

    subgraph "Processing Modes"
        UI -->|Manual Selection| MODELS[Models: Holistic, FX, etc.]
        UI -->|Batch Flag| BATCH_RUN[batch/batch_run.py]
        UI -->|Screening Command| BATCH_SCREEN[batch/batch_screening.py]
    end

    subgraph "Data & Analytics"
        MODELS -->|Fetch Data| YF[yfinance / Price Data]
        MODELS -->|Generate Insights| GEMINI[Google Gemini AI]
        BATCH_RUN -->|Worker Processes| MODELS
        BATCH_SCREEN -->|Pre-filter| DATA_MODULES[Data Metrics / Performance]
    end

    subgraph "Storage"
        MODELS -->|Store Results| MONGO[(MongoDB)]
        BATCH_RUN -->|Poll Tasks| MONGO
        DATA_MODULES -->|Sync Metadata| MONGO
        DB_TOOLS[db/ scripts] -->|Initialize/Manage| MONGO
    end

    GEMINI -.->|Proprietary Prompts| MODELS
    MONGO -.->|Settings & Config| BATCH_RUN
```
