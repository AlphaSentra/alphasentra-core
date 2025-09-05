import yfinance as yf
import pandas as pd
import numpy as np
import backtrader as bt
from backtrader.indicators import ATR, ADX
from datetime import datetime, timedelta

def calculate_stop_loss_price(tickers, trade_direction, period=14):
    """
    Calculate an appropriate stop loss price level based on ADX and ATR indicators.
    
    Parameters:
    tickers (list): List of ticker symbols as strings
    trade_direction (str): Trade direction, either "LONG" or "SHORT"
    period (int): Period for ADX and ATR calculations (default: 14)
    
    Returns:
    dict: Dictionary with ticker as key and stop loss price as value
    """
    
    # Validate trade direction
    if trade_direction not in ["LONG", "SHORT"]:
        raise ValueError("Trade direction must be either 'LONG' or 'SHORT'")
    
    # Dictionary to store stop loss prices
    stop_loss_prices = {}
    
    # Fetch data for all tickers
    for ticker in tickers:
        try:
            print(f"Processing ticker: {ticker} (type: {type(ticker)})")
            # Fetch historical data for the last 60 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            print(f"Downloaded data for {ticker}: {type(data)}")
            
            if data.empty:
                print(f"No data available for {ticker}")
                continue
            
            # Prepare data for backtrader
            print("Preparing data for backtrader...")
            data_feed = bt.feeds.PandasData(dataname=data)
            print("Data prepared for backtrader")
            
            # Create a cerebro instance
            print("Creating cerebro instance...")
            cerebro = bt.Cerebro()
            print("Cerebro instance created")
            
            # Add data to cerebro
            print("Adding data to cerebro...")
            cerebro.adddata(data_feed)
            print("Data added to cerebro")
            
            # Create a strategy to calculate indicators
            print("Creating strategy...")
            class IndicatorStrategy(bt.Strategy):
                def __init__(self):
                    print("Initializing indicators...")
                    self.atr = ATR(period=period)
                    self.adx = ADX(period=period)
                    print("Indicators initialized")
                
                def next(self):
                    pass  # We don't need to do anything in next()
            
            # Add strategy to cerebro
            print("Adding strategy to cerebro...")
            cerebro.addstrategy(IndicatorStrategy)
            print("Strategy added to cerebro")
            
            # Run cerebro to calculate indicators
            print("Running cerebro...")
            results = cerebro.run()
            print("Cerebro run completed")
            
            # Get the strategy instance
            print("Getting strategy instance...")
            strategy = results[0]
            print("Strategy instance obtained")
            
            # Get the latest values of indicators
            print("Getting indicator values...")
            current_atr = strategy.atr[0]
            current_adx = strategy.adx[0]
            current_close = data['Close'].iloc[-1]
            print(f"ATR: {current_atr}, ADX: {current_adx}, Close: {current_close}")
            
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
            
            # Store the result
            stop_loss_prices[ticker] = max(0, stop_loss_price)  # Ensure non-negative
            print(f"Stop loss price for {ticker}: {stop_loss_prices[ticker]}")
            
        except Exception as e:
            print(f"Error calculating stop loss for {ticker}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return stop_loss_prices

# Test with a single ticker
tickers = ['AAPL']
print("Testing with single ticker:")
result = calculate_stop_loss_price(tickers, 'LONG')
print(f"Result: {result}")