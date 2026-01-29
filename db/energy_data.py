import pymongo.errors
from _config import EN_ENERGY_LONG_SHORT_PROMPT, EN_ENERGY_FACTORS_PROMPT
from logging_utils import log_error

def insert_energy_commodities(db):
    """
    Inserts energy commodities into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Inserting energy commodities into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Energy commodities data to insert with prompt and model_function fields
    energy_commodities = [
        {"ticker": "CL=F", "ticker_tradingview": "TVC:USOIL", "name": "Crude Oil WTI", "region": ["US", "Global"], "prompt": EN_ENERGY_LONG_SHORT_PROMPT, "factors": EN_ENERGY_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EN", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": True},
        {"ticker": "BZ=F", "ticker_tradingview": "TVC:UKOIL", "name": "Crude Oil Brent", "region": ["UK", "Global"], "prompt": EN_ENERGY_LONG_SHORT_PROMPT, "factors": EN_ENERGY_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EN", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": True},
        {"ticker": "NG=F", "ticker_tradingview": "NATGAS", "name": "Natural Gas", "region": ["US", "Global"], "prompt": EN_ENERGY_LONG_SHORT_PROMPT, "factors": EN_ENERGY_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EN", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": True}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any energy commodities already exist to avoid duplicates
        existing_count = collection.count_documents({"ticker": {"$in": [item["ticker"] for item in energy_commodities]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing energy commodities. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all energy commodities
        result = collection.insert_many(energy_commodities)
        print(f"Successfully inserted {len(result.inserted_ids)} energy commodities into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting energy commodities", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting energy commodities", "DATA_INSERTION", e)
        return False