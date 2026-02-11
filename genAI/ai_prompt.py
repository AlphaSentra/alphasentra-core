"""
Description:
Functions to interact with Google's Gemini generative AI models.
"""

import os
import sys
import threading
import time
import random
import ast
import gc
from google import genai
from google.genai import types
from dotenv import load_dotenv


# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


load_dotenv() # Load environment variables from .env file

from helpers import DatabaseManager # Import DatabaseManager
from logging_utils import log_error, log_info # Import logging utilities

# Load AI model prompts from environment variables
DEFAULT_PROMPT = os.getenv("DEFAULT_PROMPT")

def get_random_api_key():
    """
    Get a random API key from the GEMINI_API_KEY comma-separated string stored in environment variables.
    Returns:
    str: A randomly selected API key from the list
    """
    
    api_keys_str = ""

    if not api_keys_str:
        api_keys_str = os.getenv("GEMINI_API_KEY")
    
    try:
        # Split the comma-separated string into a list of API keys
        api_keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]
        if len(api_keys) == 0:
            raise ValueError("GEMINI_API_KEY must contain at least one API key in a comma-separated format")
        
        # Randomly select one API key from the list
        return random.choice(api_keys)
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Invalid GEMINI_API_KEY format: {e}")

# Get model names from environment variables
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")

def _show_progress(batch_mode=False):
    """
    Display a simple progress indicator while waiting for the AI model response.
    """
    if not batch_mode:
        chars = "|/-\\"
        idx = 0
        while not threading.current_thread().stop_progress:
            print(f"\rGenerating AI response... {chars[idx % len(chars)]}", end="", flush=True)
            idx += 1
            time.sleep(0.1)
        print("\rAI response generated.", end="", flush=True)
        print()  # Move to next line

def get_gen_ai_response(tickers, model_strategy, prompt=None, gemini_model=None, batch_mode=False):
    """
    Description:
    This function generates a response from the Gemini generative AI model based on the provided parameters.

    Parameters:
    - tickers (list): A list of stock tickers to be included in the AI prompt.
    - model_strategy (str): The strategy to be used for the AI model (e.g., "Flash" or "Pro").
    - prompt (str, optional): A custom prompt string to override the default. Defaults to None.
    - gemini_model (str, optional): The specific Gemini model to use. Defaults to None, which means the default model based on the strategy will be used.
    - batch_mode (bool, optional): A flag indicating whether the function is running in batch mode. Defaults to False.

    Returns:
    - str: The AI model's generated response text, or an error message if an issue occurs.

    Raises:
    - ValueError: If the GEMINI_API_KEY is not configured correctly or is invalid.
    - Exception: For any other errors during the AI response generation process.

    Note:
    - This function also increments the `ai_prompt_count` in the `settings` collection and checks against `max_daily_ai_prompt_count`.
    If the limit is reached, it returns an error message without calling the AI model.
    """
    # Increment ai_prompt_count in the settings collection
    try:
        client = DatabaseManager().get_client()
        db_name = os.getenv("MONGODB_DATABASE", "alphasentra-core")
        db = client[db_name]
        settings_collection = db['settings']

        # Retrieve settings to check prompt count against daily limit
        batch_settings = settings_collection.find_one({"key": "batch_settings", "value": "default"})
        if batch_settings:
            current_ai_prompt_count = batch_settings.get("ai_prompt_count", 0)
            max_daily_ai_prompt_count = batch_settings.get("max_daily_ai_prompt_count")

            if max_daily_ai_prompt_count is not None and current_ai_prompt_count >= max_daily_ai_prompt_count:
                error_message = f"Daily AI prompt limit reached ({current_ai_prompt_count}/{max_daily_ai_prompt_count})."
                log_error(error_message, "AI_PROMPT_LIMIT_REACHED", None)
                return error_message # Return early if limit is reached

        settings_collection.update_one(
            {
                "key": "batch_settings",
                "value": "default"
            },
            {
                "$inc": {
                    "ai_prompt_count": 1
                }
            }
        )
        log_info("Incremented ai_prompt_count in settings collection.")
    except Exception as e:
        log_error(f"Error incrementing ai_prompt_count: {e}", "AI_PROMPT_COUNT_INCREMENT", e)

    """
    Get a response from the Gemini generative AI model based on the selected strategy.
    Parameters:
    tickers (list): List of stock tickers to include in the prompt
    model_strategy (str): The strategy to use ("Flash" or "Pro")
    prompt (str, optional): Custom prompt to use. If None, uses DEFAULT_PROMPT from environment variables.
    gemini_model (str, optional): Specific Gemini model to use. If None, uses default model based on strategy.
    Returns:
    str: The AI model's response text
    """
    # If no model is specified, use the default model from environment variables
    if gemini_model is None:
        gemini_model = os.getenv("GEMINI_DEFAULT", "gemini-2.5-flash-lite")
    
    tickers_str = tickers if isinstance(tickers, str) else ', '.join([str(t) for t in tickers])
    print(f"\033[94m\n=== Model: {model_strategy} using {gemini_model} === ticker: {tickers_str} ===\033[0m")

    client = None
    progress_thread = None
    # "Clean Slate" Method: Create a new client for each request.
    try:
        # Create client instance with a randomly selected API key for each call
        api_key = get_random_api_key()
        print(f"API Key: {api_key}")
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=600000))

        # Create a thread for the progress indicator
        progress_thread = threading.Thread(target=lambda: _show_progress(batch_mode))
        progress_thread.stop_progress = False
        
        # Start the progress indicator
        progress_thread.start()
        
        # Generate content with google search grounding (this will block until completion)
        response = client.models.generate_content(
            model=gemini_model,
            contents=prompt,
            config={
                    "tools": [{"google_search": {}}],
                    "temperature": 0.1,
                    "thinking_config": {
                                "thinking_budget": 0    #0 is disabled, -1 is default, Range from 1 to 24576  
                    },
                    "safety_settings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"}
                    ]                    
            },
        )
        
        # Stop the progress indicator
        progress_thread.stop_progress = True
        progress_thread.join()
        
        return response.text
    except Exception as e:
        # Make sure to stop the progress indicator even if there's an error
        if progress_thread and progress_thread.is_alive():
            progress_thread.stop_progress = True
            progress_thread.join()
        return f"Error generating content: {str(e)}"
    finally:
        # "Clean Slate" Method: Destroy the client after each use to ensure
        # that no client-side state is carried over between calls and that
        # all resources are properly released.
        if client:
            # In Python, deleting the reference is a way to signal that the
            # object can be garbage collected. If the client had a close()
            # method, it would be called here. As of this implementation,
            # the genai.Client does not have an explicit close() method.
            del client
        # Force garbage collection to release memory immediately.
        gc.collect()
