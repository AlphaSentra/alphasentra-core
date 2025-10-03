"""
Description:
Multi-threaded batch runner for processing tickers from MongoDB.
Calls model functions specified in tickers collection and updates document_generated flag.
"""

import sys
import os

# Add the parent directory to the Python path to ensure imports work (must be first)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Now safe to import modules from root
from dotenv import load_dotenv
import threading
import importlib
import inspect
from concurrent.futures import ThreadPoolExecutor, as_completed
import pymongo
from pymongo.errors import OperationFailure
from logging_utils import log_error, log_warning, log_info
from _config import BATCH_SIZE
from helpers import DatabaseManager

# Load environment variables
load_dotenv()

# MongoDB database name
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "alphagora")

def derive_module_and_func(model_function, model_name=None):
    """
    Dynamically derive module name and function name from model_function string and optional model_name.
    Uses model_name (py file name) for module if provided, else falls back to derivation from function name.
    
    Args:
        model_function (str): e.g., "run_fx_model"
        model_name (str, optional): e.g., "fx_long_short.py"
    
    Returns:
        tuple: (module_name, func_name) or None if cannot derive
    """
    func_name = model_function
    
    if model_name:
        module = model_name.replace('.py', '')
        return module, func_name
    
    # Fallback: general derivation without hardcodes
    base = model_function.replace('run_', '')
    module = base.replace('_model', '')
    return module, func_name

# No hardcoded dictionary - use derivation function instead


def process_ticker(doc):
    """
    Process a single ticker document: import and call the model function, then update flag.
    
    Args:
        doc (dict): Ticker document from MongoDB
    """
    try:
        model_function = doc.get("model_function")
        if not model_function:
            log_warning(f"No model_function for ticker {doc.get('ticker')}", "INVALID_FUNCTION")
            return False
        
        model_name = doc.get("model_name")  # Assume optional field in doc for py file name
        module_info = derive_module_and_func(model_function, model_name)
        if not module_info:
            log_warning(f"Cannot derive module for model_function: {model_function} for ticker {doc.get('ticker')}", "INVALID_FUNCTION")
            return False
        
        module_name, func_name = module_info
        
        # Dynamically import the module and function
        try:
            module = importlib.import_module(f"models.{module_name}")
            func = getattr(module, func_name)
        except (ImportError, AttributeError) as e:
            log_warning(f"Failed to import {module_name}.{func_name}: {e} for ticker {doc.get('ticker')}", "IMPORT_ERROR")
            return False
        
        # Prepare parameters
        tickers_list = [doc["ticker"]]
        prompt = doc.get("prompt")
        factors = doc.get("factors")
        decimal = doc.get("decimal", 2)
        
        # Dynamically prepare kwargs based on function signature
        sig = inspect.signature(func)
        kwargs = {'tickers': tickers_list, 'decimal_digits': decimal}
        
        if 'prompt' in sig.parameters:
            kwargs['prompt'] = prompt
        if 'factors' in sig.parameters:
            kwargs['factors'] = factors
        if 'batch_mode' in sig.parameters:
            kwargs['batch_mode'] = True
        
        # Call the function with filtered kwargs
        func(**kwargs)
        return False
        
    except Exception as e:
        log_error(f"Error processing ticker {doc.get('ticker')}", "TICKER_PROCESSING", e)
        return False

def process_pipeline(doc):
    """
    Process a single pipeline document: import and call the model function, then update flag.
    
    Args:
        doc (dict): Pipeline document from MongoDB
    """
    try:
        model_function = doc.get("model_function")
        if not model_function:
            log_warning(f"No model_function for pipeline", "INVALID_FUNCTION")
            return False
        
        model_name = doc.get("model_name")  # Assume optional field in doc for py file name
        module_info = derive_module_and_func(model_function, model_name)
        if not module_info:
            log_warning(f"Cannot derive module for model_function: {model_function}", "INVALID_FUNCTION")
            return False
        
        module_name, func_name = module_info
        
        # Dynamically import the module and function
        try:
            module = importlib.import_module(f"models.{module_name}")
            func = getattr(module, func_name)
        except (ImportError, AttributeError) as e:
            log_warning(f"Failed to import {module_name}.{func_name}: {e}", "IMPORT_ERROR")
            return False
        
        # Prepare parameters for pipeline functions
        decimal = 2  # Default for ETFs/indices
        
        # kwargs based on function signature (known: batch_mode and decimal_digits)
        kwargs = {'batch_mode': True, 'decimal_digits': decimal}
        
        # Call the function
        func(**kwargs)

        # If successful (no exception), update the document
        client = DatabaseManager().get_client()
        db = client[MONGODB_DATABASE]
        pipelines_coll = db['pipeline']
        if pipelines_coll is not None:
            result = pipelines_coll.update_one(
                {"_id": doc["_id"]},
                {"$set": {"task_completed": True}}
            )
            if result.modified_count > 0:
                print(f"Successfully updated task_completed for {model_function}")
                return True
            else:
                log_warning(f"Failed to update document for {model_function}", "DB_UPDATE")
                return False

        return False
    
    except Exception as e:
        log_error(f"Error processing pipeline {doc.get('model_function')}", "PIPELINE_PROCESSING", e)
        return False

def run_batch_processing(max_workers=BATCH_SIZE):
    """
    Main batch processing function using multi-threading.
    
    Args:
        max_workers (int): Maximum number of threads
    """
    print("Starting multi-threaded batch processing...")
    
    client = DatabaseManager().get_client()
    db = client[MONGODB_DATABASE]
    tickers_coll = db['tickers']
    if tickers_coll is None:
        print("Failed to connect to database. Exiting.")
        return
    
    # Find tickers where document_generated == False
    pending_tickers = list(tickers_coll.find({"document_generated": False}))
    if not pending_tickers:
        log_info("No pending tickers to process.")
        return
    
    print(f"Found {len(pending_tickers)} pending tickers to process.")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_doc = {executor.submit(process_ticker, doc): doc for doc in pending_tickers}
        
        # Collect results
        for future in as_completed(future_to_doc):
            doc = future_to_doc[future]
            try:
                future.result()
            except Exception as exc:
                log_error(f"Thread generated an exception for {doc['ticker']}", "THREAD_ERROR", exc)
                
        log_info(f"Batch processing completed. Processed {len(pending_tickers)} tickers")

    # Process pipelines
    print("\nStarting multi-threaded pipeline processing...")
    
    pipelines_coll = db['pipeline']
    if pipelines_coll is None:
        print("Failed to connect to database for pipelines. Skipping.")
        return
    
    # Find pipelines where task_completed == False
    pending_pipelines = list(pipelines_coll.find({"task_completed": False}))
    if not pending_pipelines:
        log_info("No pending pipelines to process.")
        return
    
    print(f"Found {len(pending_pipelines)} pending pipelines to process.")
    
    successful_pipelines = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_doc = {executor.submit(process_pipeline, doc): doc for doc in pending_pipelines}
        
        # Collect results
        for future in as_completed(future_to_doc):
            doc = future_to_doc[future]
            try:
                if future.result():
                    successful_pipelines += 1
            except Exception as exc:
                log_error(f"Thread generated an exception for pipeline {doc.get('model_function')}", "THREAD_ERROR_PIPELINE", exc)
    
    log_info(f"Pipeline processing completed. Successful: {successful_pipelines}/{len(pending_pipelines)}")

if __name__ == "__main__":
    run_batch_processing()