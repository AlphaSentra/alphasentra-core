import os
from genAI.ai_prompt import get_gen_ai_response
from _config import INSTRUMENT_DESCRIPTION_PROMPT
from crypt import decrypt_string
import json

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
        ticker=ticker,
        instrument_name=instrument_name
    )
    
    # Get AI response
    response_text = get_gen_ai_response(
        tickers=[ticker],
        model_strategy="Description",
        prompt=full_prompt,
        gemini_model="gemini-2.5-flash"
    )
    
    try:
        # Parse JSON response
        response_data = json.loads(response_text)
        description = response_data.get("description", "")
        sector = response_data.get("sector", "")

        # Update tickers collection in MongoDB
        try:
            from helpers import DatabaseManager
            client = DatabaseManager().get_client()
            db = client[os.getenv("MONGODB_DATABASE", "alphagora")]
            tickers_coll = db['tickers']

            # Update the current ticker document
            tickers_coll.update_one(
                {"ticker": ticker},  # Use the function parameter
                {"$set": {
                    "description": description,
                    "sector": sector
                }}
            )
        except Exception as e:
            print(f"Error updating ticker document: {str(e)}")

        return {
            "description": description,
            "sector": sector
        }
    
    except json.JSONDecodeError as e:
        from logging_utils import log_error
        log_error(f"Failed to parse AI response: {response_text}", "JSON_PARSE", e)
        return
