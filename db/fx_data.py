import pymongo
from _config import FX_LONG_SHORT_PROMPT, FX_FACTORS_PROMPT
from logging_utils import log_error

def insert_fx_pairs(db):
    """
    Inserts FX currency pairs into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Inserting FX pairs into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # FX pairs data to insert with prompt and model_function fields
    fx_pairs = [
        {"ticker": "AUDUSD=X", "ticker_tradingview": "FX_IDC:AUDUSD", "name": "Australian Dollar / U.S. Dollar", "region": ["Australia", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal":4, "decimal":4, "document_generated": True},
        {"ticker": "CADJPY=X", "ticker_tradingview": "FX_IDC:CADJPY", "name": "Canadian Dollar / Japanese Yen", "region": ["Canada", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal":4, "decimal":4, "document_generated": True},
        {"ticker": "CHFJPY=X", "ticker_tradingview": "FX_IDC:CHFJPY", "name": "Swiss Franc / Japanese Yen", "region": ["Switzerland", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal":4, "decimal":4, "document_generated": True},
        {"ticker": "EURAUD=X", "ticker_tradingview": "FX_IDC:EURAUD", "name": "Euro / Australian Dollar", "region": ["Eurozone", "Australia"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal":4, "document_generated": True},
        {"ticker": "EURCAD=X", "ticker_tradingview": "FX_IDC:EURCAD", "name": "Euro / Canadian Dollar", "region": ["Eurozone", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal":4, "document_generated": True},
        {"ticker": "EURGBP=X", "ticker_tradingview": "FX_IDC:EURGBP", "name": "Euro / Great British Pound", "region": ["Eurozone", "UK"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal":4, "document_generated": True},
        {"ticker": "EURJPY=X", "ticker_tradingview": "FX_IDC:EURJPY", "name": "Euro / Japanese Yen", "region": ["Eurozone", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal":4, "document_generated": True},
        {"ticker": "EURUSD=X", "ticker_tradingview": "FX_IDC:EURUSD", "name": "Euro / U.S. Dollar", "region": ["Eurozone", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal":4, "document_generated": True},
        {"ticker": "GBPJPY=X", "ticker_tradingview": "FX_IDC:GBPJPY", "name": "Great British Pound / Japanese Yen", "region": ["UK", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal":4, "document_generated": True},
        {"ticker": "GBPUSD=X", "ticker_tradingview": "FX_IDC:GBPUSD", "name": "Great British Pound / U.S. Dollar", "region": ["UK", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal":4, "document_generated": True},
        {"ticker": "NZDUSD=X", "ticker_tradingview": "FX_IDC:NZDUSD", "name": "New Zealand Dollar / U.S. Dollar", "region": ["New Zealand", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal":4, "document_generated": True},
        {"ticker": "USDCAD=X", "ticker_tradingview": "FX_IDC:USDCAD", "name": "U.S. Dollar / Canadian Dollar", "region": ["US", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal":4, "document_generated": True},
        {"ticker": "USDCHF=X", "ticker_tradingview": "FX_IDC:USDCHF", "name": "U.S. Dollar / Swiss Franc", "region": ["US", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal":4, "document_generated": True},
        {"ticker": "USDCNH=X", "ticker_tradingview": "FX_IDC:USDCNH", "name": "U.S. Dollar / Offshore Chinese Yuan", "region": ["US", "China"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal":4, "document_generated": True},
        {"ticker": "USDJPY=X", "ticker_tradingview": "FX_IDC:USDJPY", "name": "U.S. Dollar / Japanese Yen", "region": ["US", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal":4, "document_generated": True}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any FX pairs already exist to avoid duplicates
        existing_count = collection.count_documents({"ticker": {"$in": [pair["ticker"] for pair in fx_pairs]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing FX pairs. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all FX pairs
        result = collection.insert_many(fx_pairs)
        print(f"Successfully inserted {len(result.inserted_ids)} FX pairs into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting FX pairs", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting FX pairs", "DATA_INSERTION", e)
        return False