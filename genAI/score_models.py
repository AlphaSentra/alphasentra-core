import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

# Step 1: Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # Set your Gemini key in environment variable

# Step 2: List available models
print("Available models:")
for model_info in genai.list_models():
    if "generateContent" in model_info.supported_generation_methods:
        print(f"- {model_info.name}: {model_info.display_name}")

# Step 3: Set up the Gemini 2.5 Pro model
model = genai.GenerativeModel("gemini-2.5-flash")

# Step 4: AI prompt
prompt = """
Execute the following multi-step process to determine a 20-day forward investment strategy for U.S. equity sectors with latest data as of today:
1.  **Analyze Core Indicators:** For the upcoming 20-day period, analyze the seven key indicator categories: Macroeconomic Indicators, Earnings & Corporate Guidance, Market Liquidity & Flows, Geopolitical & Event Risk, Technical & Sentiment Indicators, Sentiment Surveys & News Tone, and Business Cycle.
2.  **Score Each Category:** Assign a score from 10 (most bullish) to 1 (most bearish) to each of the seven categories based on your analysis of current data and forward-looking expectations.
3.  **Calculate Weighted Score:** Apply the following weighting model to the scores from Step 2 to calculate a raw weighted score: Geopolitical (30%), Macroeconomic (20%), Technical/Sentiment (20%), Liquidity (10%), Earnings (10%), Business Cycle (5%), Sentiment Surveys (5%).
4.  **Synthesize Narratives:** Formulate a coherent "Bull Case" and "Bear Case" for the market over the next 20 days, drawing from your indicator analysis.
5.  **Determine Final Score:** Based on the relative strength of the bull vs. bear narratives and the raw weighted score, determine a final overall forward bull/bear score from 1 to 10.
6.  **But also in the selection consideration consider also sectors that have been performing well in the last 3 months, as they may have momentum to continue performing well.
7.  **Recommend Sectors:** Based on your final score and the key drivers identified in your analysis, identify five sector ETFs suitable for investment from the following list: XLC, XLY, XLP, XLE, XLF, XLV, XLI, XLB, XLRE, XLK, XLU. Provide a detailed rationale for each selection, explaining how it aligns with your market outlook.
"""

# Step 5: Run prompt
print("Sending test prompt to Gemini API...")
response = model.generate_content(prompt)

# Step 6: Output result
print("\n=== Test Response ===")
print(response.text)
