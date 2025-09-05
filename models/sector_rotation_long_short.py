"""
Project:     Alphagora Trading System
File:        sector_rotation_long_short.py
Author:      Daiviet Huynh
Created:     2025-09-05
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Sector rotation ETF long/short model.
"""

import sys
import os
import json
from dotenv import load_dotenv

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Load environment variables
load_dotenv()

from _config import SECTOR_ETFS, WEIGHTS_PERCENT
from genAI.ai_prompt import get_gen_ai_response
from helpers import add_stop_loss_to_recommendations, add_entry_price_to_recommendations

# Load AI model prompt from environment variables
SECTOR_ROTATION_LONG_SHORT_PROMPT = os.getenv("SECTOR_ROTATION_LONG_SHORT_PROMPT")

# Format the prompt with the necessary variables
if SECTOR_ROTATION_LONG_SHORT_PROMPT:
    # Create a comma-separated string of tickers for the prompt
    tickers_str = ", ".join(SECTOR_ETFS) if SECTOR_ETFS else "No tickers provided"
    
    # Format the prompt with both tickers_str and weights
    SECTOR_ROTATION_LONG_SHORT_PROMPT = SECTOR_ROTATION_LONG_SHORT_PROMPT.format(
        tickers_str=tickers_str,
        geopolitical_weight=WEIGHTS_PERCENT['Geopolitical'],
        macroeconomic_weight=WEIGHTS_PERCENT['Macroeconomics'],
        technical_sentiment_weight=WEIGHTS_PERCENT['Technical_Sentiment'],
        liquidity_weight=WEIGHTS_PERCENT['Liquidity'],
        earnings_weight=WEIGHTS_PERCENT['Earnings'],
        business_cycle_weight=WEIGHTS_PERCENT['Business_Cycle'],
        sentiment_surveys_weight=WEIGHTS_PERCENT['Sentiment_Surveys']
    )


def run_sector_rotation_model():
    
    try:
        # Get AI recommendations with None as prompt since it's pre-formatted
        result = get_gen_ai_response(SECTOR_ETFS, "sector rotation long/short", SECTOR_ROTATION_LONG_SHORT_PROMPT)
        
        # Try to parse the result as JSON
        try:
            # Remove any markdown code block markers if present
            if result.startswith("```json"):
                result = result[7:]
            if result.endswith("```"):
                result = result[:-3]
                
            recommendations = json.loads(result)

            print(result)
            
            # Add stop loss prices to recommendations
            # Check if the AI returned recommendations in the expected format
            if 'recommendations' in recommendations:
                # Rename 'recommendations' to 'sector_recommendations' for consistency
                recommendations['sector_recommendations'] = recommendations.pop('recommendations')
            
            recommendations = add_stop_loss_to_recommendations(recommendations)
            recommendations = add_entry_price_to_recommendations(recommendations)
                        
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
            
            # Display sector recommendations
            if 'sector_recommendations' in recommendations:
                print("=== Sector Recommendations ===")
                for sector in recommendations['sector_recommendations']:
                    ticker = sector.get('ticker', 'N/A')
                    direction = sector.get('trade_direction', 'N/A')
                    score = sector.get('bull_bear_score', 'N/A')
                    stop_loss = sector.get('stop_loss', 'N/A')
                    entry_price = sector.get('entry_price', 'N/A')
                    print(f"- {ticker}: {direction.upper()} (Score: {score}/10, Entry Price: {entry_price}, Stop Loss: {stop_loss})")
        except json.JSONDecodeError:
            # If JSON parsing fails, display the raw result
            print("\n=== AI Analysis ===")
            print(result)
            
    except Exception as e:
        print(f"Error running sector rotation model: {e}")


# Testing the function
if __name__ == "__main__":
    run_sector_rotation_model()