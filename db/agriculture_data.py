"""
Agriculture commodities data insertion functions for MongoDB
"""

import pymongo
from _config import AG_AGRICULTURE_LONG_SHORT_PROMPT, AG_AGRICULTURE_FACTORS_PROMPT
from logging_utils import log_error

def insert_agriculture_commodities(db):
    """
    Inserts agriculture commodities into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Inserting agriculture commodities into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Agriculture commodities data to insert with prompt and model_function fields
    agriculture_commodities = [
        {"ticker": "ZC=F", "ticker_tradingview": "CORN", "name": "Corn", "region": ["US"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": True},
        {"ticker": "ZS=F", "ticker_tradingview": "SOYBEAN", "name": "Soybeans", "region": ["US"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": True},
        {"ticker": "ZL=F", "ticker_tradingview": "SOYOIL", "name": "Soybean Oil", "region": ["US"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 4, "recurrence": "multi", "decimal":4, "document_generated": True},
        {"ticker": "ZW=F", "ticker_tradingview": "WHEAT", "name": "Wheat (US)", "region": ["US"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": True}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any agriculture commodities already exist to avoid duplicates
        existing_count = collection.count_documents({"ticker": {"$in": [item["ticker"] for item in agriculture_commodities]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing agriculture commodities. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all agriculture commodities
        result = collection.insert_many(agriculture_commodities)
        print(f"Successfully inserted {len(result.inserted_ids)} agriculture commodities into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting agriculture commodities", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting agriculture commodities", "DATA_INSERTION", e)
        return False