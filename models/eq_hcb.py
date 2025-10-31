"""
Equity High Conviction Backtest (eq_hcb) Model

This module provides functionality to fetch and analyze high conviction equity insights
from MongoDB with positive sentiment scores. Used for backtesting trading strategies.
"""
import os
import sys
import pymongo
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import DatabaseManager

def get_positive_high_conviction_insights():
    """
    Fetch insights from last week with positive sentiment and high conviction.
    
    Retrieves insights from MongoDB that meet the following criteria:
    - Created within the last 7 days
    - Positive sentiment score (>0)
    - High conviction level (>=0.70)
    
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
        print(f"Database connection failed: {e}")
        return []
    collection = db["insights"]
    
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
        "sentiment_score": {"$gt": 0},
        "conviction": {"$gte": 0.70}
    }
    
    results = list(collection.find(query).sort([
        ("conviction", pymongo.DESCENDING),
        ("sentiment_score", pymongo.DESCENDING)
    ]))
    print(f"Found {len(results)} insights:")
    for insight in results:
        print(insight)
        
    return results


if __name__ == "__main__":
    get_positive_high_conviction_insights()