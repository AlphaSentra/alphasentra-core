"""
Project:     Alphagora
File:        main.py
Author:      Daiviet Huynh
Created:     2025-08-10
License:     MIT License
Repository:  https://github.com/Alphagora-Edge/Alphagora

Description:
Main entry point for the Alphagora, allowing users to select model.
"""

from menu import MENU_ITEMS
from _config import LANGUAGE


def print_menu():
    print("\n" + "=" * 100)
    print("Alphagora - Main Menu - " + LANGUAGE.upper())
    print("=" * 100)
    print("Select from the menu below, the model you want to run:\n")

    # Create a list of selectable items (skip separators with None function)
    selectable_items = []
    menu_mapping = {}  # Maps displayed number to MENU_ITEMS index
    
    displayed_number = 1
    for i, (desc, action) in enumerate(MENU_ITEMS):
        if action is not None:  # This is a selectable item
            print(f"{displayed_number}. {desc}")
            menu_mapping[displayed_number] = i
            displayed_number += 1
        else:  # This is a separator
            print(f"   {desc}")
    
    print(f"{displayed_number}. Exit")
    return menu_mapping, displayed_number


def main():
    while True:
        menu_mapping, exit_number = print_menu()
        try:
            choice = int(input("\nEnter your choice: "))

            if 1 <= choice < exit_number:
                # Get the actual MENU_ITEMS index from the mapping
                actual_index = menu_mapping[choice]
                _, action = MENU_ITEMS[actual_index]
                action()
            elif choice == exit_number:
                print("\nExiting Alphagora. Goodbye!")
                break
            else:
                print("\nInvalid choice. Please select a valid option.")
        except ValueError:
            print("\nInvalid input. Please enter an integer.")
        except KeyboardInterrupt:
            print("\n\nExiting Alphagora. Goodbye!")
            break


if __name__ == "__main__":
    main()
