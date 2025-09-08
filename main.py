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


# Define menu items as tuples: (description, function)
MENU_ITEMS = [
    ("EQ: Sector Rotation Long/Short Model", 
     lambda: sector_rotation_long_short.run_sector_rotation_model()),

    ("EQ: Regional Rotation Long/Short Model", 
     lambda: regional_rotation_long_short.run_regional_rotation_model()),

    ("FX: Long/Short Model: US Dollar Index (DXY)", 
     lambda: fx_long_short.run_fx_model(['DX=F'], ['US'])),

    ("FX: Long/Short Model: EUR/USD", 
     lambda: fx_long_short.run_fx_model(['EURUSD=X'], ['US', 'Eurozone'])),

    ("FX: Long/Short Model: GBP/USD", 
     lambda: fx_long_short.run_fx_model(['GBPUSD=X'], ['UK', 'US'])),

    ("FX: Long/Short Model: USD/JPY", 
     lambda: fx_long_short.run_fx_model(['USDJPY=X'], ['US', 'JPY'])),

    ("FX: Long/Short Model: AUD/USD", 
     lambda: fx_long_short.run_fx_model(['AUDUSD=X'], ['Australia', 'US'])),

    ("FX: Long/Short Model: USD/CHF", 
     lambda: fx_long_short.run_fx_model(['USDCHF=X'], ['Switzerland', 'US'])),

    ("FX: Long/Short Model: USD/CAD", 
     lambda: fx_long_short.run_fx_model(['USDCAD=X'], ['US', 'Canada'])),

    ("FX: Long/Short Model: NZD/USD", 
     lambda: fx_long_short.run_fx_model(['NZDUSD=X'], ['New Zealand', 'US']))
]


def print_menu():
    print("\n" + "=" * 100)
    print("Alphagora System - Main Menu")
    print("=" * 100)
    print("Select from the menu below, the model you want to run:\n")

    for i, (desc, _) in enumerate(MENU_ITEMS, start=1):
        print(f"{i}. {desc}")
    print(f"{len(MENU_ITEMS) + 1}. Exit")


def main():
    while True:
        print_menu()
        try:
            choice = int(input("\nEnter your choice: "))

            if 1 <= choice <= len(MENU_ITEMS):
                _, action = MENU_ITEMS[choice - 1]
                action()
            elif choice == len(MENU_ITEMS) + 1:
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