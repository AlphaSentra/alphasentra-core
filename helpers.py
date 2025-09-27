"""
Description:
Helper functions
"""



# --- HELPER FUNCTIONS ---
from data.price import calculate_trade_levels, calculate_entry_price, get_current_price
import os
from dotenv import load_dotenv
import sys


# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from logging_utils import log_error

# Load environment variables
load_dotenv()




def get_trade_recommendations(tickers_with_direction, decimal_digits=2):
    """
    Return trade recommendations including stop loss and target prices in the specified JSON format.
    
    Parameters:
    tickers_with_direction (list): List of dictionaries with 'ticker' and 'trade_direction' keys
    decimal_digits (int): Number of decimal digits for rounding prices (default: 2)
    
    Returns:
    list: Array of objects with 'ticker', 'trade_direction', 'stop_loss', and 'target_price' keys
    """
    
    # Group tickers by trade direction
    long_tickers = []
    short_tickers = []
    
    for item in tickers_with_direction:
        ticker = item.get('ticker')
        direction = item.get('trade_direction', '').upper()
        
        if ticker and direction:
            if direction == 'LONG':
                long_tickers.append(ticker)
            elif direction == 'SHORT':
                short_tickers.append(ticker)
    
    # Calculate stop loss prices for LONG positions
    long_stop_losses = {}
    if long_tickers:
        long_stop_losses = calculate_trade_levels(long_tickers, 'LONG', decimal_digits=decimal_digits)
    
    # Calculate stop loss prices for SHORT positions
    short_stop_losses = {}
    if short_tickers:
        short_stop_losses = calculate_trade_levels(short_tickers, 'SHORT', decimal_digits=decimal_digits)
    
    # Combine all results in the required format
    recommendations = []
    
    for item in tickers_with_direction:
        ticker = item.get('ticker')
        direction = item.get('trade_direction', '').upper()
        
        if ticker and direction:
            stop_loss = None
            target_price = None
            if direction == 'LONG' and ticker in long_stop_losses:
                stop_loss_data = long_stop_losses[ticker]
                stop_loss = round(stop_loss_data['stop_loss'], decimal_digits)
                target_price = round(stop_loss_data['target_price'], decimal_digits)
            elif direction == 'SHORT' and ticker in short_stop_losses:
                stop_loss_data = short_stop_losses[ticker]
                stop_loss = round(stop_loss_data['stop_loss'], decimal_digits)
                target_price = round(stop_loss_data['target_price'], decimal_digits)
        
        recommendations.append({
            'ticker': ticker,
            'trade_direction': direction,
            'stop_loss': stop_loss if stop_loss is not None else 'N/A',
            'target_price': target_price if target_price is not None else 'N/A'
        })
    
    return recommendations


def add_trade_levels_to_recommendations(recommendations, gemini_model=None, decimal_digits=2):
    """
    Add stop loss and target prices to recommendations.
    
    Parameters:
    recommendations (dict): The AI recommendations dictionary
    gemini_model (str, optional): The Gemini model to use for analysis
    decimal_digits (int): Number of decimal digits for rounding prices (default: 2)
    
    Returns:
    dict: The recommendations dictionary with stop loss and target prices added
    """
        
    try:        
        # Check if recommendations has the expected structure
        if 'recommendations' not in recommendations:
            return recommendations
        
        # Group tickers by trade direction
        long_tickers = []
        short_tickers = []
        
        for trade in recommendations['recommendations']:
            ticker = trade.get('ticker')
            direction = trade.get('trade_direction', '').upper()
            
            if ticker and direction:
                if direction == 'LONG':
                    long_tickers.append(ticker)
                elif direction == 'SHORT':
                    short_tickers.append(ticker)
        
        
        # Calculate stop loss prices for LONG positions
        if long_tickers:
            # Get market outlook narrative if available
            long_stop_losses = calculate_trade_levels(long_tickers, 'LONG', decimal_digits=decimal_digits)
            
            # Add stop loss prices to recommendations
            for trade in recommendations['recommendations']:
                if trade.get('trade_direction', '').upper() == 'LONG':
                    ticker = trade.get('ticker')
                    if ticker in long_stop_losses:
                        stop_loss_data = long_stop_losses[ticker]
                        trade['stop_loss'] = round(stop_loss_data['stop_loss'], decimal_digits)
                        trade['target_price'] = round(stop_loss_data['target_price'], decimal_digits)
        
        # Calculate stop loss prices for SHORT positions
        if short_tickers:
            # Get market outlook narrative if available
            short_stop_losses = calculate_trade_levels(short_tickers, 'SHORT', decimal_digits=decimal_digits)
            
            # Add stop loss prices to recommendations
            for trade in recommendations['recommendations']:
                if trade.get('trade_direction', '').upper() == 'SHORT':
                    ticker = trade.get('ticker')
                    if ticker in short_stop_losses:
                        stop_loss_data = short_stop_losses[ticker]
                        trade['stop_loss'] = round(stop_loss_data['stop_loss'], decimal_digits)
                        trade['target_price'] = round(stop_loss_data['target_price'], decimal_digits)
        
        return recommendations
    except Exception as e:
        log_error("Error in add_trade_levels_to_recommendations", "TRADE_LEVELS", e)
        return recommendations



