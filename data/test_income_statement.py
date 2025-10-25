import yfinance as yf
import pandas as pd

# 1. Define the ticker symbol
ticker_symbol = "PG"
ticker = yf.Ticker(ticker_symbol)

# 2. Get the annual income statement
# The 'financials' attribute returns the annual Income Statement as a pandas DataFrame
income_statement = ticker.financials

# 3. Extract the 'Net Income' row and select the last 5 columns (years)
try:
    # .loc['Net Income'] selects the row
    # .iloc[:, :5] selects the first 5 columns (most recent 5 years)
    net_income_series = income_statement.loc['Net Income'].iloc[:5]
    
    # Format the output for better readability
    net_income_df = net_income_series.to_frame(name='Net Income')
    net_income_df['Net Income'] = net_income_df['Net Income'].apply(lambda x: f"${x:,.0f}")
    
    print(f"Annual Net Income for {ticker_symbol} (Last 5 Years):\n")
    print(net_income_df)
    
except KeyError:
    print(f"Could not find 'Net Income' in the financials for {ticker_symbol}.")
except IndexError:
    print(f"Only found {len(income_statement.columns)} years of data. Displaying all available annual Net Income:")
    net_income_series = income_statement.loc['Net Income']
    net_income_df = net_income_series.to_frame(name='Net Income')
    net_income_df['Net Income'] = net_income_df['Net Income'].apply(lambda x: f"${x:,.0f}")
    print(net_income_df)
except Exception as e:
    print(f"An error occurred: {e}")