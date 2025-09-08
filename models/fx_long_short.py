"""
Project:     Alphagora Trading System
File:        fx_long_short.py
Author:      Daiviet Huynh
Created:     2025-09-07
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
FX long/short model.
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

from _config import WEIGHTS_PERCENT
from genAI.ai_prompt import get_gen_ai_response
from helpers import add_trade_levels_to_recommendations, add_entry_price_to_recommendations, factcheck_market_outlook


def run_fx_model(tickers, fx_regions=None):
    """
    Run the FX long/short model.
    
    Args:
        tickers (str): The FX pair ticker to analyze
        fx_regions (list, optional): List of regions to consider for FX analysis
    """
    
    # Load AI model prompts from environment variables
    FX_LONG_SHORT_PROMPT = os.getenv("FX_LONG_SHORT_PROMPT")
    FACTOR_WEIGHTS_PROMPT = os.getenv("FACTOR_WEIGHTS")

    # Get AI-generated weights
    ai_weights = None
    if FACTOR_WEIGHTS_PROMPT:
        try:
            # Call get_gen_ai_response with the FACTOR_WEIGHTS prompt
            ai_weights_response = get_gen_ai_response([tickers], "factor weights", FACTOR_WEIGHTS_PROMPT)
            
            # Try to parse the response as JSON
            try:
                # Remove any markdown code block markers if present
                if ai_weights_response.startswith("```json"):
                    ai_weights_response = ai_weights_response[7:]
                if ai_weights_response.endswith("```"):
                    ai_weights_response = ai_weights_response[:-3]
                
                # Parse JSON to get the weights
                ai_weights_raw = json.loads(ai_weights_response)            
                print(ai_weights_raw)
                
                # Map AI response keys to the keys used in the main prompt
                ai_weights = {
                    'Geopolitical': ai_weights_raw.get('Geopolitical', WEIGHTS_PERCENT['Geopolitical']),
                    'Macroeconomics': ai_weights_raw.get('Macroeconomics', WEIGHTS_PERCENT['Macroeconomics']),
                    'Technical_Sentiment': ai_weights_raw.get('Technical/Sentiment', WEIGHTS_PERCENT['Technical_Sentiment']),
                    'Liquidity': ai_weights_raw.get('Liquidity', WEIGHTS_PERCENT['Liquidity']),
                    'Earnings': ai_weights_raw.get('Earnings', WEIGHTS_PERCENT['Earnings']),
                    'Business_Cycle': ai_weights_raw.get('Business Cycle', WEIGHTS_PERCENT['Business_Cycle']),
                    'Sentiment_Surveys': ai_weights_raw.get('Sentiment Surveys', WEIGHTS_PERCENT['Sentiment_Surveys'])
                }
            except json.JSONDecodeError:
                print(f"Error parsing AI weights response as JSON: {ai_weights_response}")
                ai_weights = None
        except Exception as e:
            print(f"Error getting AI weights: {e}")
            ai_weights = None

    # Format the prompt with the necessary variables
    if FX_LONG_SHORT_PROMPT:
        # Create a comma-separated string of tickers for the prompt
        tickers_str = tickers
        fx_regions_str = ", ".join(fx_regions) if fx_regions else "Global"

        # Create current date in the format "September 6, 2025"
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        
        # Use AI-generated weights if available, otherwise use the hardcoded ones
        if ai_weights:
            weights_to_use = ai_weights
        else:
            weights_to_use = WEIGHTS_PERCENT
        
        # Format the prompt with tickers_str and weights
        FX_LONG_SHORT_PROMPT = FX_LONG_SHORT_PROMPT.format(
                    tickers_str=tickers_str,
                    current_date=current_date,
                    fx_regions_str=fx_regions_str,
                    geopolitical_weight=weights_to_use['Geopolitical'],
                    macroeconomic_weight=weights_to_use['Macroeconomics'],
                    technical_sentiment_weight=weights_to_use['Technical_Sentiment'],
                    liquidity_weight=weights_to_use['Liquidity'],
                    earnings_weight=weights_to_use['Earnings'],
                    business_cycle_weight=weights_to_use['Business_Cycle'],
                    sentiment_surveys_weight=weights_to_use['Sentiment_Surveys'],
                )
    
    try:
        # Get AI recommendations with None as prompt since it's pre-formatted
        # Keep getting AI recommendations until we get accurate market outlook
        recommendations = None
        max_attempts = 5  # Limit the number of attempts to avoid infinite loops
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            print(f"Attempt {attempts} to get accurate market outlook...")
            
            result = get_gen_ai_response([tickers], "fx long/short", FX_LONG_SHORT_PROMPT)
            
            # Try to parse the result as JSON
            try:
                # Remove any markdown code block markers if present
                if result.startswith("```json"):
                    result = result[7:]
                if result.endswith("```"):
                    result = result[:-3]
                # Parse JSON
                recommendations = json.loads(result)
                
                # Check if we have a market outlook narrative to factcheck
                if 'market_outlook_narrative' in recommendations:
                    # Factcheck the market outlook narrative
                    factcheck_result = factcheck_market_outlook(recommendations['market_outlook_narrative'])
                    print(f"Factcheck result: {factcheck_result}")
                    
                    if factcheck_result == "accurate":
                        print("Market outlook is accurate. Proceeding with recommendations.")
                        break  # Exit the loop if accurate
                    else:
                        print("Market outlook is inaccurate. Getting new recommendations...")
                        recommendations = None  # Reset recommendations to get new ones
                else:
                    # If there's no market outlook narrative, we can't factcheck, so proceed
                    print("No market outlook narrative to factcheck. Proceeding with recommendations.")
                    break  # Exit the loop
            except json.JSONDecodeError:
                print(f"Error parsing AI response as JSON: {result}")
                recommendations = None  # Reset recommendations to get new ones
        
        # If we still don't have recommendations after max attempts, get one more try without factchecking
        if recommendations is None:
            print(f"Failed to get accurate market outlook after {max_attempts} attempts. Getting final recommendations without factchecking.")
            result = get_gen_ai_response([tickers], "fx long/short", FX_LONG_SHORT_PROMPT)
            
            # Try to parse the result as JSON
            try:
                # Remove any markdown code block markers if present
                if result.startswith("```json"):
                    result = result[7:]
                if result.endswith("```"):
                    result = result[:-3]
                # Parse JSON
                recommendations = json.loads(result)
            except json.JSONDecodeError:
                print(f"Error parsing final AI response as JSON: {result}")
                recommendations = None

        # Add stop loss and target prices to recommendations
        if recommendations:
            recommendations = add_trade_levels_to_recommendations(recommendations)
            # Add entry prices to recommendations
            recommendations = add_entry_price_to_recommendations(recommendations)

            #Display Model Output header
            print("\n" + "="*100)
            print("FX Long/Short Model")
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
                    tickers = trade.get('ticker', 'UNKNOWN')
                    direction = trade.get('trade_direction', 'NONE')
                    score = trade.get('bull_bear_score', 0)
                    probability = trade.get('probability', 'N/A')
                    
                    # For stop_loss, target_price, and entry_price, use 'N/A' as default but validate they exist
                    stop_loss = trade.get('stop_loss', 'N/A')
                    target_price = trade.get('target_price', 'N/A')
                    entry_price = trade.get('entry_price', 'N/A')
                    
                    # Validate that required fields are present
                    if tickers == 'UNKNOWN':
                        print("- Warning: Missing ticker information")
                        continue
                    
                    if direction == 'NONE':
                        print(f"- {tickers}: Warning - Missing trade direction")
                        direction = 'HOLD'  # Default to HOLD if direction is missing
                    
                    # Ensure score is within valid range
                    if not isinstance(score, int) or score < 1 or score > 10:
                        print(f"- {tickers}: Warning - Invalid score ({score}), setting to 5")
                        score = 5
                    
                    # Validate stop_loss and entry_price
                    if stop_loss == 'N/A':
                        print(f"- {tickers}: Warning - Missing stop loss data")
                    
                    if target_price == 'N/A':
                        print(f"- {tickers}: Warning - Missing target price data")
                    
                    if entry_price == 'N/A':
                        print(f"- {tickers}: Warning - Missing entry price data")
                    
                    print(f"- {tickers}: {direction.upper()} (Score: {score}/10, Probability: {probability}, Entry Price: {entry_price}, Stop Loss: {stop_loss}, Target Price: {target_price})")
            else:
                # If JSON parsing fails, display the raw result
                print("\n=== AI Analysis ===")
                print(result)
            
    except Exception as e:
        print(f"Error running FX model: {e}")


# Testing the function
if __name__ == "__main__":
    # Example usage with default FX pair and regions
    run_fx_model('EURUSD=X', ['US', 'Eurozone'])