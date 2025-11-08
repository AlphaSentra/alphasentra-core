import pymongo
import os
from helpers import DatabaseManager
from logging_utils import log_error

def create_ticker_document(ticker, ticker_tradingview, name, asset_class=None, region=None,
                         prompt=None, factors=None, model_function=None, model_name=None,
                         importance=4, recurrence="multi", decimal=2):
    """
    Create a new document in the tickers collection with comprehensive fields.
    
    Parameters:
    ticker (str): The ticker symbol
    ticker_tradingview (str): The TradingView formatted ticker symbol
    name (str): The full name of the instrument
    asset_class (str): The asset class (default: None falls back to "EQ")
    region (str/list): Geographic region(s) for the instrument
    prompt (str): Analysis prompt for AI processing
    factors (str): Factor weights for analysis
    model_function (str): Processing function name
    model_name (str): Model name for analysis
    importance (int): Importance level (1-5, default:4)
    recurrence (str): Analysis frequency ("single"|"multi", default:"multi")
    decimal (int): Decimal precision for prices (default:2)
    
    Returns:
    InsertOneResult: The result of the insert operation
    """
    try:
        # Create the base document
        document = {
            "ticker": ticker,
            "ticker_tradingview": ticker_tradingview,
            "name": name,
            "asset_class": asset_class or "EQ",  # Default to EQ if not provided
            "document_generated": False,
            "importance": importance,
            "recurrence": recurrence,
            "decimal": decimal
        }
        
        # Add optional fields if provided
        if region:
            document["region"] = [region] if isinstance(region, str) else region
        if prompt:
            document["prompt"] = prompt
        if factors:
            document["factors"] = factors
        if model_function:
            document["model_function"] = model_function
        if model_name:
            document["model_name"] = model_name



        # Get MongoDB connection
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        collection = db['tickers']
        
        # Insert the document
        result = collection.insert_one(document)
        return result
        
    except pymongo.errors.DuplicateKeyError:
        log_error(f"Duplicate ticker: {ticker}", "TICKER_CREATION")
        return None
    except Exception as e:
        log_error(f"Error creating ticker {ticker}", "TICKER_CREATION", e)
        return None