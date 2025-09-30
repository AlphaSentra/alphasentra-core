"""
Description:
Regional rotation ETF long/short model.
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

from _config import REGIONAL_ETFS, WEIGHTS_PERCENT, REGIONAL_REGIONS, REGIONAL_ROTATION_LONG_SHORT_PROMPT, FACTOR_WEIGHTS, LANGUAGE, REGIONAL_ASSET_CLASS, REGIONAL_IMPORTANCE, REGIONAL_ETFS_NAME, REGIONAL_FACTORS_PROMPT
from genAI.ai_prompt import get_gen_ai_response
from helpers import add_trade_levels_to_recommendations, add_entry_price_to_recommendations, strip_markdown_code_blocks, analyze_sentiment, get_current_gmt_timestamp, get_ai_weights, save_to_db_with_fallback, get_factors
from logging_utils import log_error, log_warning


def run_regional_rotation_model(tickers=None, regions=None):
    """
    Run the regional rotation long/short model.
    
    Args:
        tickers (list): List of ETF tickers to analyze.
        regional_regions (list, optional): List of regions to consider for regional analysis.
    """

    # Use default tickers and regions if not provided
    if tickers is None:
        tickers = REGIONAL_ETFS
    if regions is None:
        regions = REGIONAL_REGIONS

    # Get AI-generated weights using helper function
    ai_weights = get_ai_weights(tickers, FACTOR_WEIGHTS, WEIGHTS_PERCENT, os.getenv("GEMINI_PRO_MODEL"))

    # Format the prompt with the necessary variables
    if REGIONAL_ROTATION_LONG_SHORT_PROMPT:
        # Decrypt REGIONAL_ROTATION_LONG_SHORT_PROMPT first
        try:
            decrypted_regional_prompt = decrypt_string(REGIONAL_ROTATION_LONG_SHORT_PROMPT)
        except Exception as e:
            log_error("Error decrypting REGIONAL_ROTATION_LONG_SHORT_PROMPT", "DECRYPTION", e)
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
        result = get_gen_ai_response(tickers, "regional rotation long/short", formatted_prompt, os.getenv("GEMINI_PRO_MODEL"))
        
        # Try to parse the result as JSON
        try:
            # Remove any markdown code block markers if present
            result = strip_markdown_code_blocks(result)
            # Parse JSON
            recommendations = json.loads(result)
            
        except json.JSONDecodeError as e:
            log_error("Error parsing AI response as JSON", "AI_PARSING", e)
            log_warning(f"Raw response content: {result[:200]}...", "DATA_MISSING")
            recommendations = None


        # --------------------- Add additional data to JSON Model ---------------------
        if recommendations:
            # Add stop loss and target prices to recommendations
            recommendations = add_trade_levels_to_recommendations(recommendations, decimal_digits=1)
            # Add entry prices to recommendations
            recommendations = add_entry_price_to_recommendations(recommendations, decimal_digits=1)
            # Get sentiment score for market outlook if available
            sentiment_score = analyze_sentiment(recommendations.get('market_outlook_narrative', ''))
            recommendations['sentiment_score'] = sentiment_score            
            # Add current GMT timestamp to recommendations
            recommendations['timestamp_gmt'] = get_current_gmt_timestamp()
            # Add language code to recommendations
            recommendations['language_code'] = LANGUAGE
            # Add regions to recommendations
            recommendations['regions'] = REGIONAL_REGIONS
            # Add asset classes to recommendations
            recommendations['asset_class'] = REGIONAL_ASSET_CLASS
            # Add importance
            recommendations['importance'] = REGIONAL_IMPORTANCE
            # Add to factors
            recommendations['factors'] = get_factors(tickers, REGIONAL_ETFS_NAME, current_date, prompt=REGIONAL_FACTORS_PROMPT)
        # -----------------------------------------------------------------------------------

            #Display Model Output header
            print("\n" + "="*100)
            print("Regional Rotation Long/Short Model")
            print("="*100)
            print()

            # Display timestamp if available
            if 'timestamp_gmt' in recommendations:
                print("=== Timestamp ===")
                print()
                print(f"Timestamp (GMT): {recommendations['timestamp_gmt']}")
                print()

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
            
            # Display sentiment score if available
            if 'sentiment_score' in recommendations:
                print("=== Sentiment Score ===")
                print()
                print(f"Sentiment: {recommendations['sentiment_score']}")
                print()

            # Display market impact if available
            if 'market_impact' in recommendations:
                print("=== Market Impact ===")
                print()
                print(f"Market Impact: {recommendations['market_impact']}")
                print()

            # Display rationale if available
            if 'rationale' in recommendations:
                print("=== Rationale ===")
                print()
                print(recommendations['rationale'])
                print()

            # Display analysis if available
            if 'analysis' in recommendations:
                print("=== Analysis ===")
                print()
                print(recommendations['analysis'])
                print()
            
            # Display sources if available
            if 'sources' in recommendations:
                print("=== Sources ===")
                print()
                for source in recommendations['sources']:
                    source_name = source.get('source_name', 'Unknown Source')
                    source_title = source.get('source_title', 'No Title')
                    print(f"- {source_name}: {source_title}")
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
                        log_warning("Missing ticker information", "DATA_MISSING")
                        continue
                    
                    if direction == 'NONE':
                        log_warning(f"{ticker}: Missing trade direction", "DATA_MISSING")
                        direction = 'HOLD'  # Default to HOLD if direction is missing
                    
                    # Ensure score is within valid range
                    if not isinstance(score, int) or score < 1 or score > 10:
                        log_warning(f"{ticker}: Invalid score ({score}), setting to 5", "DATA_VALIDATION")
                        score = 5
                    
                    # Validate stop_loss and entry_price
                    if stop_loss == 'N/A':
                        log_warning(f"{ticker}: Missing stop loss data", "DATA_MISSING")
                    
                    if target_price == 'N/A':
                        log_warning(f"{ticker}: Missing target price data", "DATA_MISSING")
                    
                    if entry_price == 'N/A':
                        log_warning(f"{ticker}: Missing entry price data", "DATA_MISSING")
                    
                    print(f"- {ticker}: {direction.upper()} (Score: {score}/10, Entry Price: {entry_price}, Stop Loss: {stop_loss}, Target Price: {target_price})")
            else:
                # If JSON parsing fails, display the raw result
                print("\n=== AI Analysis ===")
                print(result)
            
    except Exception as e:
        log_error("Error in regional_rotation_long_short", "MODEL_EXECUTION", e)
        
    # Save recommendations to database with robust error handling
    if recommendations:
        success = save_to_db_with_fallback(recommendations, flag_document_generated=False)
        if not success:
            log_warning("Failed to save recommendations to database", "DATABASE")

# Testing the function
if __name__ == "__main__":
    run_regional_rotation_model(['EFA', 'EEM'], ['US', 'Global'])