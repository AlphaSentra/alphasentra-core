import os
import re
import json
from genAI.ai_prompt import get_gen_ai_response
from _config import INSTRUMENT_DESCRIPTION_PROMPT
from crypt import decrypt_string
from logging_utils import log_error
from helpers import DatabaseManager, get_asset_classes
from data.price import (
    calculate_performance_metrics,
    get_dividend_yield,
    get_growth_profitability_chart,
    financial_health_chart,
    get_capital_structure_chart,
    get_dividend_history_chart
)


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
        # Helper function for JSON parsing
        def parse_ai_response(text):
            json_match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
            return json.loads(json_match.group(1) if json_match else text)
        
        response_data = parse_ai_response(response_text)
        
        # Helper function for grade validation
        def validate_grade(value):
            valid_grades = {'A', 'B', 'C', 'D', 'E', 'F'}
            return value if value in valid_grades else ""
        
        # Extract and validate core data
        core_data = {}
        if response_data.get("description"):
            core_data["description"] = response_data["description"]
        if response_data.get("sector"):
            core_data["sector"] = response_data["sector"]
        if response_data.get("cashflow_health"):
            core_data["cashflow_health"] = validate_grade(response_data["cashflow_health"])
        if response_data.get("profit_health"):
            core_data["profit_health"] = validate_grade(response_data["profit_health"])
        if response_data.get("price_momentum"):
            core_data["price_momentum"] = validate_grade(response_data["price_momentum"])
        if response_data.get("growth_health"):
            core_data["growth_health"] = validate_grade(response_data["growth_health"])
        
        # Always include dividend_yield
        core_data["dividend_yield"] = round(float(get_dividend_yield(ticker[0] if isinstance(ticker, list) else ticker) or 0.0), 4)
        
        def process_equity_charts(ticker):
            """Process charts specifically for equity asset class"""
            
            def extract_chart(chart_key):
                chart_functions = {
                    "growth_profitability_chart": get_growth_profitability_chart,
                    "financial_health_chart": financial_health_chart,
                    "capital_structure_chart": get_capital_structure_chart,
                    "dividend_history_chart": get_dividend_history_chart
                }
                
                if chart_key not in chart_functions:
                    return {
                        "title": "",
                        "xAxis": {},
                        "yAxis": {},
                        "series": []
                    }
                
                # Get asset classes and check if any is 'EQ'
                ticker_to_check = ticker[0] if isinstance(ticker, list) else ticker
                asset_classes = get_asset_classes(ticker_to_check)
                if 'EQ' not in asset_classes:
                    return {
                        "title": "",
                        "xAxis": {},
                        "yAxis": {},
                        "series": []
                    }
                
                chart_data = chart_functions[chart_key](ticker_to_check)
                return chart_data.get(chart_key, {})
            
            return {
                "growth_profitability": extract_chart("growth_profitability_chart"),
                "financial_health": extract_chart("financial_health_chart"),
                "capital_structure": extract_chart("capital_structure_chart"),
                "dividend_history": extract_chart("dividend_history_chart")
            }
        
        # Process equity charts
        charts = process_equity_charts(ticker)
        
        # Update database
        try:
            ticker_str = ticker[0] if isinstance(ticker, list) else ticker
            performance_data = calculate_performance_metrics(ticker_str)
            
            client = DatabaseManager().get_client()
            db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
            tickers_coll = db['tickers']
            
            update_payload = {
                **core_data,
                **performance_data,
                "financial_health_chart": charts["financial_health"],
                "growth_profitability_chart": charts["growth_profitability"],
                "capital_structure_chart": charts["capital_structure"],
                "dividend_history_chart": charts["dividend_history"]
            }
            
            tickers_coll.update_one(
                {"ticker": ticker},
                {"$set": update_payload}
            )
            
        except Exception as e:
            log_error(f"Error updating ticker document: {str(e)}", "DB_UPDATE", e)
        
        return {
            "description": core_data["description"],
            "sector": core_data["sector"]
        }
        
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse AI response: {response_text}", "JSON_PARSE", e)
        return {"error": "Invalid response format"}
