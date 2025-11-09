"""
Description:
Script to create MongoDB database 'alphasentra-core'.
"""

import pymongo
from db.fx_data import insert_fx_pairs
from db.equities_data import insert_equities
from db.indices_data import insert_indices
from db.energy_data import insert_energy_commodities
from db.metal_data import insert_metal_commodities
from db.agriculture_data import insert_agriculture_commodities
from db.crypto_data import insert_crypto_assets
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
        {"model_function": "get_high_conviction_buys", "task_completed": False, "model_name": "hcb", "recurrence": "multi"},
        {"model_function": "unflag_hcb_pipeline_task", "task_completed": False, "model_name": "hcb", "recurrence": "multi"}

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
            create_pipeline_collection,
            create_asset_classes_collection,
            insert_asset_classes_data,
            insert_fx_pairs,
            #insert_indices,
            insert_energy_commodities,
            insert_metal_commodities,
            insert_agriculture_commodities,
            insert_crypto_assets,
            insert_equities,
            insert_pipeline_data,
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