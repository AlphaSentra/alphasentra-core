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
from _config import BATCH_SIZE, BATCH_TIMEOUT, BATCH_PAUSE_IN_SECONDS
from helpers import DatabaseManager
import gc
import tracemalloc
import time
from tqdm import tqdm

# Load environment variables
load_dotenv()

# MongoDB database name
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "alphasentra-core")

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
            # Refresh factors if empty
            if not factors:
                try:
                    from models.holistic import get_factors
                    from datetime import datetime
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    instrument_name = doc.get("instrument_name", doc["ticker"])
                    factors = get_factors(tickers_list, instrument_name, current_date, prompt=prompt)
                except Exception as e:
                    log_warning(f"Failed to refresh factors for {doc['ticker']}: {str(e)}", "FACTORS_REFRESH")
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
        sig = inspect.signature(func)
        kwargs = {}
        if 'batch_mode' in sig.parameters:
            kwargs['batch_mode'] = True
        if 'decimal_digits' in sig.parameters:
            kwargs['decimal_digits'] = decimal
        
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


def run_batch_processing(max_workers=BATCH_SIZE):
    """
    Main batch processing function using multi-threading with memory optimizations.
    Runs continuously for max 4 hours or until all tickers/pipelines are processed.
    
    Args:
        max_workers (int): Maximum number of threads
    """
    tracemalloc.start()
    print("Starting continuous batch processing with 4-hour timeout...")
    
    client = DatabaseManager().get_client()
    db = client[MONGODB_DATABASE]
    
    TIMEOUT = BATCH_TIMEOUT
    CHECK_INTERVAL = 60  # Check for new items every 60 seconds
    start_time = time.time()
    
    while time.time() - start_time < TIMEOUT:
        # Process tickers
        tickers_processed = 0
        tickers_coll = db['tickers']
        if tickers_coll is not None:
            pending_tickers = list(tickers_coll.aggregate([
                {"$match": {"document_generated": False}},
                {"$sample": {"size": BATCH_SIZE}}
            ]))
            
            if pending_tickers:
                print(f"Processing {len(pending_tickers)} tickers")
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_doc = {executor.submit(process_ticker, doc, client): doc
                                    for doc in pending_tickers}
                    
                    for future in as_completed(future_to_doc):
                        doc = future_to_doc[future]
                        try:
                            future.result()
                            tickers_processed += 1
                        except Exception as exc:
                            log_error(f"Thread generated an exception for {doc['ticker']}", "THREAD_ERROR", exc)
                
                # Explicit cleanup
                del pending_tickers
                gc.collect()
        
        # Process pipelines
        pipelines_processed = 0
        pipelines_coll = db['pipeline']
        if pipelines_coll is not None:
            pending_pipelines = list(pipelines_coll.find({"task_completed": False}).limit(BATCH_SIZE))
            
            if pending_pipelines:
                print(f"Processing {len(pending_pipelines)} pipelines")
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_doc = {executor.submit(process_pipeline, doc, client): doc
                                    for doc in pending_pipelines}
                    
                    for future in as_completed(future_to_doc):
                        doc = future_to_doc[future]
                        try:
                            if future.result():
                                pipelines_processed += 1
                        except Exception as exc:
                            log_error(f"Thread generated an exception for pipeline {doc.get('model_function')}", "THREAD_ERROR_PIPELINE", exc)
                
                # Explicit cleanup
                del pending_pipelines
                gc.collect()
        
        # Check completion status
        remaining_tickers = tickers_coll.count_documents({"document_generated": False}) if tickers_coll is not None else 0
        remaining_pipelines = pipelines_coll.count_documents({"task_completed": False}) if pipelines_coll is not None else 0
        
        log_info(f"Batch cycle completed. Processed: {tickers_processed} tickers, {pipelines_processed} pipelines. Remaining: {remaining_tickers} tickers, {remaining_pipelines} pipelines")
        
        # Add pause with progress bar and memory cleanup
        if tickers_processed > 0 or pipelines_processed > 0:
            # Pre-pause memory report
            snapshot1 = tracemalloc.take_snapshot()
            top_stats1 = snapshot1.statistics('lineno')
            mem_usage1 = sum(stat.size for stat in top_stats1[:10])
            log_info(f"Memory before cleanup: {mem_usage1/1024:.1f} KB")

            try:
                # Force garbage collection and delete large variables
                gc.collect()
                del future_to_doc
                
                # Progress bar with memory cleanup every 10 seconds
                with tqdm(total=BATCH_PAUSE_IN_SECONDS, desc="Time before next batch") as pbar:
                    for i in range(BATCH_PAUSE_IN_SECONDS):
                        if i % 10 == 0:
                            gc.collect()
                        time.sleep(1)
                        pbar.update(1)

                # Post-pause memory report
                snapshot2 = tracemalloc.take_snapshot()
                top_stats2 = snapshot2.statistics('lineno')
                mem_usage2 = sum(stat.size for stat in top_stats2[:10])
                log_info(f"Memory after cleanup: {mem_usage2/1024:.1f} KB (saved {mem_usage1-mem_usage2:.1f} bytes)")
            except KeyboardInterrupt:
                log_info("Batch pause interrupted", "PAUSE_INTERRUPTED")
        
        # Exit if no more work
        if remaining_tickers == 0 and remaining_pipelines == 0:
            log_info("All tickers and pipelines processed successfully!")
            break
            
        # Sleep before next check if no items were processed
        if tickers_processed == 0 and pipelines_processed == 0:
            time.sleep(CHECK_INTERVAL)
    
    # Final status report
    if time.time() - start_time >= TIMEOUT:
        remaining_tickers = tickers_coll.count_documents({"document_generated": False}) if tickers_coll else 0
        remaining_pipelines = pipelines_coll.count_documents({"task_completed": False}) if pipelines_coll else 0
        log_warning(f"Timeout reached after 4 hours. Remaining: {remaining_tickers} tickers, {remaining_pipelines} pipelines", "TIMEOUT")
    
    # Memory analysis
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    mem_report = "\n[Top 10 memory allocations]\n" + "\n".join(str(stat) for stat in top_stats[:10])
    log_info(mem_report)
    
    # Memory analysis
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    mem_report = "\n[Top 10 memory allocations]\n" + "\n".join(str(stat) for stat in top_stats[:10])
    log_info(mem_report)

if __name__ == "__main__":
    run_batch_processing()