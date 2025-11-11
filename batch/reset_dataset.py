"""
Comprehensive dataset reset script for the Alphasentra system.

This script provides functions to:
- Reset the document_generated field to False for all tickers in the tickers collection
- Reset the task_completed field to False for all documents in the pipeline collection
- Delete tickers with recurrence 'once' from the tickers collection
- Delete pipeline documents with recurrence 'once' from the pipeline collection
- Perform all reset operations in sequence via reset_all()
"""

import os
from dotenv import load_dotenv
from logging_utils import AgLogger
from helpers import DatabaseManager

# Load environment variables
load_dotenv()

# Initialize logger
logger = AgLogger('reset_dataset')

def reset_document_generated():
    """
    Reset the document_generated field to False for all documents in the tickers collection
    except those where recurrence is 'processed'.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting reset of document_generated field in tickers collection")
        
        # Get MongoDB client using DatabaseManager
        client = DatabaseManager().get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        db = client[db_name]
        collection = db['tickers']
        
        # Update all documents to set document_generated to False except 'processed' tickers
        result = collection.update_many(
            filter={"recurrence": {"$ne": "processed"}},
            update={"$set": {"document_generated": False}}
        )
        
        logger.info(f"Successfully updated {result.modified_count} documents in tickers collection")
        logger.info("Reset of document_generated field completed")
        return True
        
    except Exception as e:
        logger.error("Failed to reset document_generated field", "DATABASE_OPERATION", e)
        return False

def reset_pipeline_completed():
    """
    Reset the task_completed field to False for all documents in the pipeline collection.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting reset of task_completed field in pipeline collection")
        
        # Get MongoDB client using DatabaseManager
        client = DatabaseManager().get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        db = client[db_name]
        collection = db['pipeline']
        
        # Update all documents to set task_completed to False
        result = collection.update_many(
            filter={},  # Match all documents
            update={"$set": {"task_completed": False}}
        )
        
        logger.info(f"Successfully updated {result.modified_count} documents in pipeline collection")
        logger.info("Reset of task_completed field completed")
        return True
        
    except Exception as e:
        logger.error("Failed to reset task_completed field", "DATABASE_OPERATION", e)
        return False

def delete_tickers():
    """
    Delete documents in the tickers collection where recurrence is
    'once', or 'processed' with no documents in the insights collection.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting deletion of tickers with recurrence 'once'")
        
        # Get MongoDB client using DatabaseManager
        client = DatabaseManager().get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        db = client[db_name]
        collection = db['tickers']
        
        # Delete documents where recurrence is 'once'
        result = collection.delete_many(
            filter={"recurrence": "once"}
        )

        logger.info(f"Successfully deleted {result.deleted_count} documents with recurrence 'once' from tickers collection")
        logger.info("Deletion of once tickers completed")
        
        # Now delete processed tickers with no matching insights
        logger.info("Starting deletion of processed tickers with no insights")
        
        pipeline = [
            {"$match": {"recurrence": "processed"}},
            {
                "$lookup": {
                    "from": "insights",
                    "let": {"ticker": "$ticker"},
                    "pipeline": [
                        {"$unwind": "$recommendations"},
                        {"$match": {"$expr": {"$eq": ["$recommendations.ticker", "$$ticker"]}}}
                    ],
                    "as": "matching_insights"
                }
            },
            {"$match": {"matching_insights": {"$size": 0}}},
            {"$project": {"_id": 1}}
        ]
        
        docs_to_delete = collection.aggregate(pipeline)
        delete_ids = [doc["_id"] for doc in docs_to_delete]
        
        if delete_ids:
            result = collection.delete_many({"_id": {"$in": delete_ids}})
            logger.info(f"Deleted {result.deleted_count} processed tickers with no insights")
        else:
            logger.info("No processed tickers without insights found")
        
        return True
        
    except Exception as e:
        logger.error("Failed to delete once tickers", "DATABASE_OPERATION", e)
        return False

def delete_once_pipeline():
    """
    Delete documents in the pipeline collection where recurrence is 'once'.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting deletion of pipeline documents with recurrence 'once'")
        
        # Get MongoDB client using DatabaseManager
        client = DatabaseManager().get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        db = client[db_name]
        collection = db['pipeline']
        
        # Delete documents where recurrence is 'once'
        result = collection.delete_many(
            filter={"recurrence": "once"}
        )
        
        logger.info(f"Successfully deleted {result.deleted_count} documents with recurrence 'once' from pipeline collection")
        logger.info("Deletion of once pipeline documents completed")
        return True
        
    except Exception as e:
        logger.error("Failed to delete once pipeline documents", "DATABASE_OPERATION", e)
        return False
    

def remove_all_weight_factors():
    """
    Remove all documents from the 'weight_factors' collection.
    
    Returns:
        int: Number of documents deleted.
    """
    try:
        logger.info("Starting deletion of all weigh_factors documents")
        
        # Get MongoDB client using DatabaseManager
        client = DatabaseManager().get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        db = client[db_name]
        collection = db['weight_factors']

        result = collection.delete_many({})
        deleted_count = result.deleted_count
        if deleted_count > 0:
            logger.info(f"Successfully deleted {deleted_count} documents from 'weight_factors'.")
        else:
            logger.info("No documents found in 'weight_factors'.")

        return True

    except Exception as e:
        logger.error("Failed to delete weight_factors documents", "DATABASE_OPERATION", e)
        return False

def reset_all():
    """
    Call all reset and delete functions in sequence.
    
    Returns:
        bool: True if all operations succeed, False otherwise
    """
    try:
        logger.info("Starting comprehensive dataset reset")
        
        # Call all functions in sequence
        success = (
            reset_document_generated() and
            reset_pipeline_completed() and
            delete_tickers() and
            delete_once_pipeline() and
            remove_all_weight_factors()
        )
        
        if success:
            logger.info("All reset operations completed successfully")
        else:
            logger.error("One or more reset operations failed")
        
        return success
        
    except Exception as e:
        logger.error("Unexpected error in reset_all", "DATABASE_OPERATION", e)
        return False

if __name__ == "__main__":
    success = reset_all()
    if success:
        logger.info("Comprehensive dataset reset completed successfully")
    else:
        logger.error("Comprehensive dataset reset failed - check logs for details")
        exit(1)