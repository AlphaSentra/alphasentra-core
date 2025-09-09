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

from menu import MENU_ITEMS


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