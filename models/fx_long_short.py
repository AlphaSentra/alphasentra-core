"""
Description:
FX long/short model.
"""

import sys
import os
import json
import datetime
from dotenv import load_dotenv
from crypt import decrypt_string

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Load environment variables
load_dotenv()

from _config import WEIGHTS_PERCENT, FX_LONG_SHORT_PROMPT, FACTOR_WEIGHTS
from genAI.ai_prompt import get_gen_ai_response
from helpers import add_trade_levels_to_recommendations, add_entry_price_to_recommendations, strip_markdown_code_blocks



def run_fx_model(tickers, fx_regions=None):
    """
    Run the FX long/short model.
    
    Args:
        tickers (str): The FX pair ticker to analyze
        fx_regions (list, optional): List of regions to consider for FX analysis
    """
    
    # Use AI model prompts from _config.py directly
    FACTOR_WEIGHTS_PROMPT = FACTOR_WEIGHTS

    # Get AI-generated weights
    ai_weights = None
    if FACTOR_WEIGHTS_PROMPT:
        try:
            # Decrypt FACTOR_WEIGHTS_PROMPT first
            decrypted_factor_weights = decrypt_string(FACTOR_WEIGHTS_PROMPT)
            # Call get_gen_ai_response with the decrypted FACTOR_WEIGHTS prompt
            ai_weights_response = get_gen_ai_response([tickers], "factor weights", decrypted_factor_weights, os.getenv("GEMINI_PRO_MODEL"))
            
            # Try to parse the response as JSON
            try:
                # Remove any markdown code block markers if present
                ai_weights_response = strip_markdown_code_blocks(ai_weights_response)
                
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
        # Decrypt FX_LONG_SHORT_PROMPT first
        try:
            decrypted_fx_prompt = decrypt_string(FX_LONG_SHORT_PROMPT)
        except Exception as e:
            print(f"Error decrypting FX_LONG_SHORT_PROMPT: {e}")
            decrypted_fx_prompt = FX_LONG_SHORT_PROMPT  # Fallback to encrypted version
        
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
        formatted_prompt = decrypted_fx_prompt.format(
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
        result = get_gen_ai_response([tickers], "fx long/short", formatted_prompt, os.getenv("GEMINI_PRO_MODEL"))
        
        # Try to parse the result as JSON
        try:
            # Remove any markdown code block markers if present
            result = strip_markdown_code_blocks(result)
            # Parse JSON
            recommendations = json.loads(result)
        except json.JSONDecodeError:
            print(f"Error parsing AI response as JSON: {result}")
            recommendations = None

        if recommendations:
            # Add stop loss and target prices to recommendations
            recommendations = add_trade_levels_to_recommendations(recommendations, os.getenv("GEMINI_FLASH_MODEL"), decimal_digits=4)
            # Add entry prices to recommendations
            recommendations = add_entry_price_to_recommendations(recommendations, os.getenv("GEMINI_FLASH_MODEL"), decimal_digits=4)

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
                    
                    print(f"- {tickers}: {direction.upper()} (Score: {score}/10, Entry Price: {entry_price}, Stop Loss: {stop_loss}, Target Price: {target_price})")
            else:
                # If JSON parsing fails, display the raw result
                print("\n=== AI Analysis ===")
                print(result)
            
    except Exception as e:
        print(f"Error in fx_long_short.py: {e}")

# Testing the function
if __name__ == "__main__":
    # Example usage with default FX pair and regions
    run_fx_model('EURUSD=X', ['US', 'Eurozone'])