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
        
        # Collection name
        collection_name = 'documents'
        
        # Check if collection already exists
        if collection_name in db.list_collection_names():
            print(f"Collection '{collection_name}' already exists. Skipping creation.")
            return True
        
        # Create collection with schema validation
        validator = {
            '$jsonSchema': {
                'bsonType': 'object',
                'required': [
                    'market_outlook_narrative',
                    'rationale',
                    'analysis',
                    'sources',
                    'recommendations',
                    'sentiment_score',
                    'timestamp_gmt',
                    'language_code'
                ],
                'properties': {
                    'title': {
                        'bsonType': 'string',
                                            },
                    'market_outlook_narrative': {
                        'bsonType': 'array',
                        'items': {
                            'bsonType': 'string'
                        },
                                            },
                    'rationale': {
                        'bsonType': 'string',
                                            },
                    'analysis': {
                        'bsonType': 'string',
                                            },
                    'sources': {
                        'bsonType': 'array',
                        'items': {
                            'bsonType': 'object',
                            'required': ['source_name', 'source_title'],
                            'properties': {
                                'source_name': {
                                    'bsonType': 'string',
                                                                    },
                                'source_title': {
                                    'bsonType': 'string',
                                                                    }
                            }
                        },
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
                                    'bsonType': 'string',
                                                                    },
                                'trade_direction': {
                                    'bsonType': 'string',
                                                                    },
                                'bull_bear_score': {
                                    'bsonType': 'int',
                                    'minimum': -100,
                                    'maximum': 100,
                                                                    },
                                'stop_loss': {
                                    'bsonType': 'double',
                                                                    },
                                'target_price': {
                                    'bsonType': 'double',
                                                                    },
                                'entry_price': {
                                    'bsonType': 'double',
                                                                    },
                                'price': {
                                    'bsonType': 'double',
                                                                    }
                            }
                        },
                                            },
                    'sentiment_score': {
                        'bsonType': 'double',
                        'minimum': -1.0,
                        'maximum': 1.0,
                                            },
                    'timestamp_gmt': {
                        'bsonType': 'string',
                        'pattern': '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d+)?Z$',
                                            },
                    'language_code': {
                        'bsonType': 'string',
                        'pattern': '^[a-z]{2}(-[A-Z]{2})?$',
                                            }
                }
            }
        }
        
        # Create collection with validation
        db.create_collection(
            collection_name,
            validator=validator
        )
        
        # Create indexes for better query performance
        collection = db[collection_name]
        collection.create_index([('timestamp_gmt', pymongo.DESCENDING)])
        collection.create_index([('sentiment_score', pymongo.DESCENDING)])
        collection.create_index([('language_code', pymongo.ASCENDING)])
        collection.create_index([('recommendations.ticker', pymongo.ASCENDING)])
        
        print(f"Successfully created database 'alphagora' with collection '{collection_name}'")
        print("Collection schema validation rules applied:")
        print("   - Required fields: market_outlook_narrative, rationale, analysis, sources, recommendations, sentiment_score, timestamp_gmt, language_code")
        print("   - Optional field: title")
        print("   - Indexes created: timestamp_gmt, sentiment_score, language_code")
        
        return True
        
    except pymongo.errors.ServerSelectionTimeoutError:
        print("MongoDB server not found. Please ensure MongoDB is running on localhost:27017")
        return False
    except pymongo.errors.OperationFailure as e:
        print(f"MongoDB operation failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
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
    print("Collection: documents")
    print("-" * 50)
    
    success = create_alphagora_database()
    
    if success:
        print("-" * 50)
        print("Database setup completed successfully!")
    else:
        print("-" * 50)
        print("Database setup failed. Please check the error messages above.")
        sys.exit(1)