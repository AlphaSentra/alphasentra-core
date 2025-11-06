import pymongo
import os
import sys

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from logging_utils import log_info, log_warning, log_error
from _config import DB_SIZE_LIMIT_MB
from helpers import DatabaseManager
import os

def enforce_db_size_limit(max_size_mb: int = DB_SIZE_LIMIT_MB) -> None:
    """
    Remove oldest documents from 'insights' collection until database size is under limit.
    Deletes documents one at a time to be conservative.
    
    Args:
        max_size_mb: Maximum allowed database size in megabytes
    """
    
    client = DatabaseManager().get_client()
    db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
    insights = db.insights
    max_size_bytes = max_size_mb * 1024 * 1024
    
    try:
        current_stats = db.command("dbstats")
        current_size = current_stats["dataSize"]
        
        if current_size <= max_size_bytes:
            log_info(f"Database size {current_size/1024/1024:.2f}MB is under threshold of {max_size_mb}MB")
            return
            
        log_warning(f"Database size {current_size/1024/1024:.2f}MB exceeds {max_size_mb}MB limit", "DATABASE")
        
        # Safety limit to prevent infinite loops
        max_deletions = 1000  
        deleted_count = 0
        
        while current_size > max_size_bytes and deleted_count < max_deletions:
            # Find and remove oldest document by _id (which contains timestamp)
            oldest_doc = insights.find_one(sort=[("_id", pymongo.ASCENDING)])
            if not oldest_doc:
                log_warning("No documents remaining in insights collection")
                break
                
            insights.delete_one({"_id": oldest_doc["_id"]})
            deleted_count += 1
            
            # Refresh stats after deletion
            current_stats = db.command("dbstats")
            current_size = current_stats["dataSize"]
            
            log_info(f"Deleted document {oldest_doc['_id']} - new size: {current_size/1024/1024:.2f}MB")
            
        if deleted_count >= max_deletions:
            log_error("Reached maximum deletion limit without reaching size target", "DATABASE")
            
        log_info(f"Finished cleanup. Final database size: {current_size/1024/1024:.2f}MB")
        
    except pymongo.errors.PyMongoError as e:
        log_error(f"Error enforcing database size limit: {str(e)}", "DATABASE", e)
        raise