"""
Description:
Regional rotation ETF long/short model.
"""

import sys
import os
import json
import datetime
from crypt import decrypt_string
from dotenv import load_dotenv

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Load environment variables
load_dotenv()

from _config import REGIONAL_ETFS, WEIGHTS_PERCENT, REGIONAL_REGIONS, REGIONAL_ROTATION_LONG_SHORT_PROMPT, FACTOR_WEIGHTS, FACTCHECK_AMENDMENT_PROMPT
from genAI.ai_prompt import get_gen_ai_response
from helpers import add_trade_levels_to_recommendations, add_entry_price_to_recommendations, factcheck_market_outlook, strip_markdown_code_blocks


def run_regional_rotation_model(tickers=None, regions=None):
    """
    Run the regional rotation long/short model.
    
    Args:
        tickers (list, optional): List of ETF tickers to analyze. Defaults to REGIONAL_ETFS from config.
        regions (list, optional): List of regions to consider for regional analysis. Defaults to REGIONAL_REGIONS from config.
    """
    
    # Use default tickers and regions if not provided
    if tickers is None:
        tickers = REGIONAL_ETFS
    if regions is None:
        regions = REGIONAL_REGIONS
    
    # Use AI model prompts from _config.py directly
    FACTOR_WEIGHTS_PROMPT = FACTOR_WEIGHTS

    # Get AI-generated weights
    ai_weights = None
    if FACTOR_WEIGHTS_PROMPT:
        try:
            # Decrypt FACTOR_WEIGHTS_PROMPT first
            decrypted_factor_weights = decrypt_string(FACTOR_WEIGHTS_PROMPT)
            # Call get_gen_ai_response with the decrypted FACTOR_WEIGHTS prompt
            ai_weights_response = get_gen_ai_response(tickers, "factor weights", decrypted_factor_weights, os.getenv("GEMINI_PRO_MODEL"))
            
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
    if REGIONAL_ROTATION_LONG_SHORT_PROMPT:
        # Decrypt REGIONAL_ROTATION_LONG_SHORT_PROMPT first
        try:
            decrypted_regional_prompt = decrypt_string(REGIONAL_ROTATION_LONG_SHORT_PROMPT)
        except Exception as e:
            print(f"Error decrypting REGIONAL_ROTATION_LONG_SHORT_PROMPT: {e}")
            decrypted_regional_prompt = REGIONAL_ROTATION_LONG_SHORT_PROMPT  # Fallback to encrypted version
        
        # Create a comma-separated string of tickers for the prompt
        tickers_str = ", ".join(tickers) if tickers else "No tickers provided"
        regional_regions_str = ", ".join(regions) if regions else "No regions provided"

        # Create current date in the format "September 6, 2025"
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        
        # Use AI-generated weights if available, otherwise use the hardcoded ones
        if ai_weights:
            weights_to_use = ai_weights
        else:
            weights_to_use = WEIGHTS_PERCENT
        
        # Format the prompt with tickers_str and weights
        formatted_prompt = decrypted_regional_prompt.format(
                    tickers_str=tickers_str,
                    current_date=current_date,
                    regional_regions_str=regional_regions_str,
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
        max_attempts = 1  # Limit the number of attempts to avoid infinite loops
        attempts = 0
        last_inaccurate_recommendations = None
        last_factcheck_result = None
        
        while attempts < max_attempts:
            attempts += 1
            print(f"Attempt {attempts} to get accurate market outlook...")
            
            result = get_gen_ai_response(tickers, "regional rotation long/short", formatted_prompt, os.getenv("GEMINI_PRO_MODEL"))
            
            # Try to parse the result as JSON
            try:
                # Remove any markdown code block markers if present
                result = strip_markdown_code_blocks(result)
                # Parse JSON
                recommendations = json.loads(result)
                
                # Check if we have a market outlook narrative to factcheck
                if 'market_outlook_narrative' in recommendations:
                    # Factcheck the market outlook narrative
                    factcheck_result = factcheck_market_outlook(recommendations['market_outlook_narrative'], os.getenv("GEMINI_PRO_MODEL"))
                    print(f"Factcheck result: {factcheck_result}")
                    
                    # Extract from factcheck_results JSON: factcheck into factcheck_status and factcheck_issues
                    if isinstance(factcheck_result, dict):
                        factcheck_status = factcheck_result.get("factcheck", "inaccurate")
                        factcheck_issues = factcheck_result.get("issues", [])
                    else:
                        factcheck_status = factcheck_result
                        factcheck_issues = []
                    
                    if factcheck_status == "accurate":
                        print("Market outlook is accurate. Proceeding with recommendations.")
                        break  # Exit the loop if accurate
                    else:
                        print("Market outlook is inaccurate. Getting new recommendations...")
                        # Store the inaccurate recommendations and factcheck issues for potential fallback use
                        last_inaccurate_recommendations = recommendations.get("market_outlook_narrative", "")
                        last_factcheck_issues = factcheck_issues
                        recommendations = None  # Reset recommendations to get new ones
                else:
                    # If there's no market outlook narrative, we can't factcheck, so proceed
                    print("No market outlook narrative to factcheck. Proceeding with recommendations.")
                    break  # Exit the loop
            except json.JSONDecodeError:
                print(f"Error parsing AI response as JSON: {result}")
                recommendations = None  # Reset recommendations to get new ones
        
        # If we still don't have recommendations after max attempts, get one more try
        # using the last inaccurate recommendations and factcheck result to rewrite them
        if recommendations is None:
            print(f"Failed to get accurate market outlook after {max_attempts} attempts. Getting final recommendations by rewriting inaccurate ones.")
            
            # Initialize rewrite_prompt with formatted_prompt as fallback
            rewrite_prompt = formatted_prompt  # Fallback to original prompt
            
            if last_inaccurate_recommendations and last_factcheck_issues:
                # Create a prompt that includes the inaccurate recommendations and factcheck issues
                # Use the encrypted FACTCHECK_AMENDMENT_PROMPT constant from _config.py
                # Variables in FACTCHECK_AMENDMENT_PROMPT are {last_factcheck_result} and {previous_recommendations}
                try:
                    decrypted_amendment_prompt = decrypt_string(FACTCHECK_AMENDMENT_PROMPT)
                    rewrite_prompt = decrypted_amendment_prompt.format(
                        factcheck_result=last_factcheck_issues,
                        previous_recommendations=last_inaccurate_recommendations
                    )
                except Exception as e:
                    print("=" * 100)
                    print(f"Error decrypting FACTCHECK_AMENDMENT_PROMPT: {e}")
                    print("=" * 100)
                    
                
                result = get_gen_ai_response(tickers, "regional rotation long/short", rewrite_prompt, os.getenv("GEMINI_PRO_MODEL"))
            else:
                # Fallback to original prompt if no previous inaccurate recommendations are available
                result = get_gen_ai_response(tickers, "regional rotation long/short", formatted_prompt, os.getenv("GEMINI_PRO_MODEL"))
            
            # Try to parse the result as JSON
            try:
                # Remove any markdown code block markers if present
                result = strip_markdown_code_blocks(result)
                # Parse JSON
                recommendations = json.loads(result)
            except json.JSONDecodeError:
                print(f"Error parsing final AI response as JSON: {result}")
                recommendations = None

        # Add stop loss and target prices to recommendations
        if recommendations:
            recommendations = add_trade_levels_to_recommendations(recommendations, os.getenv("GEMINI_FLASH_MODEL"), decimal_digits=1)
            # Add entry prices to recommendations
            recommendations = add_entry_price_to_recommendations(recommendations, os.getenv("GEMINI_FLASH_MODEL"), decimal_digits=1)

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
                    
                    print(f"- {ticker}: {direction.upper()} (Score: {score}/10, Entry Price: {entry_price}, Stop Loss: {stop_loss}, Target Price: {target_price})")
            else:
                # If JSON parsing fails, display the raw result
                print("\n=== AI Analysis ===")
                print(result)
            
    except Exception as e:
        print(f"Error in regional_rotation_long_short.py: {e}")

# Testing the function
if __name__ == "__main__":
    run_regional_rotation_model()