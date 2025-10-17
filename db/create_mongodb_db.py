"""
Description:
Script to create MongoDB database 'alphagora'.
"""

import pymongo
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from helpers import DatabaseManager

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from logging_utils import log_error, log_warning

def create_collection_with_schema(db, collection_name, validator, indexes=None):
    """
    Creates a MongoDB collection with schema validation and indexes.
    
    Args:
        db: MongoDB database object
        collection_name: Name of the collection to create
        validator: JSON schema validator for the collection
        indexes: List of index specifications (optional)
        
    Returns:
        bool: True if collection was created or already exists, False on error
    """
    try:
        # Check if collection already exists
        if collection_name in db.list_collection_names():
            print(f"Collection '{collection_name}' already exists. Skipping creation.")
            return True
        
        # Create collection with validation
        db.create_collection(
            collection_name,
            validator=validator
        )
        
        # Create indexes if provided
        if indexes:
            collection = db[collection_name]
            for index_spec in indexes:
                collection.create_index(index_spec)
        
        print(f"Successfully created collection '{collection_name}'")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error(f"MongoDB operation failed for collection '{collection_name}'", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error(f"Unexpected error creating collection '{collection_name}'", "COLLECTION_CREATION", e)
        return False


def create_insights_collection(db):
    """
    Creates the 'insights' collection with schema validation and indexes.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if collection was created or already exists, False on error
    """
    collection_name = 'insights'
    
    print()
    print("=" * 100)
    print(f"Creating '{collection_name}' collection...")
    print("=" * 100)
    print()

    # Create collection with schema validation
    validator = {
    '$jsonSchema': {
        'bsonType': 'object',
        'required': [
            'title',
            'market_outlook_narrative',
            'rationale',
            'analysis',
            'recommendations',
            'sentiment_score',
            'market_impact',
            'timestamp_gmt',
            'language_code'
        ],
        'properties': {
            'title': {
                'bsonType': 'string'
            },
            'market_outlook_narrative': {
                'bsonType': 'array',
                'items': {
                    'bsonType': 'string'
                }
            },
            'rationale': {
                'bsonType': 'string'
            },
            'analysis': {
                'bsonType': 'string'
            },
            'key_takeaways': {},
            'sources': {
                'bsonType': 'array',
                'items': {
                    'bsonType': 'object',
                    'required': ['source_name', 'source_title'],
                    'properties': {
                        'source_name': {
                            'bsonType': 'string'
                        },
                        'source_title': {
                            'bsonType': 'string'
                        }
                    }
                }
            },
            'recommendations': {
                'bsonType': 'array',
                'items': {
                    'bsonType': 'object',
                    'required': [
                        'ticker',
                        'trade_direction',
                        'bull_bear_score',
                        'stop_loss',
                        'target_price',
                        'entry_price',
                        'price'
                    ],
                    'properties': {
                        'ticker': {
                            'bsonType': 'string'
                        },
                        'trade_direction': {
                            'bsonType': 'string'
                        },
                        'bull_bear_score': {
                            'bsonType': 'int',
                            'minimum': 1,
                            'maximum': 10
                        },
                        'stop_loss': {
                            'bsonType': 'double'
                        },
                        'target_price': {
                            'bsonType': 'double'
                        },
                        'entry_price': {
                            'bsonType': 'double'
                        },
                        'price': {
                            'bsonType': 'double'
                        }
                    }
                }
            },
            'sentiment_score': {
                'bsonType': 'double',
                'minimum': 0,
                'maximum': 1.0
            },
            'market_impact': {
                'bsonType': 'int',
                'minimum': 1,
                'maximum': 10
            },
            'factors':{},
            'timestamp_gmt': {
                'bsonType': 'string',
                'pattern': '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d+)?Z$'
            },
            'language_code': {
                'bsonType': 'string',
                'pattern': '^[a-z]{2}(-[A-Z]{2})?$'
            },
            'importance': {
                'bsonType': 'int',
                'minimum': 1,
                'maximum': 5
            },
            'asset_class': {},
            'region': {},
            'tag': {
                'bsonType': 'string'
            }
        }
    }
    }
    
    # Define indexes for better query performance
    indexes = [
        [('timestamp_gmt', pymongo.DESCENDING)],
        [('sentiment_score', pymongo.DESCENDING)],
        [('language_code', pymongo.ASCENDING)],
        [('recommendations.ticker', pymongo.ASCENDING)]
    ]
    
    # Use the generic function to create the collection
    success = create_collection_with_schema(db, collection_name, validator, indexes)
    
    if success:
        print(f"Successfully created collection '{collection_name}'")
        print("Collection schema validation rules applied:")
        print("   - Required fields: title, market_outlook_narrative, rationale, analysis, recommendations, sentiment_score, market_impact, timestamp_gmt, language_code")
        print("   - Optional field: sources")
        print("   - Indexes created: timestamp_gmt, sentiment_score, language_code, recommendations.ticker")
    
    return success


def create_tickers_collection(db):
    """
    Creates the 'tickers' collection with schema validation and indexes.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if collection was created or already exists, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Creating '{collection_name}' collection...")
    print("=" * 100)
    print()

    # Create collection with schema validation
    validator = {
        '$jsonSchema': {
            'bsonType': 'object',
            'required': [
                'ticker',
                'name',
                'region',
                'prompt',
                'model_function'
            ],
            'properties': {
                'ticker': {
                    'bsonType': 'string',
                },
                'ticker_tradingview': {
                    'bsonType': 'string',
                },
                'name': {
                    'bsonType': 'string',
                },
                'region': {},
                'prompt': {
                    'bsonType': 'string',
                },
                'factor':{
                    'bsonType': 'string',
                },
                'model_function': {
                    'bsonType': 'string',
                },
                'model_name': {
                    'bsonType': 'string',
                },
                'asset_class': {},
                'importance': {
                    'bsonType': 'int',
                    'minimum': 1,
                    'maximum': 5,
                },
                'recurrence': {
                    'bsonType': 'string',
                    'enum': ['multi','once'],
                },
                'decimal': {
                    'bsonType': 'int',
                },
                'document_generated':{
                    'bsonType': 'bool',
                }                
            }
        }
    }
    
    # Define indexes for better query performance
    indexes = [
        [('ticker', pymongo.ASCENDING)],
        [('name', pymongo.ASCENDING)],
        [('region', pymongo.ASCENDING)]
    ]
    
    # Use the generic function to create the collection
    success = create_collection_with_schema(db, collection_name, validator, indexes)
    
    if success:
        print(f"Successfully created collection '{collection_name}'")
        print("Collection schema validation rules applied:")
        print("   - Required fields: ticker, name, region, prompt, model_function")
        print("   - Optional field: asset_class")
        print("   - Indexes created: ticker, name, region")
    
    return success


def insert_fx_pairs(db):
    """
    Inserts FX currency pairs into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Inserting FX pairs into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Import FX_LONG_SHORT_PROMPT from _config
    from _config import FX_LONG_SHORT_PROMPT, FX_FACTORS_PROMPT
    
    # FX pairs data to insert with prompt and model_function fields
    fx_pairs = [
        {"ticker": "AUDCAD=X", "ticker_tradingview": "FX_IDC:AUDCAD", "name": "Australian Dollar / Canadian Dollar", "region": ["Australia", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "AUDCHF=X", "ticker_tradingview": "FX_IDC:AUDCHF", "name": "Australian Dollar / Swiss Franc", "region": ["Australia", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "AUDJPY=X", "ticker_tradingview": "FX_IDC:AUDJPY", "name": "Australian Dollar / Japanese Yen", "region": ["Australia", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "AUDNZD=X", "ticker_tradingview": "FX_IDC:AUDNZD", "name": "Australian Dollar / New Zealand Dollar", "region": ["Australia", "New Zealand"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "AUDSGD=X", "ticker_tradingview": "FX_IDC:AUDSGD", "name": "Australian Dollar / Singapore Dollar", "region": ["Australia", "Singapore"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "AUDUSD=X", "ticker_tradingview": "FX_IDC:AUDUSD", "name": "Australian Dollar / U.S. Dollar", "region": ["Australia", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "CADCHF=X", "ticker_tradingview": "FX_IDC:CADCHF", "name": "Canadian Dollar / Swiss Franc", "region": ["Canada", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "CADJPY=X", "ticker_tradingview": "FX_IDC:CADJPY", "name": "Canadian Dollar / Japanese Yen", "region": ["Canada", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "CHFJPY=X", "ticker_tradingview": "FX_IDC:CHFJPY", "name": "Swiss Franc / Japanese Yen", "region": ["Switzerland", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURAUD=X", "ticker_tradingview": "FX_IDC:EURAUD", "name": "Euro / Australian Dollar", "region": ["Eurozone", "Australia"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURCAD=X", "ticker_tradingview": "FX_IDC:EURCAD", "name": "Euro / Canadian Dollar", "region": ["Eurozone", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURCHF=X", "ticker_tradingview": "FX_IDC:EURCHF", "name": "Euro / Swiss Franc", "region": ["Eurozone", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURGBP=X", "ticker_tradingview": "FX_IDC:EURGBP", "name": "Euro / Great British Pound", "region": ["Eurozone", "UK"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURHKD=X", "ticker_tradingview": "FX_IDC:EURHKD", "name": "Euro / Hong Kong Dollar", "region": ["Eurozone", "Hong Kong"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURHUF=X", "ticker_tradingview": "FX_IDC:EURHUF", "name": "Euro / Hungarian Forint", "region": ["Eurozone", "Hungary"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURJPY=X", "ticker_tradingview": "FX_IDC:EURJPY", "name": "Euro / Japanese Yen", "region": ["Eurozone", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURNOK=X", "ticker_tradingview": "FX_IDC:EURNOK", "name": "Euro / Norwegian Krone", "region": ["Eurozone", "Norway"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURNZD=X", "ticker_tradingview": "FX_IDC:EURNZD", "name": "Euro / New Zealand Dollar", "region": ["Eurozone", "New Zealand"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURSGD=X", "ticker_tradingview": "FX_IDC:EURSGD", "name": "Euro / Singapore Dollar", "region": ["Eurozone", "Singapore"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "EURUSD=X", "ticker_tradingview": "FX_IDC:EURUSD", "name": "Euro / U.S. Dollar", "region": ["Eurozone", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPAUD=X", "ticker_tradingview": "FX_IDC:GBPAUD", "name": "Great British Pound / Australian Dollar", "region": ["UK", "Australia"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPCAD=X", "ticker_tradingview": "FX_IDC:GBPCAD", "name": "Great British Pound / Canadian Dollar", "region": ["UK", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPCHF=X", "ticker_tradingview": "FX_IDC:GBPCHF", "name": "Great British Pound / Swiss Franc", "region": ["UK", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPJPY=X", "ticker_tradingview": "FX_IDC:GBPJPY", "name": "Great British Pound / Japanese Yen", "region": ["UK", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPNZD=X", "ticker_tradingview": "FX_IDC:GBPNZD", "name": "Great British Pound / New Zealand Dollar", "region": ["UK", "New Zealand"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPSGD=X", "ticker_tradingview": "FX_IDC:GBPSGD", "name": "Great British Pound / Singapore Dollar", "region": ["UK", "Singapore"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPUSD=X", "ticker_tradingview": "FX_IDC:GBPUSD", "name": "Great British Pound / U.S. Dollar", "region": ["UK", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "NZDCAD=X", "ticker_tradingview": "FX_IDC:NZDCAD", "name": "New Zealand Dollar / Canadian Dollar", "region": ["New Zealand", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "NZDCHF=X", "ticker_tradingview": "FX_IDC:NZDCHF", "name": "New Zealand Dollar / Swiss Franc", "region": ["New Zealand", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "NZDJPY=X", "ticker_tradingview": "FX_IDC:NZDJPY", "name": "New Zealand Dollar / Japanese Yen", "region": ["New Zealand", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "NZDSGD=X", "ticker_tradingview": "FX_IDC:NZDSGD", "name": "New Zealand Dollar / Singapore Dollar", "region": ["New Zealand", "Singapore"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "NZDUSD=X", "ticker_tradingview": "FX_IDC:NZDUSD", "name": "New Zealand Dollar / U.S. Dollar", "region": ["New Zealand", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "SGDJPY=X", "ticker_tradingview": "FX_IDC:SGDJPY", "name": "Singapore Dollar / Japanese Yen", "region": ["Singapore", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDCAD=X", "ticker_tradingview": "FX_IDC:USDCAD", "name": "U.S. Dollar / Canadian Dollar", "region": ["US", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDCHF=X", "ticker_tradingview": "FX_IDC:USDCHF", "name": "U.S. Dollar / Swiss Franc", "region": ["US", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDCNH=X", "ticker_tradingview": "FX_IDC:USDCNH", "name": "U.S. Dollar / Offshore Chinese Yuan", "region": ["US", "China"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDDKK=X", "ticker_tradingview": "FX_IDC:USDDKK", "name": "U.S. Dollar / Danish Krone", "region": ["US", "Denmark"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDHUF=X", "ticker_tradingview": "FX_IDC:USDHUF", "name": "U.S. Dollar / Hungarian Forint", "region": ["US", "Hungary"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDJPY=X", "ticker_tradingview": "FX_IDC:USDJPY", "name": "U.S. Dollar / Japanese Yen", "region": ["US", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDMXN=X", "ticker_tradingview": "FX_IDC:USDMXN", "name": "U.S. Dollar / Mexican Peso", "region": ["US", "Mexico"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDNOK=X", "ticker_tradingview": "FX_IDC:USDNOK", "name": "U.S. Dollar / Norwegian Krone", "region": ["US", "Norway"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDSGD=X", "ticker_tradingview": "FX_IDC:USDSGD", "name": "U.S. Dollar / Singapore Dollar", "region": ["US", "Singapore"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "document_generated": False}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any FX pairs already exist to avoid duplicates
        existing_count = collection.count_documents({"ticker": {"$in": [pair["ticker"] for pair in fx_pairs]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing FX pairs. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all FX pairs
        result = collection.insert_many(fx_pairs)
        print(f"Successfully inserted {len(result.inserted_ids)} FX pairs into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting FX pairs", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting FX pairs", "DATA_INSERTION", e)
        return False


def insert_indices(db):
    """
    Inserts stock indices into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Inserting indices into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Import IX_INDEX_LONG_SHORT_PROMPT from _config
    from _config import IX_INDEX_LONG_SHORT_PROMPT, IX_INDEX_FACTORS_PROMPT
    
    # Indices data to insert with prompt and model_function fields
    indices = [
        {"ticker": "^GSPC", "ticker_tradingview": "SPX500USD", "name": "US SPX 500 Index (S&P 500)", "region": ["US"], "prompt": "IX_INDEX_LONG_SHORT_PROMPT", "factors": "IX_INDEX_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "^IXIC", "ticker_tradingview": "NAS100USD", "name": "US Tech 100 Index (NASDAQ 100)", "region": ["US"], "prompt": "IX_INDEX_LONG_SHORT_PROMPT", "factors": "IX_INDEX_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^DJI", "ticker_tradingview": "US30USD", "name": "US Wall Street 30 Index (Dow Jones)", "region": ["US"], "prompt": "IX_INDEX_LONG_SHORT_PROMPT", "factors": "IX_INDEX_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^GDAXI", "ticker_tradingview": "GER30", "name": "Germany 30 Index (DAX)", "region": ["Germany"], "prompt": "IX_INDEX_LONG_SHORT_PROMPT", "factors": "IX_INDEX_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^FTSE", "ticker_tradingview": "UK100GBP", "name": "UK 100 Index (FTSE 100)", "region": ["UK"], "prompt": "IX_INDEX_LONG_SHORT_PROMPT", "factors": "IX_INDEX_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^N225", "ticker_tradingview": "JP225", "name": "Japan 225 Index (Nikkei)", "region": ["Japan"], "prompt": "IX_INDEX_LONG_SHORT_PROMPT", "factors": "IX_INDEX_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^HSI", "ticker_tradingview": "HK50", "name": "Hong Kong 50 Index (Hang Seng)", "region": ["Hong Kong"], "prompt": "IX_INDEX_LONG_SHORT_PROMPT", "factors": "IX_INDEX_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^RUT", "ticker_tradingview": "US2000USD", "name": "Russell 2000 Index", "region": ["US"], "prompt": "IX_INDEX_LONG_SHORT_PROMPT", "factors": "IX_INDEX_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^STOXX50E", "ticker_tradingview": "EUSTX50", "name": "Euro Stoxx 50 Index", "region": ["Eurozone"], "prompt": "IX_INDEX_LONG_SHORT_PROMPT", "factors": "IX_INDEX_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^FCHI", "ticker_tradingview": "FRA40", "name": "France 40 Index (CAC 40)", "region": ["France"], "prompt": "IX_INDEX_LONG_SHORT_PROMPT", "factors": "IX_INDEX_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^AXJO", "ticker_tradingview": "AUS200", "name": "Australia 200 Index (ASX 200)", "region": ["Australia"], "prompt": "IX_INDEX_LONG_SHORT_PROMPT", "factors": "IX_INDEX_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^SSMI", "ticker_tradingview": "SWI20", "name": "Switzerland 20 Index (SMI)", "region": ["Switzerland"], "prompt": "IX_INDEX_LONG_SHORT_PROMPT", "factors": "IX_INDEX_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^AEX", "ticker_tradingview": "NTH25", "name": "Netherlands 25 Cash Index (AEX)", "region": ["Netherlands"], "prompt": "IX_INDEX_LONG_SHORT_PROMPT", "factors": "IX_INDEX_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any indices already exist to avoid duplicates
        existing_count = collection.count_documents({"ticker": {"$in": [index["ticker"] for index in indices]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing indices. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all indices
        result = collection.insert_many(indices)
        print(f"Successfully inserted {len(result.inserted_ids)} indices into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting indices", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting indices", "DATA_INSERTION", e)
        return False


def insert_equities(db):
    """
    Inserts global equities into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Inserting equities into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Import EQ_EQUITIES_LONG_SHORT_PROMPT from _config
    from _config import EQ_EQUITIES_LONG_SHORT_PROMPT, EQ_EQUITIES_FACTORS_PROMPT
    
    # Equities data to insert with prompt and model_function fields
    equities = [
        {"ticker": "NVDA", "ticker_tradingview": "NASDAQ:NVDA", "name": "NVIDIA Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MSFT", "ticker_tradingview": "NASDAQ:MSFT", "name": "Microsoft Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AAPL", "ticker_tradingview": "NASDAQ:AAPL", "name": "Apple Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GOOGL", "ticker_tradingview": "NASDAQ:GOOGL", "name": "Alphabet Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GOOG", "ticker_tradingview": "NASDAQ:GOOG", "name": "Alphabet Inc. (Class C)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AMZN", "ticker_tradingview": "NASDAQ:AMZN", "name": "Amazon.com, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "META", "ticker_tradingview": "NASDAQ:META", "name": "Meta Platforms, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AVGO", "ticker_tradingview": "NASDAQ:AVGO", "name": "Broadcom Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TSLA", "ticker_tradingview": "NASDAQ:TSLA", "name": "Tesla, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BRK.B", "ticker_tradingview": "NYSE:BRK.B", "name": "Berkshire Hathaway Inc. (B)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "JPM", "ticker_tradingview": "NYSE:JPM", "name": "JPMorgan Chase & Co.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LLY", "ticker_tradingview": "NYSE:LLY", "name": "Eli Lilly and Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "V", "ticker_tradingview": "NYSE:V", "name": "Visa Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NFLX", "ticker_tradingview": "NASDAQ:NFLX", "name": "Netflix, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MA", "ticker_tradingview": "NYSE:MA", "name": "Mastercard Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ORCL", "ticker_tradingview": "NYSE:ORCL", "name": "Oracle Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WMT", "ticker_tradingview": "NYSE:WMT", "name": "Walmart Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "XOM", "ticker_tradingview": "NYSE:XOM", "name": "Exxon Mobil Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "JNJ", "ticker_tradingview": "NYSE:JNJ", "name": "Johnson & Johnson", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PLTR", "ticker_tradingview": "NYSE:PLTR", "name": "Palantir Technologies Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "COST", "ticker_tradingview": "NASDAQ:COST", "name": "Costco Wholesale Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ABBV", "ticker_tradingview": "NYSE:ABBV", "name": "AbbVie Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HD", "ticker_tradingview": "NYSE:HD", "name": "The Home Depot, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PG", "ticker_tradingview": "NYSE:PG", "name": "The Procter & Gamble Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BAC", "ticker_tradingview": "NYSE:BAC", "name": "Bank of America Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "UNH", "ticker_trading_view": "NYSE:UNH", "name": "UnitedHealth Group Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AMD", "ticker_tradingview": "NASDAQ:AMD", "name": "Advanced Micro Devices, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GE", "ticker_tradingview": "NYSE:GE", "name": "GE Aerospace", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CVX", "ticker_tradingview": "NYSE:CVX", "name": "Chevron Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "KO", "ticker_tradingview": "NYSE:KO", "name": "The Coca-Cola Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CSCO", "ticker_tradingview": "NASDAQ:CSCO", "name": "Cisco Systems, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WFC", "ticker_tradingview": "NYSE:WFC", "name": "Wells Fargo & Co.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "IBM", "ticker_tradingview": "NYSE:IBM", "name": "International Business Machines Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MS", "ticker_tradingview": "NYSE:MS", "name": "Morgan Stanley", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "T-MUS", "ticker_tradingview": "NASDAQ:TMUS", "name": "T-Mobile US, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CAT", "ticker_tradingview": "NYSE:CAT", "name": "Caterpillar Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PM", "ticker_tradingview": "NYSE:PM", "name": "Philip Morris International Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GS", "ticker_tradingview": "NYSE:GS", "name": "The Goldman Sachs Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CRM", "ticker_tradingview": "NYSE:CRM", "name": "Salesforce, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AXP", "ticker_tradingview": "NYSE:AXP", "name": "American Express Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MU", "ticker_tradingview": "NASDAQ:MU", "name": "Micron Technology, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ABT", "ticker_tradingview": "NYSE:ABT", "name": "Abbott Laboratories", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MCD", "ticker_tradingview": "NYSE:MCD", "name": "McDonald's Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "RTX", "ticker_tradingview": "NYSE:RTX", "name": "RTX Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MRK", "ticker_tradingview": "NYSE:MRK", "name": "Merck & Co., Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PEP", "ticker_tradingview": "NASDAQ:PEP", "name": "PepsiCo, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LIN", "ticker_tradingview": "NYSE:LIN", "name": "Linde plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TMO", "ticker_tradingview": "NYSE:TMO", "name": "Thermo Fisher Scientific Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DIS", "ticker_tradingview": "NYSE:DIS", "name": "The Walt Disney Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "UBER", "ticker_tradingview": "NYSE:UBER", "name": "Uber Technologies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "T", "ticker_tradingview": "NYSE:T", "name": "AT&T Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NOW", "ticker_tradingview": "NYSE:NOW", "name": "ServiceNow, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ANET", "ticker_tradingview": "NYSE:ANET", "name": "Arista Networks, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BLK", "ticker_tradingview": "NYSE:BLK", "name": "BlackRock, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AMAT", "ticker_tradingview": "NASDAQ:AMAT", "name": "Applied Materials, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "INTU", "ticker_tradingview": "NASDAQ:INTU", "name": "Intuit Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LRCX", "ticker_tradingview": "NASDAQ:LRCX", "name": "Lam Research Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "QCOM", "ticker_tradingview": "NASDAQ:QCOM", "name": "Qualcomm Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NEE", "ticker_tradingview": "NYSE:NEE", "name": "NextEra Energy, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "INTC", "ticker_tradingview": "NASDAQ:INTC", "name": "Intel Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "C", "ticker_tradingview": "NYSE:C", "name": "Citigroup Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "VZ", "ticker_tradingview": "NYSE:VZ", "name": "Verizon Communications Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SCHW", "ticker_tradingview": "NYSE:SCHW", "name": "The Charles Schwab Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GEV", "ticker_tradingview": "NYSE:GEV", "name": "GE Vernova Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TXN", "ticker_tradingview": "NASDAQ:TXN", "name": "Texas Instruments Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BKNG", "ticker_tradingview": "NASDAQ:BKNG", "name": "Booking Holdings Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BA", "ticker_tradingview": "NYSE:BA", "name": "The Boeing Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AMGN", "ticker_tradingview": "NASDAQ:AMGN", "name": "Amgen Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TJX", "ticker_tradingview": "NYSE:TJX", "name": "The TJX Companies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HON", "ticker_tradingview": "NASDAQ:HON", "name": "Honeywell International Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SPGI", "ticker_tradingview": "NYSE:SPGI", "name": "S&P Global Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "UNP", "ticker_tradingview": "NYSE:UNP", "name": "Union Pacific Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GILD", "ticker_tradingview": "NASDAQ:GILD", "name": "Gilead Sciences, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CMCSA", "ticker_tradingview": "NASDAQ:CMCSA", "name": "Comcast Corporation (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ADP", "ticker_tradingview": "NASDAQ:ADP", "name": "Automatic Data Processing, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PFE", "ticker_tradingview": "NYSE:PFE", "name": "Pfizer Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SYK", "ticker_tradingview": "NYSE:SYK", "name": "Stryker Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DE", "ticker_tradingview": "NYSE:DE", "name": "Deere & Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LOW", "ticker_tradingview": "NYSE:LOW", "name": "Lowe's Companies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ETN", "ticker_tradingview": "NYSE:ETN", "name": "Eaton Corporation plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PANW", "ticker_tradingview": "NASDAQ:PANW", "name": "Palo Alto Networks, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DHR", "ticker_tradingview": "NYSE:DHR", "name": "Danaher Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "COF", "ticker_tradingview": "NYSE:COF", "name": "Capital One Financial Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MMC", "ticker_tradingview": "NYSE:MMC", "name": "Marsh & McLennan Companies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "VRTX", "ticker_tradingview": "NASDAQ:VRTX", "name": "Vertex Pharmaceuticals Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "COP", "ticker_tradingview": "NYSE:COP", "name": "ConocoPhillips", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ADI", "ticker_tradingview": "NASDAQ:ADI", "name": "Analog Devices, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MDT", "ticker_tradingview": "NYSE:MDT", "name": "Medtronic plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CB", "ticker_tradingview": "NYSE:CB", "name": "Chubb Limited", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CRWD", "ticker_tradingview": "NASDAQ:CRWD", "name": "CrowdStrike Holdings, Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "APH", "ticker_tradingview": "NYSE:APH", "name": "Amphenol Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "KLAC", "ticker_tradingview": "NASDAQ:KLAC", "name": "KLA Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CME", "ticker_tradingview": "NASDAQ:CME", "name": "CME Group Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MO", "ticker_tradingview": "NYSE:MO", "name": "Altria Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BX", "ticker_tradingview": "NYSE:BX", "name": "Blackstone Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ICE", "ticker_tradingview": "NYSE:ICE", "name": "Intercontinental Exchange, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AMT", "ticker_tradingview": "NYSE:AMT", "name": "American Tower Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LMT", "ticker_tradingview": "NYSE:LMT", "name": "Lockheed Martin Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SO", "ticker_tradingview": "NYSE:SO", "name": "The Southern Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PLD", "ticker_tradingview": "NYSE:PLD", "name": "Prologis, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BMY", "ticker_tradingview": "NYSE:BMY", "name": "Bristol-Myers Squibb Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TT", "ticker_tradingview": "NYSE:TT", "name": "Trane Technologies plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SBUX", "ticker_tradingview": "NASDAQ:SBUX", "name": "Starbucks Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ELV", "ticker_tradingview": "NYSE:ELV", "name": "Elevance Health, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FI", "ticker_tradingview": "NYSE:FI", "name": "Fiserv, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DUK", "ticker_tradingview": "NYSE:DUK", "name": "Duke Energy Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WELL", "ticker_tradingview": "NYSE:WELL", "name": "Welltower Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MCK", "ticker_tradingview": "NYSE:MCK", "name": "McKesson Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CEG", "ticker_tradingview": "NASDAQ:CEG", "name": "Constellation Energy Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CDNS", "ticker_tradingview": "NASDAQ:CDNS", "name": "Cadence Design Systems, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CI", "ticker_tradingview": "NYSE:CI", "name": "The Cigna Group", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AJG", "ticker_tradingview": "NYSE:AJG", "name": "Arthur J. Gallagher & Co.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WM", "ticker_tradingview": "NYSE:WM", "name": "Waste Management, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PH", "ticker_tradingview": "NYSE:PH", "name": "Parker-Hannifin Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MDLZ", "ticker_tradingview": "NASDAQ:MDLZ", "name": "Mondelez International, Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EQIX", "ticker_tradingview": "NASDAQ:EQIX", "name": "Equinix, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SHW", "ticker_tradingview": "NYSE:SHW", "name": "The Sherwin-Williams Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MMM", "ticker_tradingview": "NYSE:MMM", "name": "3M Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "KKR", "ticker_tradingview": "NYSE:KKR", "name": "KKR & Co. Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TDG", "ticker_tradingview": "NYSE:TDG", "name": "TransDigm Group Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ORLY", "ticker_tradingview": "NASDAQ:ORLY", "name": "O'Reilly Automotive, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CVS", "ticker_tradingview": "NYSE:CVS", "name": "CVS Health Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SNPS", "ticker_tradingview": "NASDAQ:SNPS", "name": "Synopsys, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AON", "ticker_tradingview": "NYSE:AON", "name": "Aon plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CTAS", "ticker_tradingview": "NASDAQ:CTAS", "name": "Cintas Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CL", "ticker_tradingview": "NYSE:CL", "name": "Colgate-Palmolive Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MCO", "ticker_tradingview": "NYSE:MCO", "name": "Moody's Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZTS", "ticker_tradingview": "NYSE:ZTS", "name": "Zoetis Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MSI", "ticker_tradingview": "NYSE:MSI", "name": "Motorola Solutions, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PYPL", "ticker_tradingview": "NASDAQ:PYPL", "name": "PayPal Holdings, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NKE", "ticker_tradingview": "NYSE:NKE", "name": "NIKE, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WMB", "ticker_tradingview": "NYSE:WMB", "name": "The Williams Companies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GD", "ticker_tradingview": "NYSE:GD", "name": "General Dynamics Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "UPS", "ticker_tradingview": "NYSE:UPS", "name": "United Parcel Service, Inc. (Class B)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DASH", "ticker_tradingview": "NYSE:DASH", "name": "DoorDash, Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CMG", "ticker_tradingview": "NYSE:CMG", "name": "Chipotle Mexican Grill, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HCA", "ticker_tradingview": "NYSE:HCA", "name": "HCA Healthcare, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PNC", "ticker_tradingview": "NYSE:PNC", "name": "The PNC Financial Services Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "USB", "ticker_tradingview": "NYSE:USB", "name": "U.S. Bancorp", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HWM", "ticker_tradingview": "NYSE:HWM", "name": "Howmet Aerospace Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ECL", "ticker_tradingview": "NYSE:ECL", "name": "Ecolab Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EMR", "ticker_tradingview": "NYSE:EMR", "name": "Emerson Electric Co.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ITW", "ticker_tradingview": "NYSE:ITW", "name": "Illinois Tool Works Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FTNT", "ticker_tradingview": "NASDAQ:FTNT", "name": "Fortinet, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AZO", "ticker_tradingview": "NYSE:AZO", "name": "AutoZone, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NOC", "ticker_tradingview": "NYSE:NOC", "name": "Northrop Grumman Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "JCI", "ticker_tradingview": "NYSE:JCI", "name": "Johnson Controls International plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BK", "ticker_tradingview": "NYSE:BK", "name": "The Bank of New York Mellon Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "REGN", "ticker_tradingview": "NASDAQ:REGN", "name": "Regeneron Pharmaceuticals, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ADSK", "ticker_tradingview": "NASDAQ:ADSK", "name": "Autodesk, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EOG", "ticker_tradingview": "NYSE:EOG", "name": "EOG Resources, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TRV", "ticker_tradingview": "NYSE:TRV", "name": "The Travelers Companies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ROP", "ticker_tradingview": "NYSE:ROP", "name": "Roper Technologies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "APD", "ticker_tradingview": "NYSE:APD", "name": "Air Products and Chemicals, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NEM", "ticker_tradingview": "NYSE:NEM", "name": "Newmont Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MAR", "ticker_tradingview": "NASDAQ:MAR", "name": "Marriott International, Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HLT", "ticker_tradingview": "NYSE:HLT", "name": "Hilton Worldwide Holdings Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "RCL", "ticker_tradingview": "NYSE:RCL", "name": "Royal Caribbean Group", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CSX", "ticker_tradingview": "NASDAQ:CSX", "name": "CSX Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "APO", "ticker_tradingview": "NYSE:APO", "name": "Apollo Global Management, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CARR", "ticker_tradingview": "NYSE:CARR", "name": "Carrier Global Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WDAY", "ticker_tradingview": "NASDAQ:WDAY", "name": "Workday, Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ABNB", "ticker_tradingview": "NASDAQ:ABNB", "name": "Airbnb, Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AEP", "ticker_tradingview": "NASDAQ:AEP", "name": "American Electric Power Company, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "COIN", "ticker_tradingview": "NASDAQ:COIN", "name": "Coinbase Global, Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FCX", "ticker_tradingview": "NYSE:FCX", "name": "Freeport-McMoRan Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ADBE", "ticker_tradingview": "NASDAQ:ADBE", "name": "Adobe Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ISRG", "ticker_tradingview": "NASDAQ:ISRG", "name": "Intuitive Surgical, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ACN", "ticker_tradingview": "NYSE:ACN", "name": "Accenture plc (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PGR", "ticker_tradingview": "NYSE:PGR", "name": "The Progressive Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FIS", "ticker_tradingview": "NYSE:FIS", "name": "Fidelity National Information Services, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MC", "ticker_tradingview": "NYSE:MC", "name": "Moelis & Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DXCM", "ticker_tradingview": "NASDAQ:DXCM", "name": "DexCom, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HPQ", "ticker_tradingview": "NYSE:HPQ", "name": "HP Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DOW", "ticker_tradingview": "NYSE:DOW", "name": "Dow Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EIX", "ticker_tradingview": "NYSE:EIX", "name": "Edison International", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "KHC", "ticker_tradingview": "NASDAQ:KHC", "name": "The Kraft Heinz Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BKR", "ticker_tradingview": "NASDAQ:BKR", "name": "Baker Hughes Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EQT", "ticker_tradingview": "NYSE:EQT", "name": "EQT Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PAYC", "ticker_tradingview": "NYSE:PAYC", "name": "Paycom Software, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NDAQ", "ticker_tradingview": "NASDAQ:NDAQ", "name": "Nasdaq, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ALB", "ticker_tradingview": "NYSE:ALB", "name": "Albemarle Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ALLE", "ticker_tradingview": "NYSE:ALLE", "name": "Allegion plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CDW", "ticker_tradingview": "NASDAQ:CDW", "name": "CDW Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CE", "ticker_tradingview": "NYSE:CE", "name": "Celanese Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DVA", "ticker_tradingview": "NYSE:DVA", "name": "DaVita Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DD", "ticker_tradingview": "NYSE:DD", "name": "DuPont de Nemours, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EW", "ticker_tradingview": "NYSE:EW", "name": "Edwards Lifesciences Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FTV", "ticker_tradingview": "NYSE:FTV", "name": "Fortive Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FOXA", "ticker_tradingview": "NASDAQ:FOXA", "name": "Fox Corporation (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GWW", "ticker_tradingview": "NYSE:GWW", "name": "W.W. Grainger, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HES", "ticker_tradingview": "NYSE:HES", "name": "Hess Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "IR", "ticker_tradingview": "NYSE:IR", "name": "Ingersoll Rand Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "KR", "ticker_tradingview": "NYSE:KR", "name": "The Kroger Co.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LVS", "ticker_tradingview": "NYSE:LVS", "name": "Las Vegas Sands Corp.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MAA", "ticker_tradingview": "NYSE:MAA", "name": "Mid-America Apartment Communities, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "O", "ticker_tradingview": "NYSE:O", "name": "Realty Income Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PXD", "ticker_tradingview": "NYSE:PXD", "name": "Pioneer Natural Resources Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ROST", "ticker_tradingview": "NASDAQ:ROST", "name": "Ross Stores, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SJM", "ticker_tradingview": "NYSE:SJM", "name": "The J.M. Smucker Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SPG", "ticker_tradingview": "NYSE:SPG", "name": "Simon Property Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TGT", "ticker_tradingview": "NYSE:TGT", "name": "Target Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "VLO", "ticker_tradingview": "NYSE:VLO", "name": "Valero Energy Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WBA", "ticker_tradingview": "NASDAQ:WBA", "name": "Walgreens Boots Alliance, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "XEL", "ticker_tradingview": "NASDAQ:XEL", "name": "Xcel Energy Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZBH", "ticker_tradingview": "NYSE:ZBH", "name": "Zimmer Biomet Holdings, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AFL", "ticker_tradingview": "NYSE:AFL", "name": "Aflac Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AKAM", "ticker_tradingview": "NASDAQ:AKAM", "name": "Akamai Technologies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "APTV", "ticker_tradingview": "NYSE:APTV", "name": "Aptiv PLC", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ATVI", "ticker_tradingview": "NASDAQ:ATVI", "name": "Activision Blizzard, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AWK", "ticker_tradingview": "NYSE:AWK", "name": "American Water Works Company, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BAX", "ticker_tradingview": "NYSE:BAX", "name": "Baxter International Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CAH", "ticker_tradingview": "NYSE:CAH", "name": "Cardinal Health, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CF", "ticker_tradingview": "NYSE:CF", "name": "CF Industries Holdings, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DLR", "ticker_tradingview": "NYSE:DLR", "name": "Digital Realty Trust, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DOV", "ticker_tradingview": "NYSE:DOV", "name": "Dover Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DRI", "ticker_tradingview": "NYSE:DRI", "name": "Darden Restaurants, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EL", "ticker_tradingview": "NYSE:EL", "name": "The Estée Lauder Companies Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EQIX", "ticker_tradingview": "NASDAQ:EQIX", "name": "Equinix, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EXC", "ticker_tradingview": "NASDAQ:EXC", "name": "Exelon Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FAST", "ticker_tradingview": "NASDAQ:FAST", "name": "Fastenal Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FRC", "ticker_tradingview": "NYSE:FRC", "name": "First Republic Bank", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GIS", "ticker_tradingview": "NYSE:GIS", "name": "General Mills, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GLW", "ticker_tradingview": "NYSE:GLW", "name": "Corning Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HAL", "ticker_tradingview": "NYSE:HAL", "name": "Halliburton Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HRL", "ticker_tradingview": "NYSE:HRL", "name": "Hormel Foods Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "IP", "ticker_tradingview": "NYSE:IP", "name": "International Paper Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "IQV", "ticker_tradingview": "NYSE:IQV", "name": "IQVIA Holdings Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "KEY", "ticker_tradingview": "NYSE:KEY", "name": "KeyCorp", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "KMB", "ticker_tradingview": "NYSE:KMB", "name": "Kimberly-Clark Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LDOS", "ticker_tradingview": "NYSE:LDOS", "name": "Leidos Holdings, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MGM", "ticker_tradingview": "NYSE:MGM", "name": "MGM Resorts International", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MLM", "ticker_tradingview": "NYSE:MLM", "name": "Martin Marietta Materials, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MPC", "ticker_tradingview": "NYSE:MPC", "name": "Marathon Petroleum Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NI", "ticker_tradingview": "NYSE:NI", "name": "NiSource Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "OXY", "ticker_tradingview": "NYSE:OXY", "name": "Occidental Petroleum Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PEG", "ticker_tradingview": "NYSE:PEG", "name": "Public Service Enterprise Group Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PPL", "ticker_tradingview": "NYSE:PPL", "name": "PPL Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PRU", "ticker_tradingview": "NYSE:PRU", "name": "Prudential Financial, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PSX", "ticker_tradingview": "NYSE:PSX", "name": "Phillips 66", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SRE", "ticker_tradingview": "NYSE:SRE", "name": "Sempra", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "STX", "ticker_tradingview": "NASDAQ:STX", "name": "Seagate Technology Holdings plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SWK", "ticker_tradingview": "NYSE:SWK", "name": "Stanley Black & Decker, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TSN", "ticker_tradingview": "NYSE:TSN", "name": "Tyson Foods, Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TXT", "ticker_tradingview": "NYSE:TXT", "name": "Textron Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WST", "ticker_tradingview": "NYSE:WST", "name": "West Pharmaceutical Services, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "XOM", "ticker_tradingview": "NYSE:XOM", "name": "Exxon Mobil Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "YUM", "ticker_tradingview": "NYSE:YUM", "name": "Yum! Brands, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZION", "ticker_tradingview": "NASDAQ:ZION", "name": "Zions Bancorporation, National Association", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AEE", "ticker_tradingview": "NYSE:AEE", "name": "Ameren Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AJM", "ticker_tradingview": "NYSE:AJM", "name": "Ajamco Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ALL", "ticker_tradingview": "NYSE:ALL", "name": "The Allstate Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AMCR", "ticker_tradingview": "NYSE:AMCR", "name": "Amcor plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AME", "ticker_tradingview": "NYSE:AME", "name": "AMETEK, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AMP", "ticker_tradingview": "NYSE:AMP", "name": "Ameriprise Financial, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "APA", "ticker_tradingview": "NASDAQ:APA", "name": "APA Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ARE", "ticker_tradingview": "NYSE:ARE", "name": "Alexandria Real Estate Equities, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CBOE", "ticker_tradingview": "BATS:CBOE", "name": "Cboe Global Markets, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CCL", "ticker_tradingview": "NYSE:CCL", "name": "Carnival Corporation & plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CEF", "ticker_tradingview": "NYSE:CEF", "name": "Central Fund of Canada Limited", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CFG", "ticker_tradingview": "NYSE:CFG", "name": "Citizens Financial Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CHRW", "ticker_tradingview": "NASDAQ:CHRW", "name": "C.H. Robinson Worldwide, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CTSH", "ticker_tradingview": "NASDAQ:CTSH", "name": "Cognizant Technology Solutions Corporation (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DTE", "ticker_tradingview": "NYSE:DTE", "name": "DTE Energy Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EA", "ticker_tradingview": "NASDAQ:EA", "name": "Electronic Arts Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EBAY", "ticker_tradingview": "NASDAQ:EBAY", "name": "eBay Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EOG", "ticker_tradingview": "NYSE:EOG", "name": "EOG Resources, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ESS", "ticker_tradingview": "NYSE:ESS", "name": "Essex Property Trust, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ETR", "ticker_tradingview": "NYSE:ETR", "name": "Entergy Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EXPE", "ticker_tradingview": "NASDAQ:EXPE", "name": "Expedia Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "F", "ticker_tradingview": "NYSE:F", "name": "Ford Motor Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FDX", "ticker_tradingview": "NYSE:FDX", "name": "FedEx Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FITB", "ticker_tradingview": "NASDAQ:FITB", "name": "Fifth Third Bancorp", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GPC", "ticker_tradingview": "NYSE:GPC", "name": "Genuine Parts Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GRMN", "ticker_tradingview": "NASDAQ:GRMN", "name": "Garmin Ltd.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HBI", "ticker_tradingview": "NYSE:HBI", "name": "Hanesbrands Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HBAN", "ticker_tradingview": "NASDAQ:HBAN", "name": "Huntington Bancshares Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HOLX", "ticker_tradingview": "NASDAQ:HOLX", "name": "Hologic, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HST", "ticker_tradingview": "NYSE:HST", "name": "Host Hotels & Resorts, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HSIC", "ticker_tradingview": "NASDAQ:HSIC", "name": "Henry Schein, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "IPG", "ticker_tradingview": "NYSE:IPG", "name": "The Interpublic Group of Companies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "IRM", "ticker_tradingview": "NYSE:IRM", "name": "Iron Mountain Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "JBHT", "ticker_tradingview": "NASDAQ:JBHT", "name": "J.B. Hunt Transport Services, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LNT", "ticker_tradingview": "NASDAQ:LNT", "name": "Alliant Energy Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LUV", "ticker_tradingview": "NYSE:LUV", "name": "Southwest Airlines Co.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MKC", "ticker_tradingview": "NYSE:MKC", "name": "McCormick & Company, Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MNST", "ticker_tradingview": "NASDAQ:MNST", "name": "Monster Beverage Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MRNA", "ticker_tradingview": "NASDAQ:MRNA", "name": "Moderna, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NTAP", "ticker_tradingview": "NASDAQ:NTAP", "name": "NetApp, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PCAR", "ticker_tradingview": "NASDAQ:PCAR", "name": "PACCAR Inc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PNW", "ticker_tradingview": "NYSE:PNW", "name": "Pinnacle West Capital Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "RHI", "ticker_tradingview": "NYSE:RHI", "name": "Robert Half Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SPG", "ticker_tradingview": "NYSE:SPG", "name": "Simon Property Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "STLD", "ticker_tradingview": "NASDAQ:STLD", "name": "Steel Dynamics, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TFC", "ticker_tradingview": "NYSE:TFC", "name": "Truist Financial Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TROW", "ticker_tradingview": "NASDAQ:TROW", "name": "T. Rowe Price Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "VRSN", "ticker_tradingview": "NASDAQ:VRSN", "name": "VeriSign, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WYNN", "ticker_tradingview": "NASDAQ:WYNN", "name": "Wynn Resorts, Limited", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "A", "ticker_tradingview": "NYSE:A", "name": "Agilent Technologies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ALLE", "ticker_tradingview": "NYSE:ALLE", "name": "Allegion plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BIIB", "ticker_tradingview": "NASDAQ:BIIB", "name": "Biogen Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CPRT", "ticker_tradingview": "NASDAQ:CPRT", "name": "Copart, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CSGP", "ticker_tradingview": "NASDAQ:CSGP", "name": "CoStar Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DDOG", "ticker_tradingview": "NASDAQ:DDOG", "name": "Datadog, Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DELL", "ticker_tradingview": "NYSE:DELL", "name": "Dell Technologies Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DHI", "ticker_tradingview": "NYSE:DHI", "name": "D.R. Horton, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DVN", "ticker_tradingview": "NYSE:DVN", "name": "Devon Energy Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GM", "ticker_tradingview": "NYSE:GM", "name": "General Motors Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HPE", "ticker_tradingview": "NYSE:HPE", "name": "Hewlett Packard Enterprise Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LUMN", "ticker_tradingview": "NYSE:LUMN", "name": "Lumen Technologies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MTD", "ticker_tradingview": "NYSE:MTD", "name": "Mettler-Toledo International Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NDSN", "ticker_tradingview": "NASDAQ:NDSN", "name": "Nordson Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PPG", "ticker_tradingview": "NYSE:PPG", "name": "PPG Industries, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "RGA", "ticker_tradingview": "NYSE:RGA", "name": "Reinsurance Group of America, Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "RJF", "ticker_tradingview": "NYSE:RJF", "name": "Raymond James Financial, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SEE", "ticker_tradingview": "NYSE:SEE", "name": "Sealed Air Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SLB", "ticker_tradingview": "NYSE:SLB", "name": "Schlumberger Limited", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SNV", "ticker_tradingview": "NYSE:SNV", "name": "Synovus Financial Corp.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TFX", "ticker_tradingview": "NYSE:TFX", "name": "Teleflex Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "URI", "ticker_tradingview": "NYSE:URI", "name": "United Rentals, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WAB", "ticker_tradingview": "NYSE:WAB", "name": "Westinghouse Air Brake Technologies Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WBD", "ticker_tradingview": "NASDAQ:WBD", "name": "Warner Bros. Discovery, Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WRK", "ticker_tradingview": "NYSE:WRK", "name": "WestRock Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WY", "ticker_tradingview": "NYSE:WY", "name": "Weyerhaeuser Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "Z", "ticker_tradingview": "NASDAQ:Z", "name": "Zillow Group, Inc. (Class C)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZBRA", "ticker_tradingview": "NASDAQ:ZBRA", "name": "Zebra Technologies Corporation (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZEN", "ticker_tradingview": "NYSE:ZEN", "name": "Zendesk, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ALGN", "ticker_tradingview": "NASDAQ:ALGN", "name": "Align Technology, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CDAY", "ticker_tradingview": "NASDAQ:CDAY", "name": "Ceridian HCM Holding Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CINF", "ticker_tradingview": "NASDAQ:CINF", "name": "Cincinnati Financial Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DLR", "ticker_tradingview": "NYSE:DLR", "name": "Digital Realty Trust, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EXPE", "ticker_tradingview": "NASDAQ:EXPE", "name": "Expedia Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GEN", "ticker_tradingview": "NASDAQ:GEN", "name": "Gen Digital Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "IR", "ticker_tradingview": "NYSE:IR", "name": "Ingersoll Rand Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MCHP", "ticker_tradingview": "NASDAQ:MCHP", "name": "Microchip Technology Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NTRS", "ticker_tradingview": "NASDAQ:NTRS", "name": "Northern Trust Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PAYX", "ticker_tradingview": "NASDAQ:PAYX", "name": "Paychex, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "VTRS", "ticker_tradingview": "NASDAQ:VTRS", "name": "Viatris Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WAT", "ticker_tradingview": "NYSE:WAT", "name": "Waters Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ADNT", "ticker_tradingview": "NYSE:ADNT", "name": "Adient plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ALV", "ticker_tradingview": "NYSE:ALV", "name": "Autoliv, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AOS", "ticker_tradingview": "NYSE:AOS", "name": "A. O. Smith Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BWA", "ticker_tradingview": "NYSE:BWA", "name": "BorgWarner Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CBOE", "ticker_tradingview": "BATS:CBOE", "name": "Cboe Global Markets, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CFG", "ticker_tradingview": "NYSE:CFG", "name": "Citizens Financial Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DOV", "ticker_tradingview": "NYSE:DOV", "name": "Dover Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DVN", "ticker_tradingview": "NYSE:DVN", "name": "Devon Energy Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ESS", "ticker_tradingview": "NYSE:ESS", "name": "Essex Property Trust, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FMC", "ticker_tradingview": "NYSE:FMC", "name": "FMC Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GPC", "ticker_tradingview": "NYSE:GPC", "name": "Genuine Parts Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LUMN", "ticker_tradingview": "NYSE:LUMN", "name": "Lumen Technologies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MTD", "ticker_tradingview": "NYSE:MTD", "name": "Mettler-Toledo International Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NDSN", "ticker_tradingview": "NASDAQ:NDSN", "name": "Nordson Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PPG", "ticker_tradingview": "NYSE:PPG", "name": "PPG Industries, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},   
        {"ticker": "RGA", "ticker_tradingview": "NYSE:RGA", "name": "Reinsurance Group of America, Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "RJF", "ticker_tradingview": "NYSE:RJF", "name": "Raymond James Financial, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SEE", "ticker_tradingview": "NYSE:SEE", "name": "Sealed Air Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SLB", "ticker_tradingview": "NYSE:SLB", "name": "Schlumberger Limited", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},       
        {"ticker": "SNV", "ticker_tradingview": "NYSE:SNV", "name": "Synovus Financial Corp.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TFX", "ticker_tradingview": "NYSE:TFX", "name": "Teleflex Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "URI", "ticker_tradingview": "NYSE:URI", "name": "United Rentals, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WAB", "ticker_tradingview": "NYSE:WAB", "name": "Westinghouse Air Brake Technologies Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WRK", "ticker_tradingview": "NYSE:WRK", "name": "WestRock Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WY", "ticker_tradingview": "NYSE:WY", "name": "Weyerhaeuser Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZBRA", "ticker_tradingview": "NASDAQ:ZBRA", "name": "Zebra Technologies Corporation (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AIG", "ticker_tradingview": "NYSE:AIG", "name": "American International Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ARE", "ticker_tradingview": "NYSE:ARE", "name": "Alexandria Real Estate Equities, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BKR", "ticker_tradingview": "NASDAQ:BKR", "name": "Baker Hughes Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CDNS", "ticker_tradingview": "NASDAQ:CDNS", "name": "Cadence Design Systems, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CF", "ticker_tradingview": "NYSE:CF", "name": "CF Industries Holdings, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CINF", "ticker_tradingview": "NASDAQ:CINF", "name": "Cincinnati Financial Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CSGP", "ticker_tradingview": "NASDAQ:CSGP", "name": "CoStar Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DOW", "ticker_tradingview": "NYSE:DOW", "name": "Dow Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DXCM", "ticker_tradingview": "NASDAQ:DXCM", "name": "DexCom, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EIX", "ticker_tradingview": "NYSE:EIX", "name": "Edison International", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EPR", "ticker_tradingview": "NYSE:EPR", "name": "EPR Properties", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EQT", "ticker_tradingview": "NYSE:EQT", "name": "EQT Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EW", "ticker_tradingview": "NYSE:EW", "name": "Edwards Lifesciences Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FOXA", "ticker_tradingview": "NASDAQ:FOXA", "name": "Fox Corporation (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FRC", "ticker_tradingview": "NYSE:FRC", "name": "First Republic Bank", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FTV", "ticker_tradingview": "NYSE:FTV", "name": "Fortive Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GWW", "ticker_tradingview": "NYSE:GWW", "name": "W.W. Grainger, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HES", "ticker_tradingview": "NYSE:HES", "name": "Hess Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HPQ", "ticker_tradingview": "NYSE:HPQ", "name": "HP Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "IQV", "ticker_tradingview": "NYSE:IQV", "name": "IQVIA Holdings Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "KR", "ticker_tradingview": "NYSE:KR", "name": "The Kroger Co.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LVS", "ticker_tradingview": "NYSE:LVS", "name": "Las Vegas Sands Corp.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MAA", "ticker_tradingview": "NYSE:MAA", "name": "Mid-America Apartment Communities, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NDAQ", "ticker_tradingview": "NASDAQ:NDAQ", "name": "Nasdaq, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NDSN", "ticker_tradingview": "NASDAQ:NDSN", "name": "Nordson Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PXD", "ticker_tradingview": "NYSE:PXD", "name": "Pioneer Natural Resources Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SJM", "ticker_tradingview": "NYSE:SJM", "name": "The J.M. Smucker Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SPG", "ticker_tradingview": "NYSE:SPG", "name": "Simon Property Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "STX", "ticker_tradingview": "NASDAQ:STX", "name": "Seagate Technology Holdings plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SWK", "ticker_tradingview": "NYSE:SWK", "name": "Stanley Black & Decker, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TGT", "ticker_tradingview": "NYSE:TGT", "name": "Target Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TSN", "ticker_tradingview": "NYSE:TSN", "name": "Tyson Foods, Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TXT", "ticker_tradingview": "NYSE:TXT", "name": "Textron Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "VLO", "ticker_tradingview": "NYSE:VLO", "name": "Valero Energy Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WBA", "ticker_tradingview": "NASDAQ:WBA", "name": "Walgreens Boots Alliance, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WST", "ticker_tradingview": "NYSE:WST", "name": "West Pharmaceutical Services, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "XEL", "ticker_tradingview": "NASDAQ:XEL", "name": "Xcel Energy Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "YUM", "ticker_tradingview": "NYSE:YUM", "name": "Yum! Brands, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZBH", "ticker_tradingview": "NYSE:ZBH", "name": "Zimmer Biomet Holdings, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},        
        {"ticker": "ZION", "ticker_tradingview": "NASDAQ:ZION", "name": "Zions Bancorporation, National Association", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZEN", "ticker_tradingview": "NYSE:ZEN", "name": "Zendesk, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BIIB", "ticker_tradingview": "NASDAQ:BIIB", "name": "Biogen Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CDW", "ticker_tradingview": "NASDAQ:CDW", "name": "CDW Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CHRW", "ticker_tradingview": "NASDAQ:CHRW", "name": "C.H. Robinson Worldwide, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DTE", "ticker_tradingview": "NYSE:DTE", "name": "DTE Energy Company", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "EBAY", "ticker_tradingview": "NASDAQ:EBAY", "name": "eBay Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GIS", "ticker_tradingview": "NYSE:GIS", "name": "General Mills, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HOLX", "ticker_tradingview": "NASDAQ:HOLX", "name": "Hologic, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HST", "ticker_tradingview": "NYSE:HST", "name": "Host Hotels & Resorts, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HSIC", "ticker_tradingview": "NASDAQ:HSIC", "name": "Henry Schein, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "IPG", "ticker_tradingview": "NYSE:IPG", "name": "The Interpublic Group of Companies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "IRM", "ticker_tradingview": "NYSE:IRM", "name": "Iron Mountain Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "JBHT", "ticker_tradingview": "NASDAQ:JBHT", "name": "J.B. Hunt Transport Services, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "KEY", "ticker_tradingview": "NYSE:KEY", "name": "KeyCorp", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "KMB", "ticker_tradingview": "NYSE:KMB", "name": "Kimberly-Clark Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LDOS", "ticker_tradingview": "NYSE:LDOS", "name": "Leidos Holdings, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LNT", "ticker_tradingview": "NASDAQ:LNT", "name": "Alliant Energy Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LUV", "ticker_tradingview": "NYSE:LUV", "name": "Southwest Airlines Co.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MCHP", "ticker_tradingview": "NASDAQ:MCHP", "name": "Microchip Technology Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MGM", "ticker_tradingview": "NYSE:MGM", "name": "MGM Resorts International", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MLM", "ticker_tradingview": "NYSE:MLM", "name": "Martin Marietta Materials, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MNST", "ticker_tradingview": "NASDAQ:MNST", "name": "Monster Beverage Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MPC", "ticker_tradingview": "NYSE:MPC", "name": "Marathon Petroleum Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MRNA", "ticker_tradingview": "NASDAQ:MRNA", "name": "Moderna, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NI", "ticker_tradingview": "NYSE:NI", "name": "NiSource Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NTRS", "ticker_tradingview": "NASDAQ:NTRS", "name": "Northern Trust Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "OXY", "ticker_tradingview": "NYSE:OXY", "name": "Occidental Petroleum Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PAYC", "ticker_tradingview": "NYSE:PAYC", "name": "Paycom Software, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PCAR", "ticker_tradingview": "NASDAQ:PCAR", "name": "PACCAR Inc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PEG", "ticker_tradingview": "NYSE:PEG", "name": "Public Service Enterprise Group Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PNW", "ticker_tradingview": "NYSE:PNW", "name": "Pinnacle West Capital Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PPL", "ticker_tradingview": "NYSE:PPL", "name": "PPL Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PRU", "ticker_tradingview": "NYSE:PRU", "name": "Prudential Financial, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PSX", "ticker_tradingview": "NYSE:PSX", "name": "Phillips 66", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SRE", "ticker_tradingview": "NYSE:SRE", "name": "Sempra", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},      
        {"ticker": "TFC", "ticker_tradingview": "NYSE:TFC", "name": "Truist Financial Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TROW", "ticker_tradingview": "NASDAQ:TROW", "name": "T. Rowe Price Group, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "VTRS", "ticker_tradingview": "NASDAQ:VTRS", "name": "Viatris Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "WBD", "ticker_tradingview": "NASDAQ:WBD", "name": "Warner Bros. Discovery, Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "Z", "ticker_tradingview": "NASDAQ:Z", "name": "Zillow Group, Inc. (Class C)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AEE", "ticker_tradingview": "NYSE:AEE", "name": "Ameren Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AFL", "ticker_tradingview": "NYSE:AFL", "name": "Aflac Incorporated", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AJM", "ticker_tradingview": "NYSE:AJM", "name": "Ajamco Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AKAM", "ticker_tradingview": "NASDAQ:AKAM", "name": "Akamai Technologies, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ALL", "ticker_tradingview": "NYSE:ALL", "name": "The Allstate Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AMCR", "ticker_tradingview": "NYSE:AMCR", "name": "Amcor plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AME", "ticker_tradingview": "NYSE:AME", "name": "AMETEK, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AMP", "ticker_tradingview": "NYSE:AMP", "name": "Ameriprise Financial, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "APA", "ticker_tradingview": "NASDAQ:APA", "name": "APA Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "APTV", "ticker_tradingview": "NYSE:APTV", "name": "Aptiv PLC", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ATVI", "ticker_tradingview": "NASDAQ:ATVI", "name": "Activision Blizzard, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AWK", "ticker_tradingview": "NYSE:AWK", "name": "American Water Works Company, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AXON", "ticker_tradingview": "NASDAQ:AXON", "name": "Axon Enterprise, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BAX", "ticker_tradingview": "NYSE:BAX", "name": "Baxter International Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BWA", "ticker_tradingview": "NYSE:BWA", "name": "BorgWarner Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CAH", "ticker_tradingview": "NYSE:CAH", "name": "Cardinal Health, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CCL", "ticker_tradingview": "NYSE:CCL", "name": "Carnival Corporation & plc", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CE", "ticker_tradingview": "NYSE:CE", "name": "Celanese Corporation", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CEF", "ticker_tradingview": "NYSE:CEF", "name": "Central Fund of Canada Limited", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CPRT", "ticker_tradingview": "NASDAQ:CPRT", "name": "Copart, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DD", "ticker_tradingview": "NYSE:DD", "name": "DuPont de Nemours, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "document_generated": False},
        {"ticker": "DDOG", "ticker_tradingview": "NASDAQ:DDOG", "name": "Datadog, Inc. (Class A)", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DELL", "ticker_tradingview": "NYSE:DELL", "name": "Dell Technologies Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DHI", "ticker_tradingview": "NYSE:DHI", "name": "D.R. Horton, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DRI", "ticker_tradingview": "NYSE:DRI", "name": "Darden Restaurants, Inc.", "region": ["US"], "prompt": "EQ_EQUITIES_LONG_SHORT_PROMPT", "factors": "EQ_EQUITIES_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any equities already exist to avoid duplicates
        existing_count = collection.count_documents({"ticker": {"$in": [equity["ticker"] for equity in equities]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing equities. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all equities
        result = collection.insert_many(equities)
        print(f"Successfully inserted {len(result.inserted_ids)} equities into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting equities", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting equities", "DATA_INSERTION", e)
        return False


def insert_energy_commodities(db):
    """
    Inserts energy commodities into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Inserting energy commodities into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Import prompts from _config
    from _config import EN_ENERGY_LONG_SHORT_PROMPT, EN_ENERGY_FACTORS_PROMPT
    
    # Energy commodities data to insert with prompt and model_function fields
    energy_commodities = [
        {"ticker": "CL=F", "ticker_tradingview": "TVC:USOIL", "name": "Crude Oil WTI", "region": ["US", "Global"], "prompt": EN_ENERGY_LONG_SHORT_PROMPT, "factors": EN_ENERGY_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EN", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BZ=F", "ticker_tradingview": "TVC:UKOIL", "name": "Crude Oil Brent", "region": ["UK", "Global"], "prompt": EN_ENERGY_LONG_SHORT_PROMPT, "factors": EN_ENERGY_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EN", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "NG=F", "ticker_tradingview": "NATGAS", "name": "Natural Gas", "region": ["US", "Global"], "prompt": EN_ENERGY_LONG_SHORT_PROMPT, "factors": EN_ENERGY_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EN", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any energy commodities already exist to avoid duplicates
        existing_count = collection.count_documents({"ticker": {"$in": [item["ticker"] for item in energy_commodities]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing energy commodities. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all energy commodities
        result = collection.insert_many(energy_commodities)
        print(f"Successfully inserted {len(result.inserted_ids)} energy commodities into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting energy commodities", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting energy commodities", "DATA_INSERTION", e)
        return False


def insert_metal_commodities(db):
    """
    Inserts metal commodities into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Inserting metal commodities into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Import prompts from _config
    from _config import ME_METALS_LONG_SHORT_PROMPT, ME_METALS_FACTORS_PROMPT
    
    # Metal commodities data to insert with prompt and model_function fields
    metal_commodities = [
        {"ticker": "XAUUSD", "ticker_tradingview": "OANDA:XAUUSD", "name": "Gold", "region": ["Global"], "prompt": "ME_METALS_LONG_SHORT_PROMPT", "factors": "ME_METALS_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "ME", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "XAGUSD", "ticker_tradingview": "OANDA:XAGUSD", "name": "Silver", "region": ["Global"], "prompt": "ME_METALS_LONG_SHORT_PROMPT", "factors": "ME_METALS_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "ME", "importance": 4, "recurrence": "multi", "decimal":3, "document_generated": False},
        {"ticker": "XPTUSD", "ticker_tradingview": "OANDA:XPTUSD", "name": "Platinum", "region": ["Global"], "prompt": "ME_METALS_LONG_SHORT_PROMPT", "factors": "ME_METALS_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "ME", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any metal commodities already exist to avoid duplicates
        existing_count = collection.count_documents({"ticker": {"$in": [item["ticker"] for item in metal_commodities]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing metal commodities. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all metal commodities
        result = collection.insert_many(metal_commodities)
        print(f"Successfully inserted {len(result.inserted_ids)} metal commodities into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting metal commodities", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting metal commodities", "DATA_INSERTION", e)
        return False


def insert_agriculture_commodities(db):
    """
    Inserts agriculture commodities into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Inserting agriculture commodities into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Import prompts from _config
    from _config import AG_AGRICULTURE_LONG_SHORT_PROMPT, AG_AGRICULTURE_FACTORS_PROMPT
    
    # Agriculture commodities data to insert with prompt and model_function fields
    agriculture_commodities = [
        {"ticker": "ZC=F", "ticker_tradingview": "CORN", "name": "Corn", "region": ["US"], "prompt": "AG_AGRICULTURE_LONG_SHORT_PROMPT", "factors": "AG_AGRICULTURE_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZS=F", "ticker_tradingview": "SOYBEAN", "name": "Soybeans", "region": ["US"], "prompt": "AG_AGRICULTURE_LONG_SHORT_PROMPT", "factors": "AG_AGRICULTURE_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZL=F", "ticker_tradingview": "SOYOIL", "name": "Soybean Oil", "region": ["US"], "prompt": "AG_AGRICULTURE_LONG_SHORT_PROMPT", "factors": "AG_AGRICULTURE_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 4, "recurrence": "multi", "decimal":4, "document_generated": False},
        {"ticker": "ZW=F", "ticker_tradingview": "WHEAT", "name": "Wheat (US)", "region": ["US"], "prompt": "AG_AGRICULTURE_LONG_SHORT_PROMPT", "factors": "AG_AGRICULTURE_FACTORS_PROMPT", "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any agriculture commodities already exist to avoid duplicates
        existing_count = collection.count_documents({"ticker": {"$in": [item["ticker"] for item in agriculture_commodities]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing agriculture commodities. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all agriculture commodities
        result = collection.insert_many(agriculture_commodities)
        print(f"Successfully inserted {len(result.inserted_ids)} agriculture commodities into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting agriculture commodities", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting agriculture commodities", "DATA_INSERTION", e)
        return False

def insert_crypto_assets(db):
    """
    Inserts crypto assets into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Inserting crypto assets into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Import prompts from _config
    from _config import CR_CRYPTO_LONG_SHORT_PROMPT, CR_CRYPTO_FACTORS_PROMPT
    
    # Crypto assets data to insert with prompt and model_function fields
    crypto_assets = [
        {"ticker": "BTC-USD", "ticker_tradingview": "COINBASE:BTCUSD", "name": "Bitcoin / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ETH-USD", "ticker_tradingview": "COINBASE:ETHUSD", "name": "Ethereum / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "BNB-USD", "ticker_tradingview": "COINBASE:BNBUSD", "name": "Binance Coin / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "XRP-USD", "ticker_tradingview": "COINBASE:XRPUSD", "name": "Ripple / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ADA-USD", "ticker_tradingview": "COINBASE:ADAUSD", "name": "Cardano / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SOL-USD", "ticker_tradingview": "COINBASE:SOLUSD", "name": "Solana / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DOGE-USD", "ticker_tradingview": "COINBASE:DOGEUSD", "name": "Dogecoin / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 3, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "DOT-USD", "ticker_tradingview": "COINBASE:DOTUSD", "name": "Polkadot / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "AVAX-USD", "ticker_tradingview": "COINBASE:AVAXUSD", "name": "Avalanche / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SHIB-USD", "ticker_tradingview": "COINBASE:SHIBUSD", "name": "Shiba Inu / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 3, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "LTC-USD", "ticker_tradingview": "COINBASE:LTCUSD", "name": "Litecoin / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 3, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "UNI7083-USD", "ticker_tradingview": "COINBASE:UNIUSD", "name": "Uniswap / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 3, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ATOM-USD", "ticker_tradingview": "COINBASE:ATOMUSD", "name": "Cosmos / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "FIL-USD", "ticker_tradingview": "COINBASE:FILUSD", "name": "Filecoin / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 3, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "TRX-USD", "ticker_tradingview": "COINBASE:TRXUSD", "name": "TRON / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 3, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ALGO-USD", "ticker_tradingview": "COINBASE:ALGOUSD", "name": "Algorand / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 3, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MANA-USD", "ticker_tradingview": "COINBASE:MANAUSD", "name": "Decentraland / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 3, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "APE-USD", "ticker_tradingview": "COINBASE:APEUSD", "name": "ApeCoin / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 3, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "STX4847-USD", "ticker_tradingview": "COINBASE:STXUSD", "name": "Stacks / U.S. Dollar", "region": ["Global"], "prompt": CR_CRYPTO_LONG_SHORT_PROMPT, "factors": CR_CRYPTO_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "CR", "importance": 3, "recurrence": "multi", "decimal":2, "document_generated": False}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any crypto assets already exist to avoid duplicates
        existing_count = collection.count_documents({"ticker": {"$in": [item["ticker"] for item in crypto_assets]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing crypto assets. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all crypto assets
        result = collection.insert_many(crypto_assets)
        print(f"Successfully inserted {len(result.inserted_ids)} crypto assets into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting crypto assets", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting crypto assets", "DATA_INSERTION", e)
        return False

def insert_pipeline_data(db):
    """
    Inserts initial pipeline data into the 'pipeline' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'pipeline'
    
    print()
    print("=" * 100)
    print(f"Inserting pipeline data into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Pipeline data to insert
    pipeline_data = []
    
    try:
        collection = db[collection_name]
        
        # Check if any pipeline data already exists to avoid duplicates
        existing_count = collection.count_documents({"model_function": {"$in": [item["model_function"] for item in pipeline_data]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing pipeline entries. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all pipeline data
        result = collection.insert_many(pipeline_data)
        print(f"Successfully inserted {len(result.inserted_ids)} pipeline entries into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting pipeline data", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting pipeline data", "DATA_INSERTION", e)
        return False


def insert_asset_classes_data(db):
    """
    Inserts initial asset classes data into the 'asset_classes' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'asset_classes'
    
    print()
    print("=" * 100)
    print(f"Inserting asset classes data into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Asset classes data to insert
    asset_classes_data = [
        {"Code": "FX", "Description": "Forex"},
        {"Code": "EQ", "Description": "Equities"},
        {"Code": "IX", "Description": "Indices"},
        {"Code": "EN", "Description": "Energy"},
        {"Code": "ME", "Description": "Metal"},
        {"Code": "AG", "Description": "Agricultural"},
        {"Code": "CR", "Description": "Crypto"}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any asset classes already exist to avoid duplicates
        existing_count = collection.count_documents({"Code": {"$in": [item["Code"] for item in asset_classes_data]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing asset classes. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all asset classes data
        result = collection.insert_many(asset_classes_data)
        print(f"Successfully inserted {len(result.inserted_ids)} asset classes into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting asset classes data", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting asset classes data", "DATA_INSERTION", e)
        return False

def create_weight_factors_collection(db):
    """
    Creates the 'weight_factors' collection with schema validation and indexes.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if collection was created or already exists, False on error
    """
    collection_name = 'weight_factors'
    
    print()
    print("=" * 100)
    print(f"Creating '{collection_name}' collection...")
    print("=" * 100)
    print()

    # Create collection with schema validation
    validator = {
        '$jsonSchema': {
            'bsonType': 'object',
            'required': [
                'date'
            ],
            'properties': {
                'date': {
                    'bsonType': 'string',
                    'pattern': '^\\d{4}-\\d{2}-\\d{2}$'
                },
                'Geopolitical': {
                    'bsonType': 'string',
                    'pattern': '^\\d+%$'
                },
                'Macroneconomics': {
                    'bsonType': 'string',
                    'pattern': '^\\d+%$'
                },
                'Technical_Sentiment': {
                    'bsonType': 'string',
                    'pattern': '^\\d+%$'
                },
                'Liquidity': {
                    'bsonType': 'string',
                    'pattern': '^\\d+%$'
                },
                'Earnings': {
                    'bsonType': 'string',
                    'pattern': '^\\d+%$'
                },
                'Business_Cycle': {
                    'bsonType': 'string',
                    'pattern': '^\\d+%$'
                },
                'Sentiment_Surveys': {
                    'bsonType': 'string',
                    'pattern': '^\\d+%$'
                }
            }
        }
    }
    
    # Define indexes for better query performance
    indexes = [
        [('date', pymongo.DESCENDING)]
    ]
    
    # Use the generic function to create the collection
    success = create_collection_with_schema(db, collection_name, validator, indexes)
    
    if success:
        print(f"Successfully created collection '{collection_name}'")
        print("Collection schema validation rules applied:")
        print("   - Required field: date")
        print("   - Optional fields: Geopolitical, Macroneconomics, Technical_Sentiment, Liquidity, Earnings, Business_Cycle, Sentiment_Surveys")
        print("   - All percentage fields must follow pattern: 'number%' (e.g., '30%')")
        print("   - Index created: date")
    
    return success


def create_pipeline_collection(db):
    """
    Creates the 'pipeline' collection with schema validation.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if collection was created or already exists, False on error
    """
    collection_name = 'pipeline'
    
    print()
    print("=" * 100)
    print(f"Creating '{collection_name}' collection...")
    print("=" * 100)
    print()

    # Create collection with schema validation
    validator = {
        '$jsonSchema': {
            'bsonType': 'object',
            'required': [
                'model_function',
                'task_completed'
            ],
            'properties': {
                'model_function': {
                    'bsonType': 'string'
                },
                'model_name': {
                    'bsonType': 'string'
                },
                'recurrence': {
                    'bsonType': 'string'
                },
                'task_completed': {
                    'bsonType': 'bool'
                }
            }
        }
    }
    
    # No indexes specified
    indexes = None
    
    # Use the generic function to create the collection
    success = create_collection_with_schema(db, collection_name, validator, indexes)
    
    if success:
        print(f"Successfully created collection '{collection_name}'")
        print("Collection schema validation rules applied:")
        print("   - Required fields: model_function, task_completed")
    
    return success


def create_asset_classes_collection(db):
    """
    Creates the 'asset_classes' collection with schema validation.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if collection was created or already exists, False on error
    """
    collection_name = 'asset_classes'
    
    print()
    print("=" * 100)
    print(f"Creating '{collection_name}' collection...")
    print("=" * 100)
    print()

    # Create collection with schema validation
    validator = {
        '$jsonSchema': {
            'bsonType': 'object',
            'required': [
                'Code',
                'Description'
            ],
            'properties': {
                'Code': {
                    'bsonType': 'string',
                    'description': 'Asset class code must be a string'
                },
                'Description': {
                    'bsonType': 'string',
                    'description': 'Asset class description must be a string'
                }
            }
        }
    }
    
    # No indexes specified
    indexes = None
    
    # Use the generic function to create the collection
    success = create_collection_with_schema(db, collection_name, validator, indexes)
    
    if success:
        print(f"Successfully created collection '{collection_name}'")
        print("Collection schema validation rules applied:")
        print("   - Required fields: Code, Description")
    
    return success

def create_alphagora_database():
    """
    Creates the 'alphagora' database and required collections with schema validation.
    Performs sequential data insertions. Returns True if all steps succeed, False otherwise.
    """
    try:
        # Get database name from environment
        database = os.getenv("MONGODB_DATABASE", "alphagora")
        
        # Use DatabaseManager for connection
        client = DatabaseManager().get_client()
        db = client[database]
        
        # Define sequential operations as a list of functions
        operations = [
            create_insights_collection,
            create_tickers_collection,
            create_pipeline_collection,
            create_asset_classes_collection,
            insert_asset_classes_data,
            insert_pipeline_data,
            insert_fx_pairs,
            insert_indices,
            insert_energy_commodities,
            insert_metal_commodities,
            insert_agriculture_commodities,
            insert_crypto_assets,
            insert_equities,
            create_weight_factors_collection
        ]
        
        # Execute operations sequentially, passing db to each
        for op in operations:
            if not op(db):
                log_error("Failed during sequential operation", "DATABASE_SETUP", None)
                return False
        
        # Close connection after all operations
        DatabaseManager().close_connection()
        return True
        
    except pymongo.errors.ServerSelectionTimeoutError:
        log_error("MongoDB server not found. Ensure MongoDB is running on the specified host/port.", "MONGODB_CONNECTION", None)
        return False
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error during database creation", "DATABASE_CREATION", e)
        return False

if __name__ == "__main__":
    print("Starting alphagora database creation...")
    
    # Use DatabaseManager to get connection details
    try:
        client = DatabaseManager().get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphagora")
        print(f"MongoDB Database: {db_name}")
        print("-" * 50)
        
        success = create_alphagora_database()
        
        if success:
            print("-" * 50)
            print("Database setup completed successfully!")
        else:
            print("-" * 50)
            print("Database setup failed. Please check the error messages above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Failed to initialize DatabaseManager: {e}")
        sys.exit(1)