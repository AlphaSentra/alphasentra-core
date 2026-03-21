"""
Description:
Script to create MongoDB database 'alphasentra-core'.
"""

import pymongo
import datetime
from db.fx_data import insert_fx_pairs
from db.equities_data import insert_equities
from db.indices_data import insert_indices
from db.commodities_data import insert_commodities_asset
from db.crypto_data import insert_crypto_assets
from db.etoro_instruments import import_etoro_instruments
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
            'timestamp_gmt'
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
                'minimum': -1.0,
                'maximum': 1.0
            },
            'conviction': {
                'bsonType': 'double',
                'minimum': -1.0,
                'maximum': 1.0
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
            'asset_class': {
                'bsonType': 'string'
            },
            'region': {
                'bsonType': 'string'
            },
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
        [('timestamp_gmt', pymongo.DESCENDING), ('importance', pymongo.ASCENDING)],
        [('conviction', pymongo.DESCENDING), ('sentiment_score', pymongo.DESCENDING)]
    ]
    
    # Use the generic function to create the collection
    success = create_collection_with_schema(db, collection_name, validator, indexes)
    
    if success:
        print(f"Successfully created collection '{collection_name}'")
        print("Collection schema validation rules applied:")
        print("   - Required fields: timestamp_gmt")
        print("   - Optional field: sources")
        print("   - Indexes created: timestamp_gmt, sentiment_score, language_code, timestamp_gmt+importance")
    
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
                'ticker_tradingview',
                'ticker_etoro',
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
                'ticker_etoro': {
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
                'sector':{
                    'bsonType': 'string',
                },
                'description':{
                    'bsonType': 'string',
                },
                '1y':{
                    'bsonType': 'double',
                },
                '6m':{
                    'bsonType': 'double',
                },
                '3m':{
                    'bsonType': 'double',
                },
                '1m':{
                    'bsonType': 'double',
                },
                '1d':{
                    'bsonType': 'double',
                },
                'cashflow_health': {
                    'bsonType': 'string'
                },
                'profit_health': {
                    'bsonType': 'string'
                },
                'price_momentum': {
                    'bsonType': 'string'
                },
                'growth_health': {
                    'bsonType': 'string'
                },
                'dividend_yield': {},                
                'recurrence': {
                    'bsonType': 'string'
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


def create_trades_collection(db):
    """
    Creates the 'trades' collection with schema validation and indexes.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if collection was created or already exists, False on error
    """
    collection_name = 'trades'
    
    print()
    print("=" * 100)
    print(f"Creating '{collection_name}' collection...")
    print("=" * 100)
    print()

    # Create collection with schema validation
    validator = {
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['inputs', 'results', 'chart_data'],
            'properties': {
                'inputs': {
                    'bsonType': 'object',
                    'required': ['sessionID', 'ticker', 'strategy', 'inputs'],
                    'properties': {
                        'sessionID': {'bsonType': 'string'},
                        'ticker': {'bsonType': 'string'},
                        'strategy': {'bsonType': 'string'},
                        'inputs': {
                            'bsonType': 'object',
                            'required': ['entry_price', 'target_price', 'stop_loss', 'drift', 'volatility', 'num_simulations'],
                            'properties': {
                                'entry_price': {'bsonType': 'double'},
                                'target_price': {'bsonType': 'double'},
                                'stop_loss': {'bsonType': 'double'},
                                'drift': {'bsonType': 'double'},
                                'volatility': {'bsonType': 'double'},
                                'num_simulations': {'bsonType': 'int'}
                            }
                        }
                    }
                },
                'results': {
                    'bsonType': 'object',
                    'required': ['win_probability', 'risk_of_ruin', 'avg_days_to_target', 'expired_probability', 'maximum_drawdown', 'expected_value'],
                    'properties': {
                        'win_probability': {'bsonType': 'double'},
                        'risk_of_ruin': {'bsonType': 'double'},
                        'avg_days_to_target': {'bsonType': 'double'},
                        'expired_probability': {'bsonType': 'double'},
                        'maximum_drawdown': {'bsonType': 'double'},
                        'expected_value': {'bsonType': 'double'}
                    }
                },
                'chart_data': {
                    'bsonType': 'object',
                    'required': ['time_index', 'percentiles', 'sample_paths'],
                    'properties': {
                        'time_index': {
                            'bsonType': 'array',
                            'items': {'bsonType': 'int'}
                        },
                        'percentiles': {
                            'bsonType': 'object',
                            'required': ['p5', 'p50', 'p95'],
                            'properties': {
                                'p5': {
                                    'bsonType': 'array',
                                    'items': {'bsonType': 'double'}
                                },
                                'p50': {
                                    'bsonType': 'array',
                                    'items': {'bsonType': 'double'}
                                },
                                'p95': {
                                    'bsonType': 'array',
                                    'items': {'bsonType': 'double'}
                                }
                            }
                        },
                        'sample_paths': {
                            'bsonType': 'array',
                            'items': {
                                'bsonType': 'array',
                                'items': {'bsonType': 'double'}
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Define indexes for better query performance
    indexes = [
        [("inputs.sessionID", pymongo.ASCENDING)],
        [("inputs.ticker", pymongo.ASCENDING)]
    ]
    
    # Use the generic function to create the collection
    success = create_collection_with_schema(db, collection_name, validator, indexes)
    
    if success:
        print(f"Successfully created collection '{collection_name}'")
        print("Collection schema validation rules applied.")
    
    return success

def create_users_collection(db):
    """
    Creates the 'users' collection with schema validation and indexes.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if collection was created or already exists, False on error
    """
    collection_name = 'users'
    
    print()
    print("=" * 100)
    print(f"Creating '{collection_name}' collection...")
    print("=" * 100)
    print()

    # Create collection with schema validation
    validator = {
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['email', 'passcode', 'first_name','etoro_username', 'number_of_analysis', 'country', 'stocks', 'forex', 'crypto', 'commodities', 'last_login', 'created_at', 'expiry_subscription'],
            'properties': {
                'email': {
                    'bsonType': 'string'
                },
                'passcode': {
                    'bsonType': 'int'
                },
                'first_name': {
                    'bsonType': 'string'
                },
                'etoro_username': {
                    'bsonType': ['string', 'null']
                },
                'country': {
                    'bsonType': 'string'
                },
                'stocks': {
                    'bsonType': 'bool'
                },
                'forex': {
                    'bsonType': 'bool'
                },
                'crypto': {
                    'bsonType': 'bool'
                },
                'commodities': {
                    'bsonType': 'bool'
                },
                'number_of_analysis': {
                    'bsonType': 'int'
                },
                'created_at': {
                    'bsonType': 'date'
                },
                'last_login': {
                    'bsonType': ['date', 'null']
                },
                'expiry_subscription': {
                    'bsonType': ['date', 'null']
                }
            }
        }
    }
    
    # Define indexes for better query performance
    indexes = [
        [('email', pymongo.ASCENDING)]
    ]
    
    # Use the generic function to create the collection
    success = create_collection_with_schema(db, collection_name, validator, indexes)
    
    if success:
        print(f"Successfully created collection '{collection_name}'")
        print("Collection schema validation rules applied:")
        print("   - Required fields: email, passcode, first_name")
        print("   - Indexes created: email")
    
    return success


def create_settings_collection(db):
    """
    Creates the 'settings' collection with schema validation.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if collection was created or already exists, False on error
    """
    collection_name = 'settings'
    
    print()
    print("=" * 100)
    print(f"Creating '{collection_name}' collection...")
    print("=" * 100)
    print()

    # Create collection with schema validation
    validator = {
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['key', 'value', 'batch_id', 'ai_prompt_count', 'max_daily_ai_prompt_count'],
            'properties': {
                'key': {
                    'bsonType': 'string'
                },
                'value': {},
                'batch_id': {
                    'bsonType': 'int'
                },
                'ai_prompt_count': {
                    'bsonType': 'int'
                },
                'max_daily_ai_prompt_count': {
                    'bsonType': 'int'
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
        print("   - Required fields: key, value, batch_id, ai_prompt_count, max_daily_ai_prompt_count")
    
    return success


def insert_user_data(db):
    """
    Inserts initial user data into the 'users' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'users'
    
    print()
    print("=" * 100)
    print(f"Inserting user data into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # User data to insert
    user_data = {
        "email": "admin@alphasentra.com",
        "passcode": 123456,
        "first_name": "Admin",
        "country": "United Kingdom",
        "stocks": True,
        "forex": True,
        "crypto": True,
        "commodities": True,
        "number_of_analysis": 0,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "last_login": None,
        "expiry_subscription": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365 * 100)
    }
    
    try:
        collection = db[collection_name]
        
        # Check if the user already exists to avoid duplicates
        existing_user = collection.find_one({"email": user_data["email"]})
        if existing_user:
            print(f"User with email '{user_data['email']}' already exists. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert the user data
        result = collection.insert_one(user_data)
        print(f"Successfully inserted user data with id {result.inserted_id} into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting user data", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting user data", "DATA_INSERTION", e)
        return False

def insert_settings_data(db):
    """
    Inserts initial settings data into the 'settings' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'settings'
    
    print()
    print("=" * 100)
    print(f"Inserting settings data into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Settings data to insert
    settings_data = {
        "key": "batch_settings",
        "value": "default",
        "batch_id": 0,
        "ai_prompt_count": 0,
        "max_daily_ai_prompt_count": 3000
    }
    
    try:
        collection = db[collection_name]
        
        # Check if the setting already exists to avoid duplicates
        existing_setting = collection.find_one({"key": settings_data["key"]})
        if existing_setting:
            print(f"Setting with key '{settings_data['key']}' already exists. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert the settings data
        result = collection.insert_one(settings_data)
        print(f"Successfully inserted settings data with id {result.inserted_id} into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting settings data", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting settings data", "DATA_INSERTION", e)
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
        {"code": "FX", "etoro_instrumentTypeId": 1, "description": "Forex"},
        {"code": "EQ", "etoro_instrumentTypeId": 5, "description": "Equities"},
        {"code": "ETF", "etoro_instrumentTypeId": 6, "description": "ETFs"},
        {"code": "IX", "etoro_instrumentTypeId": 4, "description": "Indices"},
        {"code": "CO", "etoro_instrumentTypeId": 2, "description": "Commodities"},
        {"code": "CR", "etoro_instrumentTypeId": 10, "description": "Crypto"}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any asset classes already exist to avoid duplicates
        existing_count = collection.count_documents({"code": {"$in": [item["code"] for item in asset_classes_data]}})
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
    

def insert_regions_data(db):
    """
    Inserts initial regions data into the 'regions' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'regions'
    
    print()
    print("=" * 100)
    print(f"Inserting regions data into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Regions data to insert
    regions_data = [
        {"region": "Global", "etoro_exchangeID": 1, "exchange_name": "FX", "yahoo_finance_exchange_code": "=X", "tradingview_exchange_code": ""},
        {"region": "Global", "etoro_exchangeID": 2, "exchange_name": "Commodity", "yahoo_finance_exchange_code": "", "tradingview_exchange_code": ""},
        {"region": "Global", "etoro_exchangeID": 3, "exchange_name": "Indices (CFD)", "yahoo_finance_exchange_code": "^", "tradingview_exchange_code": "INDEX:"},
        {"region": "US", "etoro_exchangeID": 4, "exchange_name": "Nasdaq", "yahoo_finance_exchange_code": "", "tradingview_exchange_code": "NASDAQ:"},
        {"region": "US", "etoro_exchangeID": 5, "exchange_name": "NYSE", "yahoo_finance_exchange_code": "", "tradingview_exchange_code": "NYSE:"},
        {"region": "Germany", "etoro_exchangeID": 6, "exchange_name": "Frankfurt (Xetra)", "yahoo_finance_exchange_code": ".DE", "tradingview_exchange_code": "XETR:"},
        {"region": "UK", "etoro_exchangeID": 7, "exchange_name": "London", "yahoo_finance_exchange_code": ".L", "tradingview_exchange_code": "LSE:"},
        {"region": "Global", "etoro_exchangeID": 8, "exchange_name": "Crypto", "yahoo_finance_exchange_code": "-USD", "tradingview_exchange_code": "USD"},
        {"region": "France", "etoro_exchangeID": 9, "exchange_name": "Paris", "yahoo_finance_exchange_code": ".PA", "tradingview_exchange_code": "EURONEXT:"},
        {"region": "Spain", "etoro_exchangeID": 10, "exchange_name": "Madrid", "yahoo_finance_exchange_code": ".MC", "tradingview_exchange_code": "BME:"},
        {"region": "Italy", "etoro_exchangeID": 11, "exchange_name": "Borsa Italiana", "yahoo_finance_exchange_code": ".MI", "tradingview_exchange_code": "MIL:"},
        {"region": "Switzerland", "etoro_exchangeID": 12, "exchange_name": "Zurich", "yahoo_finance_exchange_code": ".SW", "tradingview_exchange_code": "SIX:"},
        {"region": "Norway", "etoro_exchangeID": 14, "exchange_name": "Oslo", "yahoo_finance_exchange_code": ".OL", "tradingview_exchange_code": "OSL:"},
        {"region": "Sweden", "etoro_exchangeID": 15, "exchange_name": "Stockholm", "yahoo_finance_exchange_code": ".ST", "tradingview_exchange_code": "OMXSTO:"},
        {"region": "Denmark", "etoro_exchangeID": 16, "exchange_name": "Copenhagen", "yahoo_finance_exchange_code": ".CO", "tradingview_exchange_code": "OMXCOP:"},
        {"region": "Finland", "etoro_exchangeID": 17, "exchange_name": "Helsinki", "yahoo_finance_exchange_code": ".HE", "tradingview_exchange_code": "OMXHEX:"},
        {"region": "US", "etoro_exchangeID": 20, "exchange_name": "Chicago (CME/CBOT)", "yahoo_finance_exchange_code": "", "tradingview_exchange_code": "CME:"},
        {"region": "Hong Kong", "etoro_exchangeID": 21, "exchange_name": "Hong Kong", "yahoo_finance_exchange_code": ".HK", "tradingview_exchange_code": "HKEX:"},
        {"region": "Portugal", "etoro_exchangeID": 22, "exchange_name": "Lisbon", "yahoo_finance_exchange_code": ".LS", "tradingview_exchange_code": "EURONEXT:"},
        {"region": "Belgium", "etoro_exchangeID": 23, "exchange_name": "Brussels", "yahoo_finance_exchange_code": ".BR", "tradingview_exchange_code": "EURONEXT:"},
        {"region": "Saudi Arabia", "etoro_exchangeID": 24, "exchange_name": "Tadawul", "yahoo_finance_exchange_code": ".SR", "tradingview_exchange_code": "TADAWUL:"},
        {"region": "Netherlands", "etoro_exchangeID": 30, "exchange_name": "Amsterdam", "yahoo_finance_exchange_code": ".AS", "tradingview_exchange_code": "EURONEXT:"},
        {"region": "Australia", "etoro_exchangeID": 31, "exchange_name": "ASX (Sydney)", "yahoo_finance_exchange_code": ".AX", "tradingview_exchange_code": "ASX:"},
        {"region": "Austria", "etoro_exchangeID": 32, "exchange_name": "Vienna", "yahoo_finance_exchange_code": ".VI", "tradingview_exchange_code": "VIE:"},
        {"region": "Ireland", "etoro_exchangeID": 33, "exchange_name": "Dublin", "yahoo_finance_exchange_code": ".IR", "tradingview_exchange_code": "EURONEXT:"},
        {"region": "Global", "etoro_exchangeID": 34, "exchange_name": "ETFs (CFD)", "yahoo_finance_exchange_code": "", "tradingview_exchange_code": "AMEX:"},
        {"region": "Germany", "etoro_exchangeID": 38, "exchange_name": "Xetra ETFs", "yahoo_finance_exchange_code": ".DE", "tradingview_exchange_code": "XETR:"},
        {"region": "UAE", "etoro_exchangeID": 39, "exchange_name": "Dubai", "yahoo_finance_exchange_code": ".DU", "tradingview_exchange_code": "DFM:"},
        {"region": "Global", "etoro_exchangeID": 40, "exchange_name": "Commodities", "yahoo_finance_exchange_code": "=F", "tradingview_exchange_code": "COMEX:"},
        {"region": "UAE", "etoro_exchangeID": 41, "exchange_name": "Abu Dhabi", "yahoo_finance_exchange_code": ".AD", "tradingview_exchange_code": "ADX:"},
        {"region": "UK", "etoro_exchangeID": 42, "exchange_name": "LSE AIM", "yahoo_finance_exchange_code": ".L", "tradingview_exchange_code": "LSE:"},
        {"region": "Japan", "etoro_exchangeID": 56, "exchange_name": "Tokyo", "yahoo_finance_exchange_code": ".T", "tradingview_exchange_code": "TSE:"}
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any regions already exist to avoid duplicates
        existing_count = collection.count_documents({"region": {"$in": [item["region"] for item in regions_data]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing regions. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all regions data
        result = collection.insert_many(regions_data)
        print(f"Successfully inserted {len(result.inserted_ids)} regions into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting regions data", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting regions data", "DATA_INSERTION", e)
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


def create_regions_collection(db):
    """
    Creates the 'regions' collection with schema validation.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if collection was created or already exists, False on error
    """
    collection_name = 'regions'
    
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
                'region',
                'etoro_exchangeID',
                'exchange_name'
            ],
            'properties': {
                'region': {
                    'bsonType': 'string',
                    'description': 'Region code must be a string'
                },
                'etoro_exchangeID': {
                    'bsonType': 'int',
                    'description': 'eToro exchange ID must be an integer'
                },
                'exchange_name': {
                    'bsonType': 'string',
                    'description': 'Exchange name must be a string'
                },
                'yahoo_finance_exchange_code': {
                    'bsonType': 'string',
                    'description': 'Yahoo Finance exchange code must be a string'
                },
                'tradingview_exchange_code': {
                    'bsonType': 'string',
                    'description': 'TradingView exchange code must be a string'
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
        print("   - Required fields: region, etoro_exchangeID, exchange_name")
    
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
                'code',
                'description'
            ],
            'properties': {
                'code': {
                    'bsonType': 'string',
                    'description': 'Asset class code must be a string'
                },
                'etoro_instrumentTypeId': {
                    'bsonType': 'int',
                    'description': 'eToro instrument type ID must be an integer'
                },
                'description': {
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
        print("   - Required fields: code, description")
    
    return success


def create_alphasentra_database():
    """
    Creates the 'alphasentra-core' database and required collections with schema validation.
    Performs sequential data insertions. Returns True if all steps succeed, False otherwise.
    """
    try:
        # Get database name from environment
        database = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        
        # Use DatabaseManager for connection
        client = DatabaseManager().get_client()
        db = client[database]
        
        # Define sequential operations as a list of functions
        operations = [
            create_insights_collection,
            create_tickers_collection,
            create_trades_collection,
            create_pipeline_collection,
            create_asset_classes_collection,
            create_settings_collection,
            create_users_collection,
            insert_settings_data,
            insert_user_data,
            insert_asset_classes_data,
            create_regions_collection,
            insert_regions_data,
            import_etoro_instruments,            
            insert_fx_pairs,
            #insert_indices,
            insert_commodities_asset,
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
    print("Starting alphasentra-core database creation...")
    
    # Use DatabaseManager to get connection details
    try:
        client = DatabaseManager().get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        print(f"MongoDB Database: {db_name}")
        print("-" * 50)
        
        success = create_alphasentra_database()
        
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