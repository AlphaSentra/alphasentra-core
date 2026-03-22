"""
Description:
Script to fetch and import eToro instruments metadata into MongoDB.
"""

import os
import sys
import requests
import json

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from _config import (
    ETORO_API_INSTRUMENTS_METADATA,
    FX_LONG_SHORT_PROMPT,
    FX_FACTORS_PROMPT,
    IX_INDEX_LONG_SHORT_PROMPT,
    IX_INDEX_FACTORS_PROMPT,
    EQ_EQUITY_LONG_SHORT_PROMPT,
    EQ_EQUITY_FACTORS_PROMPT
)
from helpers import DatabaseManager, get_ticker_exchange_mapping
from logging_utils import log_info, log_error

def import_etoro_instruments(db=None):
    """
    Fetches all instruments from eToro API and imports them into 'etoro_instruments' collection.
    Clears existing data before importing.
    """
    collection_name = "etoro_instruments"

    print()
    print("=" * 100)
    print(f"Inserting metadata into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    try:
        # 1. Fetch data from eToro API
        log_info(f"Fetching eToro instruments from: {ETORO_API_INSTRUMENTS_METADATA}")
        response = requests.get(ETORO_API_INSTRUMENTS_METADATA)
        response.raise_for_status()
        
        data = response.json()
        
        # eToro API usually returns an object with an 'InstrumentDisplayDatas' key or similar
        # Based on typical eToro API structure, we expect a list of instruments
        instruments = []
        if isinstance(data, list):
            instruments = data
        elif isinstance(data, dict):
            # Try common keys if it's a dict
            instruments = data.get('InstrumentDisplayDatas', data.get('instruments', []))
            if not instruments and len(data) > 0:
                # If it's a dict but no common keys, maybe the data is the dict itself or in another key
                # For this API, it's usually a list or has a specific key.
                # Let's check if there's any list value in the dict
                for key, value in data.items():
                    if isinstance(value, list):
                        instruments = value
                        break
        
        if not instruments:
            log_error("No instruments found in eToro API response", "ETORO_IMPORT")
            return False
            
        log_info(f"Successfully fetched {len(instruments)} instruments from eToro")

        # 2. Connect to MongoDB if db is not provided
        if db is None:
            db_manager = DatabaseManager()
            client = db_manager.get_client()
            db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
            db = client[db_name]
        
        collection = db[collection_name]

        # 3. Clear existing collection data
        log_info(f"Clearing existing data from collection '{collection_name}'")
        delete_result = collection.delete_many({})
        log_info(f"Deleted {delete_result.deleted_count} existing documents")

        # 4. Import new data
        log_info(f"Importing {len(instruments)} new instruments into '{collection_name}'")
        if instruments:
            # MongoDB insert_many has a limit on document size and count, but for instruments it should be fine.
            # However, it's safer to do it in batches if the list is very large.
            batch_size = 1000
            for i in range(0, len(instruments), batch_size):
                batch = instruments[i:i + batch_size]
                collection.insert_many(batch)
            
            log_info(f"Successfully imported all instruments into '{collection_name}'")
        
        return True

    except requests.exceptions.RequestException as e:
        log_error(f"Failed to fetch data from eToro API: {e}", "ETORO_API_ERROR")
        return False
    except Exception as e:
        log_error(f"An error occurred during eToro instruments import: {e}", "ETORO_IMPORT_ERROR")
        return False

def create_excluded_etoro_instruments_collection(db=None):
    """
    Creates a collection 'etoro_instruments_excluded' containing documents from 'etoro_instruments'
    that do not exist in the 'tickers' collection (matching 'SymbolFull' in etoro_instruments 
    with 'ticker_etoro' in tickers).
    """
    source_collection_name = "etoro_instruments"
    target_collection_name = "etoro_instruments_excluded"
    tickers_collection_name = "tickers"

    log_info(f"Creating collection '{target_collection_name}' from instruments excluded in '{tickers_collection_name}'...")

    try:
        # 1. Connect to MongoDB if db is not provided
        if db is None:
            db_manager = DatabaseManager()
            client = db_manager.get_client()
            db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
            db = client[db_name]

        source_collection = db[source_collection_name]
        target_collection = db[target_collection_name]
        tickers_collection = db[tickers_collection_name]

        # 2. Get all ticker_etoro values from tickers collection
        log_info(f"Fetching existing eToro tickers from '{tickers_collection_name}'...")
        existing_tickers = tickers_collection.distinct("ticker_etoro")
        existing_tickers_set = set(existing_tickers)
        log_info(f"Found {len(existing_tickers_set)} unique eToro tickers in '{tickers_collection_name}'")

        # 3. Get all SymbolFull already in etoro_instruments_excluded to avoid duplicates
        log_info(f"Fetching existing symbols from '{target_collection_name}'...")
        already_excluded = target_collection.distinct("SymbolFull")
        already_excluded_set = set(already_excluded)
        log_info(f"Found {len(already_excluded_set)} symbols already in '{target_collection_name}'")

        # 4. Find instruments in etoro_instruments that are not in tickers AND not already in target_collection
        log_info(f"Finding new instruments in '{source_collection_name}'...")
        all_etoro_instruments = list(source_collection.find({}))
        
        new_excluded_instruments = []
        for instrument in all_etoro_instruments:
            symbol_full = instrument.get("SymbolFull")
            if symbol_full and symbol_full not in existing_tickers_set and symbol_full not in already_excluded_set:
                # Add excluded key with default value False
                instrument["excluded"] = False
                new_excluded_instruments.append(instrument)

        log_info(f"Found {len(new_excluded_instruments)} new instruments to add to '{target_collection_name}'")

        # 5. Insert new excluded instruments into target collection
        if new_excluded_instruments:
            log_info(f"Inserting {len(new_excluded_instruments)} new excluded instruments into '{target_collection_name}'...")
            batch_size = 1000
            for i in range(0, len(new_excluded_instruments), batch_size):
                batch = new_excluded_instruments[i:i + batch_size]
                target_collection.insert_many(batch)
            log_info(f"Successfully updated '{target_collection_name}'")
        else:
            log_info(f"No new excluded instruments found.")

        return True

    except Exception as e:
        log_error(f"An error occurred while creating excluded eToro instruments collection: {e}", "ETORO_EXCLUDED_ERROR")
        return False
    
def set_etoro_instrument_excluded_status(symbol_full=None, excluded=True, db=None):
    """
    Updates the 'excluded' status of instruments in 'etoro_instruments_excluded' collection.
    If symbol_full is None, it updates ALL documents in the collection.
    """
    collection_name = "etoro_instruments_excluded"

    try:
        # 1. Connect to MongoDB if db is not provided
        if db is None:
            db_manager = DatabaseManager()
            client = db_manager.get_client()
            db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
            db = client[db_name]

        collection = db[collection_name]

        # 2. Update the excluded status
        if symbol_full:
            log_info(f"Setting 'excluded' to {excluded} for instrument '{symbol_full}' in '{collection_name}'")
            result = collection.update_one(
                {"SymbolFull": symbol_full},
                {"$set": {"excluded": excluded}}
            )
            if result.matched_count == 0:
                log_error(f"No instrument found with SymbolFull '{symbol_full}' in '{collection_name}'", "ETORO_UPDATE_ERROR")
                return False
        else:
            log_info(f"Setting 'excluded' to {excluded} for ALL documents in '{collection_name}'")
            result = collection.update_many(
                {},
                {"$set": {"excluded": excluded}}
            )
            log_info(f"Updated {result.modified_count} documents in '{collection_name}'")

        return True

    except Exception as e:
        log_error(f"An error occurred while updating excluded status: {e}", "ETORO_UPDATE_ERROR")
        return False

def display_non_excluded_instruments(db=None):
    """
    Displays a beautiful table in the terminal of documents where excluded = False.
    Maps InstrumentTypeID to asset_class and ExchangeID to region using reference collections.
    """
    collection_name = "etoro_instruments_excluded"
    
    try:
        # 1. Connect to MongoDB if db is not provided
        if db is None:
            db_manager = DatabaseManager()
            client = db_manager.get_client()
            db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
            db = client[db_name]

        collection = db[collection_name]
        asset_classes_col = db["asset_classes"]
        regions_col = db["regions"]

        # 2. Fetch reference data for mapping
        asset_map = {doc["etoro_instrumentTypeId"]: doc.get("code", "N/A")
                     for doc in asset_classes_col.find({"etoro_instrumentTypeId": {"$exists": True}})}
        region_map = {doc["etoro_exchangeID"]: doc.get("region", "N/A")
                      for doc in regions_col.find({"etoro_exchangeID": {"$exists": True}})}

        # 3. Fetch non-excluded documents
        query = {"excluded": False}
        instruments = list(collection.find(query))

        if not instruments:
            print("\nNo instruments found with excluded = False.\n")
            return True

        # 4. Print table header
        header = f"{'DisplayName':<40} | {'SymbolFull':<20} | {'Asset Class':<15} | {'TypeID':<8} | {'Region':<15} | {'ExchID':<8}"
        print("\n" + "=" * len(header))
        print("NEW ETORO INSTRUMENTS")
        print("=" * len(header))
        print(header)
        print("-" * len(header))

        # 5. Print rows
        for inst in instruments:
            display_name = inst.get("InstrumentDisplayName", "N/A")[:40]
            type_id = inst.get("InstrumentTypeID", "N/A")
            exchange_id = inst.get("ExchangeID", "N/A")
            symbol_full = inst.get("SymbolFull", "N/A")[:20]

            asset_class = asset_map.get(type_id, "N/A")
            region = region_map.get(exchange_id, "N/A")

            print(f"{display_name:<40} | {symbol_full:<20} | {asset_class:<15} | {str(type_id):<8} | {region:<15} | {str(exchange_id):<8}")

        print("-" * len(header))
        print(f"Total: {len(instruments)} instruments")
        print("=" * len(header) + "\n")

        return True

    except Exception as e:
        log_error(f"An error occurred while displaying instruments: {e}", "ETORO_DISPLAY_ERROR")
        return False

def export_non_excluded_to_json(db=None):
    """
    Exports non-excluded instruments to a structured JSON file importable to MongoDB.
    """
    collection_name = "etoro_instruments_excluded"
    output_file = "etoro_importable.json"
    
    try:
        if db is None:
            db_manager = DatabaseManager()
            client = db_manager.get_client()
            db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
            db = client[db_name]

        collection = db[collection_name]
        asset_classes_col = db["asset_classes"]
        regions_col = db["regions"]

        # Fetch reference data
        # asset_map maps type_id to code
        asset_map = {doc["etoro_instrumentTypeId"]: doc.get("code", "N/A")
                     for doc in asset_classes_col.find({"etoro_instrumentTypeId": {"$exists": True}})}
        region_map = {doc["etoro_exchangeID"]: doc.get("region", "N/A")
                      for doc in regions_col.find({"etoro_exchangeID": {"$exists": True}})}

        instruments = list(collection.find({"excluded": False}))

        if not instruments:
            log_info("No non-excluded instruments to export.")
            return False

        export_data = []
        for inst in instruments:
            symbol_full = inst.get("SymbolFull")
            display_name = inst.get("InstrumentDisplayName", inst.get("SymbolFull"))
            type_id = inst.get("InstrumentTypeID")
            exchange_id = inst.get("ExchangeID")
            
            asset_code = asset_map.get(type_id, "N/A")
            region = region_map.get(exchange_id, "N/A")

            # Default values
            model_function = "run_holistic_market_model"
            model_name = "holistic"
            prompt = ""
            factors = ""

            # Mapping based on asset code (FX=FX, IX=Indices, EQ=Equities)
            if asset_code == "FX":
                model_function = "run_fx_model"
                model_name = "fx_long_short"
                prompt = FX_LONG_SHORT_PROMPT
                factors = FX_FACTORS_PROMPT
            elif asset_code == "IX":
                prompt = IX_INDEX_LONG_SHORT_PROMPT
                factors = IX_INDEX_FACTORS_PROMPT
            elif asset_code == "EQ":
                prompt = EQ_EQUITY_LONG_SHORT_PROMPT
                factors = EQ_EQUITY_FACTORS_PROMPT

            # Structure based on user requirements
            entry = {
                "ticker": get_ticker_exchange_mapping(symbol_full, exchange_id, "yfinance", "auto"),
                "ticker_tradingview": get_ticker_exchange_mapping(symbol_full, exchange_id, "tradingview", "auto"),
                "ticker_etoro": symbol_full,
                "name": display_name,
                "region": [region] if region != "N/A" else [],
                "prompt": prompt,
                "factors": factors,
                "model_function": model_function,
                "model_name": model_name,
                "asset_class": asset_code,
                "importance": 4,
                "recurrence": "multi",
                "decimal": 2,
                "document_generated": True,
                "instrumenttypeID": type_id
            }
            export_data.append(entry)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)

        log_info(f"Successfully exported {len(export_data)} instruments to {output_file}")
        print(f"\nFile '{output_file}' has been created with {len(export_data)} entries.\n")
        return True

    except Exception as e:
        log_error(f"An error occurred during JSON export: {e}", "ETORO_EXPORT_ERROR")
        return False

