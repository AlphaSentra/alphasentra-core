"""
Equity High Conviction Backtest (eq_hcb) Model

This module provides functionality to fetch and analyze high conviction equity insights
from MongoDB with positive sentiment scores. Used for backtesting trading strategies.
"""
import logging
import os
import sys
import re
import pymongo
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import DatabaseManager, check_pending_ticker_documents

def get_high_conviction_buys():
    """
    Fetch insights from last week with positive sentiment and high conviction.
    
    Retrieves insights that meet the following criteria:
    - Created within the last 7 days
    - Positive sentiment score
    - High conviction level
    
    Returns:
        list: A list of insight documents sorted by conviction (descending)
              then sentiment score (descending)
              
    Raises:
        Exception: Logs database connection errors but continues execution
    """
    try:
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
    except Exception as e:
        return []
    collection = db["insights"]
    
    # Configuration variables
    tag_string = ">high conviction buy ↗"
    min_sentiment_score = 0  # Minimum sentiment score to include
    conviction_threshold = 0.7  # Minimum conviction level to include
    importance_level = 3  # Importance level to set for matched insights
    p1m_threshold = 0.01  # 1-Month price change threshold (5%)
    p3m_threshold = 0.01  # 3-Month price change threshold (10%)
    p6m_threshold = 0.01  # 6-Month price change threshold (15%)    

    # Calculate date range
    now = datetime.now(timezone.utc)
    last_session = now - timedelta(days=1)
    
    # Query documents
    # Convert datetime objects to ISO strings for string comparison
    query = {
        "timestamp_gmt": {
            "$gte": last_session.isoformat(),
            "$lte": now.isoformat()
        },
        "sentiment_score": {"$gt": min_sentiment_score},
        "conviction": {"$gte": conviction_threshold},
        "tag": {"$not": {"$regex": re.escape(tag_string)}}
    }
    
    results = list(collection.find(query).sort([
        ("conviction", pymongo.DESCENDING),
        ("sentiment_score", pymongo.DESCENDING)
    ]))
    

    for insight in results:
        p1m = 0.0
        p3m = 0.0
        p6m = 0.0

        # Fetch ticker data for each insight
        ticker_collection = db["tickers"]
        if insight.get("recommendations"):
            ticker = insight["recommendations"][0].get("ticker")
            if ticker:
                ticker_data = ticker_collection.find_one({"ticker": ticker})
                if ticker_data:
                    p1m = ticker_data.get("1m", 0.0) or 0.0
                    p3m = ticker_data.get("3m", 0.0) or 0.0
                    p6m = ticker_data.get("6m", 0.0) or 0.0
        
        if (p1m or 0.0) >= p1m_threshold and (p3m or 0.0) >= p3m_threshold and (p6m or 0.0) >= p6m_threshold:
            print(ticker, p1m, p3m, p6m)
            collection.update_one(
                {"_id": insight["_id"]},
                [{
                    "$set": {
                        "importance": importance_level,
                        "tag": {
                            "$cond": [
                                {"$not": {"$regexMatch": {"input": {"$ifNull": ["$tag", ""]}, "regex": re.escape(tag_string)}}},
                                {
                                    "$cond": {
                                        "if": {"$gt": [{"$strLenCP": {"$ifNull": ["$tag", ""]}}, 0]},
                                        "then": {"$concat": ["$tag", ",", tag_string]},
                                        "else": tag_string
                                    }
                                },
                                "$tag"
                            ]
                        }
                    }
                }]
            )
    
    # Uncheck flag for function unflag_hcb_pipeline_task()
    collection = db["pipeline"]
    collection.update_one(
        {"model_function": "unflag_hcb_pipeline_task"},
        {"$set": {"task_completed": False}}
    )

    return results


def unflag_hcb_pipeline_task() -> None:
    """
    Unflag the HCB pipeline task_completed check in MongoDB.
    
    This function will:
    1. Connect to the MongoDB database
    2. Check if there are pending ticker documents
    3. If pending documents exist, unflag the pipeline task
    
    Raises:
        pymongo.errors.PyMongoError: For database operation errors (logged but not raised)
    """
    try:
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        pipeline_collection = db["pipeline"]
        
        if not check_pending_ticker_documents():
            return
            
        update_result = pipeline_collection.update_one(
            {"model_function": "get_high_conviction_buys"},
            {"$set": {"task_completed": False}}
        )
        
        if update_result.matched_count == 0:
            logging.warning("No pipeline document found to unflag")
        elif update_result.modified_count == 0:
            logging.info("Pipeline task was already unflagged")
            
    except pymongo.errors.PyMongoError as e:
        logging.error(f"Database operation failed: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error in unflag_hcb_pipeline_task: {str(e)}")


if __name__ == "__main__":
    get_high_conviction_buys()
