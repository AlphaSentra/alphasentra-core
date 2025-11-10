import datetime
import json
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from helpers import DatabaseManager, check_pending_ticker_documents
from _config import EQ_EQUITY_LONG_SHORT_PROMPT, EQ_EQUITY_FACTORS_PROMPT, CR_CRYPTO_LONG_SHORT_PROMPT, CR_CRYPTO_FACTORS_PROMPT
from data.check_ticker import ticker_exists
from db.create_ticker import create_ticker_document
from genAI.ai_prompt import get_gen_ai_response
from _config import EQ_EQUITY_TRENDING_PROMPT, CR_CRYPTO_TRENDING_PROMPT, FX_FOREX_TRENDING_PROMPT,MARKET
from crypt import decrypt_string

# Load environment variables
load_dotenv()


from logging_utils import log_error, log_warning, log_info

def update_ticker_recurrence(instruments):
    """
    Update ticker documents' recurrence and document_generated fields for trending instruments.
    
    Args:
        instruments (list): List of instrument dictionaries containing ticker data
        
    Returns:
        None: Updates documents in the tickers collection
    """
    try:
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        tickers_collection = db['tickers']
        
        for instrument in instruments:
            ticker = instrument['ticker']
            result = tickers_collection.update_one(
                {"ticker": ticker, "recurrence": "processed"},
                {"$set": {"recurrence": "once", "document_generated": False}}
            )
            if result.modified_count > 0:
                log_info(f"Updated recurrence for ticker {ticker}")
    except Exception as e:
        log_error("Failed to update ticker recurrence", "DB_UPDATE", e)


def strip_markdown_code_blocks(text):
    """Remove markdown code block markers from a string"""
    return text.replace('```json', '').replace('```', '').strip()

def update_pipeline_run_count(model_function):
    """Update pipeline run count and task completion status"""
    try:
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        pipeline_collection = db['pipeline']
        
        # Check if document exists first
        existing_doc = pipeline_collection.find_one({"model_function": model_function})
        
        if not existing_doc:
            # Insert new document with initial run_count
            pipeline_collection.insert_one({
                "model_function": model_function,
                "model_name": "trending",
                "recurrence": "multi",
                "run_count": 1,
                "task_completed": False
            })
        else:
            # Update existing document
            pipeline_collection.update_one(
                {"model_function": model_function},
                {
                    "$inc": {"run_count": 1},
                    "$set": {
                        "task_completed": {
                            "$cond": {
                                "if": {"$gte": ["$run_count", 4]},
                                "then": True,
                                "else": "$task_completed"
                            }
                        }
                    }
                }
            )
            log_info(f"Updated pipeline run count for {model_function}")
    except Exception as e:
        log_error("Failed to update pipeline run count", "DB_UPDATE", e)


def create_new_ticker_documents(asset_class, instruments, new_tickers):
    """
    Create ticker documents for new trending instruments in the database.
    
    Handles configuration and creation of ticker documents based on asset class,
    setting appropriate prompts, factors, and model references for each type.
    
    Args:
        asset_class (str): The type of asset ("EQ" for equities, "CR" for crypto)
        instruments (list): List of instrument dictionaries containing ticker data
        new_tickers (list): List of ticker strings that need to be created
        
    Note:
        This function has side effects - it creates documents in the database
        through the create_ticker_document function.
    """
    # Configure parameters based on asset class
    if asset_class == "EQ":
        prompt = EQ_EQUITY_LONG_SHORT_PROMPT
        factors = EQ_EQUITY_FACTORS_PROMPT
        model_function = "run_holistic_market_model"
        model_name = "holistic"
    elif asset_class == "CR":
        prompt = CR_CRYPTO_LONG_SHORT_PROMPT
        factors = CR_CRYPTO_FACTORS_PROMPT
        model_function = "run_holistic_market_model"
        model_name = "holistic"
    else:
        prompt = None
        factors = None
        model_function = None
        model_name = None

    for instrument in instruments:
        if instrument['ticker'] in new_tickers:
            create_ticker_document(
                ticker=instrument['ticker'],
                ticker_tradingview=instrument['ticker_tradingview'],
                name=instrument['name'],
                asset_class=asset_class,
                region=MARKET,
                prompt=prompt,
                factors=factors,
                model_function=model_function,
                model_name=model_name,
                importance=5,
                recurrence="once",
                decimal=instrument['decimal']
            )


