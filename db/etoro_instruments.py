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

from _config import ETORO_API_INSTRUMENTS_METADATA
from helpers import DatabaseManager
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

if __name__ == "__main__":
    import_etoro_instruments()
