import sys
import os
import importlib
import inspect
import threading
import gc
import tracemalloc
import time
from datetime import datetime, timedelta
from queue import Queue
from multiprocessing import Pool
from pymongo.write_concern import WriteConcern
from pymongo.read_concern import ReadConcern
from dotenv import load_dotenv
from tqdm import tqdm

# Internal imports
from logging_utils import log_error, log_warning, log_info
from _config import BATCH_SIZE, BATCH_TIMEOUT, BATCH_PAUSE_IN_SECONDS
from helpers import DatabaseManager, update_ticker_fail_status

# Load environment variables
load_dotenv()
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "alphasentra-core")

try:
    from _config import CHECK_INTERVAL
except ImportError:
    CHECK_INTERVAL = BATCH_PAUSE_IN_SECONDS

def derive_module_and_func(model_function, model_name=None):
    """Derive module and function names from DB strings."""
    func_name = model_function
    if model_name:
        module = model_name.replace('.py', '')
        return module, func_name
    base = model_function.replace('run_', '')
    module = base.replace('_model', '')
    return module, func_name

def process_ticker(doc):
    """Process a single ticker with atomic checks and correct WriteConcern application."""
    try:
        client = DatabaseManager().get_client()
        db = client[MONGODB_DATABASE]
        tickers_coll = db.get_collection('tickers')

        # 1. ATOMIC PRE-CHECK: Skip if already done
        current_doc = tickers_coll.find_one({"_id": doc["_id"], "document_generated": False})
        if not current_doc:
            return False 

        model_function = doc.get("model_function")
        if not model_function: return False
        
        module_info = derive_module_and_func(model_function, doc.get("model_name"))
        if not module_info: return False
        
        module_name, func_name = module_info
        
        try:
            module = importlib.import_module(f"models.{module_name}")
            func = getattr(module, func_name)
        except (ImportError, AttributeError):
            return False
        
        # Prepare parameters
        tickers_list = [doc["ticker"]]
        sig = inspect.signature(func)
        kwargs = {'tickers': tickers_list, 'decimal_digits': doc.get("decimal", 2)}
        
        if 'prompt' in sig.parameters: kwargs['prompt'] = doc.get("prompt")
        if 'factors' in sig.parameters: kwargs['factors'] = doc.get("factors")
        if 'batch_mode' in sig.parameters: kwargs['batch_mode'] = True
        
        # Call the actual model function
        func(**kwargs)
        
        # 2. CORRECTED WRITE CONCERN UPDATE
        # Create a collection instance with the write concern applied
        wc_tickers = tickers_coll.with_options(write_concern=WriteConcern(w="majority", j=True))
        
        update_result = wc_tickers.update_one(
            {"_id": doc["_id"], "document_generated": False},
            {"$set": {"document_generated": True, "last_processed": datetime.now()}}
        )
        return update_result.modified_count > 0
        
    except Exception as e:
        log_error(f"Error processing ticker {doc.get('ticker')}", "TICKER_PROCESSING", e)
        update_ticker_fail_status(doc.get('ticker'))
        return False

def process_pipeline(doc):
    """Process a pipeline document with fixed WriteConcern syntax."""
    try:
        client = DatabaseManager().get_client()
        db = client[MONGODB_DATABASE]
        pipelines_coll = db.get_collection('pipeline')

        # 1. ATOMIC PRE-CHECK
        current_doc = pipelines_coll.find_one({"_id": doc["_id"], "task_completed": False})
        if not current_doc:
            return False

        model_function = doc.get("model_function")
        module_info = derive_module_and_func(model_function, doc.get("model_name"))
        if not module_info: return False
        
        module_name, func_name = module_info

        try:
            module = importlib.import_module(f"models.{module_name}")
            func = getattr(module, func_name)
        except:
            try:
                module = importlib.import_module("models.default")
                func = getattr(module, func_name)
            except: return False
        
        sig = inspect.signature(func)
        kwargs = {}
        if 'batch_mode' in sig.parameters: kwargs['batch_mode'] = True
        if 'decimal_digits' in sig.parameters: kwargs['decimal_digits'] = 2
        
        func(**kwargs)
        
        # 2. CORRECTED WRITE CONCERN UPDATE
        wc_pipelines = pipelines_coll.with_options(write_concern=WriteConcern(w="majority", j=True))
        
        update_result = wc_pipelines.update_one(
            {"_id": doc["_id"], "task_completed": False},
            {"$set": {"task_completed": True}}
        )
        return update_result.modified_count > 0
    except Exception as e:
        log_error(f"Error processing pipeline {doc.get('model_function')}", "PIPELINE_PROCESSING", e)
        return False

