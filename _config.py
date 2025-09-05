"""
Project:     Alphagora Trading System
File:        _config.py
Author:      Daiviet Huynh
Created:     2025-08-26
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Store all the variables for configuration for all the models and systems.
"""

# Sector Rotation Model Configuration
SECTOR_ETFS = ['XLC', 'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU']
MOMENTUM_ALLOCATION_MIN = 0.50  # 50%
MOMENTUM_ALLOCATION_MAX = 0.75  # 75%


# Weight configuration for AI model scoring
WEIGHTS = {
    'Geopolitical': 0.30,        # 30%
    'Macroeconomics': 0.20,      # 20%
    'Technical_Sentiment': 0.20, # 20%
    'Liquidity': 0.10,           # 10%
    'Earnings': 0.10,            # 10%
    'Business_Cycle': 0.05,      # 5%
    'Sentiment_Surveys': 0.05    # 5%
}

# Convert to percentage strings for display
WEIGHTS_PERCENT = {
    'Geopolitical': '30%',
    'Macroeconomics': '20%',
    'Technical_Sentiment': '20%',
    'Liquidity': '10%',
    'Earnings': '10%',
    'Business_Cycle': '5%',
    'Sentiment_Surveys': '5%'
}
