"""
Project:     Alphagora Trading System
File:        portfolio_system.py
Author:      Daiviet Huynh
Created:     2025-07-22
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Main entry point for the Alphagora "all-weather" portfolio system, combining ETF regional and sector rotation
and mean-reversion gold and volatility strategies to achieve asymmetrical returns.
"""

import momentum as momentum
import mean_rev as mean_rev
from datetime import datetime


# --- MAIN EXECUTION ---

def main():
    """
    Main function to run the Alphagora "all-weather" portfolio system.
    """
    print("="*100)
    print("Alphagora Trading System - Daily Trade Execution Instructions")
    print(f"Date: {datetime.today().strftime('%Y-%m-%d')}")
    print("="*100)
    
    # --- Part 1: Momentum Engine ---
    try:
        bull_bear_score = int(input("\nEnter the Bull/Bear Score (1-10, where 10 is most bullish): "))
        momentum.get_momentum_recommendations(bull_bear_score)

    except ValueError:
        print("Invalid input. Please enter an integer between 1 and 10.")
        return

    # --- Part 2: Mean-Reversion Engine ---
    mean_rev.mean_reversion_engine()

if __name__ == "__main__":
    main()