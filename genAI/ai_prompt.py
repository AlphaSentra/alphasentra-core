"""
Description:
Functions to interact with Google's Gemini generative AI models.
"""

import os
import sys
import threading
import time
from google import genai
from dotenv import load_dotenv

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


load_dotenv() # Load environment variables from .env file

# Load AI model prompts from environment variables
DEFAULT_PROMPT = os.getenv("DEFAULT_PROMPT")

# Get the API key from the environment
api_key = os.getenv("GEMINI_API_KEY")

# Get model names from environment variables
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")

def _show_progress():
    """
    Display a simple progress indicator while waiting for the AI model response.
    """
    chars = "|/-\\"
    idx = 0
    while not threading.current_thread().stop_progress:
        print(f"\rGenerating AI response... {chars[idx % len(chars)]}", end="", flush=True)
        idx += 1
        time.sleep(0.1)
    print("\rAI response generated.", end="", flush=True)
    print()  # Move to next line

def get_gen_ai_response(tickers, model_strategy, prompt=None, gemini_model=None):
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
        gemini_model = os.getenv("GEMINI_DEFAULT", "gemini-2.5-pro")
    
    print("\n=== Model: "+ model_strategy +" using "+ gemini_model +" ===")

    # Create client instance
    client = genai.Client()

    # Run prompt and return response
    try:
        # Create a thread for the progress indicator
        progress_thread = threading.Thread(target=_show_progress)
        progress_thread.stop_progress = False
        
        # Start the progress indicator
        progress_thread.start()
        
        # Generate content with google search grounding (this will block until completion)
        response = client.models.generate_content(
            model=gemini_model,
            contents=prompt,
            config={"tools": [{"google_search": {}}]},
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
    