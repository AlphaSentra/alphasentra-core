# Alphagora
![screenshot](img/banner.png)

Alphagora is an agentic AI that leverages generative intelligence to convert market, economic, and sentiment data into insights, opinions, and recommendations. It autonomously tests, adapts, and executes strategies to capture patterns driven by collective sentiment.

## Install Packages
To run this script, you need to make sure of the requirements:

`pip install -r requirements.txt`

## Google Gemini API
Create an .env in the root of the directory

with the following lines:

<pre>
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_DEFAULT=gemini-2.5-pro
GEMINI_FLASH_MODEL=gemini-2.5-pro
GEMINI_PRO_MODEL=gemini-2.5-pro
ENCRYPTION_SECRET=provide_the_secret
</pre>

1. **Gemini API Key**: Provide your Gemini API key using the ```GEMINI_API_KEY``` constant from [Google AI Studio](https://aistudio.google.com). 
2. **Gemini Model**: You can select which Gemini model to use. By default, we are using gemini-2.5-pro: ```GEMINI_FLASH_MODEL=gemini-2.5-pro```.
3. **Encryption**: The ```ENCRYPTION_SECRET``` constant is used as the key for encrypting and decrypting our proprietary prompt designs.

## AI Prompt Variables and Output

**Model [prompt] contain some of the following variables:**

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
- Factcheck_result: `{last_factcheck_result}`
- Unchecked Recommendations JSON: `{json.dumps(last_inaccurate_recommendations, indent=2)}`

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