"""
Project:     Alphagora Trading System
File:        main.py
Author:      Daiviet Huynh
Created:     2025-08-10
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Main entry point for the Alphagora system, allowing users to select between the portfolio or trading system.
"""

import portfolio_system
import trading_system


def main():
    """
    Main menu function to select which trading system to run.
    """
    while True:
        print("="*100)
        print("Alphagora Portfolio & Trading System - Main Menu")
        print("="*100)
        print("1. Run Portfolio System")
        print("2. Run Trading System")
        print("3. Exit")
        
        try:
            choice = int(input("\nEnter your choice (1-3): "))
            
            if choice == 1:
                portfolio_system.main()
            elif choice == 2:
                trading_system.main()
            elif choice == 3:
                print("\nExiting Alphagora Trading System. Goodbye!")
                break
            else:
                print("\nInvalid choice. Please enter a number between 1 and 3.")
                
        except ValueError:
            print("\nInvalid input. Please enter an integer.")
        except KeyboardInterrupt:
            print("\n\nExiting Alphagora Trading System. Goodbye!")
            break


if __name__ == "__main__":
    main()