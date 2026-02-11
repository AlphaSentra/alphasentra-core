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
from concurrent.futures import ProcessPoolExecutor
from pymongo.write_concern import WriteConcern
from pymongo.read_concern import ReadConcern
from dotenv import load_dotenv
import pymongo
from tqdm import tqdm

# Internal imports
from logging_utils import log_error, log_warning, log_info
from _config import BATCH_SIZE, BATCH_TIMEOUT, BATCH_PAUSE_IN_SECONDS
from helpers import DatabaseManager, update_ticker_fail_status

load_dotenv()
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "alphasentra-core")

CHECK_INTERVAL = BATCH_PAUSE_IN_SECONDS

# --- HELPER FUNCTIONS ---

def derive_module_and_func(model_function, model_name=None):
    func_name = model_function
    if model_name:
        module = model_name.replace(".py", "")
        return module, func_name
    base = model_function.replace("run_", "").replace("_model", "")
    return base, func_name

def process_ticker(doc):
    """Atomic worker for individual tickers."""
    try:
        client = DatabaseManager().get_client()
        db = client[MONGODB_DATABASE]
        tickers_coll = db.get_collection('tickers')

        # Atomic check: only process if not already done
        current = tickers_coll.find_one({"_id": doc["_id"], "document_generated": False})
        if not current: return False

        module_info = derive_module_and_func(doc.get("model_function"), doc.get("model_name"))
        if not module_info: return False
        
        module_name, func_name = module_info
        module = importlib.import_module(f"models.{module_name}")
        func = getattr(module, func_name)
        
        sig = inspect.signature(func)
        kwargs = {'tickers': [doc["ticker"]], 'decimal_digits': doc.get("decimal", 2)}
        if 'prompt' in sig.parameters: kwargs['prompt'] = doc.get("prompt")
        if 'factors' in sig.parameters: kwargs['factors'] = doc.get("factors")
        if 'batch_mode' in sig.parameters: kwargs['batch_mode'] = True
        
        func(**kwargs)
        
        # Safe update with WriteConcern
        wc_coll = tickers_coll.with_options(write_concern=WriteConcern(w="majority", j=True))
        wc_coll.update_one(
            {"_id": doc["_id"], "document_generated": False},
            {"$set": {"document_generated": True, "last_processed": datetime.now()}}
        )
        return True
    except Exception as e:
        log_error(f"Ticker {doc.get('ticker')} failed", "TICKER_ERR", e)
        update_ticker_fail_status(doc.get('ticker'))
        return False

def process_pipeline(doc):
    """Atomic worker for pipelines."""
    try:
        client = DatabaseManager().get_client()
        db = client[MONGODB_DATABASE]
        pipelines_coll = db.get_collection('pipeline')

        current = pipelines_coll.find_one({"_id": doc["_id"], "task_completed": False})
        if not current: return False

        module_info = derive_module_and_func(doc.get("model_function"), doc.get("model_name"))
        if not module_info: return False
        
        module_name, func_name = module_info
        try:
            module = importlib.import_module(f"models.{module_name}")
            func = getattr(module, func_name)
        except:
            module = importlib.import_module("models.default")
            func = getattr(module, func_name)
        
        sig = inspect.signature(func)
        kwargs = {'batch_mode': True} if 'batch_mode' in sig.parameters else {}
        func(**kwargs)
        
        wc_coll = pipelines_coll.with_options(write_concern=WriteConcern(w="majority", j=True))
        wc_coll.update_one({"_id": doc["_id"]}, {"$set": {"task_completed": True}})
        return True
    except Exception as e:
        log_error(f"Pipeline {doc.get('model_function')} failed", "PIPE_ERR", e)
        return False

# --- MAIN RUNNER ---

