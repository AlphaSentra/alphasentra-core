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
import importlib
import inspect
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def process_ticker(doc, client):
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

def process_pipeline(doc, client):
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

import gc
import tracemalloc

def run_batch_processing(max_workers=BATCH_SIZE):
    """
    Main batch processing function using multi-threading with memory optimizations.
    
    Args:
        max_workers (int): Maximum number of threads
    """
    tracemalloc.start()
    print("Starting multi-threaded batch processing...")
    
    client = DatabaseManager().get_client()
    db = client[MONGODB_DATABASE]
    
    # Process tickers in batches
    tickers_coll = db['tickers']
    if tickers_coll is None:
        print("Failed to connect to database. Exiting.")
        return
    
    skip = 0  # Uses imported BATCH_SIZE from _config for document batches
    total_processed = 0
    
    while True:
        # Get batch of pending tickers
        pending_tickers = list(tickers_coll.find({"document_generated": False})
                              .skip(skip).limit(BATCH_SIZE))  # Uses imported BATCH_SIZE
        if not pending_tickers:
            break
            
        print(f"Processing tickers batch {skip//BATCH_SIZE + 1} ({len(pending_tickers)} documents)")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_doc = {executor.submit(process_ticker, doc, client): doc
                            for doc in pending_tickers}
            
            for future in as_completed(future_to_doc):
                doc = future_to_doc[future]
                try:
                    future.result()
                except Exception as exc:
                    log_error(f"Thread generated an exception for {doc['ticker']}", "THREAD_ERROR", exc)
        
        total_processed += len(pending_tickers)
        skip += BATCH_SIZE
        
        # Explicit cleanup
        del pending_tickers
        gc.collect()
    
    log_info(f"Ticker processing completed. Processed {total_processed} tickers")

    # Process pipelines in batches
    print("\nStarting multi-threaded pipeline processing...")
    
    pipelines_coll = db['pipeline']
    if pipelines_coll is None:
        print("Failed to connect to database for pipelines. Skipping.")
        return
    
    skip = 0
    total_successful = 0
    total_pipelines = 0
    
    while True:
        # Get batch of pending pipelines
        pending_pipelines = list(pipelines_coll.find({"task_completed": False})
                                .skip(skip).limit(BATCH_SIZE))  # Uses imported BATCH_SIZE
        if not pending_pipelines:
            break
            
        print(f"Processing pipelines batch {skip//BATCH_SIZE + 1} ({len(pending_pipelines)} documents)")
        total_pipelines += len(pending_pipelines)
        batch_successful = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_doc = {executor.submit(process_pipeline, doc, client): doc
                            for doc in pending_pipelines}
            
            for future in as_completed(future_to_doc):
                doc = future_to_doc[future]
                try:
                    if future.result():
                        batch_successful += 1
                except Exception as exc:
                    log_error(f"Thread generated an exception for pipeline {doc.get('model_function')}", "THREAD_ERROR_PIPELINE", exc)
        
        total_successful += batch_successful
        skip += BATCH_SIZE
        
        # Explicit cleanup
        del pending_pipelines
        gc.collect()
    
    log_info(f"Pipeline processing completed. Successful: {total_successful}/{total_pipelines}")
    
    # Memory analysis
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    mem_report = "\n[Top 10 memory allocations]\n" + "\n".join(str(stat) for stat in top_stats[:10])
    log_info(mem_report)

if __name__ == "__main__":
    run_batch_processing()