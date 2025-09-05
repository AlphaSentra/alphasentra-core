import yfinance as yf
from datetime import datetime, timedelta

# Test with a string ticker
print("Testing with string ticker 'AAPL':")
end_date = datetime.now()
start_date = end_date - timedelta(days=60)
try:
    data = yf.download('AAPL', start=start_date, end=end_date, progress=False)
    print(f"Success: {type(data)}")
except Exception as e:
    print(f"Error: {e}")

# Test with a variable containing a string
print("\nTesting with variable containing string ticker:")
ticker = 'AAPL'
try:
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    print(f"Success: {type(data)}")
except Exception as e:
    print(f"Error: {e}")

# Test with a tuple containing a string
print("\nTesting with tuple containing string ticker:")
ticker = ('AAPL',)
try:
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    print(f"Success: {type(data)}")
except Exception as e:
    print(f"Error: {e}")

# Test with a list containing a string
print("\nTesting with list containing string ticker:")
ticker = ['AAPL']
try:
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    print(f"Success: {type(data)}")
except Exception as e:
    print(f"Error: {e}")