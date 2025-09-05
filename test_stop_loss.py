"""
Test script for stop loss recommendation function
"""

from helpers import get_stop_loss_recommendations

def test_stop_loss_recommendations():
    # Test data
    tickers_with_direction = [
        {'ticker': 'AAPL', 'trade_direction': 'LONG'},
        {'ticker': 'GOOGL', 'trade_direction': 'SHORT'},
        {'ticker': 'MSFT', 'trade_direction': 'LONG'},
        {'ticker': 'AMZN', 'trade_direction': 'SHORT'}
    ]
    
    # Get stop loss recommendations
    recommendations = get_stop_loss_recommendations(tickers_with_direction)
    
    # Print results
    print("Stop Loss Recommendations:")
    print("[")
    for i, rec in enumerate(recommendations):
        comma = "," if i < len(recommendations) - 1 else ""
        print(f"  {{'ticker': '{rec['ticker']}', 'trade_direction': '{rec['trade_direction']}', 'stop_loss': {rec['stop_loss']}}}{comma}")
    print("]")
    
    return recommendations

if __name__ == "__main__":
    test_stop_loss_recommendations()