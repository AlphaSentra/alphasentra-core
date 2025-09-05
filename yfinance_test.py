import yfinance as yf
from datetime import datetime, timedelta

# Test yf.download with a valid ticker
print("Testing with valid ticker AAPL:")
end_date = datetime.now()
start_date = end_date - timedelta(days=60)
data = yf.download('AAPL', start=start_date, end=end_date, progress=False)
print(f"Type: {type(data)}")
print(f"Data: {data}")

# Test yf.download with an invalid ticker
print("\nTesting with invalid ticker INVALID:")
data = yf.download('INVALID', start=start_date, end=end_date, progress=False)
print(f"Type: {type(data)}")
print(f"Data: {data}")

# Test yf.download with a list of tickers
print("\nTesting with list of tickers ['AAPL', 'MSFT']:")
data = yf.download(['AAPL', 'MSFT'], start=start_date, end=end_date, progress=False)
print(f"Type: {type(data)}")
print(f"Data: {data}")