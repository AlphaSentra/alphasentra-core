import yfinance as yf
import pandas as pd

# 1. Define the ticker symbol
ticker_symbol = "PG"
ticker = yf.Ticker(ticker_symbol)

# --- 2. Extract Data from Financial Statements ---

# 2a. Get Total Debt and Cash from the Annual Balance Sheet
# We use .T to transpose the data to have dates as the index
balance_sheet = ticker.balance_sheet.T

# 2b. Get Free Cash Flow from the Annual Cash Flow Statement
cash_flow = ticker.cashflow.T

# 2c. Get Net Income from Annual Income Statement (Just for reference/completeness)
income_statement = ticker.financials.T

# --- 3. Consolidate Data ---

# Define the data points we need and their source attribute
data_points = {
    "Total Debt": balance_sheet.get('Total Debt', pd.Series()), # Note: Label might vary for some stocks
    "Cash and Equivalents": balance_sheet.get('Cash And Cash Equivalents', pd.Series()),
    "Free Cash Flow": cash_flow.get('Free Cash Flow', pd.Series())
}

# Create a DataFrame to hold the consolidated data
financial_data = pd.DataFrame(data_points)

# --- 4. Clean and Display the Last 5 Years ---

# Filter the DataFrame to show only the last 5 available years and format
if not financial_data.empty:
    # Sort by date (index) descending to ensure we get the *most recent* 5 years
    financial_data = financial_data.sort_index(ascending=False).head(5)

    # Convert the values to a readable format (Millions or Billions with $)
    def format_value(value):
        if pd.isna(value):
            return "N/A"
        # Display as Billions to 1 decimal place, e.g., 50,000,000,000 -> $50.0B
        return f"${value / 1e9:,.1f}B"

    formatted_data = financial_data.applymap(format_value)

    print(f"Annual Key Financial Data for {ticker_symbol} (Last 5 Available Years):\n")
    print(formatted_data)
else:
    print(f"Could not retrieve financial data for {ticker_symbol}.")

# --- Important Note on Data Field Names ---

# Financial data field names can sometimes vary slightly in yfinance depending on the company's reporting.
# The code above uses the most common label: 'Total Debt' and 'Cash And Cash Equivalents'.
# If you run the code and see 'N/A' for Total Debt or Cash, you may need to inspect the full
# 'ticker.balance_sheet' output to find the exact label being used for that specific company.
# For example, 'Cash And Cash Equivalents' might be just 'Cash' or 'Cash, Cash Equivalents & Restricted Cash'.