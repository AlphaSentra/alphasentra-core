"""
Description:
Price data functions using yfinance library.
Centralized location for all price data functions.

# License & Third-Party Notices

## MIT License

Copyright (c) [Year] [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Third-Party Libraries

This project uses the following third-party libraries:

- **yfinance** ([MIT License](https://pypi.org/project/yfinance/))  

  Please note: This library fetches data from Yahoo Finance. The data itself
  is subject to Yahoo Finance's Terms of Service. You may use the data
  internally within this application, but redistribution or bulk downloads
  may require additional permissions from Yahoo Finance.
"""


import yfinance as yf
import backtrader as bt
from backtrader.indicators import ATR, ADX
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def calculate_trade_levels(tickers, trade_direction, period=14, decimal_digits=2):
    """
    Calculate appropriate stop loss and target price levels based on ADX and ATR indicators.
    
    Parameters:
    tickers (list): List of ticker symbols as strings
    trade_direction (str): Trade direction, either "LONG" or "SHORT"
    period (int): Period for ADX and ATR calculations (default: 14)
    decimal_digits (int): Number of decimal digits for rounding prices (default: 2)
    
    Returns:
    dict: Dictionary with ticker as key and dict with 'stop_loss' and 'target_price' as values
    """
    
    try:
        # Validate trade direction
        if trade_direction not in ["LONG", "SHORT"]:
            raise ValueError("Trade direction must be either 'LONG' or 'SHORT'")
        
        # Dictionary to store stop loss prices
        stop_loss_prices = {}

        logger.info("Calculating stop loss prices...")

        # Fetch data for all tickers
        for ticker in tickers:
            try:
                # Fetch historical data for the last 60 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=60)
                data = yf.download(ticker, start=start_date, end=end_date, progress=False, multi_level_index=False)
                
                if data.empty:
                    logger.error(f"No data available for {ticker}")
                    continue
                
                # Prepare data for backtrader
                data_feed = bt.feeds.PandasData(dataname=data)
                
                # Create a cerebro instance
                cerebro = bt.Cerebro()
                
                # Add data to cerebro
                cerebro.adddata(data_feed)
                
                # Create a strategy to calculate indicators
                class IndicatorStrategy(bt.Strategy):
                    def __init__(self):
                        self.atr = ATR(period=period)
                        self.adx = ADX(period=period)
                    
                    def next(self):
                        pass  # We don't need to do anything in next()
                
                # Add strategy to cerebro
                cerebro.addstrategy(IndicatorStrategy)
                
                # Run cerebro to calculate indicators
                results = cerebro.run()
                
                # Get the strategy instance
                strategy = results[0]
                
                # Get the latest values of indicators
                current_atr = strategy.atr[0]
                current_adx = strategy.adx[0]
                current_close = data['Close'].iloc[-1]
                
                # Calculate stop loss based on ADX strength and ATR
                # Higher ADX means stronger trend, so we can place stop loss further away
                # Lower ADX means weaker trend, so we place stop loss closer
                
                # Normalize ADX (typically ranges from 0 to 100)
                adx_strength = min(current_adx / 100, 1.0)  # Cap at 1.0
                
                # Use ATR as the base for stop loss distance
                # Multiply by a factor that depends on ADX strength
                # For stronger trends (high ADX), use 1.5x ATR
                # For weaker trends (low ADX), use 2.5x ATR
                atr_multiplier = 2.5 - (adx_strength * 1.0)  # Ranges from 2.5 to 1.5
                
                # Calculate stop loss distance
                stop_loss_distance = current_atr * atr_multiplier
                
                # Calculate stop loss price based on trade direction
                if trade_direction == "LONG":
                    stop_loss_price = current_close - stop_loss_distance
                else:  # SHORT
                    stop_loss_price = current_close + stop_loss_distance
                
                # Calculate entry price for this ticker
                entry_prices = calculate_entry_price([ticker], trade_direction)
                entry_price = entry_prices.get(ticker, current_close)  # Fallback to current close if entry price calculation fails
                
                # Calculate target price for consistent 1:2.5 risk-reward ratio
                # Use actual risk distance (entry to stop loss) rather than ATR-based distance
                risk_distance = abs(entry_price - stop_loss_price)
                if trade_direction == "LONG":
                    target_price = entry_price + (2.0 * risk_distance)
                else:  # SHORT
                    target_price = entry_price - (2.0 * risk_distance)
                
                # Store the result
                stop_loss_prices[ticker] = {
                    'stop_loss': max(0, stop_loss_price),  # Ensure non-negative
                    'target_price': max(0, target_price)   # Ensure non-negative
                }
                
                
            except Exception as e:
                logger.error(f"Error calculating stop loss for {ticker}: {e}")
                logger.exception("Traceback for stop loss calculation error")
                continue
        
        return stop_loss_prices
    except Exception as e:
        logger.error(f"ERROR in calculate_trade_levels: {e}")
        logger.exception("Traceback for calculate_trade_levels error")
        return {}


