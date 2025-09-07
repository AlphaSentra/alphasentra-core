"""
Project:     Alphagora Trading System
File:        main.py
Author:      Daiviet Huynh
Created:     2025-08-10
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Main entry point for the Alphagora system, allowing users to select model.
"""

import models.sector_rotation_long_short as sector_rotation_long_short
import models.regional_rotation_long_short as regional_rotation_long_short
import models.fx_long_short as fx_long_short


def main():
    """
    Main menu function to select which trading system to run.
    """
    while True:
        print()
        print("="*100)
        print("Alphagora System - Main Menu")
        print("="*100)
        print("Select from the menu below, the model you want to run:")
        print()
        print("1. Sector Rotation Long/Short Model")
        print("2. Regional Rotation Long/Short Model")
        print("3. FX Long/Short Model: US Dollar Index (DXY)")
        print("4. FX Long/Short Model: EUR/USD")
        print("5. FX Long/Short Model: GBP/USD")
        print("6. FX Long/Short Model: USD/JPY")
        print("7. FX Long/Short Model: AUD/USD")
        print("8. FX Long/Short Model: USD/CHF")
        print("9. FX Long/Short Model: USD/CAD")
        print("10. FX Long/Short Model: NZD/USD")
        print("11. Exit")
        
        try:
            choice = int(input("\nEnter your choice (1-11): "))
            
            if choice == 1:
                sector_rotation_long_short.run_sector_rotation_model()
            elif choice == 2:
                regional_rotation_long_short.run_regional_rotation_model()
            elif choice == 3:
                fx_long_short.run_fx_model(tickers=['DX=F'], fx_regions=['US'])
            elif choice == 4:
                fx_long_short.run_fx_model(tickers=['EURUSD=X'], fx_regions=['US', 'Eurozone'])
            elif choice == 5:
                fx_long_short.run_fx_model(tickers=['GBPUSD=X'], fx_regions=['UK', 'US'])
            elif choice == 6:
                fx_long_short.run_fx_model(tickers=['USDJPY=X'], fx_regions=['US', 'JPY'])
            elif choice == 7:
                fx_long_short.run_fx_model(tickers=['AUDUSD=X'], fx_regions=['Australia', 'US'])
            elif choice == 8:
                fx_long_short.run_fx_model(tickers=['USDCHF=X'], fx_regions=['Switzerland', 'US'])
            elif choice == 9:
                fx_long_short.run_fx_model(tickers=['USDCAD=X'], fx_regions=['US', 'Canada'])
            elif choice == 10:
                fx_long_short.run_fx_model(tickers=['NZDUSD=X'], fx_regions=['New Zealand', 'US'])
            elif choice == 11:
                print("\nExiting Alphagora System. Goodbye!")
                break
            else:
                print("\nInvalid choice. Please select a valid option.")
                
        except ValueError:
            print("\nInvalid input. Please enter an integer.")
        except KeyboardInterrupt:
            print("\n\nExiting Alphagora System. Goodbye!")
            break


if __name__ == "__main__":
    main()