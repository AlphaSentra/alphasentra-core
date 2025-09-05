"""
Project:     Alphagora Trading System
File:        helpers.py
Author:      Daiviet Huynh
Created:     2025-07-22
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Helper functions for the Alphagora Trading System.
"""



# --- HELPER FUNCTIONS ---
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

    print()
    print("Calculating stop loss prices...")

    # Fetch data for all tickers
    for ticker in tickers:
        try:
            # Fetch historical data for the last 60 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            data = yf.download(ticker, start=start_date, end=end_date, progress=False, multi_level_index=False)
            
            if data.empty:
                print(f"No data available for {ticker}")
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
            
            # Calculate stop loss distance (doubled)
            stop_loss_distance = current_atr * atr_multiplier * 2
            
            # Calculate stop loss price based on trade direction
            if trade_direction == "LONG":
                stop_loss_price = current_close - stop_loss_distance
            else:  # SHORT
                stop_loss_price = current_close + stop_loss_distance
            
            # Store the result
            stop_loss_prices[ticker] = max(0, stop_loss_price)  # Ensure non-negative
            
        except Exception as e:
            print(f"Error calculating stop loss for {ticker}: {e}")
            continue
    
    return stop_loss_prices


def get_stop_loss_recommendations(tickers_with_direction):
    """
    Return stop loss prices in the specified JSON format.
    
    Parameters:
    tickers_with_direction (list): List of dictionaries with 'ticker' and 'trade_direction' keys
    
    Returns:
    list: Array of objects with 'ticker', 'trade_direction', and 'stop_loss' keys
    """
    
    # Group tickers by trade direction
    long_tickers = []
    short_tickers = []
    
    for item in tickers_with_direction:
        ticker = item.get('ticker')
        direction = item.get('trade_direction', '').upper()
        
        if ticker and direction:
            if direction == 'LONG':
                long_tickers.append(ticker)
            elif direction == 'SHORT':
                short_tickers.append(ticker)
    
    # Calculate stop loss prices for LONG positions
    long_stop_losses = {}
    if long_tickers:
        long_stop_losses = calculate_stop_loss_price(long_tickers, 'LONG')
    
    # Calculate stop loss prices for SHORT positions
    short_stop_losses = {}
    if short_tickers:
        short_stop_losses = calculate_stop_loss_price(short_tickers, 'SHORT')
    
    # Combine all results in the required format
    recommendations = []
    
    for item in tickers_with_direction:
        ticker = item.get('ticker')
        direction = item.get('trade_direction', '').upper()
        
        if ticker and direction:
            stop_loss = None
            if direction == 'LONG' and ticker in long_stop_losses:
                stop_loss = round(long_stop_losses[ticker], 2)
            elif direction == 'SHORT' and ticker in short_stop_losses:
                stop_loss = round(short_stop_losses[ticker], 2)
            
            recommendations.append({
                'ticker': ticker,
                'trade_direction': direction,
                'stop_loss': stop_loss if stop_loss is not None else 'N/A'
            })
    
    return recommendations


def add_stop_loss_to_recommendations(recommendations):
    """
    Add stop loss prices to sector recommendations.
    
    Parameters:
    recommendations (dict): The AI recommendations dictionary
    
    Returns:
    dict: The recommendations dictionary with stop loss prices added
    """
    
    # Check if sector_recommendations exist in the recommendations
    if 'sector_recommendations' not in recommendations:
        print("No sector recommendations found in the AI response")
        return recommendations
    
    # Group tickers by trade direction
    long_tickers = []
    short_tickers = []
    
    for sector in recommendations['sector_recommendations']:
        ticker = sector.get('ticker')
        direction = sector.get('trade_direction', '').upper()
        
        if ticker and direction:
            if direction == 'LONG':
                long_tickers.append(ticker)
            elif direction == 'SHORT':
                short_tickers.append(ticker)
    
    # Calculate stop loss prices for LONG positions
    if long_tickers:
        long_stop_losses = calculate_stop_loss_price(long_tickers, 'LONG')
        
        # Add stop loss prices to recommendations
        for sector in recommendations['sector_recommendations']:
            if sector.get('trade_direction', '').upper() == 'LONG':
                ticker = sector.get('ticker')
                if ticker in long_stop_losses:
                    sector['stop_loss'] = round(long_stop_losses[ticker], 2)
    
    # Calculate stop loss prices for SHORT positions
    if short_tickers:
        short_stop_losses = calculate_stop_loss_price(short_tickers, 'SHORT')
        
        # Add stop loss prices to recommendations
        for sector in recommendations['sector_recommendations']:
            if sector.get('trade_direction', '').upper() == 'SHORT':
                ticker = sector.get('ticker')
                if ticker in short_stop_losses:
                    sector['stop_loss'] = round(short_stop_losses[ticker], 2)
    
    return recommendations

