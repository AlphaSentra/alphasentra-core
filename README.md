# Alphagora
![screenshot](img/banner.png)

Alphagora is an agentic AI that leverages generative intelligence to convert market, economic, and sentiment data into insights, opinions, and recommendations. It autonomously tests, adapts, and executes strategies to capture patterns driven by collective sentiment.

## Install Packages
To run this script, you need to make sure of the following steps:

### 📌 Step 1: Make sure Python is installed via Homebrew
`brew install python`

### 📌 Step 2: Create and activate a virtual environment
`python3 -m venv yenv`<br>
`source yenv/bin/activate`

### 📌 Step 3: Install required packages
`pip install yfinance pandas numpy pykalman python-dotenv statsmodels scikit-learn backtrader cryptography`

## Google Gemini API
Create an .env in the root of the directory

with the following lines:

<pre>
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL_NAME=gemini-2.5-pro
</pre>

You can select which Gemini model to use. By default, we are using gemini-2.5-pro. The following model is also available:
- gemini-2.5-flash – optimized for speed and efficiency

## AI Prompt Instructions

For the AI Agent prompt, make sure to provide the following variables in the .env file:

<pre>
TARGET_PRICE="[prompt] {ticker_str} {trade_direction} {entry_price} {stop_loss}"
FACTOR_WEIGHTS="[prompt]"
FACTCHECK_AI_RESPONSE="Factcheck the following statements as of latest data: '{market_outlook_narrative_str}':
1. **Identify statements:** Make sure that statements are not misleading, incorrect, or lack sufficient evidence from data that are available as of {current_date}.
2. **Return a JSON object**: JSON with the following structure:
2.1 Key [factcheck] with value as string 'accurate' if the response is accurate, or 'inaccurate' if any issues are found, even with one issue it would be considered 'inaccurate'.
2.2 Key [issues] as an array of strings, where each string describes a specific issue found in the response and based on what date. If no issues are found, return an empty array for [issues]."

SECTOR_ROTATION_LONG_ONLY_PROMPT="[prompt]"
REGIONAL_ROTATION_LONG_SHORT_PROMPT=[prompt]"
FX_LONG_SHORT_PROMPT="[prompt]"
</pre>

**Model [prompt] must contain some of the following information:**

- Tickers: `{ticker_str}`,
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


**Model [prompt] should return the following JSON as well:**

```
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
```
To return the JSON, include the following line in the prompt:
<pre>
**JSON Output format:** Return your final recommendations in the following JSON format only, using this exact structure: [title] as a string, [market_outlook_narrative] as an array of strings, and [recommendations] as an array of objects, where each object includes [ticker] as a string, [trade_direction] as a string, and [bull_bear_score] as an integer.
</pre>

The JSON output will be interpreted by the Alphagora engine, which will then process, transform, and securely store the data for further analysis and use within the system.