"""
Description:
Script to create MongoDB database 'alphagora'.
"""

import pymongo
from db.fx_data import insert_fx_pairs
from db.equities_data import insert_equities
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