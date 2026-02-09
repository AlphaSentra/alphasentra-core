
from helpers import DatabaseManager
import os
from models.montecarlo import run_monte_carlo_simulation
from logging_utils import log_info, log_warning, log_error

def get_insights():
    """
    Retrieves the model names from the pipeline collection where the task_completed field is false,
    and for each model name, finds the corresponding ticker in the tickers collection and sets
    the 'document_generated' field to False. After which, it sets the 'task_completed' field to True
    for the corresponding document in the pipeline collection.
    """
    db_manager = DatabaseManager()
    client = db_manager.get_client()
    db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
    pipeline_collection = db["pipeline"]
    tickers_collection = db["tickers"]

    model_names = []
    # Find all documents where task_completed is False and get the model_name
    for doc in pipeline_collection.find({"task_completed": False}):
        if "model_name" in doc:
            model_names.append(doc["model_name"])

    # If there are any model names, update the corresponding tickers
    if model_names:
        tickers_collection.update_many(
            {"ticker": {"$in": model_names}},
            {"$set": {"document_generated": False}}
        )
        
        # Once the tickers are updated, update the pipeline collection
        pipeline_collection.update_many(
            {"model_name": {"$in": model_names}},
            {"$set": {"task_completed": True}}
        )

def test_trade():
    """
    A placeholder function for testing trade functionality.
    Currently, it does not perform any operations.
    """
    db_manager = DatabaseManager()
    client = db_manager.get_client()
    db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
    pipeline_collection = db["pipeline"]

    # Find the first document where task_completed is False
    document = pipeline_collection.find_one({"task_completed": False})

    # Variables to store retrieved data, matching requested keys structure
    ticker = ""
    sessionID = ""
    initial_price = 0.0
    strategy = "l"
    target_price = 0.0
    stop_loss = 0.0
    volatility = 0.0
    drift = 0.0
    time_horizon = 0.0
    num_simulations = 0

    if document:
        # Retrieve and assign values to variables (Model name is used as ticker for update)
        ticker = document.get("model_name", "")
        sessionID = document.get("sessionID", "")
        initial_price = document.get("initial_price", 0.0)
        strategy_short = document.get("strategy", "l") # Use temporary name for 'l'/'s'
        target_price = document.get("target_price", 0.0)
        stop_loss = document.get("stop_loss", 0.0)
        volatility = document.get("volatility", 0.0)
        drift = document.get("drift", 0.0)
        time_horizon = document.get("time_horizon", 0.0)
        num_simulations = document.get("num_simulations", 0)
        
        # Map strategy 'l' to 'long' as required by run_monte_carlo_simulation
        strategy_full = "long" if strategy_short.lower() == "l" else "short"
        
        log_info(f"Successfully gathered data for model: {ticker} (Session: {sessionID}, Strategy: {strategy_full})")

        try:
            # 1. Run Monte Carlo Simulation
            simulation_metrics = run_monte_carlo_simulation(
                sessionID=sessionID, 
                ticker=ticker, 
                initial_price=initial_price, 
                strategy=strategy_full, 
                target_price=target_price, 
                stop_loss=stop_loss, 
                volatility=volatility, 
                drift=drift, 
                time_horizon=time_horizon, 
                num_simulations=num_simulations
            )
            log_info(f"Simulation for {ticker} completed. EV: ${simulation_metrics.get('expected_value'):.4f}")
            
            # 2. Update pipeline collection status
            update_result = pipeline_collection.update_one(
                {"model_name": ticker}, # Assuming model_name is unique identifier for the pending task
                {"$set": {"task_completed": True}}
            )
            
            if update_result.modified_count > 0:
                log_info(f"Successfully marked task for model {ticker} as completed.")
            else:
                log_warning(f"Could not find or update task for model {ticker} to completed=True. It might have already been processed.")

        except Exception as e:
            log_error(f"Error during Monte Carlo simulation or status update for {ticker}: {e}", "DEFAULT_TEST_TRADE")

    else:
        log_info("No pending documents found in 'pipeline' collection where task_completed is False.")