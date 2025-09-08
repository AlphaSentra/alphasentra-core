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


load_dotenv() # Load environment variables from .env file

# Load AI model prompts from environment variables
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
    print("\rAI response generated.", end="", flush=True)
    print()  # Move to next line

def get_gen_ai_response(tickers, model_strategy, prompt=None):
    
    print("\n=== Model: "+ model_strategy +" using "+ os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-pro") +" ===")


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
    
def factcheck_market_outlook(market_outlook_narrative):
    """
    Factcheck the market outlook narrative using the AI model.
    
    Args:
        market_outlook_narrative (list): List of paragraphs in the market outlook narrative
    
    Returns:
        str: 'accurate' if the narrative is accurate, 'inaccurate' otherwise
    """
    from dotenv import load_dotenv
    import os
    import json
    
    # Load environment variables
    load_dotenv()
    
    # Get the factcheck prompt from environment variables
    FACTCHECK_AI_RESPONSE = os.getenv("FACTCHECK_AI_RESPONSE")
    
    if not FACTCHECK_AI_RESPONSE:
        print("Warning: FACTCHECK_AI_RESPONSE prompt not found in environment variables")
        return "accurate"  # Default to accurate if prompt is not available
    
    # Join the narrative paragraphs into a single string
    market_outlook_narrative_str = " ".join(market_outlook_narrative)
    
    # Format the prompt with the market outlook narrative
    factcheck_prompt = FACTCHECK_AI_RESPONSE.format(
        market_outlook_narrative_str=market_outlook_narrative_str
    )
    
    try:
        # Get AI factcheck response
        factcheck_response = get_gen_ai_response([], "factcheck", factcheck_prompt)
        
        # Try to parse the response as JSON
        try:
            # Remove any markdown code block markers if present
            if factcheck_response.startswith("```json"):
                factcheck_response = factcheck_response[7:]
            if factcheck_response.endswith("```"):
                factcheck_response = factcheck_response[:-3]
            
            # Parse JSON
            factcheck_result = json.loads(factcheck_response)
            
            # Return the factcheck result
            return factcheck_result.get("factcheck", "accurate")
        except json.JSONDecodeError:
            print(f"Error parsing factcheck response as JSON: {factcheck_response}")
            return "accurate"  # Default to accurate if parsing fails
    except Exception as e:
        print(f"Error factchecking market outlook: {e}")
        return "accurate"  # Default to accurate if there's any error

# Example usage (can be removed or commented out in production)
if __name__ == "__main__":
    # List available models
    print("Available models:")
    for model_info in genai.list_models():
        if "generateContent" in model_info.supported_generation_methods:
            print(f"- {model_info.name}: {model_info.display_name}")