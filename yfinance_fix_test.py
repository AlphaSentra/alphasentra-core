import yfinance as yf
from datetime import datetime, timedelta

# Test yf.download with multi_level_index=False
print("Testing with multi_level_index=False:")
end_date = datetime.now()
start_date = end_date - timedelta(days=60)
data = yf.download('AAPL', start=start_date, end=end_date, progress=False, multi_level_index=False)
print(f"Type: {type(data)}")
print(f"Columns: {data.columns}")
print(f"Columns type: {type(data.columns)}")
print(f"Columns values: {data.columns.values}")
print(f"Columns values type: {type(data.columns.values)}")

# Test accessing individual column names
print("\nTesting column name access:")
for i, col in enumerate(data.columns.values):
    print(f"Column {i}: {col} (type: {type(col)})")
    if hasattr(col, 'lower'):
        print(f"  lower(): {col.lower()}")
    else:
        print(f"  No lower() method")

# Test with group_by='ticker'
print("\n\nTesting with group_by='ticker':")
data2 = yf.download('AAPL', start=start_date, end=end_date, progress=False, group_by='ticker')
print(f"Type: {type(data2)}")
print(f"Columns: {data2.columns}")
print(f"Columns type: {type(data2.columns)}")
print(f"Columns values: {data2.columns.values}")
print(f"Columns values type: {type(data2.columns.values)}")

# Test accessing individual column names
print("\nTesting column name access:")
for i, col in enumerate(data2.columns.values):
    print(f"Column {i}: {col} (type: {type(col)})")
    if hasattr(col, 'lower'):
        print(f"  lower(): {col.lower()}")
    else:
        print(f"  No lower() method")