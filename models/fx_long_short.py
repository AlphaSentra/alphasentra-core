"""
Description:
FX long/short model.
"""

import sys
import os
import json
import datetime
import time
from dotenv import load_dotenv
from crypt import decrypt_string

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Load environment variables
load_dotenv()

from _config import WEIGHTS_PERCENT, FX_LONG_SHORT_PROMPT, FACTOR_WEIGHTS, LANGUAGE, FX_FACTORS_PROMPT, AI_RESPONSE_MAX_RETRIES, AI_PAUSE_BETWEEN_RETRIES_IN_SECONDS, MONTE_CARLO_MODEL_TIME_HORIZON, MONTE_CARLO_MODEL_NUM_SIMULATIONS
from genAI.ai_prompt import get_gen_ai_response
from helpers import add_trade_levels_to_recommendations, add_entry_price_to_recommendations, strip_markdown_code_blocks, get_current_gmt_timestamp, get_ai_weights, save_to_db_with_fallback, get_regions, get_asset_classes, get_importance, get_factors, get_ticker_name, get_ticker_performance, calculate_average_sentiment, extract_json_from_text
from logging_utils import log_error, log_warning, log_info
from models.analysis import run_analysis
from models.simulation import process_simulation_data
from data.price_action import calculate_volatility, calculate_drift
from models.montecarlo import run_monte_carlo_simulation

