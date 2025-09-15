"""
Description:
Define menu items and their corresponding actions for the main menu.
"""

import models.sector_rotation_long_short as sector_rotation_long_short
import models.regional_rotation_long_short as regional_rotation_long_short
import models.fx_long_short as fx_long_short

# Define menu items as tuples: (description, function)
MENU_ITEMS = [
    ("EQ: Sector Rotation Long/Short Model",
     lambda: sector_rotation_long_short.run_sector_rotation_model()),

    ("EQ: Regional Rotation Long/Short Model",
     lambda: regional_rotation_long_short.run_regional_rotation_model()),

    ("FX: Long/Short Model: US Dollar Index (DXY)",
     lambda: fx_long_short.run_fx_model(['DX=F'], ['US'])),

    ("FX: Long/Short Model: EUR/USD",
     lambda: fx_long_short.run_fx_model(['EURUSD=X'], ['US', 'Eurozone'])),

    ("FX: Long/Short Model: GBP/USD",
     lambda: fx_long_short.run_fx_model(['GBPUSD=X'], ['UK', 'US'])),

    ("FX: Long/Short Model: USD/JPY",
     lambda: fx_long_short.run_fx_model(['USDJPY=X'], ['US', 'JPY'])),

    ("FX: Long/Short Model: AUD/USD",
     lambda: fx_long_short.run_fx_model(['AUDUSD=X'], ['Australia', 'US'])),

    ("FX: Long/Short Model: USD/CHF",
     lambda: fx_long_short.run_fx_model(['USDCHF=X'], ['Switzerland', 'US'])),

    ("FX: Long/Short Model: USD/CAD",
     lambda: fx_long_short.run_fx_model(['USDCAD=X'], ['US', 'Canada'])),

    ("FX: Long/Short Model: NZD/USD",
     lambda: fx_long_short.run_fx_model(['NZDUSD=X'], ['New Zealand', 'US']))
]
