# Alphagora
Alphagora is a framework that leverages generative AI to analyze a wide spectrum of information, including market data, economic indicators, and sentiment signals from news and social media. By integrating these diverse inputs across asset classes — from equities and commodities to metals, FX, and ETFs — it identifies trends and generates precise investment and trading recommendations, with the goal of achieving absolute returns. Built on the belief that collective sentiment drives market direction, we are developing a framework that incorporates industry and academic best practices from our research to identify and capitalize on these patterns.

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