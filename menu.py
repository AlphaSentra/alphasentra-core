"""
Description:
Define menu items and their corresponding actions for the main menu.
"""

import models.sector_rotation_long_short as sector_rotation_long_short
import models.regional_rotation_long_short as regional_rotation_long_short
import models.fx_long_short as fx_long_short
import models.holistic as holistic
import db.create_mongodb_db as create_mongodb_db

def run_fx_model_with_input():
    """
    Run FX model with user-provided tickers and regions.
    """
    print("\n=== FX Long/Short Model Input ===")
    
    # Get ticker input
    ticker_input = input("Enter FX ticker(s) (comma-separated, e.g., EURUSD=X, GBPUSD=X, Dollar Index: DX=F): ").strip()
    tickers = [t.strip() for t in ticker_input.split(',')] if ticker_input else []
    
    # Get region input
    region_input = input("Enter region(s) to analyze (comma-separated, e.g., US, Eurozone): ").strip()
    regions = [r.strip() for r in region_input.split(',')] if region_input else []
    
    if tickers:
        fx_long_short.run_fx_model(tickers, regions)
    else:
        print("No tickers provided. Please enter at least one FX ticker.")

def run_holistic_model_with_input():
    """
    Run holistic market model with user-provided tickers.
    """
    print("\n=== Holistic Market Model Input ===")
    
    # Get ticker input
    ticker_input = input("Enter ticker(s) (comma-separated, e.g., SPY, QQQ, IWM): ").strip()
    tickers = [t.strip() for t in ticker_input.split(',')] if ticker_input else []
    
    if tickers:
        # Convert list of tickers to comma-separated string for the holistic model
        tickers_str = ','.join(tickers)
        holistic.run_holistic_market_model(tickers_str)
    else:
        print("No tickers provided. Please enter at least one ticker.")


# Define menu items as tuples: (description, function)
# Use None as function for separator items
MENU_ITEMS = [
    # Equity category
    ("----- EQUITIES -----", None),
    ("", None),
    
    ("EQ: U.S. Sector Rotation Model",
     lambda: sector_rotation_long_short.run_sector_rotation_model()),

    ("EQ: EMs vs. DMs - Regional Rotation Model",
     lambda: regional_rotation_long_short.run_regional_rotation_model()),

    # Currency/FX category
    ("", None),
    ("----- CURRENCIES -----", None),
    ("", None),

    ("FX: Forex Model",
     run_fx_model_with_input),

    # Others
    ("", None),
    ("----- OTHERS -----", None),
    ("", None),
    
    ("Holistic Market Model",
     run_holistic_model_with_input),
    
    # Configuration
    ("", None),
    ("----- CONFIG -----", None),
    ("", None),

    ("Configure database connection settings",
     create_mongodb_db.create_alphagora_database)

]

