"""
Project:     Alphagora Trading System
File:        momentum.py
Author:      Daiviet Huynh
Created:     2025-07-22
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
ETF sector rotation, momentum trading engine.
"""

from datetime import datetime, timedelta
import yfinance as yf
import numpy as np
import pandas as pd  # Required for robust Series/DataFrame handling
from _config import MOMENTUM_ETFS, MOMENTUM_ALLOCATION_MIN, MOMENTUM_ALLOCATION_MAX


# --- MOMENTUM ENGINE ---

def get_momentum_recommendations(bull_bear_score):
    """
    Calculates and prints recommendations for the momentum sleeve of the portfolio.
    """
    print("\n--- Momentum Engine (50% - 75% Allocation) ---\n")
    print(f"Comparing the following {len(MOMENTUM_ETFS)} sector ETFs: {', '.join(MOMENTUM_ETFS)}")
    print("Strategy: Monthly rotation of top 3 sectors based on 12-1 month momentum.")

    # Validate bull_bear_score
    if not 1 <= bull_bear_score <= 10:
        print("Error: Bull/Bear score must be between 1 and 10.")
        return

    # Calculate allocation based on the score
    momentum_allocation = MOMENTUM_ALLOCATION_MIN + (bull_bear_score - 1) * (MOMENTUM_ALLOCATION_MAX - MOMENTUM_ALLOCATION_MIN) / 9
    print(f"Bull/Bear Score: {bull_bear_score}/10 -> Momentum Allocation: {momentum_allocation:.2%}")
    print("\n" + "")
    
    try:
        end_date = datetime.today()

        # --- MARKET FILTER: Check if SPY is trading above 200-day moving average ---
        spy_data = yf.download("SPY", start=end_date - timedelta(days=300), end=end_date, interval='1d', progress=False, auto_adjust=True)
        if spy_data.empty or 'Close' not in spy_data:
            print("Could not retrieve SPY data for market trend check.")
            return

        spy_close = spy_data['Close']

        # Ensure spy_close is a Series
        if isinstance(spy_close, pd.DataFrame):
            spy_close = spy_close.iloc[:, 0]

        spy_200dma_series = spy_close.rolling(window=200).mean()

        # Drop NaNs and get latest values
        spy_close_clean = spy_close.dropna()
        spy_200dma_clean = spy_200dma_series.dropna()

        if spy_close_clean.empty or spy_200dma_clean.empty:
            print("Insufficient SPY data to compute 200-day moving average.")
            return

        spy_latest = spy_close_clean.iloc[-1]
        spy_200dma_latest = spy_200dma_clean.iloc[-1]

        if spy_latest < spy_200dma_latest:
            print("\n")
            print("="*100)
            print("--- MOMENTUM TRADE INSTRUCTION: Market Trend Filter Triggered ---")
            print("="*100)
            print("SPY is trading below its 200-day moving average.")
            print("No sector ETF trades should be entered. Consider exiting existing positions.\n")
            return

        # Fetch ~16 months of monthly data
        start_date = end_date - timedelta(days=480)

        full_data = yf.download(MOMENTUM_ETFS, start=start_date, end=end_date, interval='1mo', progress=True, auto_adjust=True)

        if full_data.empty:
            print("Could not download momentum data. Please check tickers and network connection.")
            return

        data = full_data['Close']

        if data.empty:
            print("Could not extract price data. Please check tickers and network connection.")
            return

        # Calculate 12-1 month momentum
        momentum = (data.shift(1) / data.shift(13)) - 1

        # Get the latest momentum scores
        latest_momentum = momentum.iloc[-1].dropna()

        if len(latest_momentum) < 3 and len(momentum) > 1:
            print("Last row has insufficient data, attempting to use second to last row.")
            latest_momentum = momentum.iloc[-2].dropna()

        if len(latest_momentum) < 3:
            print("Error: Not enough data to rank ETFs for momentum even after fallback.")
            print("This can happen if the script is run over a weekend or at the very start of a month.")
            return

        # Sort all ETFs by momentum score
        all_ranked_etfs = latest_momentum.sort_values(ascending=False)

        print("\nFull Ranking of Sector ETFs by Momentum Score (for comparison):")
        print("\n" + all_ranked_etfs.to_string())

        # Select top 3
        top_3_etfs = all_ranked_etfs.head(3)

        # Generate trade instructions
        print("\n")
        print("="*100)
        print("--- MOMENTUM TRADE INSTRUCTIONS ---")
        print("="*100)
        print(f"1. Adjust total allocation to the momentum sleeve to {momentum_allocation:.2%}.")
        print("2. Sell any currently held sector ETFs that are NOT in the list below.")
        print("3. Buy the following Top 3 ETFs in equal weights:")
        print("\n")
        for etf, score in top_3_etfs.items():
            weight_per_etf = momentum_allocation / 3
            print(f"   - {etf}: Allocate {weight_per_etf:.2%} of the total portfolio. (Momentum Score: {score:.4f})")

    except Exception as e:
        print(f"An error occurred in the momentum engine: {e}")

    print("\n" + "="*100)

# --- END OF MOMENTUM ENGINE ---
