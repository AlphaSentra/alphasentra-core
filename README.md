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

SECTOR_ROTATION_LONG_ONLY_PROMPT="Geopolitical ({geopolitical_weight}), Macroeconomic ({macroeconomic_weight}), Technical/Sentiment ({technical_sentiment_weight}), Liquidity ({liquidity_weight}), Earnings ({earnings_weight}), Business Cycle ({business_cycle_weight}), Sentiment Surveys ({sentiment_surveys_weight}). {tickers_str}."

REGIONAL_ROTATION_LONG_ONLY_PROMPT="Geopolitical ({geopolitical_weight}), Macroeconomic ({macroeconomic_weight}), Technical/Sentiment ({technical_sentiment_weight}), Liquidity ({liquidity_weight}), Earnings ({earnings_weight}), Business Cycle ({business_cycle_weight}), Sentiment Surveys ({sentiment_surveys_weight}). {tickers_str}."

FX_LONG_SHORT_PROMPT="Geopolitical ({geopolitical_weight}), Macroeconomic ({macroeconomic_weight}), Technical/Sentiment ({technical_sentiment_weight}), Liquidity ({liquidity_weight}), Earnings ({earnings_weight}), Business Cycle ({business_cycle_weight}), Sentiment Surveys ({sentiment_surveys_weight}). {tickers_str}."

DEFAULT_PROMPT="Geopolitical ({geopolitical_weight}), Macroeconomic ({macroeconomic_weight}), Technical/Sentiment ({technical_sentiment_weight}), Liquidity ({liquidity_weight}), Earnings ({earnings_weight}), Business Cycle ({business_cycle_weight}), Sentiment Surveys ({sentiment_surveys_weight}). {tickers_str}."
</pre>

For the AI Agent prompt, make sure to provide the following variables:

- Tickers: {ticker_str},
- Geopolitical ({geopolitical_weight}),
- Macroeconomic ({macroeconomic_weight}),
- Technical/Sentiment ({technical_sentiment_weight}),
- Liquidity ({liquidity_weight}),
- Earnings ({earnings_weight}),
- Business Cycle ({business_cycle_weight}),
- Sentiment Surveys ({sentiment_surveys_weight})


and set the return value of the prompt response in JSON format.