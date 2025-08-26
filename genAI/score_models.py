import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

# Step 1: Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # Set your Gemini key in environment variable
print(os.getenv("GEMINI_API_KEY"))  # Debug: Print the API key to ensure it's loaded correctly

# Step 2: Set up the model
model = genai.GenerativeModel("gemini-pro")

# Step 3: Define the prompt to Gemini
prompt = """
You are a financial analyst. Based on this week's market events, provide a bull/bear sentiment score from 1 (very bearish) to 10 (very bullish). 

Assess the following categories:
1. Macroeconomic indicators (U.S./global CPI, GDP, PMI, jobs, Fed policy)
2. Corporate earnings and guidance
3. Market liquidity and positioning (flows, Fed balance sheet, VIX, CFTC)
4. Geopolitical and policy risks (war, elections, trade)
5. Sentiment and technicals (breadth, put/call, surveys, media tone)

Give a short reasoning for each category and a final overall score.

Respond in the following JSON format:
{
  "macro_score": 0,
  "macro_comment": "...",
  "earnings_score": 0,
  "earnings_comment": "...",
  "liquidity_score": 0,
  "liquidity_comment": "...",
  "geopolitics_score": 0,
  "geopolitics_comment": "...",
  "sentiment_score": 0,
  "sentiment_comment": "...",
  "overall_score": 0,
  "overall_comment": "..."
}
"""

# Step 4: Run prompt
response = model.generate_content(prompt)

# Step 5: Output result
print("\n=== Bull/Bear Market Sentiment Score ===")
print(response.text)