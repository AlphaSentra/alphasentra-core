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
        {"ticker": "EURUSD=X", "ticker_tradingview": "FX_IDC:EURUSD", "name": "Euro / U.S. Dollar", "region": ["Eurozone", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "USDJPY=X", "ticker_tradingview": "FX_IDC:USDJPY", "name": "U.S. Dollar / Japanese Yen", "region": ["US", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "GBPUSD=X", "ticker_tradingview": "FX_IDC:GBPUSD", "name": "British Pound / U.S. Dollar", "region": ["UK", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "USDCHF=X", "ticker_tradingview": "FX_IDC:USDCHF", "name": "U.S. Dollar / Swiss Franc", "region": ["US", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "AUDUSD=X", "ticker_tradingview": "FX_IDC:AUDUSD", "name": "Australian Dollar / U.S. Dollar", "region": ["Australia", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "USDCAD=X", "ticker_tradingview": "FX_IDC:USDCAD", "name": "U.S. Dollar / Canadian Dollar", "region": ["US", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "NZDUSD=X", "ticker_tradingview": "FX_IDC:NZDUSD", "name": "New Zealand Dollar / U.S. Dollar", "region": ["New Zealand", "US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "EURGBP=X", "ticker_tradingview": "FX_IDC:EURGBP", "name": "Euro / British Pound", "region": ["Eurozone", "UK"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "EURJPY=X", "ticker_tradingview": "FX_IDC:EURJPY", "name": "Euro / Japanese Yen", "region": ["Eurozone", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "GBPJPY=X", "ticker_tradingview": "FX_IDC:GBPJPY", "name": "British Pound / Japanese Yen", "region": ["UK", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "EURCHF=X", "ticker_tradingview": "FX_IDC:EURCHF", "name": "Euro / Swiss Franc", "region": ["Eurozone", "Switzerland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "AudJPY=X", "ticker_tradingview": "FX_IDC:AUDJPY", "name": "Australian Dollar / Japanese Yen", "region": ["Australia", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "CADJPY=X", "ticker_tradingview": "FX_IDC:CADJPY", "name": "Canadian Dollar / Japanese Yen", "region": ["Canada", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "NZDJPY=X", "ticker_tradingview": "FX_IDC:NZDJPY", "name": "New Zealand Dollar / Japanese Yen", "region": ["New Zealand", "Japan"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "AUDNZD=X", "ticker_tradingview": "FX_IDC:AUDNZD", "name": "Australian Dollar / New Zealand Dollar", "region": ["Australia", "New Zealand"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "EURCAD=X", "ticker_tradingview": "FX_IDC:EURCAD", "name": "Euro / Canadian Dollar", "region": ["Eurozone", "Canada"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "USDTRY=X", "ticker_tradingview": "FX_IDC:USDTRY", "name": "U.S. Dollar / Turkish Lira", "region": ["US", "Turkey"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "USDZAR=X", "ticker_tradingview": "FX_IDC:USDZAR", "name": "U.S. Dollar / South African Rand", "region": ["US", "South Africa"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "EURTRY=X", "ticker_tradingview": "FX_IDC:EURTRY", "name": "Euro / Turkish Lira", "region": ["Eurozone", "Turkey"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "USDMXN=X", "ticker_tradingview": "FX_IDC:USDMXN", "name": "U.S. Dollar / Mexican Peso", "region": ["US", "Mexico"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "USDPLN=X", "ticker_tradingview": "FX_IDC:USDPLN", "name": "U.S. Dollar / Polish Zloty", "region": ["US", "Poland"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "USDSEK=X", "ticker_tradingview": "FX_IDC:USDSEK", "name": "U.S. Dollar / Swedish Krona", "region": ["US", "Sweden"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "USDNOK=X", "ticker_tradingview": "FX_IDC:USDNOK", "name": "U.S. Dollar / Norwegian Krone", "region": ["US", "Norway"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "USDTHB=X", "ticker_tradingview": "FX_IDC:USDTHB", "name": "U.S. Dollar / Thai Baht", "region": ["US", "Thailand"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "USDSGD=X", "ticker_tradingview": "FX_IDC:USDSGD", "name": "U.S. Dollar / Singapore Dollar", "region": ["US", "Singapore"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "CNH=X", "ticker_tradingview": "FX_IDC:USDCNH", "name": "U.S. Dollar / Chinese Yuan (Offshore)", "region": ["US", "China"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "EURCNH=X", "ticker_tradingview": "FX_IDC:EURCNH", "name": "Euro / Chinese Yuan (Offshore)", "region": ["Eurozone", "China"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "USDCNY=X", "ticker_tradingview": "FX_IDC:USDCNY", "name": "U.S. Dollar / Chinese Yuan (Onshore)", "region": ["US", "China"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "USDRUB=X", "ticker_tradingview": "FX_IDC:USDRUB", "name": "U.S. Dollar / Russian Ruble", "region": ["US", "Russia"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "DX=F", "ticker_tradingview": "TVC:DXY", "name": "U.S. Dollar Index", "region": ["US"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 4, "recurrence": "multi", "decimal": 4, "document_generated": False},
        {"ticker": "EURRUB=X", "ticker_tradingview": "FX_IDC:EURRUB", "name": "Euro / Russian Ruble", "region": ["Eurozone", "Russia"], "prompt": FX_LONG_SHORT_PROMPT, "factors": FX_FACTORS_PROMPT, "model_function": "run_fx_model", "model_name":"fx_long_short", "asset_class": "FX", "importance": 5, "recurrence": "multi", "decimal": 4, "document_generated": False}
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
        {"ticker": "^GSPC", "ticker_tradingview": "CME_MINI:ES1!", "name": "S&P 500", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "document_generated": False},
        {"ticker": "^NDX", "ticker_tradingview": "CME_MINI:NQ1!", "name": "NASDAQ 100", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^DJI", "ticker_tradingview": "CBOT_MINI:YM1!", "name": "Dow Jones Industrial Average", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^RUT", "ticker_tradingview": "ICEUS:RTY1!", "name": "Russell 2000", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^VIX", "ticker_tradingview": "CBOE:VIX", "name": "CBOE Volatility Index", "region": ["US"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^N225", "ticker_tradingview": "TVC:NIKKEI", "name": "Nikkei 225", "region": ["Japan"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^GDAXI", "ticker_tradingview": "TVC:DE40", "name": "DAX 40", "region": ["Germany"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^FCHI", "ticker_tradingview": "TVC:FR40", "name": "CAC 40", "region": ["France"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^FTSE", "ticker_tradingview": "TVC:UKX", "name": "FTSE 100", "region": ["UK"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^STOXX50E", "ticker_tradingview": "TVC:STOXX50E", "name": "Euro Stoxx 50", "region": ["Eurozone"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^SSMI", "ticker_tradingview": "TVC:CH20", "name": "Swiss Market Index (SMI)", "region": ["Switzerland"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^HSI", "ticker_tradingview": "TVC:HSI", "name": "Hang Seng Index", "region": ["Hong Kong"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "000001.SS", "ticker_tradingview": "SSE:000001", "name": "SSE 50", "region": ["China"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "000300.SS", "ticker_tradingview": "CSI:000300", "name": "CSI 300", "region": ["China"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "399001.SZ", "ticker_tradingview": "SZSE:399001", "name": "Shenzhen Component", "region": ["China"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^AXJO", "ticker_tradingview": "TVC:AUS200", "name": "ASX 200", "region": ["Australia"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^AORD", "ticker_tradingview": "TVC:AORD", "name": "All Ordinaries", "region": ["Australia"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^NSEI", "ticker_tradingview": "NSE:NIFTY", "name": "Nifty 50", "region": ["India"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^BSESN", "ticker_tradingview": "BSE:SENSEX", "name": "BSE Sensex", "region": ["India"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^STI", "ticker_tradingview": "TVC:STI", "name": "STI", "region": ["Singapore"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^KS11", "ticker_tradingview": "TVC:KS11", "name": "KOSPI", "region": ["South Korea"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^MXX", "ticker_tradingview": "TVC:MEXBOL", "name": "IPC Mexico General", "region": ["Mexico"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^BVSP", "ticker_tradingview": "TVC:BVSP", "name": "Bovespa", "region": ["Brazil"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^GSPTSE", "ticker_tradingview": "TVC:TSX", "name": "S&P/TSX Composite", "region": ["Canada"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "^NZ50", "ticker_tradingview": "TVC:NZ50", "name": "NZX 50", "region": ["New Zealand"], "prompt": IX_INDEX_LONG_SHORT_PROMPT, "factors": IX_INDEX_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "IX, EQ", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False}
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
        {"ticker": "NG=F", "ticker_tradingview": "NYMEX:NG1!", "name": "Natural Gas", "region": ["US", "Global"], "prompt": EN_ENERGY_LONG_SHORT_PROMPT, "factors": EN_ENERGY_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EN", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "RB=F", "ticker_tradingview": "NYMEX:RBOB1!", "name": "Gasoline RBOB", "region": ["US"], "prompt": EN_ENERGY_LONG_SHORT_PROMPT, "factors": EN_ENERGY_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EN", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HO=F", "ticker_tradingview": "NYMEX:HO1!", "name": "Heating Oil", "region": ["US"], "prompt": EN_ENERGY_LONG_SHORT_PROMPT, "factors": EN_ENERGY_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EN", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "QA=F", "ticker_tradingview": "NYMEX:QA1!", "name": "Crude Oil Oman", "region": ["Middle East", "Asia"], "prompt": EN_ENERGY_LONG_SHORT_PROMPT, "factors": EN_ENERGY_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EN", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "D1N=F", "ticker_tradingview": "NYMEX:HH1!", "name": "Henry Hub Natural Gas", "region": ["US"], "prompt": EN_ENERGY_LONG_SHORT_PROMPT, "factors": EN_ENERGY_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EN", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "MTF=F", "ticker_tradingview": "ICE:MTF1!", "name": "TTF Natural Gas (Netherlands)", "region": ["Europe"], "prompt": EN_ENERGY_LONG_SHORT_PROMPT, "factors": EN_ENERGY_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EN", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZC=F", "ticker_tradingview": "CFE:ZC", "name": "China Thermal Coal (Zhengzhou)", "region": ["China"], "prompt": EN_ENERGY_LONG_SHORT_PROMPT, "factors": EN_ENERGY_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "EN", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False}
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
        {"ticker": "GC=F", "ticker_tradingview": "COMEX:GC1!", "name": "Gold", "region": ["Global"], "prompt": ME_METALS_LONG_SHORT_PROMPT, "factors": ME_METALS_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "ME", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SI=F", "ticker_tradingview": "COMEX:SI1!", "name": "Silver", "region": ["Global"], "prompt": ME_METALS_LONG_SHORT_PROMPT, "factors": ME_METALS_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "ME", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PL=F", "ticker_tradingview": "NYMEX:PL1!", "name": "Platinum", "region": ["Global"], "prompt": ME_METALS_LONG_SHORT_PROMPT, "factors": ME_METALS_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "ME", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "PA=F", "ticker_tradingview": "NYMEX:PA1!", "name": "Palladium", "region": ["Global"], "prompt": ME_METALS_LONG_SHORT_PROMPT, "factors": ME_METALS_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "ME", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HG=F", "ticker_tradingview": "COMEX:HG1!", "name": "Copper", "region": ["Global"], "prompt": ME_METALS_LONG_SHORT_PROMPT, "factors": ME_METALS_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "ME", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ALI=F", "ticker_tradingview": "LME:AL", "name": "Aluminium", "region": ["Global"], "prompt": ME_METALS_LONG_SHORT_PROMPT, "factors": ME_METALS_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "ME", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZN=F", "ticker_tradingview": "LME:ZN", "name": "Zinc", "region": ["Global"], "prompt": ME_METALS_LONG_SHORT_PROMPT, "factors": ME_METALS_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "ME", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
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
        {"ticker": "ZC=F", "ticker_tradingview": "CME:ZC1!", "name": "Corn (US)", "region": ["US"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZW=F", "ticker_tradingview": "CME:ZW1!", "name": "Wheat (US)", "region": ["US"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZS=F", "ticker_tradingview": "CME:ZS1!", "name": "Soybeans (US)", "region": ["US"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CC=F", "ticker_tradingview": "ICE:CC1!", "name": "Cocoa", "region": ["Global"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "KC=F", "ticker_tradingview": "ICE:KC1!", "name": "Coffee", "region": ["Global"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "SB=F", "ticker_tradingview": "ICE:SB1!", "name": "Sugar", "region": ["Global"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "CT=F", "ticker_tradingview": "ICE:CT1!", "name": "Cotton", "region": ["Global"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "OJ=F", "ticker_tradingview": "ICE:OJ1!", "name": "Orange Juice", "region": ["US"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 3, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZCN=F", "ticker_tradingview": "DCE:C", "name": "China Corn (DCE)", "region": ["China"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZWN=F", "ticker_tradingview": "DCE:W", "name": "China Wheat (DCE)", "region": ["China"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "ZSN=F", "ticker_tradingview": "DCE:S", "name": "China Soybeans (DCE)", "region": ["China"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "XU=F", "ticker_tradingview": "ASX:WHEAT", "name": "Australia Wheat (ASX)", "region": ["Australia"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "XSB=F", "ticker_tradingview": "ASX:SB", "name": "Australia Sugar (ASX)", "region": ["Australia"], "prompt": AG_AGRICULTURE_LONG_SHORT_PROMPT, "factors": AG_AGRICULTURE_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "AG", "importance": 3, "recurrence": "multi", "decimal":2, "document_generated": False}
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


def insert_livestock_commodities(db):
    """
    Inserts livestock commodities into the 'tickers' collection.
    
    Args:
        db: MongoDB database object
        
    Returns:
        bool: True if insertion was successful, False on error
    """
    collection_name = 'tickers'
    
    print()
    print("=" * 100)
    print(f"Inserting livestock commodities into '{collection_name}' collection...")
    print("=" * 100)
    print()
    
    # Import prompts from _config
    from _config import LI_LIVESTOCK_LONG_SHORT_PROMPT, LI_LIVESTOCK_FACTORS_PROMPT
    
    # Livestock commodities data to insert with prompt and model_function fields
    livestock_commodities = [
        {"ticker": "LE=F", "ticker_tradingview": "CME:LE1!", "name": "Live Cattle (US)", "region": ["US"], "prompt": LI_LIVESTOCK_LONG_SHORT_PROMPT, "factors": LI_LIVESTOCK_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "LI", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "HE=F", "ticker_tradingview": "CME:HE1!", "name": "Lean Hogs (US)", "region": ["US"], "prompt": LI_LIVESTOCK_LONG_SHORT_PROMPT, "factors": LI_LIVESTOCK_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "LI", "importance": 5, "recurrence": "multi", "decimal":2, "document_generated": False},
        {"ticker": "GF=F", "ticker_tradingview": "CME:GF1!", "name": "Feeder Cattle (US)", "region": ["US"], "prompt": LI_LIVESTOCK_LONG_SHORT_PROMPT, "factors": LI_LIVESTOCK_FACTORS_PROMPT, "model_function": "run_holistic_market_model", "model_name":"holistic", "asset_class": "LI", "importance": 4, "recurrence": "multi", "decimal":2, "document_generated": False},
    ]
    
    try:
        collection = db[collection_name]
        
        # Check if any livestock commodities already exist to avoid duplicates
        existing_count = collection.count_documents({"ticker": {"$in": [item["ticker"] for item in livestock_commodities]}})
        if existing_count > 0:
            print(f"Found {existing_count} existing livestock commodities. Skipping insertion to avoid duplicates.")
            return True
        
        # Insert all livestock commodities
        result = collection.insert_many(livestock_commodities)
        print(f"Successfully inserted {len(result.inserted_ids)} livestock commodities into '{collection_name}' collection")
        return True
        
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed for inserting livestock commodities", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error inserting livestock commodities", "DATA_INSERTION", e)
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
    pipeline_data = [
        {"model_function": "run_sector_rotation_model", "model_name": "sector_rotation_long_short", "recurrence":"multi", "task_completed": False},     
        {"model_function": "run_regional_rotation_model", "model_name": "regional_rotation_long_short", "recurrence":"multi", "task_completed": False}
    ]
    
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
        {"Code": "FX", "Description": "Foreign Exchange Pairs"},
        {"Code": "EQ", "Description": "Equities and Stocks"},
        {"Code": "IX", "Description": "Stock Indices"},
        {"Code": "EN", "Description": "Energy Commodities"},
        {"Code": "ME", "Description": "Metal Commodities"},
        {"Code": "AG", "Description": "Agricultural Commodities"},
        {"Code": "LI", "Description": "Livestock Commodities"},
        {"Code": "CR", "Description": "Cryptocurrencies"}
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
        # Fetch MongoDB connection details from environment variables
        config = {
            'host': os.getenv("MONGODB_HOST", "localhost"),
            'port': int(os.getenv("MONGODB_PORT", "27017")),
            'database': os.getenv("MONGODB_DATABASE", "alphagora"),
            'username': os.getenv("MONGODB_USERNAME"),
            'password': os.getenv("MONGODB_PASSWORD"),
            'auth_source': os.getenv("MONGODB_AUTH_SOURCE", "admin")
        }
        
        # Construct URI
        if config['username'] and config['password']:
            uri = f"mongodb://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?authSource={config['auth_source']}"
        else:
            uri = f"mongodb://{config['host']}:{config['port']}/{config['database']}"
        
        # Use context manager for client
        with MongoClient(uri) as client:
            db = client[config['database']]
            
            # Define sequential operations as a list of functions
            operations = [
                create_documents_collection,
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
                insert_livestock_commodities,
                insert_crypto_assets,
                create_weight_factors_collection
            ]
            
            # Execute operations sequentially, passing db to each
            for op in operations:
                if not op(db):
                    log_error("Failed during sequential operation", "DATABASE_SETUP", None)
                    return False
            
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
    print("-" * 50)
    
    success = create_alphagora_database()
    
    if success:
        print("-" * 50)
        print("Database setup completed successfully!")
    else:
        print("-" * 50)
        print("Database setup failed. Please check the error messages above.")
        sys.exit(1)