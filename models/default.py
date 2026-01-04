
from helpers import DatabaseManager
import os

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
