"""
Project:     AlphaSentra
File:        main.py
Author:      Daiviet Huynh
Created:     2025-08-10
License:     MIT License
Repository:  https://github.com/AlphaSentra

Description:
Main entry point for the AlphaSentra, allowing users to select model.
"""

import argparse
from menu import MENU_ITEMS
from _config import LANGUAGE
from batch.batch_run import run_batch_processing
from batch.reset_dataset import reset_all
from batch.db_quota import enforce_db_size_limit


def print_menu():
    print("\n" + "=" * 100)
    print("AlphaSentra - Main Menu - " + LANGUAGE.upper())
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
                print("\nExiting AlphaSentra. Goodbye!")
                break
            else:
                print("\nInvalid choice. Please select a valid option.")
        except ValueError:
            print("\nInvalid input. Please enter an integer.")
        except KeyboardInterrupt:
            print("\n\nExiting AlphaSentra. Goodbye!")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-batch", action="store_true",
                        help="Run batch processing directly")
    parser.add_argument("-reset", action="store_true",
                        help="Reset all datasets")
    parser.add_argument("-dblimit", nargs='?', const=True, type=int,
                        help="Enforce database size limit (optional MB value)")

    args = parser.parse_args()
    
    if args.batch:
        run_batch_processing()
    elif args.reset:
        reset_all()
    elif args.dblimit:
        enforce_db_size_limit()
    else:
        main()
