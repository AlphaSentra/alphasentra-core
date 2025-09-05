import yfinance as yf
from datetime import datetime, timedelta

# Test what happens when we pass a single character to yf.download
print("Testing with single character 'A':")
end_date = datetime.now()
start_date = end_date - timedelta(days=60)
try:
    data = yf.download('A', start=start_date, end=end_date, progress=False)
    print(f"Success: {type(data)}")
except Exception as e:
    print(f"Error: {e}")

# Test what happens when we iterate through a string
print("\nTesting iterating through string 'AAPL':")
ticker = 'AAPL'
for char in ticker:
    print(f"Character: {char}")
    try:
        data = yf.download(char, start=start_date, end=end_date, progress=False)
        print(f"  Success: {type(data)}")
    except Exception as e:
        print(f"  Error: {e}")