def calculate_entry_price(tickers, trade_direction, period=5):
    """
    Calculate an appropriate entry price based on past week's high and low.
    
    For LONG positions: Entry price is set at the high since the past week to now
    For SHORT positions: Entry price is set at the low since the past week to now
    
    Parameters:
    tickers (list): List of ticker symbols as strings
    trade_direction (str): Trade direction, either "LONG" or "SHORT"
    period (int): Period for high/low calculations in days (default: 5 for one week)
    
    Returns:
    dict: Dictionary with ticker as key and entry price as value
    """
    
    try:
        # Validate trade direction
        if trade_direction not in ["LONG", "SHORT"]:
            raise ValueError("Trade direction must be either 'LONG' or 'SHORT'")
        
        # Dictionary to store entry prices
        entry_prices = {}

        logger.info("Calculating entry prices...")

        # Fetch data for all tickers
        for ticker in tickers:
            try:
                # Fetch historical data for the last 30 days (to ensure we have enough data for weekly calculations)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                data = yf.download(ticker, start=start_date, end=end_date, progress=False, multi_level_index=False)
                
                if data.empty:
                    logger.error(f"No data available for {ticker}")
                    continue
                
                # Get data for the past week only (last 5 trading days)
                week_data = data.tail(period)
                
                if len(week_data) < period:
                    logger.warning(f"Not enough data for {ticker} to calculate weekly high/low")
                    continue
                
                # Calculate weekly high and low
                week_high = week_data['High'].max()
                week_low = week_data['Low'].min()
                
                # Calculate entry price based on trade direction
                # For LONG positions, entry price is at the high since past week to now
                # For SHORT positions, entry price is at the low since past week to now
                if trade_direction == "LONG":
                    # Enter at the high since past week to now
                    entry_price = week_high
                else:  # SHORT
                    # Enter at the low since past week to now
                    entry_price = week_low
                
                # Store the result as Python float
                entry_prices[ticker] = float(max(0, entry_price))  # Ensure non-negative
                
                
            except Exception as e:
                logger.error(f"Error calculating entry price for {ticker}: {e}")
                logger.exception("Traceback for entry price calculation error")
                continue
        
        return entry_prices
    except Exception as e:
        logger.error(f"ERROR in calculate_entry_price: {e}")
        logger.exception("Traceback for calculate_entry_price error")
        return {}


def get_current_price(ticker):
    """
    Get the current market price for a given ticker.
    
    Parameters:
    ticker (str): Ticker symbol
    
    Returns:
    float: Current market price, or None if unavailable
    """
    try:
        # Fetch data with multiple periods to get latest available price
        stock = yf.Ticker(ticker)
        
        # Try multiple periods to get the latest available data
        periods = ['1d', '5d', '1mo', '3mo']
        
        for period in periods:
            data = stock.history(period=period)
            if not data.empty:
                # Get the most recent closing price
                latest_price = data['Close'].iloc[-1]
                return float(latest_price)
        
        logger.error(f"No data available for {ticker} with any period")
        return None
        
    except Exception as e:
        logger.error(f"Error getting price data for {ticker}: {e}")
        return None
    

