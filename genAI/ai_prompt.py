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
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


load_dotenv() # Load environment variables from .env file

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

    # Create client instance with a randomly selected API key for each call
    api_key = get_random_api_key()
    print(f"API Key: {api_key}")
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=600000))

    # Run prompt and return response
    try:
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
                    "temperature": 0.0,
                    "top_p": 0.95,
                    "max_output_tokens": 10000
            },
        )
        
        # Stop the progress indicator
        progress_thread.stop_progress = True
        progress_thread.join()
        
        return response.text
    except Exception as e:
        # Make sure to stop the progress indicator even if there's an error
        if 'progress_thread' in locals():
            progress_thread.stop_progress = True
            progress_thread.join()
        return f"Error generating content: {str(e)}"
    