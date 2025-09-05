"""
Project:     Alphagora Trading System
File:        score_models.py
Author:      Daiviet Huynh
Created:     2025-08-27
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Run the Generative AI model to score and recommend trades based on various data inputs.
"""

import os
import sys
import json
import threading
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from _config import WEIGHTS, WEIGHTS_PERCENT, SECTOR_ETFS  # Import configuration variables


load_dotenv() # Load environment variables from .env file

# Load AI model prompts from environment variables
SECTOR_ROTATION_LONG_SHORT_PROMPT = os.getenv("SECTOR_ROTATION_LONG_SHORT_PROMPT")
REGIONAL_ROTATION_LONG_ONLY_PROMPT = os.getenv("REGIONAL_ROTATION_LONG_ONLY_PROMPT")
FX_LONG_SHORT_PROMPT = os.getenv("FX_LONG_SHORT_PROMPT")
DEFAULT_PROMPT = os.getenv("DEFAULT_PROMPT")

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # Set your Gemini key in environment variable

# Set up the Gemini 2.5 Pro model
model = genai.GenerativeModel(os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-pro"))

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
    print("\rAI response generated.          ", end="", flush=True)
    print()  # Move to next line

def get_gen_ai_response(tickers, model_strategy):
    """
    Generate investment recommendations based on AI analysis of market indicators.
    
    Parameters:
    tickers (list): List of ticker symbols to analyze
    model_strategy (str): Strategy to use for analysis. Options:
        - "sector_rotation_long_short"
        - "regional_rotation_long_only"
        - "fx_long_short"
        - Any other string for default analysis
    
    Returns:
    str: AI-generated response with trade recommendations
    """
    
    print("\n=== Model: "+ model_strategy +" using "+ os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-pro") +" ===")

    # Create a comma-separated string of tickers for the prompt
    tickers_str = ", ".join(tickers) if tickers else "No tickers provided"
    
    # Define prompts for different strategies
    if model_strategy == "sector_rotation_long_short":
        prompt = SECTOR_ROTATION_LONG_SHORT_PROMPT.format(
            tickers_str=tickers_str,
            geopolitical_weight=WEIGHTS_PERCENT['Geopolitical'],
            macroeconomic_weight=WEIGHTS_PERCENT['Macroeconomics'],
            technical_sentiment_weight=WEIGHTS_PERCENT['Technical_Sentiment'],
            liquidity_weight=WEIGHTS_PERCENT['Liquidity'],
            earnings_weight=WEIGHTS_PERCENT['Earnings'],
            business_cycle_weight=WEIGHTS_PERCENT['Business_Cycle'],
            sentiment_surveys_weight=WEIGHTS_PERCENT['Sentiment_Surveys']
        )
        
    elif model_strategy == "regional_rotation_long_only":
        prompt = REGIONAL_ROTATION_LONG_ONLY_PROMPT.format(
            tickers_str=tickers_str,
            geopolitical_weight=WEIGHTS_PERCENT['Geopolitical'],
            macroeconomic_weight=WEIGHTS_PERCENT['Macroeconomics'],
            technical_sentiment_weight=WEIGHTS_PERCENT['Technical_Sentiment'],
            liquidity_weight=WEIGHTS_PERCENT['Liquidity'],
            earnings_weight=WEIGHTS_PERCENT['Earnings'],
            business_cycle_weight=WEIGHTS_PERCENT['Business_Cycle'],
            sentiment_surveys_weight=WEIGHTS_PERCENT['Sentiment_Surveys']
        )
        
    elif model_strategy == "fx_long_short":
        prompt = FX_LONG_SHORT_PROMPT.format(
            tickers_str=tickers_str,
            geopolitical_weight=WEIGHTS_PERCENT['Geopolitical'],
            macroeconomic_weight=WEIGHTS_PERCENT['Macroeconomics'],
            technical_sentiment_weight=WEIGHTS_PERCENT['Technical_Sentiment'],
            liquidity_weight=WEIGHTS_PERCENT['Liquidity'],
            earnings_weight=WEIGHTS_PERCENT['Earnings'],
            business_cycle_weight=WEIGHTS_PERCENT['Business_Cycle'],
            sentiment_surveys_weight=WEIGHTS_PERCENT['Sentiment_Surveys']
        )
        
    else:  # Default strategy
        prompt = DEFAULT_PROMPT.format(
            tickers_str=tickers_str,
            geopolitical_weight=WEIGHTS_PERCENT['Geopolitical'],
            macroeconomic_weight=WEIGHTS_PERCENT['Macroeconomics'],
            technical_sentiment_weight=WEIGHTS_PERCENT['Technical_Sentiment'],
            liquidity_weight=WEIGHTS_PERCENT['Liquidity'],
            earnings_weight=WEIGHTS_PERCENT['Earnings'],
            business_cycle_weight=WEIGHTS_PERCENT['Business_Cycle'],
            sentiment_surveys_weight=WEIGHTS_PERCENT['Sentiment_Surveys']
        )
    
    # Run prompt and return response
    try:
        # Create a thread for the progress indicator
        progress_thread = threading.Thread(target=_show_progress)
        progress_thread.stop_progress = False
        
        # Start the progress indicator
        progress_thread.start()
        
        # Generate content (this will block until completion)
        response = model.generate_content(prompt)
        
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

# Example usage (can be removed or commented out in production)
if __name__ == "__main__":
    # List available models
    print("Available models:")
    for model_info in genai.list_models():
        if "generateContent" in model_info.supported_generation_methods:
            print(f"- {model_info.name}: {model_info.display_name}")
    
    # Testing the function
    sample_tickers = SECTOR_ETFS
    result = get_gen_ai_response(sample_tickers, "sector_rotation_long_short")
    print(result)