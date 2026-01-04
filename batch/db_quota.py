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

def purge_insights_collection() -> None:
    """
    Delete all documents in the 'insights' collection.
    """
    
    client = DatabaseManager().get_client()
    db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
    insights = db.insights
    
    try:
        result = insights.delete_many({})
        deleted_count = result.deleted_count
        
        if deleted_count > 0:
            log_info(f"Deleted {deleted_count} documents from insights collection")
        else:
            log_info("No documents found in insights collection")
            
    except pymongo.errors.PyMongoError as e:
        log_error(f"Error purging insights collection: {str(e)}", "DATABASE", e)
        raise