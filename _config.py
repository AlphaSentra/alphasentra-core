"""
Project:     Alphagora Trading System
File:        _config.py
Author:      Daiviet Huynh
Created:     2025-08-26
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Store all the variables for configuration for all the models and systems.
"""

# Momentum Engine Configuration
MOMENTUM_ETFS = ['XLC', 'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU']
MOMENTUM_ALLOCATION_MIN = 0.50  # 50%
MOMENTUM_ALLOCATION_MAX = 0.75  # 75%

# Mean Reversion Engine Configuration
PAIRS = {
    'VXX_vs_SVXY': ('VXX', 'SVXY'),
}
PAIRS_LOOKBACK_YEARS = 1
ENABLE_COINTEGRATION_TEST = False  # Set to False to skip cointegration check

# AI Model Prompts Configuration
AI_MODEL_PROMPTS = {
    "sector_rotation_long_only": """
        Execute the following multi-step process to determine a 20-day forward investment strategy for U.S. equity sectors with latest data as of today:
        1.  **Analyze Core Indicators:** For the upcoming 20-day period, analyze the seven key indicator categories: Macroeconomic Indicators, Earnings & Corporate Guidance, Market Liquidity & Flows, Geopolitical & Event Risk, Technical & Sentiment Indicators, Sentiment Surveys & News Tone, and Business Cycle.
        2.  **Score Each Category:** Assign a score from 10 (most bullish) to 1 (most bearish) to each of the seven categories based on your analysis of current data and forward-looking expectations.
        3.  **Calculate Weighted Score:** Apply the following weighting model to the scores from Step 2 to calculate a raw weighted score: Geopolitical (30%), Macroeconomic (20%), Technical/Sentiment (20%), Liquidity (10%), Earnings (10%), Business Cycle (5%), Sentiment Surveys (5%).
        4.  **Synthesize Narratives:** Formulate a coherent "Bull Case" and "Bear Case" for the market over the next 20 days, drawing from your indicator analysis.
        5.  **Determine Final Score:** Based on the relative strength of the bull vs. bear narratives and the raw weighted score, determine a final overall forward bull/bear score from 1 to 10.
        6.  **But also in the selection consideration consider also sectors that have been performing well in the last 3 months, as they may have momentum to continue performing well.
        7.  **Recommend Sectors:** Based on your final score and the key drivers identified in your analysis, identify five sector ETFs suitable for investment from the following list: {tickers_str}. Provide a detailed rationale for each selection, explaining how it aligns with your market outlook.
        """,
        
    "regional_rotation_long_only": """
        Execute the following multi-step process to determine a 20-day forward investment strategy for regional ETFs with latest data as of today:
        1.  **Analyze Core Indicators:** For the upcoming 20-day period, analyze key indicator categories: Macroeconomic Indicators, Currency Movements, Geopolitical Events, Technical & Sentiment Indicators, and Regional Economic Data.
        2.  **Score Each Region:** Assign a score from 10 (most bullish) to 1 (most bearish) to each region based on your analysis of current data and forward-looking expectations.
        3.  **Synthesize Narratives:** Formulate a coherent "Bull Case" and "Bear Case" for each region over the next 20 days.
        4.  **Determine Final Rankings:** Rank the regions from most to least favorable for investment.
        5.  **Recommend Regions:** Based on your analysis, identify the top 3 regions for long-only investment from the following list: {tickers_str}. Provide a detailed rationale for each selection.
        """,
        
    "fx_long_short": """
        Execute the following multi-step process to determine a 20-day forward FX trading strategy with latest data as of today:
        1.  **Analyze Core Indicators:** For the upcoming 20-day period, analyze key indicator categories: Interest Rate Differentials, Inflation Rates, GDP Growth, Political Stability, Central Bank Policies, and Technical Analysis.
        2.  **Score Each Currency Pair:** Assign a score from 10 (most bullish for the base currency) to 1 (most bearish for the base currency) to each pair based on your analysis.
        3.  **Identify Opportunities:** Determine which currencies are overvalued and which are undervalued.
        4.  **Synthesize Narratives:** Formulate a coherent "Bull Case" and "Bear Case" for each currency pair over the next 20 days.
        5.  **Recommend Trades:** Based on your analysis, identify up to 3 pairs for long positions and up to 3 pairs for short positions from the following list: {tickers_str}. Provide a detailed rationale for each recommendation.
        """,
        
    "default": """
        Execute the following multi-step process to determine a 20-day forward investment strategy with latest data as of today:
        1.  **Analyze Core Indicators:** For the upcoming 20-day period, analyze relevant key indicator categories for the assets provided.
        2.  **Score Each Asset:** Assign a score from 10 (most bullish) to 1 (most bearish) to each asset based on your analysis.
        3.  **Synthesize Narratives:** Formulate a coherent "Bull Case" and "Bear Case" for each asset over the next 20 days.
        4.  **Recommend Investments:** Based on your analysis, provide investment recommendations for the following assets: {tickers_str}.
        """
}