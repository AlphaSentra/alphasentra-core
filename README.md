# Alphagora
Alphagora is a framework leveraging generative AI to analyze market, economic, and sentiment data across equities, commodities, metals, FX, and ETFs. It delivers research-backed investment and trading recommendations, applying industry and academic best practices to exploit market patterns driven by collective sentiment.

## Install Packages
To run this script, you need to make sure of the following steps:

### 📌 Step 1: Make sure Python is installed via Homebrew
`brew install python`

### 📌 Step 2: Create and activate a virtual environment
`python3 -m venv yenv`<br>
`source yenv/bin/activate`

### 📌 Step 3: Install required packages
`pip install yfinance pandas numpy pykalman python-dotenv statsmodels scikit-learn`

## Google Gemini API
Create an .env in the root of the directory

with the following lines:

<pre>
GEMINI_API_KEY=your_actual_gemini_api_key
AI_MODEL_PROMPTS={"sector_rotation_long_only": "Agent Prompt with {tickers_str}", "regional_rotation_long_only": "Agent Prompt with {tickers_str}", "fx_long_short": "Agent Prompt with {tickers_str}", "default": "Agent prompt with {tickers_str}"}
</pre>

For the AI Agent prompt, make sure to provide the variable {ticker_str} and set the return value of the prompt response in JSON format.