def run_fx_model(tickers, name=None, fx_regions=None, prompt=None, decimal_digits=4, flag_document_generated: bool = True, batch_mode: bool = False):
    """
    Run the FX long/short model.
    
    Args:
        tickers (str or list): The FX pair ticker(s) to analyze. If list provided, uses first element.
        fx_regions (list, optional): List of regions to consider for FX analysis
        prompt (str, optional): Custom prompt to use. If None, uses FX_LONG_SHORT_PROMPT from _config.py
        decimal_digits (int, optional): Number of decimal places for price calculations. Defaults to 4.
        flag_document_generated (bool, optional): Whether to save the generated document to the database. Defaults to True.
        batch_mode (bool, optional): When batch_mode is True, don't print() any information. Defaults to False.
        
    Returns:
        dict: The recommendations dictionary with sentiment score if available
    """
    
    # Handle case where ticker is passed as a list
    if isinstance(tickers, list):
        if tickers:
            tickers = tickers[0]
        else:
            return None
    
    # Use provided prompt or fallback to config prompt
    if prompt is None:
        prompt = FX_LONG_SHORT_PROMPT
    
    # Get AI-generated weights using helper function
    ai_weights = get_ai_weights([tickers], FACTOR_WEIGHTS, WEIGHTS_PERCENT, os.getenv("GEMINI_FLASH_LITE_MODEL"), batch_mode=batch_mode)

    # Format the prompt with the necessary variables
    if prompt:
        # Decrypt the prompt first
        try:
            decrypted_prompt = decrypt_string(prompt)
        except Exception as e:
            log_error("Error decrypting prompt", "DECRYPTION", e)
            decrypted_prompt = prompt  # Fallback to encrypted version
        
        # Create a comma-separated string of tickers for the prompt
        tickers_str = tickers
        # Use provided name of instrument
        instrument_name = get_ticker_name(tickers)
        fx_regions_str = ", ".join(fx_regions) if fx_regions else "Global"
        # Create current date in the format "September 6, 2025"
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        # Run analysis of the current instrument
        run_analysis(tickers_str, instrument_name, batch_mode=batch_mode)
        
        # Use AI-generated weights if available, otherwise use the hardcoded ones
        if ai_weights:
            weights_to_use = ai_weights
        else:
            weights_to_use = WEIGHTS_PERCENT
        
        # Format the prompt with tickers_str and weights
        formatted_prompt = decrypted_prompt.format(
                    tickers_str=tickers_str,
                    instrument_name=instrument_name,
                    current_date=current_date,
                    fx_regions_str=fx_regions_str,
                    geopolitical_weight=weights_to_use['Geopolitical'],
                    macroeconomic_weight=weights_to_use['Macroeconomics'],
                    technical_sentiment_weight=weights_to_use['Technical_Sentiment'],
                    liquidity_weight=weights_to_use['Liquidity'],
                    earnings_weight=weights_to_use['Earnings'],
                    business_cycle_weight=weights_to_use['Business_Cycle'],
                    sentiment_surveys_weight=weights_to_use['Sentiment_Surveys'],
                    p1y = get_ticker_performance(tickers, 'p1y'),
                    p6m = get_ticker_performance(tickers, 'p6m'),
                    p3m = get_ticker_performance(tickers, 'p3m'),
                    p1m = get_ticker_performance(tickers, 'p1m'),
                    p1w = get_ticker_performance(tickers, 'p1w')
                )
    
    try:
        recommendations = None
        max_retries = AI_RESPONSE_MAX_RETRIES
        retry_count = 0
        parse_success = False

        log_info("Starting fx_long_short AI response retrieval")
        
        while retry_count < max_retries and not parse_success:
            try:
                # Get fresh AI response each retry
                result = get_gen_ai_response([tickers], "fx long/short", formatted_prompt, batch_mode=batch_mode)
                
                # Remove any markdown code block markers if present
                result = strip_markdown_code_blocks(result)
                
                # Use the enhanced JSON extraction with repair capabilities
                json_content = extract_json_from_text(result)
                
                if json_content:
                    try:
                        # Parse the extracted JSON
                        recommendations = json.loads(json_content)
                        
                        # Validate required keys
                        required_keys = ['title', 'market_outlook_narrative', 'rationale', 'analysis', 'recommendations']
                        missing_keys = [key for key in required_keys if key not in recommendations]
                        if missing_keys:
                            raise ValueError(f"Missing required keys: {', '.join(missing_keys)}")
                        
                        log_info("FX Long/Short Model JSON parsed and validated successfully")
                        parse_success = True  # Success only after full processing
                    except ValueError as e:
                        log_error(f"JSON validation error: {str(e)}", "JSON_VALIDATION")
                        raise  # This will be caught by the outer except block and trigger retry
                else:
                    retry_count += 1
                    log_error(f"JSON extraction failed (attempt {retry_count}/{max_retries})", "AI_PARSING")
                    if retry_count < max_retries:
                        time.sleep(AI_PAUSE_BETWEEN_RETRIES_IN_SECONDS)
                    else:
                        log_error("Max retries reached for JSON extraction", "FX_LONG_SHORT_FAILURE")
            except Exception as e:  # Catch all exceptions
                retry_count += 1
                log_error(f"Error processing AI response (attempt {retry_count}/{max_retries})", "AI_PROCESSING", e)
                if retry_count < max_retries:
                    time.sleep(AI_PAUSE_BETWEEN_RETRIES_IN_SECONDS)
                else:
                    log_error("Max retries reached for FX Long/Short analysis", "FX_LONG_SHORT_FAILURE")

        # --------------------- Add additional data to JSON Model ---------------------    
        if recommendations:
            # Add stop loss and target prices to recommendations
            recommendations = add_trade_levels_to_recommendations(recommendations, decimal_digits=decimal_digits)
            # Add entry prices to recommendations
            recommendations = add_entry_price_to_recommendations(recommendations, decimal_digits=decimal_digits)
            # Get sentiment score for market outlook if available
            recommendations['sentiment_score'] = calculate_average_sentiment(recommendations)
            # Get conviction from simulation if available
            recommendations['conviction'] = calculate_average_sentiment(recommendations)
            # Add current GMT timestamp to recommendations
            recommendations['timestamp_gmt'] = get_current_gmt_timestamp()
            # Add language code to recommendations
            recommendations['language_code'] = LANGUAGE
            # Add regions to recommendations
            recommendations['regions'] = get_regions(tickers)
            # Add asset classes to recommendations
            recommendations['asset_class'] = get_asset_classes(tickers)
            # Add importance
            recommendations['importance'] = get_importance(tickers)
            # Add to factors
            recommendations['factors'] = get_factors(tickers,current_date,prompt=FX_FACTORS_PROMPT, batch_mode=batch_mode)
            # Get simulation data
            recommendations['simulation'] = process_simulation_data(recommendations.get('simulation', []))
            # Monte Carlo Model — Input: Volatility (sigma)
            recommendations['volatility'] = calculate_volatility(tickers)
            # Monte Carlo Model — Input: Drift (mu)
            recommendations['drift'] = calculate_drift(tickers)
        # -----------------------------------------------------------------------------------
            
            if not batch_mode:
                # Display Model Output header
                print("\n" + "="*100)
                print("FX Long/Short Model")
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

                # Display rationale if available
                if 'rationale' in recommendations:
                    print("=== Rationale ===")
                    print()
                    print(recommendations['rationale'])
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
                        tickers = trade.get('ticker', 'UNKNOWN')
                        direction = trade.get('trade_direction', 'NONE')
                        score = trade.get('bull_bear_score', 0)
                        
                        # For stop_loss, target_price, and entry_price, use 'N/A' as default but validate they exist
                        stop_loss = trade.get('stop_loss', 'N/A')
                        target_price = trade.get('target_price', 'N/A')
                        entry_price = trade.get('entry_price', 'N/A')
                        
                        # Validate that required fields are present
                        if tickers == 'UNKNOWN':
                            log_warning("Missing ticker information", "DATA_MISSING")
                            continue
                        
                        if direction == 'NONE':
                            log_warning(f"{tickers}: Missing trade direction", "DATA_MISSING")
                            direction = 'HOLD'  # Default to HOLD if direction is missing
                        
                        # Ensure score is within valid range
                        if not isinstance(score, int) or score < 1 or score > 10:
                            log_warning(f"{tickers}: Invalid score ({score}), setting to 5", "DATA_VALIDATION")
                            score = 5
                        
                        # Validate stop_loss and entry_price
                        if stop_loss == 'N/A':
                            log_warning(f"{tickers}: Missing stop loss data", "DATA_MISSING")
                        
                        if target_price == 'N/A':
                            log_warning(f"{tickers}: Missing target price data", "DATA_MISSING")
                        
                        if entry_price == 'N/A':
                            log_warning(f"{tickers}: Missing entry price data", "DATA_MISSING")
                        
                        print(f"- {tickers}: {direction.upper()} (Score: {score}/10, Entry Price: {entry_price}, Stop Loss: {stop_loss}, Target Price: {target_price})")
                else:
                    # If JSON parsing fails, display the raw result
                    print("\n=== AI Analysis ===")
                    print(result)
            
    except Exception as e:
        log_error("Error in fx_long_short", "MODEL_EXECUTION", e)
        return None
        
    # Save recommendations to database with robust error handling
    if recommendations:
        success = save_to_db_with_fallback(recommendations, flag_document_generated=flag_document_generated)
        if success:
            log_info("Successfully saved recommendations to database. Running Monte Carlo simulation.")
            # Run Monte Carlo simulation
            try:
                # Safely get the initial price
                initial_price_str = recommendations.get('recommendations', [{}])[0].get('entry_price')
                
                # Ensure the price is valid before converting to float
                if initial_price_str and initial_price_str not in ['N/A', 'UNKNOWN']:
                    initial_price = float(initial_price_str)
                    
                    # Run the simulation
                    run_monte_carlo_simulation(
                        sessionID="default",
                        ticker=tickers,
                        initial_price=initial_price,
                        strategy=recommendations.get('recommendations', [{}])[0].get('trade_direction'),
                        target_price=recommendations.get('recommendations', [{}])[0].get('target_price'),
                        stop_loss=recommendations.get('recommendations', [{}])[0].get('stop_loss'),
                        volatility=recommendations.get('volatility'),
                        drift=recommendations.get('drift'),
                        time_horizon=MONTE_CARLO_MODEL_TIME_HORIZON,
                        num_simulations=MONTE_CARLO_MODEL_NUM_SIMULATIONS
                    )
                else:
                    log_warning("Could not run Monte Carlo simulation because entry price is not available.", "MONTE_CARLO_SIMULATION")

            except (ValueError, TypeError) as e:
                log_error(f"Could not convert entry price to float: {initial_price_str}", "MONTE_CARLO_SIMULATION", e)
            except Exception as e:
                log_error("Error running Monte Carlo simulation", "MONTE_CARLO_SIMULATION", e)
        else:
            log_warning("Failed to save recommendations to database", "DATABASE")
        
    return recommendations

# Testing the function
if __name__ == "__main__":
    # Example usage with default FX pair and regions
    run_fx_model('EURUSD=X', ['US', 'Eurozone'])
