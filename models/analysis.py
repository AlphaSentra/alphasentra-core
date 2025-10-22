import os
import re
import json
from genAI.ai_prompt import get_gen_ai_response
from _config import INSTRUMENT_DESCRIPTION_PROMPT
from crypt import decrypt_string
from logging_utils import log_error
from helpers import DatabaseManager
from data.price import calculate_performance_metrics


def run_analysis(ticker, instrument_name):
    """
    Analyze instrument using AI to extract description and sector.
    Returns JSON with 'description' and 'sector' fields.
    """
    # Decrypt and format the prompt
    decrypted_prompt = decrypt_string(INSTRUMENT_DESCRIPTION_PROMPT)
    if not decrypted_prompt:
        return {
            "description": "Prompt decryption failed",
            "sector": ""
        }
    
    # Format prompt with instrument details
    full_prompt = decrypted_prompt.format(
        tickers_str=ticker,
        instrument_name=instrument_name
    )
    
    # Get AI response
    response_text = get_gen_ai_response(
        tickers=[ticker],
        model_strategy="Analysis",
        prompt=full_prompt,
        gemini_model="gemini-2.5-flash"
    )
    
    try:
        # Extract JSON from markdown code block if present
        json_match = re.search(r'```json\s*({.*?})\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)

        # Parse cleaned JSON response
        response_data = json.loads(response_text)
        description = response_data.get("description", "")
        sector = response_data.get("sector", "")
        valid_grades = {'A', 'B', 'C', 'D', 'E', 'F'}
        
        cashflow_health = response_data.get("cashflow_health", "")
        if cashflow_health not in valid_grades:
            cashflow_health = "-"
            
        profit_health = response_data.get("profit_health", "")
        if profit_health not in valid_grades:
            profit_health = "-"
            
        price_momentum = response_data.get("price_momentum", "")
        if price_momentum not in valid_grades:
            price_momentum = "-"
            
        growth_health = response_data.get("growth_health", "")
        if growth_health not in valid_grades:
            growth_health = "-"
        dividend_yield = response_data.get("dividend_yield", "")

        # Update tickers collection in MongoDB with description, sector and performance
        try:            
            # Get performance data first
            # Ensure we pass a single ticker string
            ticker_str = ticker[0] if isinstance(ticker, list) else ticker
            performance_data = calculate_performance_metrics(ticker_str)
            
            client = DatabaseManager().get_client()
            db = client[os.getenv("MONGODB_DATABASE", "alphagora")]
            tickers_coll = db['tickers']
            
            # Combine both updates into a single operation
            tickers_coll.update_one(
                {"ticker": ticker},
                {"$set": {
                    "description": description,
                    "sector": sector,
                    "1y": performance_data.get('1y', 0.0),
                    "6m": performance_data.get('6m', 0.0),
                    "3m": performance_data.get('3m', 0.0),
                    "1m": performance_data.get('1m', 0.0),
                    "1d": performance_data.get('1d', 0.0),
                    "cashflow_health": cashflow_health,
                    "profit_health": profit_health,
                    "price_momentum": price_momentum,
                    "growth_health": growth_health,
                    "dividend_yield": dividend_yield
                }}
            )

        except Exception as e:
            log_error(f"Error updating ticker document: {str(e)}", "DB_UPDATE", e)

        return {
            "description": description,
            "sector": sector
        }
    
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse AI response: {response_text}", "JSON_PARSE", e)
        return
