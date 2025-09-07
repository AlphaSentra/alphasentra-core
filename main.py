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
        print("3. FX Long/Short Model")
        print("4. Exit")
        
        try:
            choice = int(input("\nEnter your choice (1-4): "))
            
            if choice == 1:
                sector_rotation_long_short.run_sector_rotation_model()
            if choice == 2:
                regional_rotation_long_short.run_regional_rotation_model()
            if choice == 3:
                fx_long_short.run_fx_model()
            elif choice == 4:
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