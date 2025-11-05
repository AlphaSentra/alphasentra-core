"""
Module for inserting stock indices data into MongoDB
"""

import pymongo
from logging_utils import log_error
from _config import IX_INDEX_LONG_SHORT_PROMPT, IX_INDEX_FACTORS_PROMPT
def insert_indices(db):
    """
    Inserts stock indices into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Inserting indices into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Indices data to insert with prompt and model_function fields
    indices = [
        #{"ticker": "^GSPC", "ticker_tradingview": "SPX500USD", "name": "US SPX 500 Index (S&P 500)", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "^IXIC", "ticker_tradingview": "NAS100USD", "name": "US Tech 100 Index (NASDAQ 100)", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        #{"ticker": "^DJI", "ticker_tradingview": "US30USD", "name": "US Wall Street 30 Index (Dow Jones)", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        #{"ticker": "^GDAXI", "ticker_tradingview": "GER30", "name": "Germany 30 Index (DAX)", "region": ["Germany"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^FTSE", "ticker_tradingview": "UK100GBP", "name": "UK 100 Index (FTSE 100)", "region": ["UK"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        #{"ticker": "^N225", "ticker_tradingview": "JP225", "name": "Japan 225 Index (Nikkei)", "region": ["Japan"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        #{"ticker": "^HSI", "ticker_tradingview": "HK50", "name": "Hong Kong 50 Index (Hang Seng)", "region": ["Hong Kong"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        #{"ticker": "^RUT", "ticker_tradingview": "US2000USD", "name": "Russell 2000 Index", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^STOXX50E", "ticker_tradingview": "EUSTX50", "name": "Euro Stoxx 50 Index", "region": ["Eurozone"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        #{"ticker": "^FCHI", "ticker_tradingview": "FRA40", "name": "France 40 Index (CAC 40)", "region": ["France"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^AXJO", "ticker_tradingview": "AUS200", "name": "Australia 200 Index (ASX 200)", "region": ["Australia"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        #{"ticker": "^SSMI", "ticker_tradingview": "SWI20", "name": "Switzerland 20 Index (SMI)", "region": ["Switzerland"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        #{"ticker": "^AEX", "ticker_tradingview": "NTH25", "name": "Netherlands 25 Cash Index (AEX)", "region": ["Netherlands"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any indices already exist to avoid duplicates
        existing_count = collection.count_documents({"ticker": {"$in": [index["ticker"] for index in indices]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing indices. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all indices
        result = collection.insert_many(indices)
        print(f"Successfully inserted {len(result.inserted_ids)} indices into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting indices", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting indices", "DATA_INSERTION", e)
        return False