import os
import sys
import json
from datetime import datetime, UTC # Changed for handling date fields and UTC timezone
import uuid # Added for generating task_id
from bson.objectid import ObjectId # Added for generating MongoDB ObjectId

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
import pymongo
from typing import List, Dict, Any, Optional
from helpers import DatabaseManager
from logging_utils import log_error, log_warning, log_info
from data.treasury_yield_utils import get_tlt_dividend_yield


def get_top_equities_for_selection_analysis(region: Optional[List[str]] = None, category: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Retrieves the top 10 equity tickers based on specific selection criteria for analysis.
    The criteria include:
    - asset_class: "EQ"
    - Filters and sorts dynamically based on 'category' (e.g., "growth" or "income").
    - Default sorting for "growth" category: 3m (desc), 1m (desc), 1w (desc), eps_growth (desc).

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents
                              a ticker document from the database.
                              Returns an empty list if no tickers are found or an error occurs.
    """
    load_dotenv()
    selected_equities = []
    client = None
    try:
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        tickers_collection = db["tickers"]
        pipeline_collection = db[os.getenv("MONGODB_TASK_COLLECTION", "pipeline")] # New collection for tasks (renamed to pipeline)

        query = {"asset_class": "EQ"}
        sort_fields_dict = {}

        if region and len(region) > 0:
            query["region"] = {"$in": region}

        log_info(f"Querying for equity tickers with conditions: {query}")

        if category and "growth" in category:
            query["eps_growth"] = {"$gt": 0}
            sort_fields_dict = {"3m": pymongo.DESCENDING, "1m": pymongo.DESCENDING, "1w": pymongo.DESCENDING, "eps_growth": pymongo.DESCENDING}
            log_info("Applying 'growth' category filters and sorts.")
        elif category and "income" in category:
            query["payout_ratio"] = {"$lt": 1}
            tlt_yield = get_tlt_dividend_yield() # yfinance returns dividend yield as a decimal (e.g., 0.04 for 4%)
            if tlt_yield > 0:
                query["dividend_yield"] = {"$gt": tlt_yield}
            else:
                log_warning("TLT dividend yield could not be fetched or was 0. Skipping dividend yield filter.")
            sort_fields_dict = {"3m": pymongo.DESCENDING, "1m": pymongo.DESCENDING, "1w": pymongo.DESCENDING, "dividend_yield": pymongo.DESCENDING}
            log_info("Applying 'income' category filters and sorts.")
        else:
            # Default to growth if no specific category or an unknown category is provided
            # This aligns with the original prompt's requirement for eps_growth > 0 and specific sorting
            query["eps_growth"] = {"$gt": 0}
            sort_fields_dict = {"3m": pymongo.DESCENDING, "1m": pymongo.DESCENDING, "1w": pymongo.DESCENDING, "eps_growth": pymongo.DESCENDING}
            log_warning("No specific or known category provided. Applying default 'growth' criteria.")

        sort_fields = list(sort_fields_dict.items()) if sort_fields_dict else []

        log_info(f"Final query for top equities with conditions: {query} and sorting by: {sort_fields}")

        cursor = tickers_collection.find(query).sort(sort_fields).limit(10)

        for doc in cursor:
            selected_equities.append(doc)
            
            # Construct the new document format
            new_doc = {
                "_id": ObjectId(), # Generate a new ObjectId for the task document
                "task_id": str(uuid.uuid4()),  # Generate a new UUID for task_id
                "model_function": "get_insights",
                "model_name": doc.get("ticker", "N/A"), # Use ticker from original doc
                "recurrence": "once",
                "task_completed": False,
                "createdAt": datetime.now(UTC), # Use timezone-aware datetime.now(UTC)
                "updatedAt": datetime.now(UTC), # Use timezone-aware datetime.now(UTC)
                "__v": 0
            }
            
            # Insert the new document into the tasks collection
            pipeline_collection.insert_one(new_doc)
            log_info(f"Inserted task for ticker {doc.get('ticker', 'N/A')} into the {pipeline_collection.name} collection.")

        log_info(f"Successfully retrieved {len(selected_equities)} top equities and inserted corresponding tasks for selection analysis.")

    except pymongo.errors.ServerSelectionTimeoutError as e:
        log_error("MongoDB server not found. Ensure MongoDB is running on the specified host/port.", "MONGODB_CONNECTION", e)
    except pymongo.errors.OperationFailure as e:
        log_error(f"MongoDB operation failed: {e}", "MONGODB_OPERATION", e)
    except Exception as e:
        log_error(f"An unexpected error occurred while fetching top equities from DB: {e}", "DATA_FETCHING", e)
    finally:
        if client:
            DatabaseManager().close_connection()
    return selected_equities


def get_top_cryptos_for_selection_analysis(region: Optional[List[str]] = None, category: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Retrieves the top 10 cryptocurrency tickers based on specific selection criteria for analysis.
    The criteria include:
    - asset_class: "CR"
    - Sorted by: 3m (desc), 1m (desc), 1w (desc), market_cap (desc).

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents
                              a ticker document from the database.
                              Returns an empty list if no tickers are found or an error occurs.
    """
    load_dotenv()
    selected_cryptos = []
    client = None
    region = region or [] # Ignored for cryptos as per current requirements
    category = category or [] # Ignored for cryptos as per current requirements
    try:
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        tickers_collection = db["tickers"]
        pipeline_collection = db[os.getenv("MONGODB_TASK_COLLECTION", "pipeline")]

        query = {"asset_class": "CR"} # Changed to "CR"
        log_info(f"Querying for crypto tickers with conditions: {query}")

        # Fixed sorting as per user's request
        sort_fields = [("3m", pymongo.DESCENDING), ("1m", pymongo.DESCENDING), ("1w", pymongo.DESCENDING), ("30d_volume_change", pymongo.DESCENDING)]

        log_info(f"Final query for top cryptos with conditions: {query} and sorting by: {sort_fields}")

        cursor = tickers_collection.find(query).sort(sort_fields).limit(10)

        for doc in cursor:
            selected_cryptos.append(doc)

            new_doc = {
                "_id": ObjectId(),
                "task_id": str(uuid.uuid4()),
                "model_function": "get_insights",
                "model_name": doc.get("ticker", "N/A"),
                "recurrence": "once",
                "task_completed": False,
                "createdAt": datetime.now(UTC),
                "updatedAt": datetime.now(UTC),
                "__v": 0
            }

            pipeline_collection.insert_one(new_doc)
            log_info(f"Inserted task for crypto ticker {doc.get('ticker', 'N/A')} into the {pipeline_collection.name} collection.")

        log_info(f"Successfully retrieved {len(selected_cryptos)} top cryptos and inserted corresponding tasks for selection analysis.")

    except pymongo.errors.ServerSelectionTimeoutError as e:
        log_error("MongoDB server not found. Ensure MongoDB is running on the specified host/port.", "MONGODB_CONNECTION", e)
    except pymongo.errors.OperationFailure as e:
        log_error(f"MongoDB operation failed: {e}", "MONGODB_OPERATION", e)
    except Exception as e:
        log_error(f"An unexpected error occurred while fetching top cryptos from DB: {e}", "DATA_FETCHING", e)
    finally:
        if client:
            DatabaseManager().close_connection()
    return selected_cryptos


def get_top_forex_for_selection_analysis(region: Optional[List[str]] = None, category: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Retrieves the top 10 forex tickers based on specific selection criteria for analysis.
    The criteria include:
    - asset_class: "FX"
    - Sorted by: 3m (desc), 1m (desc), 1w (desc), 30d_volume_change (desc).

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents
                              a ticker document from the database.
                              Returns an empty list if no tickers are found or an error occurs.
    """
    load_dotenv()
    selected_forex = []
    client = None
    region = region or []  # Ignored for forex as per current requirements
    category = category or []  # Ignored for forex as per current requirements
    try:
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        tickers_collection = db["tickers"]
        pipeline_collection = db[os.getenv("MONGODB_TASK_COLLECTION", "pipeline")]

        query = {"asset_class": "FX"}  # Changed to "FX"
        log_info(f"Querying for forex tickers with conditions: {query}")

        # Fixed sorting as per user's request (assuming 30d_volume_change is relevant for FX)
        sort_fields = [("absolute_momentum_spread", pymongo.DESCENDING)]

        log_info(f"Final query for top forex with conditions: {query} and sorting by: {sort_fields}")

        cursor = tickers_collection.find(query).sort(sort_fields).limit(10)

        for doc in cursor:
            selected_forex.append(doc)

            new_doc = {
                "_id": ObjectId(),
                "task_id": str(uuid.uuid4()),
                "model_function": "get_insights",
                "model_name": doc.get("ticker", "N/A"),
                "recurrence": "once",
                "task_completed": False,
                "createdAt": datetime.now(UTC),
                "updatedAt": datetime.now(UTC),
                "__v": 0
            }

            pipeline_collection.insert_one(new_doc)
            log_info(f"Inserted task for forex ticker {doc.get('ticker', 'N/A')} into the {pipeline_collection.name} collection.")

        log_info(f"Successfully retrieved {len(selected_forex)} top forex and inserted corresponding tasks for selection analysis.")

    except pymongo.errors.ServerSelectionTimeoutError as e:
        log_error("MongoDB server not found. Ensure MongoDB is running on the specified host/port.", "MONGODB_CONNECTION", e)
    except pymongo.errors.OperationFailure as e:
        log_error(f"MongoDB operation failed: {e}", "MONGODB_OPERATION", e)
    except Exception as e:
        log_error(f"An unexpected error occurred while fetching top forex from DB: {e}", "DATA_FETCHING", e)
    finally:
        if client:
            DatabaseManager().close_connection()
    return selected_forex


if __name__ == '__main__':
    get_top_equities_for_selection_analysis(region=["US"], category=["growth"])
    get_top_equities_for_selection_analysis(region=["US"], category=["income"])
    get_top_equities_for_selection_analysis(region=["AU"], category=["growth"])
    get_top_equities_for_selection_analysis(region=["AU"], category=["income"])
    get_top_cryptos_for_selection_analysis(region=None, category=None)
    get_top_forex_for_selection_analysis(region=None, category=None)