def add_entry_price_to_recommendations(recommendations, gemini_model=None, decimal_digits=2):
    """
    Add entry prices and current prices to recommendations.

    Parameters:
    recommendations (dict): The AI recommendations dictionary
    gemini_model (str, optional): The Gemini model to use for analysis
    decimal_digits (int): Number of decimal digits for rounding prices (default: 2)

    Returns:
    dict: The recommendations dictionary with entry prices and current prices added
    """
        
    try:
        # Debug: Print the recommendations structure
        
        # Check if recommendations has the expected structure
        if 'recommendations' not in recommendations:
            return recommendations
        
        # Get all unique tickers from recommendations
        all_tickers = []
        for trade in recommendations['recommendations']:
            ticker = trade.get('ticker')
            if ticker and ticker not in all_tickers:
                all_tickers.append(ticker)
        
        # Get current prices for all tickers
        current_prices = {}
        for ticker in all_tickers:
            current_price = get_current_price(ticker)
            if current_price is not None:
                current_prices[ticker] = round(current_price, decimal_digits)
        
        # Group tickers by trade direction
        long_tickers = []
        short_tickers = []
        
        for trade in recommendations['recommendations']:
            ticker = trade.get('ticker')
            direction = trade.get('trade_direction', '').upper()
            
            if ticker and direction:
                if direction == 'LONG':
                    long_tickers.append(ticker)
                elif direction == 'SHORT':
                    short_tickers.append(ticker)
        
        # Add current prices to all recommendations
        for trade in recommendations['recommendations']:
            ticker = trade.get('ticker')
            if ticker in current_prices:
                trade['price'] = current_prices[ticker]
        
        # Calculate entry prices for LONG positions
        if long_tickers:
            long_entry_prices = calculate_entry_price(long_tickers, 'LONG')
            
            # Add entry prices to recommendations
            for trade in recommendations['recommendations']:
                if trade.get('trade_direction', '').upper() == 'LONG':
                    ticker = trade.get('ticker')
                    if ticker in long_entry_prices:
                        trade['entry_price'] = round(long_entry_prices[ticker], decimal_digits)
        
        # Calculate entry prices for SHORT positions
        if short_tickers:
            short_entry_prices = calculate_entry_price(short_tickers, 'SHORT')
            
            # Add entry prices to recommendations
            for trade in recommendations['recommendations']:
                if trade.get('trade_direction', '').upper() == 'SHORT':
                    ticker = trade.get('ticker')
                    if ticker in short_entry_prices:
                        trade['entry_price'] = round(short_entry_prices[ticker], decimal_digits)
        
        return recommendations
    except Exception as e:
        log_error("Error in add_entry_price_to_recommendations", "ENTRY_PRICE", e)
        return recommendations
    

