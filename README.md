# Alphagora
Alphagora is a framework that leverages generative AI to analyze market, economic, and sentiment data across equities, commodities, metals, FX, and ETFs. It delivers research-backed opinions and investment recommendations, applying industry and academic best practices to identify and exploit market patterns driven by collective sentiment.

## Install Packages
To run this script, you need to make sure of the following steps:

### 📌 Step 1: Make sure Python is installed via Homebrew
`brew install python`

### 📌 Step 2: Create and activate a virtual environment
`python3 -m venv yenv`<br>
`source yenv/bin/activate`

### 📌 Step 3: Install required packages
`pip install yfinance pandas numpy pykalman python-dotenv statsmodels scikit-learn backtrader`

## Google Gemini API
Create an .env in the root of the directory

with the following lines:

<pre>
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL_NAME=gemini-2.5-pro
</pre>

## AI Custom Prompts

For the AI Agent prompt, make sure to provide the following variables in the .env file:

<pre>
TARGET_PRICE="[prompt] {ticker_str} {trade_direction} {entry_price} {stop_loss}"

SECTOR_ROTATION_LONG_ONLY_PROMPT="[prompt]"
REGIONAL_ROTATION_LONG_ONLY_PROMPT=[prompt]"
FX_LONG_SHORT_PROMPT="[prompt]"
</pre>

Model [prompt] must contain some of the following information:

- Tickers: {ticker_str},
- Current date: {current_date},
- Region: {region_str},
- Geopolitical: {geopolitical_weight},
- Macroeconomic: {macroeconomic_weight},
- Technical/Sentiment: {technical_sentiment_weight},
- Liquidity: {liquidity_weight},
- Earnings: {earnings_weight},
- Business Cycle: {business_cycle_weight},
- Sentiment Surveys: {sentiment_surveys_weight}


Model [prompt] should return the following JSON as well:

<pre>
{
  "title": "string, concise journalist-ready title (~12 words, explicit drivers of price)",
  "market_outlook_narrative": [
    "string, first paragraph: key catalysts, events, indicators, or data driving market movements",
    "string, second paragraph: how these factors impact pricing, provide support or weigh on market",
    "string, third paragraph: forward-looking view, upcoming events, indicators, outlook"
  ],
  "recommendations": [
    {
      "ticker": "string, ETF ticker from most suitable to least suitable for investment",
      "trade_direction": "string, either 'long' or 'short' based on bull_bear_score",
      "bull_bear_score": "integer, 1-10 reflecting bullish/bearish strength"
    },
    {
      "ticker": "string",
      "trade_direction": "string",
      "bull_bear_score": "integer"
    }
  ]
}
</pre>