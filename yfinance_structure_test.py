import yfinance as yf
from datetime import datetime, timedelta

# Test yf.download with a single ticker
print("Testing with single ticker AAPL:")
end_date = datetime.now()
start_date = end_date - timedelta(days=60)
data = yf.download('AAPL', start=start_date, end=end_date, progress=False)
print(f"Type: {type(data)}")
print(f"Columns: {data.columns}")
print(f"Index: {data.index}")
print(f"Shape: {data.shape}")

# Test accessing Close column
try:
    close_data = data['Close']
    print(f"Close data type: {type(close_data)}")
    print(f"Close data: {close_data}")
    last_close = close_data.iloc[-1]
    print(f"Last close: {last_close}")
except Exception as e:
    print(f"Error accessing Close column: {e}")

# Test yf.download with a list containing a single ticker
print("\nTesting with list containing single ticker ['AAPL']:")
data2 = yf.download(['AAPL'], start=start_date, end=end_date, progress=False)
print(f"Type: {type(data2)}")
print(f"Columns: {data2.columns}")
print(f"Index: {data2.index}")
print(f"Shape: {data2.shape}")

# Test accessing Close column for list
try:
    close_data2 = data2['Close']
    print(f"Close data type: {type(close_data2)}")
    print(f"Close data: {close_data2}")
    last_close2 = close_data2.iloc[-1]
    print(f"Last close: {last_close2}")
except Exception as e:
    print(f"Error accessing Close column: {e}")

# Test yf.download with multiple tickers
print("\nTesting with multiple tickers ['AAPL', 'MSFT']:")
data3 = yf.download(['AAPL', 'MSFT'], start=start_date, end=end_date, progress=False)
print(f"Type: {type(data3)}")
print(f"Columns: {data3.columns}")
print(f"Index: {data3.index}")
print(f"Shape: {data3.shape}")

# Test accessing Close column for multiple tickers
try:
    close_data3 = data3['Close']
    print(f"Close data type: {type(close_data3)}")
    print(f"Close data: {close_data3}")
    last_close3 = close_data3.iloc[-1]
    print(f"Last close: {last_close3}")
except Exception as e:
    print(f"Error accessing Close column: {e}")