def run_batch_processing(max_workers=BATCH_SIZE):
    tracemalloc.start()
    log_info(f"Starting Async-Parallel Runner. Max Workers: {max_workers}")

    client = DatabaseManager().get_client()
    db = client[MONGODB_DATABASE]
    settings_coll = db.get_collection("settings")

    # Atomically increment batch_id and get the new value
    updated_settings = settings_coll.find_one_and_update(
        {"key": "batch_settings"},
        {"$inc": {"batch_id": 1}},
        return_document=pymongo.ReturnDocument.AFTER,
        upsert=True # Create the document if it doesn't exist
    )

    batch_id = updated_settings.get("batch_id") if updated_settings else 0
    log_info(f"Initiating batch processing with batch_id: {batch_id}")

    work_queue = Queue()
    stop_event = threading.Event()

    # Tracking and Concurrency Control
    queued_ids = set()
    ids_lock = threading.Lock()
    semaphore = threading.BoundedSemaphore(max_workers)

    def poll_new_items():
        """Background thread: Continuously fills the queue with individual tasks."""
        client = DatabaseManager().get_client()
        db = client[MONGODB_DATABASE]

        while not stop_event.is_set():
            try:
                # Poll Pipelines (Priority)
                pipe_coll = db.get_collection('pipeline', read_concern=ReadConcern("majority"))
                new_pipes = list(pipe_coll.find({"task_completed": False}).limit(10))

                with ids_lock:
                    for p in new_pipes:
                        if p["_id"] not in queued_ids:
                            queued_ids.add(p["_id"])
                            work_queue.put(('pipeline', p))

                # Poll Tickers
                tick_coll = db.get_collection('tickers', read_concern=ReadConcern("majority"))
                new_ticks = list(tick_coll.find({
                    "document_generated": False,
                    "recurrence": {"$ne": "processed"},
                    "$or": [
                        {"last_processed": {"$exists": False}},
                        {"last_processed": {"$lt": datetime.now() - timedelta(minutes=5)}}
                    ]
                }).limit(BATCH_SIZE))

                with ids_lock:
                    for t in new_ticks:
                        if t["_id"] not in queued_ids:
                            queued_ids.add(t["_id"])
                            work_queue.put(('ticker', t))

                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                log_error("Poller encountered an error", "POLL_ERR", e)
                time.sleep(10)

    # Start Poller
    poller_thread = threading.Thread(target=poll_new_items, daemon=True)
    poller_thread.start()

    # Shared callback to release slots and clear tracking
    def task_done_callback(future, doc_id):
        semaphore.release()
        with ids_lock:
            queued_ids.discard(doc_id)

    # Use a persistent Process Pool
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        start_time = time.time()
        last_db_batch_id_check_time = time.time() # Initialize check time

        while time.time() - start_time < BATCH_TIMEOUT and not stop_event.is_set():
            # Add periodic check for batch_id in DB
            if time.time() - last_db_batch_id_check_time > CHECK_INTERVAL:
                current_db_settings = settings_coll.find_one({"key": "batch_settings"})
                db_batch_id = current_db_settings.get("batch_id") if current_db_settings else 0
                if db_batch_id > batch_id:
                    log_info(f"Detected higher batch_id in DB ({db_batch_id}) than current batch_id ({batch_id}). Stopping batch processing.")
                    stop_event.set()
                last_db_batch_id_check_time = time.time()

            try:
                # Get the next single task from the queue
                if not work_queue.empty():
                    work_type, doc = work_queue.get()

                    # 1. Acquire a slot (blocks only this loop, not the poller)
                    semaphore.acquire()

                    # 2. Assign to worker
                    worker_func = process_pipeline if work_type == 'pipeline' else process_ticker
                    future = executor.submit(worker_func, doc)

                    # 3. Non-blocking cleanup when finished
                    future.add_done_callback(lambda f, d=doc["_id"]: task_done_callback(f, d))
                    work_queue.task_done()
                else:
                    # Nothing to do? Wait a moment.
                    time.sleep(1)

                # Periodic Garbage Collection
                if int(time.time() - start_time) % 300 == 0:
                    gc.collect()

            except KeyboardInterrupt:
                log_info("Shutdown signal received.")
                stop_event.set()
                break
            except Exception as e:
                log_error("Main loop error", "MAIN_LOOP_ERR", e)

    log_info("Batch processing finished.")

if __name__ == "__main__":
    run_batch_processing()