def strip_markdown_code_blocks(text):
    """
    Remove markdown code block markers from text and extract JSON content.
    Handles various formats including ```json, ```, and variations with whitespace.
    Also extracts JSON content from the end of response strings when markdown formatting is incomplete.
    """
    import re
    
    if not isinstance(text, str):
        return text
    
    # Pattern to match markdown code blocks with optional language specifier and whitespace
    code_block_pattern = r'^```(?:\w*)\s*\n(.*?)\n```\s*$'
    
    # Try to match full code block pattern first (including trailing whitespace)
    match = re.search(code_block_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # If no full code block found, try to extract JSON from the string
    json_content = extract_json_from_text(text)
    if json_content:
        return json_content
    
    # If no JSON found, try to remove partial markdown markers
    # Remove starting ``` with optional language and whitespace
    text = re.sub(r'^```\w*\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    
    # Remove ending ``` with optional whitespace
    text = re.sub(r'\n?```\s*$', '', text)
    text = re.sub(r'\s*```\s*$', '', text)
    
    return text.strip()


def extract_json_from_text(text):
    """
    Extract JSON content from text, focusing on content at the end of strings.
    Handles various JSON formats and validates the extracted content.
    """
    import re
    import json
    
    if not isinstance(text, str):
        return None
    
    # Strategy: Look for JSON content at the end of the text
    # This handles the most common case where AI responses have JSON at the end
    
    # Pattern 1: Look for complete JSON object at the end
    # This pattern captures complete JSON objects at the end of text
    end_json_pattern = r'(\{(?:[^{}]|\{[^{}]*\})*\})\s*$'
    end_match = re.search(end_json_pattern, text, re.DOTALL)
    if end_match:
        try:
            json_content = end_match.group(1).strip()
            json.loads(json_content)  # Validate it's proper JSON
            return json_content
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Pattern 2: Look for JSON array at the end
    array_pattern = r'(\[.*\])\s*$'
    array_match = re.search(array_pattern, text, re.DOTALL)
    if array_match:
        try:
            json_content = array_match.group(1).strip()
            json.loads(json_content)  # Validate it's proper JSON
            return json_content
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Pattern 3: Look for JSON preceded by common AI response patterns
    # This handles cases like "text: {json}" or "text\n{json}"
    ai_json_patterns = [
        r'(?:analysis|recommendation|result|response|output)[:\s]*(\{.*\})\s*$',
        r'(?:^|\n)[^{}]*(\{.*\})\s*$',
    ]
    
    for pattern in ai_json_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                json_content = match.group(1).strip()
                json.loads(json_content)  # Validate it's proper JSON
                return json_content
            except (json.JSONDecodeError, ValueError):
                continue
    
    # If no JSON found at the end, try to find any valid JSON in the text
    # This is a fallback for cases where JSON might be embedded elsewhere
    json_pattern = r'(\{(?:[^{}]|\{[^{}]*\})*\})'
    json_matches = re.findall(json_pattern, text, re.DOTALL)
    for json_match in reversed(json_matches):  # Try from end to start
        try:
            json_content = json_match.strip()
            json.loads(json_content)  # Validate it's proper JSON
            return json_content
        except (json.JSONDecodeError, ValueError):
            continue
    
    return None
    

def analyze_sentiment(text):
    """
    Analyze sentiment of text using VaderSentiment.
    Returns a sentiment score between 0 (negative) and 1 (positive).
    
    Parameters:
    text (str or list): Text to analyze. Can be a string or list of strings.
    
    Returns:
    float: Sentiment score between 0.0 and 1.0
    """
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    
    # Initialize Vader sentiment analyzer
    analyzer = SentimentIntensityAnalyzer()
    
    # Convert input to list if it's a string
    if isinstance(text, str):
        text = [text]
    
    total_score = 0.0
    
    for paragraph in text:
        if not isinstance(paragraph, str):
            continue
            
        # Get sentiment scores using Vader
        sentiment_scores = analyzer.polarity_scores(paragraph)
        
        # Vader returns a compound score between -1 (most negative) and +1 (most positive)
        # Convert to 0-1 range: (compound_score + 1) / 2
        vader_score = sentiment_scores['compound']
        normalized_score = (vader_score + 1) / 2  # Convert from [-1,1] to [0,1]
        
        total_score += normalized_score
    
    # Calculate average score across all paragraphs
    if len(text) > 0:
        average_score = total_score / len(text)
        # Round to 2 decimal places for cleaner output
        return round(average_score, 2)
    else:
        return 0.5  # Return neutral if no text

def get_current_gmt_timestamp():
    """
    Get the current date and time in GMT timezone.
    
    Returns:
    str: Current timestamp in ISO 8601 format with GMT timezone
    """
    from datetime import datetime, timezone
    
    # Get current UTC time
    current_utc = datetime.now(timezone.utc)
    
    # Format as ISO 8601 with 'Z' for UTC/GMT
    return current_utc.isoformat(timespec='seconds').replace('+00:00', 'Z')

def save_to_db(recommendations):
    """
    Save data to MongoDB collections.
    
    Parameters:
    recommendations (dict): The recommendations dictionary to save
    
    Returns:
    bool: True if successful, False on error
    """
    try:
        import pymongo
        from pymongo import MongoClient
        
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
        
        # Connect to MongoDB
        client = MongoClient(mongodb_uri)
        db = client[mongodb_database]
        collection = db['documents']
        
        # Insert the recommendations document
        result = collection.insert_one(recommendations)
        return True
        
    except pymongo.errors.ServerSelectionTimeoutError:
        log_error("MongoDB server not found. Please ensure MongoDB is running", "MONGODB_CONNECTION", None)
        return False
    except pymongo.errors.OperationFailure as e:
        log_error("MongoDB operation failed", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Unexpected error saving to database", "DATABASE_SAVE", e)
        return False

def get_ai_weights(tickers, factor_weights_prompt, weights_percent, model_name=None):
    """
    Get AI-generated factor weights for market analysis with MongoDB caching.
    Checks if weights exist in database for today's date before calling AI.
    
    Parameters:
    tickers (str or list): The tickers to analyze
    factor_weights_prompt (str): The encrypted factor weights prompt
    weights_percent (dict): Default weights to use as fallback
    model_name (str, optional): The AI model name to use
    
    Returns:
    dict: AI-generated weights or None if error occurs
    """
    import os
    from crypt import decrypt_string
    from genAI.ai_prompt import get_gen_ai_response
    from logging_utils import log_error, log_warning
    import json
    from datetime import datetime, date
    
    # First check if we have cached weights for today in MongoDB
    try:
        import pymongo
        from pymongo import MongoClient
        
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
        
        # Connect to MongoDB
        client = MongoClient(mongodb_uri)
        db = client[mongodb_database]
        collection = db['weight_factors']
        
        # Check if we have weights for today
        today = date.today().isoformat()
        cached_weights = collection.find_one({"date": today})
        
        if cached_weights:
            print("Using cached weights from database")
            return cached_weights['weights']
            
    except Exception as e:
        log_error("Error checking cached weights in MongoDB", "MONGODB_CACHE", e)
        # Continue to generate new weights if cache check fails
    
    # If no cached weights found, generate new ones using AI
    ai_weights = None
    if factor_weights_prompt:
        try:
            # Decrypt FACTOR_WEIGHTS_PROMPT first
            decrypted_factor_weights = decrypt_string(factor_weights_prompt)
            
            # Use default model if not provided
            if model_name is None:
                model_name = os.getenv("GEMINI_PRO_MODEL")
            
            # Call get_gen_ai_response with the decrypted FACTOR_WEIGHTS prompt
            ai_weights_response = get_gen_ai_response(tickers, "factor weights", decrypted_factor_weights, model_name)
            
            # Try to parse the response as JSON
            try:
                # Remove any markdown code block markers if present and extract JSON
                ai_weights_response = strip_markdown_code_blocks(ai_weights_response)
                
                # Parse JSON to get the weights
                ai_weights_raw = json.loads(ai_weights_response)
                print("AI-generated weights:", ai_weights_raw)
                
                # Map AI response keys to the keys used in the main prompt
                ai_weights = {
                    'Geopolitical': ai_weights_raw.get('Geopolitical', weights_percent['Geopolitical']),
                    'Macroeconomics': ai_weights_raw.get('Macroeconomics', weights_percent['Macroeconomics']),
                    'Technical_Sentiment': ai_weights_raw.get('Technical/Sentiment', weights_percent['Technical_Sentiment']),
                    'Liquidity': ai_weights_raw.get('Liquidity', weights_percent['Liquidity']),
                    'Earnings': ai_weights_raw.get('Earnings', weights_percent['Earnings']),
                    'Business_Cycle': ai_weights_raw.get('Business Cycle', weights_percent['Business_Cycle']),
                    'Sentiment_Surveys': ai_weights_raw.get('Sentiment Surveys', weights_percent['Sentiment_Surveys'])
                }
                
                # Store the new weights in MongoDB for future use
                try:
                    collection.insert_one({
                        "date": date.today().isoformat(),
                        "timestamp": datetime.now().isoformat(),
                        "weights": ai_weights,
                        "tickers": tickers if isinstance(tickers, list) else [tickers]
                    })
                    print("Saved new weights to database for caching")
                except Exception as e:
                    log_error("Error saving weights to MongoDB", "MONGODB_SAVE", e)
                
            except json.JSONDecodeError as e:
                log_error("Error parsing AI weights response as JSON", "AI_PARSING", e)
                log_warning(f"Raw weights response: {ai_weights_response[:200]}...", "DATA_MISSING")
                ai_weights = None
        except Exception as e:
            log_error("Error getting AI weights", "AI_WEIGHTS", e)
            ai_weights = None
    
    return ai_weights
