"""
Price data functions using yfinance library.
Centralized location for all price data functions.
"""

import yfinance as yf
import backtrader as bt
from backtrader.indicators import ATR, ADX
from datetime import datetime, timedelta

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