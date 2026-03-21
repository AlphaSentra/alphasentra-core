import os
import pymongo.errors
import sys

# Add the parent directory to the Python path to ensure imports work when running from subdirectories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from logging_utils import log_error, log_info, log_warning
from _config import EQ_EQUITY_LONG_SHORT_PROMPT, EQ_EQUITY_FACTORS_PROMPT
from helpers import get_etoro_instrumenttypeid, get_ticker_exchange_mapping, DatabaseManager

def insert_equities(db):
    """
    Inserts global equities and ETFs from 'etoro_instruments' into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    etoro_collection_name = 'etoro_instruments'
    
    # Get the eToro instrumentTypeIds for "EQ" (Equities) and "ETF"
    etoro_eq_id = get_etoro_instrumenttypeid("EQ")
    etoro_etf_id = get_etoro_instrumenttypeid("ETF")
    
    if etoro_eq_id is None:
        log_error("Could not find instrumentTypeId for 'EQ'", "DATA_INSERTION")
        return False

    try:
        etoro_collection = db[etoro_collection_name]
        tickers_collection = db[collection_name]
        regions_collection = db['regions']
        
        # Pre-fetch regions mapping to identify the region for each exchange
        regions_docs = list(regions_collection.find({}, {"etoro_exchangeID": 1, "region": 1}))
        exchange_to_region = {doc['etoro_exchangeID']: doc['region'] for doc in regions_docs if 'etoro_exchangeID' in doc}
        
        # Query etoro_instruments for both EQ and ETF (if ETF id found)
        type_ids = [etoro_eq_id]
        if etoro_etf_id:
            type_ids.append(etoro_etf_id)
            
        query = {
            "IsInternalInstrument": False,
            "InstrumentTypeID": {"$in": type_ids}
        }
        
        etoro_instruments_docs = list(etoro_collection.find(query))
        
        if not etoro_instruments_docs:
            log_info(f"No instruments found in '{etoro_collection_name}' for InstrumentTypeIDs: {type_ids}")
            return True

        print()
        print("=" * 100)
        print(f"Processing and inserting equities into '{collection_name}' collection...")
        print("=" * 100)
        print()
        
        # Mapping etoro_instruments to tickers collection structure
        equities_to_insert = []
        for doc in etoro_instruments_docs:
            ticker = doc.get('SymbolFull')
            if not ticker:
                continue
                
            # Check if already exists in tickers collection to avoid duplicates
            if tickers_collection.count_documents({"ticker_etoro": ticker}) > 0:
                continue
                
            # Map fields to match the desired structure
            exchange_id = doc.get('exchangeID', doc.get('ExchangeID', 0))
            region_name = exchange_to_region.get(exchange_id, "Global")
            
            # Determine asset class based on instrumenttypeID
            doc_type_id = doc.get('InstrumentTypeID')
            asset_class = "EQ"
            if doc_type_id == etoro_etf_id:
                asset_class = "ETF"

            log_info(f"Mapping eToro ticker '{ticker}' with exchange ID '{exchange_id}' for region '{region_name}' and asset class '{asset_class}'")

            mapped_doc = {
                "ticker": get_ticker_exchange_mapping(ticker, exchange_id, "yfinance", "auto"),
                "ticker_tradingview": get_ticker_exchange_mapping(ticker, exchange_id, "tradingview", "auto"),
                "ticker_etoro": ticker,
                "name": doc.get('InstrumentDisplayName', doc.get('SymbolFull', doc.get('Symbol'))),
                "region": [region_name],
                "prompt": EQ_EQUITY_LONG_SHORT_PROMPT,
                "factors": EQ_EQUITY_FACTORS_PROMPT,
                "model_function": "run_holistic_market_model",
                "model_name": "holistic",
                "asset_class": asset_class,
                "importance": 4,
                "recurrence": "multi",
                "decimal": 2,
                "document_generated": True,
                "instrumenttypeID": doc_type_id
            }
            equities_to_insert.append(mapped_doc)
            
        if equities_to_insert:
            result = tickers_collection.insert_many(equities_to_insert)
            log_info(f"Successfully inserted {len(result.inserted_ids)} equities into '{collection_name}' collection")
        else:
            log_warning("No new equities to insert.")
            
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting equities", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting equities", "DATA_INSERTION", e)
        return False

if __name__ == "__main__":
    db_manager = DatabaseManager()
    client = db_manager.get_client()
    db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
    db = client[db_name]
    
    insert_equities(db)