def calculate_performance_metrics(ticker):
    """
    Calculate performance metrics for a ticker using yfinance
    
    Parameters:
    ticker (str): Ticker symbol
    
    Returns:
    dict: Dictionary containing performance metrics with keys:
        '1y' - 1 year percentage performance (double)
        '6m' - 6 months percentage performance (double)
        '3m' - 3 months percentage performance (double)
        '1m' - 1 month percentage performance (double)
        '1d' - previous session percentage performance (double)
    """
    # Handle case where ticker is passed as a list by mistake
    if isinstance(ticker, list):
        if ticker:
            ticker = ticker[0]
            logger.warning(f"calculate_performance_metrics received a list, using first element: {ticker}")
        else:
            logger.error("calculate_performance_metrics received an empty list")
            return {}
    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.now()
        
        # Get current price
        current_price = get_current_price(ticker)
        if current_price is None:
            return {}
        
        # Calculate performance periods
        periods = {
            '1y': end_date - timedelta(days=365),
            '6m': end_date - timedelta(days=180),
            '3m': end_date - timedelta(days=90),
            '1m': end_date - timedelta(days=30),
            '1d': end_date - timedelta(days=1)
        }
        
        performance = {}
        
        for period, start_date in periods.items():
            try:
                # Get historical price
                hist = stock.history(start=start_date, end=end_date, interval="1d")
                if not hist.empty:
                    start_price = hist['Close'].iloc[0]
                    performance[period] = ((current_price / start_price) - 1)
                else:
                    performance[period] = 0.0
            except Exception as e:
                performance[period] = 0.0
        
        # Calculate daily performance separately using previous close
        try:
            hist = stock.history(period="2d")
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
                performance['1d'] = ((current_price / prev_close) - 1)
        except Exception as e:
            performance['1d'] = 0.0
        
        return performance
        
    except Exception as e:
        print(f"Error calculating performance for {ticker}: {str(e)}")
        return {}

def get_dividend_yield(ticker):
    """
    Get the latest dividend yield for a given ticker from Yahoo Finance.
    
    Parameters:
    ticker (str): Ticker symbol
    
    Returns:
    float: Dividend yield as a double (e.g., 1% = 0.01), or None if unavailable
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        dividend_yield = info.get('dividendYield')
        if dividend_yield is not None:
            return float(dividend_yield) / 100  # Convert percentage to decimal
        
        logger.warning(f"No dividend yield data available for {ticker}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting dividend yield for {ticker}: {e}")
        return None


def get_growth_profitability_chart(ticker):
    """
    Get growth and profitability chart data for the last five years from Yahoo Finance.
    
    Parameters:
    ticker (str): Ticker symbol
    
    Returns:
    dict: Formatted chart data with revenue, net income, and net margin in specified format
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get financial statements for the last 5 years
        financials = stock.financials
        if financials.empty:
            logger.error(f"No financial data available for {ticker}")
            return {}
        
        # Get quarterly financials and resample to semi-annual
        quarterly = stock.quarterly_financials
        if quarterly.empty:
            logger.error(f"No quarterly financial data available for {ticker}")
            return {}
        
        # Convert columns to DatetimeIndex and transpose for resampling
        quarterly = quarterly.T
        quarterly.index = pd.to_datetime(quarterly.index)
        
        # Check for required columns with alternative names
        revenue_col = next((col for col in ['Total Revenue', 'Revenue'] if col in quarterly.columns), None)
        net_income_col = next((col for col in ['Net Income', 'Net Income Common Stockholders'] if col in quarterly.columns), None)
        
        if not revenue_col or not net_income_col:
            missing = []
            if not revenue_col: missing.append('revenue')
            if not net_income_col: missing.append('net income')
            logger.error(f"Missing required financial metrics ({', '.join(missing)}) for {ticker}")
            return {}
        
        # Resample to semi-annual periods (H1 and H2) using new frequency convention
        semi_annual = quarterly.resample('6ME', closed='left').sum()
        
        # Get last 11 periods (5.5 years) to ensure we have 5 full years
        semi_annual = semi_annual.iloc[:, -11:] if len(semi_annual.columns) >= 11 else semi_annual
        
        # Extract revenue and net income from columns
        try:
            revenue = semi_annual['Total Revenue'].tolist()
            net_income = semi_annual['Net Income'].tolist()
        except KeyError as e:
            logger.error(f"Missing required financial metric: {e}")
            return {}
        
        # Calculate net margin percentages
        net_margin = [(ni / rev * 100) if rev != 0 else 0 for ni, rev in zip(net_income, revenue)]
        
        # Generate period labels (H1 2020, H2 2020, etc.)
        periods = []
        for date in semi_annual.index:  # Use index after resampling
            year = date.year
            half = 'H1' if date.month <= 6 else 'H2'
            periods.append(f"{half} {year}")
        
        # Create the chart data structure
        chart_data = {
            "growth_profitability_chart": {
                "title": f"Company Performance ({periods[0]}–{periods[-1]})",
                "xAxis": {
                    "label": "Period",
                    "categories": periods
                },
                "yAxes": [
                    {
                        "id": "revenueIncomeAxis",
                        "label": "Amount (in millions)",
                        "type": "bar"
                    },
                    {
                        "id": "marginAxis",
                        "label": "Net Margin (%)",
                        "type": "line"
                    }
                ],
                "series": [
                    {
                        "name": "Revenue",
                        "type": "bar",
                        "yAxisId": "revenueIncomeAxis",
                        "data": revenue
                    },
                    {
                        "name": "Net Income",
                        "type": "bar",
                        "yAxisId": "revenueIncomeAxis",
                        "data": net_income
                    },
                    {
                        "name": "Net Margin",
                        "type": "line",
                        "yAxisId": "marginAxis",
                        "data": net_margin
                    }
                ]
            }
        }
        
        return chart_data
        
    except Exception as e:
        logger.error(f"Error generating growth/profitability chart for {ticker}: {e}")
        logger.exception("Traceback for growth/profitability chart error")
        return {}

