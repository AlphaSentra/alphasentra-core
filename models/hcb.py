"""
Equity High Conviction Backtest (eq_hcb) Model

This module provides functionality to fetch and analyze high conviction equity insights
from MongoDB with positive sentiment scores. Used for backtesting trading strategies.
"""
import os
import sys
import re
import pymongo
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import DatabaseManager

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
    last_week = now - timedelta(days=7)
    
    # Query documents
    # Convert datetime objects to ISO strings for string comparison
    query = {
        "timestamp_gmt": {
            "$gte": last_week.isoformat(),
            "$lte": now.isoformat()
        },
        "sentiment_score": {"$gt": min_sentiment_score},
        "conviction": {"$gte": conviction_threshold}
    }
    
    results = list(collection.find(query).sort([
        ("conviction", pymongo.DESCENDING),
        ("sentiment_score", pymongo.DESCENDING)
    ]))
    

    for insight in results:


        # Fetch ticker data for each insight
        ticker_collection = db["tickers"]
        if insight.get("recommendations"):
            ticker = insight["recommendations"][0].get("ticker")
            if ticker:
                ticker_data = ticker_collection.find_one({"ticker": ticker})
                if ticker_data:
                    p1m = ticker_data.get("1m")
                    p3m = ticker_data.get("3m")
                    p6m = ticker_data.get("6m")
        
        if p1m >= p1m_threshold and p3m >= p3m_threshold and p6m >= p6m_threshold:
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
        
    return results

if __name__ == "__main__":
    get_high_conviction_buys()
