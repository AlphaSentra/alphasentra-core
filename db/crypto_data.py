import pymongo
from logging_utils import log_error
from _config import CR_CRYPTO_LONG_SHORT_PROMPT, CR_CRYPTO_FACTORS_PROMPT

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