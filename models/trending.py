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


from helpers import DatabaseManager
from _config import EQ_EQUITY_LONG_SHORT_PROMPT, EQ_EQUITY_FACTORS_PROMPT, CR_CRYPTO_LONG_SHORT_PROMPT, CR_CRYPTO_FACTORS_PROMPT
from data.check_ticker import ticker_exists
from db.create_ticker import create_ticker_document
from genAI.ai_prompt import get_gen_ai_response
from _config import EQ_EQUITY_TRENDING_PROMPT, CR_CRYPTO_TRENDING_PROMPT, MARKET
from crypt import decrypt_string

# Load environment variables
load_dotenv()


from logging_utils import log_error, log_warning

def strip_markdown_code_blocks(text):
    """Remove markdown code block markers from a string"""
    return text.replace('```json', '').replace('```', '').strip()

def create_new_ticker_documents(asset_class, instruments, new_tickers):
    """Create ticker documents for new trending instruments in the database.
    
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


def get_trending_instruments(asset_class=None, model_strategy="Pro", gemini_model=None, batch_mode=True):
    """
    Get trending instruments using Gemini AI based on asset class.
    
    Parameters:
    asset_class (str): Type of assets to analyze ("EQ" for equities, "CR" for crypto)
    model_strategy (str): Gemini model strategy to use (default: "Pro")
    gemini_model (str): Specific Gemini model name (optional)
    batch_mode (bool): Whether to run in batch processing mode (default: False)
    
    Returns:
    str: AI response containing trending instruments analysis
    """
    # Select prompt based on asset class
    if asset_class.upper() == "EQ":
        prompt = EQ_EQUITY_TRENDING_PROMPT
    elif asset_class.upper() == "CR":
        prompt = CR_CRYPTO_TRENDING_PROMPT
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
        instruments = None


    # Extract tickers not present in the tickers collection
    if instruments:
        # Get all tickers from the collection
        existing_tickers = set()
        try:
            # Get MongoDB client and database
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
            print("All trending tickers already exist in the collection")

    return instruments


if __name__ == "__main__":
    print("\n=== Running Trending Instruments Analysis ===")
    trending = get_trending_instruments(asset_class="EQ")
    
    if trending:
        print("\nRecommended Instruments:")
        for instrument in trending:
            print(f"- {instrument['name']} ({instrument['ticker']})")
    else:
        print("\nNo trending instruments found")
