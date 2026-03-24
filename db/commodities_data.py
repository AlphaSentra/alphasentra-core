import os
import pymongo.errors
import sys

# Add the parent directory to the Python path to ensure imports work when running from subdirectories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from _config import EN_ENERGY_LONG_SHORT_PROMPT, EN_ENERGY_FACTORS_PROMPT
from _config import ME_METALS_FACTORS_PROMPT, ME_METALS_LONG_SHORT_PROMPT
from _config import AG_AGRICULTURE_FACTORS_PROMPT, AG_AGRICULTURE_LONG_SHORT_PROMPT
from logging_utils import log_error, log_info, log_warning
from helpers import DatabaseManager, get_etoro_instrumenttypeid, get_ticker_exchange_mapping

def insert_commodities_asset(db):
    """
    Inserts commodities assets from 'etoro_instruments' into the 'tickers' collection,
    categorizing them by keyword into Energy, Agriculture, or Metals.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    etoro_collection_name = 'etoro_instruments'
    
    # Get the eToro instrumentTypeId for "CO" (Commodities)
    etoro_instrument_type_id = get_etoro_instrumenttypeid("CO")
    
    if etoro_instrument_type_id is None:
        log_error("Could not find instrumentTypeId for 'CO'", "DATA_INSERTION")
        return False

    # Categorization keywords
    energy_keywords = ["carbon", "oil", "gas"]
    agri_keywords = ["cocoa", "cotton", "coffee", "corn", "sugar", "soybeans", "wheat"]
    metal_keywords = ["aluminum", "copper", "lead", "nickel", "zinc", "palladium", "silver", "gold", "platinum"]

    try:
        etoro_collection = db[etoro_collection_name]
        tickers_collection = db[collection_name]
        
        # Check if any commodity instruments already exist in the 'tickers' collection
        # (Commodities are categorized as EN, ME, or AG)
        if tickers_collection.count_documents({"asset_class": {"$in": ["EN", "ME", "AG"]}}) > 0:
            log_info(f"The '{collection_name}' collection already contains commodity assets (EN, ME, or AG). Skipping insertion.")
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
        print(f"Processing and inserting commodities into '{collection_name}' collection...")
        print("=" * 100)
        print()
        
        # Mapping etoro_instruments to tickers collection structure
        commodities_to_insert = []
        for doc in etoro_instruments_docs:
            ticker = doc.get('SymbolFull')
            if not ticker:
                continue
                
            # Check if already exists in tickers collection to avoid duplicates
            if tickers_collection.count_documents({"ticker": ticker}) > 0:
                continue
                
            symbol_full = doc.get('SymbolFull', '').lower()
            
            # Default values (falling back to energy if no match found)
            prompt = EN_ENERGY_LONG_SHORT_PROMPT
            factors = EN_ENERGY_FACTORS_PROMPT
            asset_class = "EN"
            
            # Check for matches in keywords
            if any(kw in symbol_full for kw in metal_keywords):
                prompt = ME_METALS_LONG_SHORT_PROMPT
                factors = ME_METALS_FACTORS_PROMPT
                asset_class = "ME"
            elif any(kw in symbol_full for kw in agri_keywords):
                prompt = AG_AGRICULTURE_LONG_SHORT_PROMPT
                factors = AG_AGRICULTURE_FACTORS_PROMPT
                asset_class = "AG"
            elif any(kw in symbol_full for kw in energy_keywords):
                prompt = EN_ENERGY_LONG_SHORT_PROMPT
                factors = EN_ENERGY_FACTORS_PROMPT
                asset_class = "EN"

            log_info(f"Mapping eToro ticker '{ticker}' for commodity asset with determined asset class '{asset_class}'")

            # Map fields to match the desired structure
            exchange_id = doc.get('exchangeID', doc.get('ExchangeID', 0))
            mapped_doc = {
                "ticker": get_ticker_exchange_mapping(ticker, exchange_id, "yfinance", "auto"),
                "ticker_tradingview": get_ticker_exchange_mapping(ticker, exchange_id, "tradingview", "auto"),
                "ticker_etoro": ticker,
                "name": doc.get('InstrumentDisplayName', doc.get('SymbolFull', doc.get('Symbol'))),
                "region": ["Global"],
                "prompt": prompt,
                "factors": factors,
                "model_function": "run_holistic_market_model",
                "model_name": "holistic",
                "asset_class": asset_class,
                "importance": 1,
                "recurrence": "multi",
                "decimal": 2,
                "document_generated": True,
                "instrumenttypeID": etoro_instrument_type_id
            }
            commodities_to_insert.append(mapped_doc)
            
        if commodities_to_insert:
            result = tickers_collection.insert_many(commodities_to_insert)
            log_info(f"Successfully inserted {len(result.inserted_ids)} commodities into '{collection_name}' collection")
        else:
            log_warning("No new commodities to insert.")
            
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting commodities", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting commodities", "DATA_INSERTION", e)
        return False
    
if __name__ == "__main__":
    db_manager = DatabaseManager()
    client = db_manager.get_client()
    db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
    db = client[db_name]
    
    insert_commodities_asset(db)
