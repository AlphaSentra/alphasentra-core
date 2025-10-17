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
        {"ticker": "AUDCAD=X", "ticker_tradingview": "FX_IDC:AUDCAD", "name": "Australian Dollar / Canadian Dollar", "region": ["Australia", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "AUDCHF=X", "ticker_tradingview": "FX_IDC:AUDCHF", "name": "Australian Dollar / Swiss Franc", "region": ["Australia", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "AUDJPY=X", "ticker_tradingview": "FX_IDC:AUDJPY", "name": "Australian Dollar / Japanese Yen", "region": ["Australia", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "AUDNZD=X", "ticker_tradingview": "FX_IDC:AUDNZD", "name": "Australian Dollar / New Zealand Dollar", "region": ["Australia", "New Zealand"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "AUDSGD=X", "ticker_tradingview": "FX_IDC:AUDSGD", "name": "Australian Dollar / Singapore Dollar", "region": ["Australia", "Singapore"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "AUDUSD=X", "ticker_tradingview": "FX_IDC:AUDUSD", "name": "Australian Dollar / U.S. Dollar", "region": ["Australia", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "CADCHF=X", "ticker_tradingview": "FX_IDC:CADCHF", "name": "Canadian Dollar / Swiss Franc", "region": ["Canada", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "CADJPY=X", "ticker_tradingview": "FX_IDC:CADJPY", "name": "Canadian Dollar / Japanese Yen", "region": ["Canada", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "CHFJPY=X", "ticker_tradingview": "FX_IDC:CHFJPY", "name": "Swiss Franc / Japanese Yen", "region": ["Switzerland", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURAUD=X", "ticker_tradingview": "FX_IDC:EURAUD", "name": "Euro / Australian Dollar", "region": ["Eurozone", "Australia"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURCAD=X", "ticker_tradingview": "FX_IDC:EURCAD", "name": "Euro / Canadian Dollar", "region": ["Eurozone", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURCHF=X", "ticker_tradingview": "FX_IDC:EURCHF", "name": "Euro / Swiss Franc", "region": ["Eurozone", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURGBP=X", "ticker_tradingview": "FX_IDC:EURGBP", "name": "Euro / Great British Pound", "region": ["Eurozone", "UK"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURHKD=X", "ticker_tradingview": "FX_IDC:EURHKD", "name": "Euro / Hong Kong Dollar", "region": ["Eurozone", "Hong Kong"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURHUF=X", "ticker_tradingview": "FX_IDC:EURHUF", "name": "Euro / Hungarian Forint", "region": ["Eurozone", "Hungary"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURJPY=X", "ticker_tradingview": "FX_IDC:EURJPY", "name": "Euro / Japanese Yen", "region": ["Eurozone", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURNOK=X", "ticker_tradingview": "FX_IDC:EURNOK", "name": "Euro / Norwegian Krone", "region": ["Eurozone", "Norway"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURNZD=X", "ticker_tradingview": "FX_IDC:EURNZD", "name": "Euro / New Zealand Dollar", "region": ["Eurozone", "New Zealand"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURSGD=X", "ticker_tradingview": "FX_IDC:EURSGD", "name": "Euro / Singapore Dollar", "region": ["Eurozone", "Singapore"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURUSD=X", "ticker_tradingview": "FX_IDC:EURUSD", "name": "Euro / U.S. Dollar", "region": ["Eurozone", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPAUD=X", "ticker_tradingview": "FX_IDC:GBPAUD", "name": "Great British Pound / Australian Dollar", "region": ["UK", "Australia"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPCAD=X", "ticker_tradingview": "FX_IDC:GBPCAD", "name": "Great British Pound / Canadian Dollar", "region": ["UK", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPCHF=X", "ticker_tradingview": "FX_IDC:GBPCHF", "name": "Great British Pound / Swiss Franc", "region": ["UK", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPJPY=X", "ticker_tradingview": "FX_IDC:GBPJPY", "name": "Great British Pound / Japanese Yen", "region": ["UK", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPNZD=X", "ticker_tradingview": "FX_IDC:GBPNZD", "name": "Great British Pound / New Zealand Dollar", "region": ["UK", "New Zealand"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPSGD=X", "ticker_tradingview": "FX_IDC:GBPSGD", "name": "Great British Pound / Singapore Dollar", "region": ["UK", "Singapore"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPUSD=X", "ticker_tradingview": "FX_IDC:GBPUSD", "name": "Great British Pound / U.S. Dollar", "region": ["UK", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "NZDCAD=X", "ticker_tradingview": "FX_IDC:NZDCAD", "name": "New Zealand Dollar / Canadian Dollar", "region": ["New Zealand", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "NZDCHF=X", "ticker_tradingview": "FX_IDC:NZDCHF", "name": "New Zealand Dollar / Swiss Franc", "region": ["New Zealand", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "NZDJPY=X", "ticker_tradingview": "FX_IDC:NZDJPY", "name": "New Zealand Dollar / Japanese Yen", "region": ["New Zealand", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "NZDSGD=X", "ticker_tradingview": "FX_IDC:NZDSGD", "name": "New Zealand Dollar / Singapore Dollar", "region": ["New Zealand", "Singapore"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "NZDUSD=X", "ticker_tradingview": "FX_IDC:NZDUSD", "name": "New Zealand Dollar / U.S. Dollar", "region": ["New Zealand", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "SGDJPY=X", "ticker_tradingview": "FX_IDC:SGDJPY", "name": "Singapore Dollar / Japanese Yen", "region": ["Singapore", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDCAD=X", "ticker_tradingview": "FX_IDC:USDCAD", "name": "U.S. Dollar / Canadian Dollar", "region": ["US", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDCHF=X", "ticker_tradingview": "FX_IDC:USDCHF", "name": "U.S. Dollar / Swiss Franc", "region": ["US", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDCNH=X", "ticker_tradingview": "FX_IDC:USDCNH", "name": "U.S. Dollar / Offshore Chinese Yuan", "region": ["US", "China"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDDKK=X", "ticker_tradingview": "FX_IDC:USDDKK", "name": "U.S. Dollar / Danish Krone", "region": ["US", "Denmark"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDHUF=X", "ticker_tradingview": "FX_IDC:USDHUF", "name": "U.S. Dollar / Hungarian Forint", "region": ["US", "Hungary"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDJPY=X", "ticker_tradingview": "FX_IDC:USDJPY", "name": "U.S. Dollar / Japanese Yen", "region": ["US", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDMXN=X", "ticker_tradingview": "FX_IDC:USDMXN", "name": "U.S. Dollar / Mexican Peso", "region": ["US", "Mexico"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDNOK=X", "ticker_tradingview": "FX_IDC:USDNOK", "name": "U.S. Dollar / Norwegian Krone", "region": ["US", "Norway"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDSGD=X", "ticker_tradingview": "FX_IDC:USDSGD", "name": "U.S. Dollar / Singapore Dollar", "region": ["US", "Singapore"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False}
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