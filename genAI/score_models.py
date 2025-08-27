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
import google.generativeai as genai
from dotenv import load_dotenv

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from _config import AI_MODEL_PROMPTS

load_dotenv() # Load environment variables from .env file

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # Set your Gemini key in environment variable

# Set up the Gemini 2.5 Pro model
model = genai.GenerativeModel("gemini-2.5-flash")

def score_model(tickers, model_strategy):
    """
    Generate investment recommendations based on AI analysis of market indicators.
    
    Parameters:
    tickers (list): List of ticker symbols to analyze
    model_strategy (str): Strategy to use for analysis. Options:
        - "sector_rotation_long_only"
        - "regional_rotation_long_only"
        - "fx_long_short"
        - Any other string for default analysis
    
    Returns:
    str: AI-generated response with trade recommendations
    """
    
    # Create a comma-separated string of tickers for the prompt
    tickers_str = ", ".join(tickers) if tickers else "No tickers provided"
    
    # Define prompts for different strategies
    if model_strategy == "sector_rotation_long_only":
        prompt = AI_MODEL_PROMPTS["sector_rotation_long_only"].format(tickers_str=tickers_str)
        
    elif model_strategy == "regional_rotation_long_only":
        prompt = AI_MODEL_PROMPTS["regional_rotation_long_only"].format(tickers_str=tickers_str)
        
    elif model_strategy == "fx_long_short":
        prompt = AI_MODEL_PROMPTS["fx_long_short"].format(tickers_str=tickers_str)
        
    else:  # Default strategy
        prompt = AI_MODEL_PROMPTS["default"].format(tickers_str=tickers_str)
    
    # Run prompt and return response
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating content: {str(e)}"

# Example usage (can be removed or commented out in production)
if __name__ == "__main__":
    # List available models
    print("Available models:")
    for model_info in genai.list_models():
        if "generateContent" in model_info.supported_generation_methods:
            print(f"- {model_info.name}: {model_info.display_name}")
    
    # Testing the function
    print("\n=== Test Prompt ===")
    sample_tickers = ['XLC', 'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU']
    result = score_model(sample_tickers, "sector_rotation_long_only")
    print(result)
