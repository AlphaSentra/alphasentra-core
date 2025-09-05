import yfinance as yf
from datetime import datetime, timedelta

# Test yf.download with a single ticker
print("Testing with single ticker AAPL:")
end_date = datetime.now()
start_date = end_date - timedelta(days=60)
data = yf.download('AAPL', start=start_date, end=end_date, progress=False)
print(f"Type: {type(data)}")
print(f"Columns: {data.columns}")
print(f"Columns type: {type(data.columns)}")
print(f"Columns values: {data.columns.values}")
print(f"Columns values type: {type(data.columns.values)}")
print(f"Columns values[0]: {data.columns.values[0]}")
print(f"Columns values[0] type: {type(data.columns.values[0])}")

# Test accessing individual column names
print("\nTesting column name access:")
for i, col in enumerate(data.columns.values):
    print(f"Column {i}: {col} (type: {type(col)})")
    if hasattr(col, 'lower'):
        print(f"  lower(): {col.lower()}")
    else:
        print(f"  No lower() method")