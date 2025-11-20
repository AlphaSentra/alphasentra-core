"""
Contains functions for inserting metal commodities data into MongoDB.
"""

import pymongo
from logging_utils import log_error
from _config import ME_METALS_LONG_SHORT_PROMPT, ME_METALS_FACTORS_PROMPT
def insert_metal_commodities(db):
    """
    Inserts metal commodities into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Inserting metal commodities into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Metal commodities data to insert with prompt and model_function fields
    metal_commodities = [
        {"ticker": "GC=F", "ticker_tradingview": "OANDA:XAUUSD", "name": "Gold", "region": ["Global"], "prompt": ME_METALS_LONG_SHORT_PROMPT, "factors": ME_METALS_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "ME", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SI=F", "ticker_tradingview": "OANDA:XAGUSD", "name": "Silver", "region": ["Global"], "prompt": ME_METALS_LONG_SHORT_PROMPT, "factors": ME_METALS_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "ME", "importance": 4, "recurrence": "multi", "decimal":3, "document_generated": False},
        {"ticker": "PL=F", "ticker_tradingview": "OANDA:XPTUSD", "name": "Platinum", "region": ["Global"], "prompt": ME_METALS_LONG_SHORT_PROMPT, "factors": ME_METALS_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "ME", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any metal commodities already exist to avoid duplicates
        existing_count = collection.count_documents({"ticker": {"$in": [item["ticker"] for item in metal_commodities]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing metal commodities. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all metal commodities
        result = collection.insert_many(metal_commodities)
        print(f"Successfully inserted {len(result.inserted_ids)} metal commodities into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting metal commodities", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting metal commodities", "DATA_INSERTION", e)
        return False