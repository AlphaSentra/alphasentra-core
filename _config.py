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

# Default factor weights used if AI model is not calculating weights
# These weights are overridden if AI model successfully returns weights
WEIGHTS_PERCENT = {
    'Geopolitical': '30%',
    'Macroeconomics': '20%',
    'Technical_Sentiment': '20%',
    'Liquidity': '10%',
    'Earnings': '10%',
    'Business_Cycle': '5%',
    'Sentiment_Surveys': '5%'
}

# Sector Rotation Model Configuration
SECTOR_ETFS = ['XLC', 'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU']
SECTOR_REGIONS = ['US']

# Regional Rotation Model Configuration
REGIONAL_ETFS = ['EEM', 'EFA', 'SPY']
REGIONAL_REGIONS = ['Emerging Markets','China','Taiwan','India','South Korea','Brazil','Japan','UK','France','Germany','Switzerland','Australia', 'US']

# FX Long/Short Model Configuration
FX_PAIRS = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'USDCHF=X', 'AUDUSD=X', 'USDCAD=X']