def update_insights_importance_for_trending(instruments):
    """
    Update importance and tags in insights collection for trending instruments.
    
    Args:
        instruments (list): List of instrument dictionaries containing ticker data
    """
    if not instruments:
        return
        
    try:
        tag = ">trending ⇧"
        ticker_list = [instrument['ticker'] for instrument in instruments]
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        insights_collection = db['insights']
        
        # Update all documents where any recommendation ticker matches our instruments
        for ticker in ticker_list:
            # Find all matching documents
            cursor = insights_collection.find({"recommendations.ticker": ticker})
            updated_count = 0
            
            for doc in cursor:
                current_tag = doc.get('tag', '')
                new_tag = tag
                
                # Only add the tag if it's not already present
                if new_tag not in current_tag:
                    if current_tag:
                        updated_tag = f"{current_tag}, {new_tag}"
                    else:
                        updated_tag = new_tag
                else:
                    updated_tag = current_tag
                
                # Update the individual document
                result = insights_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {
                        "importance": 3,
                        "tag": updated_tag
                    }}
                )
                updated_count += result.modified_count
            
            print(f"Updated {updated_count} insights documents for ticker {ticker}")
    except Exception as e:
        log_error("Failed to update insights collection", "DB_UPDATE", e)


def get_trending_instruments(asset_class=None, model_strategy="Pro", gemini_model=None, model_function=None, batch_mode=True):
    """
    Get trending instruments using Gemini AI based on asset class.
    
    Parameters:
    asset_class (str): Type of assets to analyze ("EQ" for equities, "CR" for crypto)
    model_strategy (str): Gemini model strategy to use (default: "Pro")
    gemini_model (str): Specific Gemini model name (optional)
    batch_mode (bool): Whether to run in batch processing mode (default: True)
    
    Returns:
    list | None: List of instrument dictionaries or None on error
    """
    # Check if any tickers have pending document generation
    if check_pending_ticker_documents():
        log_info(f"Skipping trending analysis - insights pending generation")
        return None

    # Select prompt based on asset class
    if asset_class.upper() == "EQ":
        prompt = EQ_EQUITY_TRENDING_PROMPT
    elif asset_class.upper() == "CR":
        prompt = CR_CRYPTO_TRENDING_PROMPT
    elif asset_class.upper() == "FX":
        prompt = FX_FOREX_TRENDING_PROMPT
    else:
        raise ValueError(f"Unsupported asset class: {asset_class}")
    
    # Create current date in the format "November 7, 2025"
    current_date = datetime.datetime.now().strftime("%B %d, %Y")

    # Decrypt and format the prompt
    decrypted_prompt = decrypt_string(prompt)
    formatted_prompt = decrypted_prompt.format(
            market=MARKET,
            current_date=current_date
        )
    
    # Call AI with empty tickers list since prompt is self-contained
    response = get_gen_ai_response(
        tickers=[],
        model_strategy=model_strategy,
        prompt=formatted_prompt,
        gemini_model=gemini_model,
        batch_mode=batch_mode
    )
    
    # Try to parse the result as JSON
    try:
        # Remove any markdown code block markers if present
        result = strip_markdown_code_blocks(response)
        # Parse JSON
        instruments = json.loads(result)
    except json.JSONDecodeError as e:
        log_error("Error parsing AI response as JSON", "AI_PARSING", e)
        log_warning(f"Raw response content: {response[:200]}...", "DATA_MISSING")
        return None


    # Extract tickers not present in the tickers collection
    if instruments:
        # Get all tickers from the collection using existing connection
        existing_tickers = set()
        try:
            client = DatabaseManager().get_client()
            db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
            tickers_collection = db['tickers']
            cursor = tickers_collection.find({}, {'ticker': 1, '_id': 0})
            existing_tickers = {doc['ticker'] for doc in cursor}
        except Exception as e:
            log_error("Error fetching tickers from collection", "DATA_FETCH", e)
        
        # Get trending instrument tickers
        trending_tickers = {instrument['ticker'] for instrument in instruments}
        
        # Find difference
        new_tickers = [ticker for ticker in (trending_tickers - existing_tickers) if ticker_exists(ticker)]
        if new_tickers:
            print(f"Found {len(new_tickers)} new tickers not in collection: {new_tickers}")
            create_new_ticker_documents(asset_class, instruments, new_tickers)
        else:
            log_info("All trending tickers already exist in the collection")
            
            # Update pipeline run count for this model function
            update_pipeline_run_count(model_function)
            
        # Flag importance (set insights importance to 3 for trending instruments)
        if instruments:
            update_ticker_recurrence(instruments)
            update_insights_importance_for_trending(instruments)
        
    return instruments


def run_trending_analysis_equity():
    """Run trending analysis for Equity asset class"""
    return get_trending_instruments(asset_class="EQ", model_function="run_trending_analysis_equity")

def run_trending_analysis_crypto():
    """Run trending analysis for Crypto asset class"""
    return get_trending_instruments(asset_class="CR", model_function="run_trending_analysis_crypto")

def run_trending_analysis_forex():
    """Run trending analysis for Forex asset class"""
    return get_trending_instruments(asset_class="FX", model_function="run_trending_analysis_forex")


if __name__ == "__main__":
    print("\n=== Running Trending Instruments Analysis ===")
    run_trending_analysis_equity()
    run_trending_analysis_crypto()
    run_trending_analysis_forex()