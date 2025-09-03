"""
Project:     Alphagora Trading System
File:        test_import.py
Author:      Daiviet Huynh
Created:     2025-09-03
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Test importing configuration variables from config.py.
"""
import os
import sys

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Test importing from config
try:
    from config import WEIGHTS, WEIGHTS_PERCENT
    print("Import successful!")
    print("WEIGHTS:", WEIGHTS)
    print("WEIGHTS_PERCENT:", WEIGHTS_PERCENT)
except Exception as e:
    print("Import failed:", e)