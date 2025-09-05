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

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from _config import SECTOR_ETFS
from genAI.ai_prompt import get_gen_ai_response


def run_sector_rotation_model():
    """
    Run the sector rotation long/short Model using AI analysis.
    """
    print("\n=== Sector Rotation Long/Short Model ===")
    print("Analyzing sector ETFs for long/short opportunities...")
    
    try:
        # Get AI recommendations
        result = get_gen_ai_response(SECTOR_ETFS, "sector_rotation_long_short")
        
        # Try to parse the result as JSON
        try:
            # Remove any markdown code block markers if present
            if result.startswith("```json"):
                result = result[7:]
            if result.endswith("```"):
                result = result[:-3]
                
            recommendations = json.loads(result)
            
            # Display title if available
            if 'title' in recommendations:
                print(f"\n=== {recommendations['title']} ===")
            
            # Display market outlook
            if 'market_outlook_narrative' in recommendations:
                print("\n=== Market Outlook ===")
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
                    print(f"- {ticker}: {direction.upper()} (Score: {score}/10)")
        except json.JSONDecodeError:
            # If JSON parsing fails, display the raw result
            print("\n=== AI Analysis ===")
            print(result)
            
    except Exception as e:
        print(f"Error running sector rotation model: {e}")


# Testing the function
if __name__ == "__main__":
    run_sector_rotation_model()