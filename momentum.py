"""
Project:     Alphagora Trading System
File:        momentum.py
Author:      Daiviet Huynh
Created:     2025-07-22
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Momentum trading engine configuration for Alphagora.
"""
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np


# --- CONFIGURATION ---

# 1. Momentum Engine Configuration
MOMENTUM_ETFS = ['XLC', 'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU']
MOMENTUM_ALLOCATION_MIN = 0.50  # 50%
MOMENTUM_ALLOCATION_MAX = 0.75  # 75%


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

    try:
        # Fetch ~16 months of monthly data to ensure we have at least 14 data points for the calculation.
        end_date = datetime.today()
        # Increased lookback period to 480 days to ensure enough data points are fetched.
        start_date = end_date - timedelta(days=480) 
        
        # Download monthly historical data. auto_adjust=True is the new yfinance default.
        # It provides adjusted prices in the 'Close' column and removes 'Adj Close'.
        full_data = yf.download(MOMENTUM_ETFS, start=start_date, end=end_date, interval='1mo', progress=True, auto_adjust=True)
        
        if full_data.empty:
            print("Could not download momentum data. Please check tickers and network connection.")
            return

        # Use the 'Close' column which is auto-adjusted by yfinance
        data = full_data['Close']
        
        if data.empty:
            print("Could not extract price data. Please check tickers and network connection.")
            return

        # Calculate 12-1 month momentum
        # Formula: (Price 1 month ago / Price 13 months ago) - 1. 
        momentum = (data.shift(1) / data.shift(13)) - 1
        
        # Get the latest momentum scores
        latest_momentum = momentum.iloc[-1].dropna()

        # Fallback for start-of-month scenarios where the last row might be incomplete
        if len(latest_momentum) < 3 and len(momentum) > 1:
            print("Last row has insufficient data, attempting to use second to last row.")
            latest_momentum = momentum.iloc[-2].dropna()
        
        if len(latest_momentum) < 3:
            print("Error: Not enough data to rank ETFs for momentum even after fallback.")
            print("This can happen if the script is run over a weekend or at the very start of a month.")
            return

        # Sort all ETFs by momentum score to show the full comparison
        all_ranked_etfs = latest_momentum.sort_values(ascending=False)
        
        print("\nFull Ranking of Sector ETFs by Momentum Score (for comparison):")
        print(all_ranked_etfs.to_string())

        # Select top 3
        top_3_etfs = all_ranked_etfs.head(3)

        # Generate trade instructions
        print("\n--- MOMENTUM TRADE INSTRUCTIONS ---")
        print(f"1. Adjust total allocation to the momentum sleeve to {momentum_allocation:.2%}.")
        print("2. Sell any currently held sector ETFs that are NOT in the list below.")
        print("3. Buy the following Top 3 ETFs in equal weights:")
        for etf, score in top_3_etfs.items():
            weight_per_etf = momentum_allocation / 3
            print(f"   - {etf}: Allocate {weight_per_etf:.2%} of the total portfolio. (Momentum Score: {score:.4f})")

    except Exception as e:
        print(f"An error occurred in the momentum engine: {e}")

# --- END OF MOMENTUM ENGINE ---
