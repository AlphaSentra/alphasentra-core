"""
Project:     Alphagora Trading System
File:        _config.py
Author:      Daiviet Huynh
Created:     2025-08-26
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Store all the variables for configuration for all the models and systems.
Tickers must be in Yahoo Finance format.
"""

# Sector Rotation Model Configuration
SECTOR_ETFS = ['XLC', 'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU']
REGIONS = ['US']

# Regional Rotation Model Configuration
REGIONAL_ETFS = ['EEM', 'VWO', 'IEMG', 'IEFA', 'VEA', 'VNQ', 'VTI', 'SPY', 'QQQ', 'DIA']


# Default weights for various factors in percentage format
WEIGHTS_PERCENT = {
    'Geopolitical': '30%',
    'Macroeconomics': '20%',
    'Technical_Sentiment': '20%',
    'Liquidity': '10%',
    'Earnings': '10%',
    'Business_Cycle': '5%',
    'Sentiment_Surveys': '5%'
}