def financial_health_chart(ticker):
    """
    Get financial health chart data for the last five years from Yahoo Finance.
    
    Parameters:
    ticker (str): Ticker symbol
    
    Returns:
    dict: Formatted chart data with debt, free cash flow, and cash & equivalents in specified format
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get and transpose financial statements immediately
        cashflow = stock.quarterly_cashflow.T
        balance_sheet = stock.quarterly_balance_sheet.T
        
        if cashflow.empty or balance_sheet.empty:
            logger.error(f"No financial data available for {ticker}")
            return {}
        
        # Calculate Free Cash Flow if not available
        if 'Free Cash Flow' not in cashflow:
            try:
                cashflow['Free Cash Flow'] = cashflow['Total Cash From Operating Activities'] - cashflow['Capital Expenditures']
            except KeyError as e:
                logger.error(f"Missing required columns for Free Cash Flow calculation: {e}")
                return {}
        
        # Find cash column with alternative names
        cash_col = next((col for col in ['Cash', 'Cash And Cash Equivalents', 'Cash And Short Term Investments']
                        if col in balance_sheet.columns), None)
        
        if not cash_col:
            logger.error(f"Missing cash-related columns in balance sheet for {ticker}")
            return {}
        
        # Create combined dataframe with required metrics
        try:
            data = pd.DataFrame({
                'Free Cash Flow': cashflow['Free Cash Flow'],
                'Cash & Cash Equivalents': balance_sheet[cash_col],
                'Total Debt': balance_sheet['Long Term Debt'] + balance_sheet.get('Short Long Term Debt', 0)
            })
        except KeyError as e:
            logger.error(f"Missing required column: {e}")
            return {}
        
        # Convert index to datetime and filter last 5 years
        data.index = pd.to_datetime(data.index)
        data = data[data.index >= pd.Timestamp.now() - pd.DateOffset(years=5)]
        
        # Group into semi-annual periods
        semi_annual_data = data.groupby(data.index.to_period('6M')).sum()
        
        # Generate period labels (H1 2020, H2 2020, etc.)
        periods = []
        for date in semi_annual_data.index:
            year = date.year
            half = 'H1' if date.month <= 6 else 'H2'
            periods.append(f"{half} {year}")
        
        # Create chart data structure
        chart_data = {
            "financial_health_chart": {
                "title": f"Financial Health ({periods[0]}–{periods[-1]})",
                "xAxis": {
                    "label": "Period",
                    "categories": periods
                },
                "yAxis": {
                    "label": "Amount (in millions)",
                    "type": "bar"
                },
                "series": [
                    {
                        "name": "Debt",
                        "type": "bar",
                        "data": (semi_annual_data['Total Debt'] / 1e6).tolist()
                    },
                    {
                        "name": "Free Cash Flow",
                        "type": "bar",
                        "data": (semi_annual_data['Free Cash Flow'] / 1e6).tolist()
                    },
                    {
                        "name": "Cash & Equivalents",
                        "type": "bar",
                        "data": (semi_annual_data['Cash & Cash Equivalents'] / 1e6).tolist()
                    }
                ]
            }
        }
        
        return chart_data
        
    except Exception as e:
        logger.error(f"Error generating financial health chart for {ticker}: {e}")
        logger.exception("Traceback for financial health chart error")
        return {}
    
def get_capital_structure_chart(ticker):
    """Fetch capital structure data from Yahoo Finance and format as pie chart"""
    import yfinance as yf
    try:
        stock = yf.Ticker(ticker)
        balance_sheet = stock.balance_sheet
        if balance_sheet.empty:
            return None
            
        latest = balance_sheet.iloc[:,0]
        equity = latest.get('Stockholders Equity', 0)
        debt = latest.get('Total Debt', 0)
        other_liabilities = latest.get('Other Liabilities', 0)
        
        return {
            "capital_structure_chart": {
                "title": "Capital Structure (Latest)",
                "type": "pie",
                "series": [
                    {"name": "Equity", "value": float(equity)},
                    {"name": "Debt", "value": float(debt)},
                    {"name": "Other Liabilities", "value": float(other_liabilities)}
                ]
            }
        }
    except Exception as e:
        print(f"Error fetching capital structure: {e}")
        return None
    

def get_dividend_history_chart(ticker):
    """
    Get dividend history chart data for the last five years from Yahoo Finance.
    
    Parameters:
    ticker (str): Ticker symbol
    
    Returns:
    dict: Formatted chart data with dividend per share and dividend yield in specified format
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get dividend history for last 5 years
        dividends = stock.dividends
        if dividends.empty:
            logger.error(f"No dividend data available for {ticker}")
            return {}
        
        # Resample to annual dividends using new frequency convention
        annual_dividends = dividends.resample('YE').sum().tail(5)
        
        # Get historical prices for yield calculation
        history = stock.history(period="5y")
        if history.empty:
            logger.error(f"No price history available for {ticker}")
            return {}
        
        # Resample to annual closing prices using new frequency convention
        annual_prices = history['Close'].resample('YE').last()
        
        # Align dividend and price data
        aligned_data = pd.DataFrame({
            'dividend': annual_dividends,
            'price': annual_prices
        }).dropna()
        
        # Calculate dividend yield (dividend / price * 100) and round to 2 decimals
        aligned_data['yield'] = ((aligned_data['dividend'] / aligned_data['price']) * 100).round(2)
        
        # Generate year labels
        years = [str(idx.year) for idx in aligned_data.index]
        
        # Create the chart data structure

        chart_data = {
            "dividend_history_chart": {
                "title": f"Dividend History ({years[0]}–{years[-1]})",
                "xAxis": {
                    "label": "Period",
                    "categories": years
                },
                "yAxes": [
                    {
                        "id": "dividendAxis",
                        "label": "Dividend per Share",
                        "type": "bar"
                    },
                    {
                        "id": "yieldAxis",
                        "label": "Dividend Yield (%)",
                        "type": "line"
                    }
                ],
                "series": [
                    {
                        "name": "Dividend per Share",
                        "type": "bar",
                        "yAxisId": "dividendAxis",
                        "data": aligned_data['dividend'].tolist()
                    },
                    {
                        "name": "Dividend Yield",
                        "type": "line",
                        "yAxisId": "yieldAxis",
                        "data": aligned_data['yield'].tolist()
                    }
                ]
            }
        }
        
        return chart_data
        
    except Exception as e:
        logger.error(f"Error generating dividend history chart for {ticker}: {e}")
        logger.exception("Traceback for dividend history chart error")
        return {}