def run_import_etoro_instruments_with_confirmation(db=None):
    """
    Runs the full import process with confirmation, including metadata import,
    excluded collection creation, and displaying the results with user action prompt.
    """
    print("\n" + "=" * 100)
    print("STARTING ETORO INSTRUMENTS IMPORT PROCESS")
    print("=" * 100)

    # 1. Connect to MongoDB if db is not provided (needed for cleanup later)
    if db is None:
        db_manager = DatabaseManager()
        client = db_manager.get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        db = client[db_name]

    # 2. Import all metadata from API
    if not import_etoro_instruments(db):
        log_error("Failed to import eToro instruments from API", "ETORO_PROCESS_ERROR")
        return False

    # 3. Update excluded collection
    if not create_excluded_etoro_instruments_collection(db):
        log_error("Failed to update excluded instruments collection", "ETORO_PROCESS_ERROR")
        return False

    # 4. Display results
    display_non_excluded_instruments(db)

    # 5. User action prompt
    print("\nActions for displayed instruments:")
    print("1. Exclude them (set excluded = True)")
    print("2. Remove them (delete from excluded collection)")
    print("3. Keep them (do nothing)")
    print("4. Download Importable JSON")
    
    choice = input("\nSelect an action (1/2/3/4): ").strip()

    if choice in ['1', '2']:
        action_name = "exclude" if choice == '1' else "remove"
        confirm_action = input(f"Are you sure you want to {action_name} these instruments? (y/n): ").strip().lower()
        if confirm_action != 'y':
            log_info("Action cancelled by user.")
            return True

    if choice == '1':
        set_etoro_instrument_excluded_status(db=db)
    elif choice == '2':
        try:
            collection = db["etoro_instruments_excluded"]
            result = collection.delete_many({"excluded": False})
            log_info(f"Deleted {result.deleted_count} instruments from 'etoro_instruments_excluded'")
        except Exception as e:
            log_error(f"Failed to remove instruments: {e}", "ETORO_REMOVE_ERROR")
    elif choice == '3':
        log_info("Keeping instruments for now.")
    elif choice == '4':
        export_non_excluded_to_json(db=db)
    else:
        print("Invalid choice. No action taken.")

    print("\n" + "=" * 100)
    print("ETORO INSTRUMENTS IMPORT PROCESS COMPLETED")
    print("=" * 100 + "\n")
    
    return True


if __name__ == "__main__":
    run_import_etoro_instruments_with_confirmation()
