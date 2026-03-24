import os
import pymongo.errors
import sys

# Add the parent directory to the Python path to ensure imports work when running from subdirectories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from logging_utils import log_error, log_info, log_warning
from _config import FX_LONG_SHORT_PROMPT, FX_FACTORS_PROMPT
from helpers import get_etoro_instrumenttypeid, get_ticker_exchange_mapping, DatabaseManager

def insert_fx_pairs(db):
    """
    Inserts FX currency pairs from 'etoro_instruments' into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    etoro_collection_name = 'etoro_instruments'
    
    # Get the eToro instrumentTypeId for "CURRENCIES" (FX)
    etoro_instrument_type_id = get_etoro_instrumenttypeid("FX")
    
    if etoro_instrument_type_id is None:
        log_error("Could not find instrumentTypeId for 'FX'", "DATA_INSERTION")
        return False

    try:
        etoro_collection = db[etoro_collection_name]
        tickers_collection = db[collection_name]
        
        # Check if any FX instruments already exist in the 'tickers' collection
        if tickers_collection.count_documents({"asset_class": "FX"}) > 0:
            log_info(f"The '{collection_name}' collection already contains 'FX' assets. Skipping insertion.")
            return True

        # Query etoro_instruments for non-internal instruments matching the instrumenttypeID
        query = {
            "IsInternalInstrument": False,
            "InstrumentTypeID": etoro_instrument_type_id
        }
        
        etoro_instruments_docs = list(etoro_collection.find(query))
        
        if not etoro_instruments_docs:
            log_info(f"No instruments found in '{etoro_collection_name}' for InstrumentTypeID: {etoro_instrument_type_id}")
            return True

        print()
        print("=" * 100)
        print(f"Processing and inserting FX pairs into '{collection_name}' collection...")
        print("=" * 100)
        print()
        
        # Mapping etoro_instruments to tickers collection structure
        fx_to_insert = []
        for doc in etoro_instruments_docs:
            ticker = doc.get('SymbolFull')
            if not ticker:
                continue
                
            # Check if already exists in tickers collection to avoid duplicates
            if tickers_collection.count_documents({"ticker_etoro": ticker}) > 0:
                continue
                
            # Map fields to match the desired structure
            exchange_id = doc.get('exchangeID', doc.get('ExchangeID', 0))
            
            # eToro FX tickers like "EURUSD" need to be mapped to Yahoo Finance "EURUSD=X"
            # and TradingView "FX_IDC:EURUSD" or similar.
            # get_ticker_exchange_mapping should handle this.

            log_info(f"Mapping eToro ticker '{ticker}' with exchange ID '{exchange_id}' for FX pair")
            
            mapped_doc = {
                "ticker": get_ticker_exchange_mapping(ticker, exchange_id, "yfinance", "auto"),
                "ticker_tradingview": get_ticker_exchange_mapping(ticker, exchange_id, "tradingview", "auto"),
                "ticker_etoro": ticker,
                "name": doc.get('InstrumentDisplayName', doc.get('SymbolFull', doc.get('Symbol'))),
                "region": ["Global"], # Defaulting to Global, but could be refined if needed
                "prompt": FX_LONG_SHORT_PROMPT,
                "factors": FX_FACTORS_PROMPT,
                "model_function": "run_fx_model",
                "model_name": "fx_long_short",
                "asset_class": "FX",
                "importance": 1,
                "recurrence": "multi",
                "decimal": 4,
                "document_generated": True,
                "instrumenttypeID": etoro_instrument_type_id
            }
            fx_to_insert.append(mapped_doc)

            
        if fx_to_insert:
            result = tickers_collection.insert_many(fx_to_insert)
            log_info(f"Successfully inserted {len(result.inserted_ids)} FX pairs into '{collection_name}' collection")
        else:
            log_warning("No new FX pairs to insert.")
            
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting FX pairs", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting FX pairs", "DATA_INSERTION", e)
        return False
    
    
if __name__ == "__main__":
    db_manager = DatabaseManager()
    client = db_manager.get_client()
    db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
    db = client[db_name]
    
    insert_fx_pairs(db)
