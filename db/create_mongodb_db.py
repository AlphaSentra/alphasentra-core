"""
Script to create MongoDB database 'alphagora' with collection 'documents'.
"""

import pymongo
from pymongo import MongoClient
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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


def create_documents_collection(db):
    """
    Creates the 'documents' collection with schema validation and indexes.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if collection was created or already exists, False on error
    """
    collection_name = 'documents'
    
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
            'region': {}
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
                'asset_class': {},
                'importance': {
                    'bsonType': 'int',
                    'minimum': 1,
                    'maximum': 5,
                },
                'recurrence': {
                    'bsonType': 'string',
                    'enum': ['multi','once'],
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
        {"ticker": "EURUSD=X", "ticker_tradingview": "FX_IDC:EURUSD", "name": "Euro / U.S. Dollar", "region": ["Eurozone", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 4, "recurrence": "multi"},
        {"ticker": "USDJPY=X", "ticker_tradingview": "FX_IDC:USDJPY", "name": "U.S. Dollar / Japanese Yen", "region": ["US", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 4, "recurrence": "multi"},
        {"ticker": "GBPUSD=X", "ticker_tradingview": "FX_IDC:GBPUSD", "name": "British Pound / U.S. Dollar", "region": ["UK", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 4, "recurrence": "multi"},
        {"ticker": "USDCHF=X", "ticker_tradingview": "FX_IDC:USDCHF", "name": "U.S. Dollar / Swiss Franc", "region": ["US", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 4, "recurrence": "multi"},
        {"ticker": "AUDUSD=X", "ticker_tradingview": "FX_IDC:AUDUSD", "name": "Australian Dollar / U.S. Dollar", "region": ["Australia", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 4, "recurrence": "multi"},
        {"ticker": "USDCAD=X", "ticker_tradingview": "FX_IDC:USDCAD", "name": "U.S. Dollar / Canadian Dollar", "region": ["US", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 4, "recurrence": "multi"},
        {"ticker": "NZDUSD=X", "ticker_tradingview": "FX_IDC:NZDUSD", "name": "New Zealand Dollar / U.S. Dollar", "region": ["New Zealand", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 4, "recurrence": "multi"},
        {"ticker": "EURGBP=X", "ticker_tradingview": "FX_IDC:EURGBP", "name": "Euro / British Pound", "region": ["Eurozone", "UK"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 4, "recurrence": "multi"},
        {"ticker": "EURJPY=X", "ticker_tradingview": "FX_IDC:EURJPY", "name": "Euro / Japanese Yen", "region": ["Eurozone", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "GBPJPY=X", "ticker_tradingview": "FX_IDC:GBPJPY", "name": "British Pound / Japanese Yen", "region": ["UK", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "EURCHF=X", "ticker_tradingview": "FX_IDC:EURCHF", "name": "Euro / Swiss Franc", "region": ["Eurozone", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 4, "recurrence": "multi"},
        {"ticker": "AudJPY=X", "ticker_tradingview": "FX_IDC:AUDJPY", "name": "Australian Dollar / Japanese Yen", "region": ["Australia", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "CADJPY=X", "ticker_tradingview": "FX_IDC:CADJPY", "name": "Canadian Dollar / Japanese Yen", "region": ["Canada", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "NZDJPY=X", "ticker_tradingview": "FX_IDC:NZDJPY", "name": "New Zealand Dollar / Japanese Yen", "region": ["New Zealand", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "AUDNZD=X", "ticker_tradingview": "FX_IDC:AUDNZD", "name": "Australian Dollar / New Zealand Dollar", "region": ["Australia", "New Zealand"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "EURCAD=X", "ticker_tradingview": "FX_IDC:EURCAD", "name": "Euro / Canadian Dollar", "region": ["Eurozone", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "USDTRY=X", "ticker_tradingview": "FX_IDC:USDTRY", "name": "U.S. Dollar / Turkish Lira", "region": ["US", "Turkey"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "USDZAR=X", "ticker_tradingview": "FX_IDC:USDZAR", "name": "U.S. Dollar / South African Rand", "region": ["US", "South Africa"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "EURTRY=X", "ticker_tradingview": "FX_IDC:EURTRY", "name": "Euro / Turkish Lira", "region": ["Eurozone", "Turkey"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "USDMXN=X", "ticker_tradingview": "FX_IDC:USDMXN", "name": "U.S. Dollar / Mexican Peso", "region": ["US", "Mexico"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "USDPLN=X", "ticker_tradingview": "FX_IDC:USDPLN", "name": "U.S. Dollar / Polish Zloty", "region": ["US", "Poland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "USDSEK=X", "ticker_tradingview": "FX_IDC:USDSEK", "name": "U.S. Dollar / Swedish Krona", "region": ["US", "Sweden"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "USDNOK=X", "ticker_tradingview": "FX_IDC:USDNOK", "name": "U.S. Dollar / Norwegian Krone", "region": ["US", "Norway"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "USDTHB=X", "ticker_tradingview": "FX_IDC:USDTHB", "name": "U.S. Dollar / Thai Baht", "region": ["US", "Thailand"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "USDSGD=X", "ticker_tradingview": "FX_IDC:USDSGD", "name": "U.S. Dollar / Singapore Dollar", "region": ["US", "Singapore"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "USDCNH=X", "ticker_tradingview": "FX_IDC:USDCNH", "name": "U.S. Dollar / Chinese Yuan (Offshore)", "region": ["US", "China"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "EURCNH=X", "ticker_tradingview": "FX_IDC:EURCNH", "name": "Euro / Chinese Yuan (Offshore)", "region": ["Eurozone", "China"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "USDCNY=X", "ticker_tradingview": "FX_IDC:USDCNY", "name": "U.S. Dollar / Chinese Yuan (Onshore)", "region": ["US", "China"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "USDRUB=X", "ticker_tradingview": "FX_IDC:USDRUB", "name": "U.S. Dollar / Russian Ruble", "region": ["US", "Russia"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"},
        {"ticker": "DX=F", "ticker_tradingview": "TVC:DXY", "name": "U.S. Dollar Index", "region": ["US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 4, "recurrence": "multi"},
        {"ticker": "EURRUB=X", "ticker_tradingview": "FX_IDC:EURRUB", "name": "Euro / Russian Ruble", "region": ["Eurozone", "Russia"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "asset_class": "FX", "importance": 5, "recurrence": "multi"}
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
        {"ticker": "^GSPC", "ticker_tradingview": "CME_MINI:ES1!", "name": "S&P 500", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^NDX", "ticker_tradingview": "CME_MINI:NQ1!", "name": "NASDAQ 100", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^DJI", "ticker_tradingview": "CBOT_MINI:YM1!", "name": "Dow Jones Industrial Average", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^RUT", "ticker_tradingview": "ICEUS:RTY1!", "name": "Russell 2000", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^VIX", "ticker_tradingview": "CBOE:VIX", "name": "CBOE Volatility Index", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^N225", "ticker_tradingview": "TVC:NIKKEI", "name": "Nikkei 225", "region": ["Japan"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^TOPX", "ticker_tradingview": "TVC:TOPIX", "name": "TOPIX", "region": ["Japan"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^GDAXI", "ticker_tradingview": "TVC:DE40", "name": "DAX 40", "region": ["Germany"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^FCHI", "ticker_tradingview": "TVC:FR40", "name": "CAC 40", "region": ["France"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^FTSE", "ticker_tradingview": "TVC:UKX", "name": "FTSE 100", "region": ["UK"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^STOXX50E", "ticker_tradingview": "TVC:STOXX50E", "name": "Euro Stoxx 50", "region": ["Eurozone"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^SSMI", "ticker_tradingview": "TVC:CH20", "name": "Swiss Market Index (SMI)", "region": ["Switzerland"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^HSI", "ticker_tradingview": "TVC:HSI", "name": "Hang Seng Index", "region": ["Hong Kong"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^SSEC", "ticker_tradingview": "TVC:SHCOMP", "name": "Shanghai Composite", "region": ["China"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "000001.SS", "ticker_tradingview": "SSE:000001", "name": "SSE 50", "region": ["China"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "000300.SS", "ticker_tradingview": "CSI:000300", "name": "CSI 300", "region": ["China"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "399001.SZ", "ticker_tradingview": "SZSE:399001", "name": "Shenzhen Component", "region": ["China"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "399006.SZ", "ticker_tradingview": "SZSE:399006", "name": "ChiNext Index", "region": ["China"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi"},
        {"ticker": "^AXJO", "ticker_tradingview": "TVC:AUS200", "name": "ASX 200", "region": ["Australia"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi"},
        {"ticker": "^AORD", "ticker_tradingview": "TVC:AORD", "name": "All Ordinaries", "region": ["Australia"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi"},
        {"ticker": "^NSEI", "ticker_tradingview": "NSE:NIFTY", "name": "Nifty 50", "region": ["India"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi"},
        {"ticker": "^BSESN", "ticker_tradingview": "BSE:SENSEX", "name": "BSE Sensex", "region": ["India"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi"},
        {"ticker": "^STI", "ticker_tradingview": "TVC:STI", "name": "STI", "region": ["Singapore"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi"},
        {"ticker": "^KS11", "ticker_tradingview": "TVC:KS11", "name": "KOSPI", "region": ["South Korea"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi"},
        {"ticker": "^MXX", "ticker_tradingview": "TVC:MEXBOL", "name": "IPC Mexico General", "region": ["Mexico"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi"},
        {"ticker": "^BVSP", "ticker_tradingview": "TVC:BVSP", "name": "Bovespa", "region": ["Brazil"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi"},
        {"ticker": "^SPTSX", "ticker_tradingview": "TVC:TSX", "name": "S&P/TSX Composite", "region": ["Canada"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi"},
        {"ticker": "^NZ50", "ticker_tradingview": "TVC:NZ50", "name": "NZX 50", "region": ["New Zealand"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi"}
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


def create_alphagora_database():
    """
    Creates the 'alphagora' database and 'documents' collection with schema validation.
    Returns True if successful, False otherwise.
    """
    try:
        # Connect to MongoDB using MONGODB_URI from environment variables
        # Get MongoDB connection details from environment variables
        mongodb_host = os.getenv("MONGODB_HOST", "localhost")
        mongodb_port = int(os.getenv("MONGODB_PORT", "27017"))
        mongodb_database = os.getenv("MONGODB_DATABASE", "alphagora")
        mongodb_username = os.getenv("MONGODB_USERNAME")
        mongodb_password = os.getenv("MONGODB_PASSWORD")
        mongodb_auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")
        
        # Construct MongoDB URI based on whether authentication is provided
        if mongodb_username and mongodb_password:
            mongodb_uri = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_host}:{mongodb_port}/{mongodb_database}?authSource={mongodb_auth_source}"
        else:
            mongodb_uri = f"mongodb://{mongodb_host}:{mongodb_port}/{mongodb_database}"
        
        client = MongoClient(mongodb_uri)
        
        # Create or get the database
        db = client[mongodb_database]
        
        # Create the documents collection
        success = create_documents_collection(db)
        
        # Create the tickers collection
        if success:
            success = create_tickers_collection(db)
        
        # Insert FX pairs into tickers collection
        if success:
            success = insert_fx_pairs(db)
        
        # Insert indices into tickers collection
        if success:
            success = insert_indices(db)
        
        # Create weight_factors collection
        if success:
            success = create_weight_factors_collection(db)
        
        return success
        
    except pymongo.errors.ServerSelectionTimeoutError:
        log_error("MongoDB server not found. Please ensure MongoDB is running on localhost:27017", "MONGODB_CONNECTION", None)
        return False
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error", "DATABASE_CREATION", e)
        return False

if __name__ == "__main__":
    print("Starting alphagora database creation...")
    
    # Get MongoDB connection details from environment variables
    mongodb_host = os.getenv("MONGODB_HOST", "localhost")
    mongodb_port = int(os.getenv("MONGODB_PORT", "27017"))
    mongodb_database = os.getenv("MONGODB_DATABASE", "alphagora")
    mongodb_username = os.getenv("MONGODB_USERNAME")
    mongodb_password = os.getenv("MONGODB_PASSWORD")
    mongodb_auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")
    
    # Construct MongoDB URI based on whether authentication is provided
    if mongodb_username and mongodb_password:
        mongodb_uri = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_host}:{mongodb_port}/{mongodb_database}?authSource={mongodb_auth_source}"
        print(f"MongoDB Connection: mongodb://{mongodb_username}:******@{mongodb_host}:{mongodb_port}/{mongodb_database}?authSource={mongodb_auth_source}")
    else:
        mongodb_uri = f"mongodb://{mongodb_host}:{mongodb_port}/{mongodb_database}"
        print(f"MongoDB Connection: {mongodb_uri}")
    print("Database: alphagora")
    print("Collections: documents, tickers, weight_factors")
    print("FX Pairs: 30 currency pairs will be inserted into tickers collection")
    print("Indices: 28 stock indices will be inserted into tickers collection")
    print("-" * 50)
    
    success = create_alphagora_database()
    
    if success:
        print("-" * 50)
        print("Database setup completed successfully!")
    else:
        print("-" * 50)
        print("Database setup failed. Please check the error messages above.")
        sys.exit(1)