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
