"""
Project:     Alphagora Trading System
File:        regional_rotation_long_short.py
Author:      Daiviet Huynh
Created:     2025-09-05
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Regional rotation ETF long/short model.
"""

import sys
import os
import json
import datetime
from dotenv import load_dotenv

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Load environment variables
load_dotenv()

from _config import REGIONAL_ETFS, WEIGHTS_PERCENT, REGIONAL_REGIONS
from genAI.ai_prompt import get_gen_ai_response
from helpers import add_trade_levels_to_recommendations, add_entry_price_to_recommendations

# Load AI model prompt from environment variables
REGIONAL_ROTATION_LONG_ONLY_PROMPT = os.getenv("REGIONAL_ROTATION_LONG_ONLY_PROMPT")

# Format the prompt with the necessary variables
if REGIONAL_ROTATION_LONG_ONLY_PROMPT:
    # Create a comma-separated string of tickers for the prompt
    tickers_str = ", ".join(REGIONAL_ETFS) if REGIONAL_ETFS else "No tickers provided"
    regional_regions_str = ", ".join(REGIONAL_REGIONS) if REGIONAL_REGIONS else "No regions provided"

    # Create current date in the format "September 6, 2025"
    current_date = datetime.datetime.now().strftime("%B %d, %Y")
    
    # Format the prompt with both tickers_str and weights
    REGIONAL_ROTATION_LONG_ONLY_PROMPT = REGIONAL_ROTATION_LONG_ONLY_PROMPT.format(
        tickers_str=tickers_str,
        current_date=current_date,
        regional_regions_str=regional_regions_str,
        geopolitical_weight=WEIGHTS_PERCENT['Geopolitical'],
        macroeconomic_weight=WEIGHTS_PERCENT['Macroeconomics'],
        technical_sentiment_weight=WEIGHTS_PERCENT['Technical_Sentiment'],
        liquidity_weight=WEIGHTS_PERCENT['Liquidity'],
        earnings_weight=WEIGHTS_PERCENT['Earnings'],
        business_cycle_weight=WEIGHTS_PERCENT['Business_Cycle'],
        sentiment_surveys_weight=WEIGHTS_PERCENT['Sentiment_Surveys'],
    )


def run_regional_rotation_model():
    """
    Run the regional rotation long/short model.
    """
    
    try:
        # Get AI recommendations with None as prompt since it's pre-formatted
        result = get_gen_ai_response(REGIONAL_ETFS, "regional rotation long/short", REGIONAL_ROTATION_LONG_ONLY_PROMPT)
        
        # Try to parse the result as JSON
        try:
            # Remove any markdown code block markers if present
            if result.startswith("```json"):
                result = result[7:]
            if result.endswith("```"):
                result = result[:-3]
            # Parse JSON
            recommendations = json.loads(result)

            # Add stop loss and target prices to recommendations
            recommendations = add_trade_levels_to_recommendations(recommendations)
            # Add entry prices to recommendations
            recommendations = add_entry_price_to_recommendations(recommendations)

            #Display Model Output header
            print("\n" + "="*100)
            print("Regional Rotation Long/Short Model")
            print("="*100)
                        
            # Display market outlook
            if 'market_outlook_narrative' in recommendations:
                print("\n=== Market Outlook ===")
                print()
                # Display title if available
                if 'title' in recommendations:
                    print(f"{recommendations['title']}")
                    print()

                for paragraph in recommendations['market_outlook_narrative']:
                    print(paragraph)
                    print()
            
            # Display recommendations
            # After processing, the recommendations are under 'recommendations' key
            if 'recommendations' in recommendations:
                print("=== Recommendations ===")
                print()
                for trade in recommendations['recommendations']:
                    # Extract required fields with better default values
                    ticker = trade.get('ticker', 'UNKNOWN')
                    direction = trade.get('trade_direction', 'NONE')
                    score = trade.get('bull_bear_score', 0)
                    probability = trade.get('probability', 'N/A')
                    
                    # For stop_loss, target_price, and entry_price, use 'N/A' as default but validate they exist
                    stop_loss = trade.get('stop_loss', 'N/A')
                    target_price = trade.get('target_price', 'N/A')
                    entry_price = trade.get('entry_price', 'N/A')
                    
                    # Validate that required fields are present
                    if ticker == 'UNKNOWN':
                        print("- Warning: Missing ticker information")
                        continue
                    
                    if direction == 'NONE':
                        print(f"- {ticker}: Warning - Missing trade direction")
                        direction = 'HOLD'  # Default to HOLD if direction is missing
                    
                    # Ensure score is within valid range
                    if not isinstance(score, int) or score < 1 or score > 10:
                        print(f"- {ticker}: Warning - Invalid score ({score}), setting to 5")
                        score = 5
                    
                    # Validate stop_loss and entry_price
                    if stop_loss == 'N/A':
                        print(f"- {ticker}: Warning - Missing stop loss data")
                    
                    if target_price == 'N/A':
                        print(f"- {ticker}: Warning - Missing target price data")
                    
                    if entry_price == 'N/A':
                        print(f"- {ticker}: Warning - Missing entry price data")
                    
                    print(f"- {ticker}: {direction.upper()} (Score: {score}/10, Probability: {probability}, Entry Price: {entry_price}, Stop Loss: {stop_loss}, Target Price: {target_price})")
        except json.JSONDecodeError:
            # If JSON parsing fails, display the raw result
            print("\n=== AI Analysis ===")
            print(result)
            
    except Exception as e:
        print(f"Error running regional rotation model: {e}")


# Testing the function
if __name__ == "__main__":
    run_regional_rotation_model()