"""
Project:     Alphagora Trading System
File:        trading_system.py
Author:      Daiviet Huynh
Created:     2025-08-10
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Main entry point for the Alphagora trading system.
"""

import models.momentum as momentum
from datetime import datetime


# --- MAIN EXECUTION ---

def main():
    """
    Main function to run the Alphagora trading system.
    """
    print("="*100)
    print("Alphagora Trading System - Strategy Execution")
    print(f"Date: {datetime.today().strftime('%Y-%m-%d')}")
    print("="*100)
    
    # Example trading system functionality
    print("\nSelect a trading strategy:")
    print("1. Momentum Trading")
    print("2. Mean Reversion Trading")
    print("3. Exit")
    
    try:
        choice = int(input("\nEnter your choice (1-3): "))
        
        if choice == 1:
            print("\nExecuting Momentum Trading Strategy...")
            momentum_score = int(input("Enter momentum score (1-10): "))
            momentum.get_momentum_recommendations(momentum_score)
        elif choice == 2:
            print("Exiting system.")
            return
        else:
            print("Invalid choice. Please enter a number between 1 and 3.")
            
    except ValueError:
        print("Invalid input. Please enter an integer.")
        return

if __name__ == "__main__":
    main()