def run_batch_processing(max_workers=BATCH_SIZE):
    tracemalloc.start()
    log_info("Starting continuous batch processing with WriteConcern and race protection...")
    
    client = DatabaseManager().get_client()
    db = client[MONGODB_DATABASE]
    start_time = time.time()
    
    work_queue = Queue()
    stop_event = threading.Event()
    
    # Local de-duplication tracking
    queued_ids = set()
    ids_lock = threading.Lock()

    def poll_new_items():
        """Background thread that avoids adding duplicates to the queue."""
        while not stop_event.is_set():
            try:
                # Use majority read concern for polling to ensure we see committed data
                pipelines_coll = db.get_collection('pipeline', read_concern=ReadConcern("majority"))
                tickers_coll = db.get_collection('tickers', read_concern=ReadConcern("majority"))

                # Poll Pipelines
                new_p = list(pipelines_coll.find({"task_completed": False}).limit(BATCH_SIZE))
                with ids_lock:
                    valid_p = [p for p in new_p if p['_id'] not in queued_ids]
                    for p in valid_p:
                        queued_ids.add(p['_id'])
                        work_queue.put(('pipeline', [p])) # Put individually or as batch

                # Poll Tickers (Filter already queued and processed items)
                new_t = list(tickers_coll.find({
                    "document_generated": False,
                    "recurrence": {"$ne": "processed"},
                    "$or": [
                        {"last_processed": {"$exists": False}},
                        {"last_processed": {"$lt": datetime.now() - timedelta(minutes=5)}}
                    ]
                }).limit(BATCH_SIZE))
                
                with ids_lock:
                    valid_t = [t for t in new_t if t['_id'] not in queued_ids]
                    if valid_t:
                        for t in valid_t: queued_ids.add(t['_id'])
                        work_queue.put(('ticker', valid_t))

                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                log_error("Background polling error", "POLLING_ERROR", e)

    # Start poller
    poller_thread = threading.Thread(target=poll_new_items, daemon=True)
    poller_thread.start()

    pipelines_processed = 0
    tickers_processed = 0

    try:
        while time.time() - start_time < BATCH_TIMEOUT and not stop_event.is_set():
            if work_queue.empty():
                time.sleep(1)
                continue

            work_type, items = work_queue.get()
            
            with Pool(processes=max_workers) as pool:
                if work_type == 'pipeline':
                    for doc in items:
                        if process_pipeline(doc):
                            pipelines_processed += 1
                        with ids_lock: queued_ids.discard(doc['_id'])
                else:
                    # Multi-threaded execution for tickers
                    results = [pool.apply_async(process_ticker, (doc,)) for doc in items]
                    for idx, r in enumerate(results):
                        if r.get():
                            tickers_processed += 1
                        with ids_lock:
                            # Remove from tracking set once finished
                            queued_ids.discard(items[idx]['_id'])

            work_queue.task_done()
            gc.collect() # Regular cleanup
            log_info(f"Cycle Done | Pipelines: {pipelines_processed} | Tickers: {tickers_processed}")

    except KeyboardInterrupt:
        log_info("Process interrupted by user.")
    finally:
        stop_event.set()
        poller_thread.join(timeout=5)
        log_info("Batch processing stopped.")

if __name__ == "__main__":
    run_batch_processing()