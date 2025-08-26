"""
Project:     Alphagora Trading System
File:        momentum.py
Author:      Daiviet Huynh
Created:     2025-08-26
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Store all the variables for configuration for all the models and systems.
"""

# Momentum Engine Configuration
MOMENTUM_ETFS = ['XLC', 'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU']
MOMENTUM_ALLOCATION_MIN = 0.50  # 50%
MOMENTUM_ALLOCATION_MAX = 0.75  # 75%

# Mean Reversion Engine Configuration
PAIRS = {
    'VXX_vs_SVXY': ('VXX', 'SVXY'),
}
PAIRS_LOOKBACK_YEARS = 1
ENABLE_COINTEGRATION_TEST = False  # Set to False to skip cointegration check