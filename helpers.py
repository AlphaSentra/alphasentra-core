"""
Description:
Helper functions
"""

from data.price import calculate_trade_levels, calculate_entry_price, get_current_price
import os
from dotenv import load_dotenv
import sys

# MongoDB imports - handle optional dependency
try:
    import pymongo
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    log_warning("pymongo not available - database functions will be limited", "MONGODB_DEPENDENCY")


# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from logging_utils import log_error, log_info, log_warning

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
    Includes JSON repair capabilities for common AI response issues.
    """
    import re
    import json
    from logging_utils import log_warning, log_error
    
    if not isinstance(text, str) or not text.strip():
        log_warning("Empty or non-string text provided to extract_json_from_text", "JSON_EXTRACTION")
        return None
    
    # Enhanced logging for debugging
    log_warning(f"Attempting to extract JSON from text (length: {len(text)} chars)", "JSON_EXTRACTION")
    
    # Strategy: Look for JSON content at the end of the text
    # This handles the most common case where AI responses have JSON at the end
    
    # Pattern 1: Look for complete JSON object at the end
    # This pattern captures complete JSON objects at the end of text
    end_json_pattern = r'(\{(?:[^{}]|\{[^{}]*\})*\})\s*$'
    end_match = re.search(end_json_pattern, text, re.DOTALL)
    if end_match:
        try:
            json_content = end_match.group(1).strip()
            # Validate JSON structure before parsing
            if validate_json_structure(json_content):
                parsed_json = json.loads(json_content)
                log_warning("Successfully extracted JSON using end object pattern", "JSON_EXTRACTION_SUCCESS")
                return json_content
        except (json.JSONDecodeError, ValueError) as e:
            # Try to repair malformed JSON before giving up
            log_warning(f"JSON parsing failed for end object pattern: {str(e)}", "JSON_EXTRACTION_ATTEMPT")
            repaired_json = repair_json_content(json_content, str(e))
            if repaired_json:
                log_warning("Successfully repaired JSON from end object pattern", "JSON_REPAIR_SUCCESS")
                return repaired_json
    
    # Pattern 2: Look for JSON array at the end
    array_pattern = r'(\[.*\])\s*$'
    array_match = re.search(array_pattern, text, re.DOTALL)
    if array_match:
        try:
            json_content = array_match.group(1).strip()
            # Validate JSON structure before parsing
            if validate_json_structure(json_content):
                parsed_json = json.loads(json_content)
                log_warning("Successfully extracted JSON using array pattern", "JSON_EXTRACTION_SUCCESS")
                return json_content
        except (json.JSONDecodeError, ValueError) as e:
            # Try to repair malformed JSON before giving up
            log_warning(f"JSON parsing failed for array pattern: {str(e)}", "JSON_EXTRACTION_ATTEMPT")
            repaired_json = repair_json_content(json_content, str(e))
            if repaired_json:
                log_warning("Successfully repaired JSON from array pattern", "JSON_REPAIR_SUCCESS")
                return repaired_json
    
    # Pattern 3: Look for JSON preceded by common AI response patterns
    # This handles cases like "text: {json}" or "text\n{json}"
    ai_json_patterns = [
        r'(?:analysis|recommendation|result|response|output)[:\s]*(\{.*\})\s*$',
        r'(?:^|\n)[^{}]*(\{.*\})\s*$',
        r'```json\s*(\{.*\})\s*```',  # Markdown code blocks
        r'```\s*(\{.*\})\s*```',      # Generic code blocks
    ]
    
    for pattern in ai_json_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                json_content = match.group(1).strip()
                # Validate JSON structure before parsing
                if validate_json_structure(json_content):
                    parsed_json = json.loads(json_content)
                    log_warning(f"Successfully extracted JSON using pattern: {pattern[:50]}...", "JSON_EXTRACTION_SUCCESS")
                    return json_content
            except (json.JSONDecodeError, ValueError) as e:
                # Try to repair malformed JSON before giving up
                log_warning(f"JSON parsing failed for pattern {pattern[:50]}...: {str(e)}", "JSON_EXTRACTION_ATTEMPT")
                repaired_json = repair_json_content(json_content, str(e))
                if repaired_json:
                    log_warning(f"Successfully repaired JSON from pattern: {pattern[:50]}...", "JSON_REPAIR_SUCCESS")
                    return repaired_json
                continue
    
    # If no JSON found at the end, try to find any valid JSON in the text
    # This is a fallback for cases where JSON might be embedded elsewhere
    json_pattern = r'(\{(?:[^{}]|\{[^{}]*\})*\})'
    json_matches = re.findall(json_pattern, text, re.DOTALL)
    for json_match in reversed(json_matches):  # Try from end to start
        try:
            json_content = json_match.strip()
            # Validate JSON structure before parsing
            if validate_json_structure(json_content):
                parsed_json = json.loads(json_content)
                log_warning("Successfully extracted JSON using fallback pattern", "JSON_EXTRACTION_SUCCESS")
                return json_content
        except (json.JSONDecodeError, ValueError) as e:
            # Try to repair malformed JSON before giving up
            log_warning(f"JSON parsing failed for fallback pattern: {str(e)}", "JSON_EXTRACTION_ATTEMPT")
            repaired_json = repair_json_content(json_content, str(e))
            if repaired_json:
                log_warning("Successfully repaired JSON from fallback pattern", "JSON_REPAIR_SUCCESS")
                return repaired_json
            continue
    
    log_error("Failed to extract any valid JSON from text", "JSON_EXTRACTION_FAILED")
    log_error(f"Text preview: {text[:500]}...", "JSON_EXTRACTION_FAILED")
    return None
    
    
def validate_json_structure(json_content):
    """
    Validate basic JSON structure before attempting to parse.
    This helps avoid unnecessary parsing attempts on clearly invalid content.
    
    Parameters:
    json_content (str): JSON content to validate
    
    Returns:
    bool: True if structure appears valid, False otherwise
    """
    import re
    
    if not json_content or not isinstance(json_content, str):
        return False
    
    # Check if content starts and ends with proper brackets
    trimmed = json_content.strip()
    if not trimmed:
        return False
    
    # Must start with { or [ and end with } or ]
    if not ((trimmed.startswith('{') and trimmed.endswith('}')) or
            (trimmed.startswith('[') and trimmed.endswith(']'))):
        return False
    
    # Basic balance check for braces/brackets
    brace_count = trimmed.count('{') - trimmed.count('}')
    bracket_count = trimmed.count('[') - trimmed.count(']')
    if brace_count != 0 or bracket_count != 0:
        return False
    
    # Check for basic JSON structure patterns
    # At minimum should have some key-value pairs or array elements
    if trimmed.startswith('{'):
        # Object should have at least one key-value pair pattern
        if not re.search(r'"[^"]*"\s*:', trimmed):
            return False
    elif trimmed.startswith('['):
        # Array should have at least one element
        if len(trimmed) <= 2:  # Just []
            return False
    
    return True
    
    
def repair_json_content(json_content, error_message=""):
    """
    Attempt to repair common JSON issues in AI responses.
    Handles missing comma delimiters, unquoted keys, and other common problems.
    
    Parameters:
    json_content (str): The malformed JSON content
    error_message (str): The JSONDecodeError message for targeted repair
    
    Returns:
    str: Repaired JSON content if successful, None if repair fails
    """
    import re
    import json
    from logging_utils import log_warning, log_error
    
    if not json_content:
        return None
    
    original_content = json_content
    
    try:
        # First try to parse as-is (might be valid after all)
        json.loads(json_content)
        return json_content
    except json.JSONDecodeError as e:
        # Store the specific error for targeted repair
        error_msg = str(e)
        
    # Enhanced comma delimiter repair with comprehensive pattern matching
    if "Expecting ',' delimiter" in error_msg:
        try:
            # Extract position information from error message
            position_match = re.search(r'line (\d+) column (\d+) \(char (\d+)\)', error_msg)
            if position_match:
                char_pos = int(position_match.group(3))
                
                # Enhanced comma insertion logic with context analysis
                if char_pos < len(json_content):
                    # Analyze the context around the error position
                    context_start = max(0, char_pos - 20)
                    context_end = min(len(json_content), char_pos + 20)
                    context = json_content[context_start:context_end]
                    
                    # Pattern 1: Missing comma between objects: }{ or ]{
                    if (char_pos > 0 and json_content[char_pos-1] in ['}', ']'] and
                        json_content[char_pos] == '{'):
                        repaired_content = json_content[:char_pos] + ',' + json_content[char_pos:]
                        json.loads(repaired_content)
                        log_warning(f"Repaired missing comma between objects at position {char_pos}", "JSON_REPAIR")
                        return repaired_content
                    
                    # Pattern 2: Missing comma after value before object: value{
                    if (char_pos > 0 and json_content[char_pos-1].isalnum() and
                        json_content[char_pos] == '{'):
                        repaired_content = json_content[:char_pos] + ',' + json_content[char_pos:]
                        json.loads(repaired_content)
                        log_warning(f"Repaired missing comma after value before object at position {char_pos}", "JSON_REPAIR")
                        return repaired_content
                    
                    # Pattern 3: Missing comma after object before value: }value
                    if (char_pos > 0 and json_content[char_pos-1] == '}' and
                        json_content[char_pos].isalnum()):
                        repaired_content = json_content[:char_pos] + ',' + json_content[char_pos:]
                        json.loads(repaired_content)
                        log_warning(f"Repaired missing comma after object before value at position {char_pos}", "JSON_REPAIR")
                        return repaired_content
                    
                    # Pattern 4: Missing comma between array elements: valuevalue
                    if (char_pos > 0 and json_content[char_pos-1].isalnum() and
                        json_content[char_pos].isalnum()):
                        repaired_content = json_content[:char_pos] + ',' + json_content[char_pos:]
                        json.loads(repaired_content)
                        log_warning(f"Repaired missing comma between array elements at position {char_pos}", "JSON_REPAIR")
                        return repaired_content
                        
        except (ValueError, IndexError, json.JSONDecodeError):
            pass  # Fall through to other repair strategies
    
    # Enhanced unquoted key repair with better pattern matching
    unquoted_key_patterns = [
        r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:',  # Basic pattern
        r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*\s+[a-zA-Z0-9_]+)\s*:',  # Multi-word keys
        r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*[-][a-zA-Z0-9_]+)\s*:',  # Hyphenated keys
    ]
    
    for pattern in unquoted_key_patterns:
        def quote_key(match):
            return f'{match.group(1)} "{match.group(2)}":'
        
        repaired_content = re.sub(pattern, quote_key, json_content)
        if repaired_content != json_content:
            try:
                json.loads(repaired_content)
                log_warning("Repaired unquoted keys in JSON", "JSON_REPAIR")
                return repaired_content
            except json.JSONDecodeError:
                continue  # Try next pattern
    
    # Enhanced trailing comma handling
    trailing_comma_patterns = [
        r',\s*([}\]])',  # Comma before closing brace/bracket
        r',\s*$',        # Comma at end
    ]
    
    for pattern in trailing_comma_patterns:
        try:
            compiled_pattern = re.compile(pattern)
            num_groups = len(compiled_pattern.groups())
            if num_groups > 0:
                replacement = r'\1'
            else:
                replacement = ''  # Remove the comma without preserving any group
            
            repaired_content = re.sub(compiled_pattern, replacement, json_content)
            
            if repaired_content != json_content:
                try:
                    json.loads(repaired_content)
                    log_warning("Removed trailing comma from JSON", "JSON_REPAIR")
                    return repaired_content
                except json.JSONDecodeError:
                    continue
        except re.error as regex_error:
            log_warning(f"Regex compilation error in trailing comma pattern '{pattern}': {regex_error}", "JSON_REPAIR_REGEX")
            continue
    
    # Enhanced single quote to double quote conversion
    if "'" in json_content:
        # Only convert single quotes that are likely to be string delimiters
        # Avoid converting apostrophes within words
        single_quote_pattern = r"'(.*?)'"
        def replace_quotes(match):
            return f'"{match.group(1)}"'
        
        repaired_content = re.sub(single_quote_pattern, replace_quotes, json_content)
        if repaired_content != json_content:
            try:
                json.loads(repaired_content)
                log_warning("Converted single quotes to double quotes in JSON", "JSON_REPAIR")
                return repaired_content
            except json.JSONDecodeError:
                pass
    
    # Enhanced JSON substring extraction with validation
    json_patterns = [
        r'(\{(?:[^{}]|\{[^{}]*\}){0,50}\})',  # Objects (limit depth)
        r'(\[(?:[^\[\]]|\[[^\[\]]*\]){0,50}\])',  # Arrays (limit depth)
    ]
    
    best_candidate = None
    best_length = 0
    
    for pattern in json_patterns:
        matches = re.findall(pattern, json_content, re.DOTALL)
        for match in matches:
            if len(match) > best_length:  # Prefer longer matches
                try:
                    json.loads(match)
                    best_candidate = match
                    best_length = len(match)
                except json.JSONDecodeError:
                    continue
    
    if best_candidate:
        log_warning(f"Extracted valid JSON substring ({best_length} chars) from malformed content", "JSON_REPAIR")
        return best_candidate
    
    # Comprehensive error logging for debugging
    log_error(f"JSON repair failed for content. Original error: {error_msg}", "JSON_REPAIR_FAILED")
    log_error(f"Content preview: {json_content[:500]}...", "JSON_REPAIR_FAILED")
    
    # Log the specific error position if available
    if "char" in error_msg:
        try:
            char_match = re.search(r'char (\d+)', error_msg)
            if char_match:
                error_pos = int(char_match.group(1))
                context_start = max(0, error_pos - 50)
                context_end = min(len(json_content), error_pos + 50)
                error_context = json_content[context_start:context_end]
                log_error(f"Error context around position {error_pos}: ...{error_context}...", "JSON_REPAIR_FAILED")
        except (ValueError, IndexError):
            pass
    
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


class DatabaseManager:
    """
    Singleton class for MongoDB connection pooling and management.
    """
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._client = None
        return cls._instance
    
    def get_client(self):
        """
        Get MongoDB client with connection pooling.
        Creates client if it doesn't exist.
        """
        if self._client is None:
            try:
                if not PYMONGO_AVAILABLE:
                    raise ImportError("pymongo not available")
                
                # Get MongoDB connection details from environment variables
                use_mongodb_srv = os.getenv("USE_MONGODB_SRV", "false").lower() == "true"
                mongodb_database = os.getenv("MONGODB_DATABASE", "alphagora")
                mongodb_username = os.getenv("MONGODB_USERNAME")
                mongodb_password = os.getenv("MONGODB_PASSWORD")
                mongodb_auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")
                
                # Construct MongoDB URI based on USE_MONGODB_SRV
                if use_mongodb_srv:
                    mongodb_srv = os.getenv("MONGODB_SRV")
                    if not mongodb_srv:
                        raise ValueError("MONGODB_SRV environment variable is required when USE_MONGODB_SRV is true")
                    mongodb_uri = f"{mongodb_srv}"
                else:
                    mongodb_host = os.getenv("MONGODB_HOST", "localhost")
                    mongodb_port = int(os.getenv("MONGODB_PORT", "27017"))
                    if mongodb_username and mongodb_password:
                        mongodb_uri = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_host}:{mongodb_port}/{mongodb_database}?authSource={mongodb_auth_source}"
                    else:
                        mongodb_uri = f"mongodb://{mongodb_host}:{mongodb_port}/{mongodb_database}"
                
                # Create client with connection pooling
                self._client = MongoClient(
                    mongodb_uri,
                    maxPoolSize=10,
                    minPoolSize=2,
                    connectTimeoutMS=5000,
                    serverSelectionTimeoutMS=5000
                )
                
                # Test connection (silent - no logging)
                self._client.admin.command('ping')
                
            except Exception as e:
                log_error("Failed to create MongoDB client", "MONGODB_CONNECTION", e)
                self._client = None
                raise
        
        return self._client
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            log_info("MongoDB connection closed")


def save_to_db(recommendations):
    """
    Save data to MongoDB collections.
    
    Parameters:
    recommendations (dict): The recommendations dictionary to save
    
    Returns:
    bool: True if successful, False on error
    """
    try:
        if not PYMONGO_AVAILABLE:
            log_error("pymongo not available - cannot save to database", "MONGODB_DEPENDENCY", None)
            return False
        
        # Use DatabaseManager for connection pooling
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphagora")]
        collection = db['insights']
        
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


# Enhanced database functions with reliability improvements
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pymongo.errors import AutoReconnect, NetworkTimeout, ConnectionFailure, OperationFailure


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((AutoReconnect, NetworkTimeout, ConnectionFailure))
)


def save_to_db_with_retry(recommendations):
    """
    Save to database with automatic retry for network issues.
    
    Parameters:
    recommendations (dict): The recommendations dictionary to save
    
    Returns:
    bool: True if successful, False on error
    """
    try:
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphagora")]
        collection = db['insights']
        
        result = collection.insert_one(recommendations)
        return True
    except OperationFailure as e:
        log_error("MongoDB operation failed", "MONGODB_OPERATION", e)
        return False
    except Exception as e:
        log_error("Failed to save to database after retries", "DATABASE_SAVE", e)
        return False


def validate_recommendations_schema(recommendations):
    """
    Validate recommendations against MongoDB schema before insertion.
    
    Parameters:
    recommendations (dict): The recommendations dictionary to validate
    
    Returns:
    bool: True if valid, False if invalid
    """
    required_fields = [
        'title', 'market_outlook_narrative', 'rationale', 'analysis',
        'recommendations', 'sentiment_score', 'market_impact',
        'timestamp_gmt', 'language_code'
    ]
    
    missing_fields = [field for field in required_fields if field not in recommendations]
    if missing_fields:
        log_warning(f"Missing required fields: {missing_fields}", "DATA_VALIDATION")
        return False
    
    # Validate recommendations array structure
    if not isinstance(recommendations.get('recommendations'), list):
        log_warning("Recommendations field must be an array", "DATA_VALIDATION")
        return False
    
    # Validate each recommendation in the array
    for i, rec in enumerate(recommendations['recommendations']):
        if not isinstance(rec, dict):
            log_warning(f"Recommendation at index {i} is not a dictionary", "DATA_VALIDATION")
            return False
        
        rec_required_fields = ['ticker', 'trade_direction', 'bull_bear_score',
                              'stop_loss', 'target_price', 'entry_price', 'price']
        missing_rec_fields = [field for field in rec_required_fields if field not in rec]
        if missing_rec_fields:
            log_warning(f"Recommendation {i} missing fields: {missing_rec_fields}", "DATA_VALIDATION")
            return False
    
    return True


def save_to_db_robust(recommendations):
    """
    Robust database save with validation and retry.
    
    Parameters:
    recommendations (dict): The recommendations dictionary to save
    
    Returns:
    bool: True if successful, False on error
    """
    if not validate_recommendations_schema(recommendations):
        log_error("Invalid recommendations schema, skipping save", "DATA_VALIDATION")
        return False
    
    return save_to_db_with_retry(recommendations)


def save_to_db_with_fallback(recommendations, flag_document_generated: bool = True):
    """
    Save to database with fallback to local file storage.
    
    Parameters:
    recommendations (dict): The recommendations dictionary to save
    flag_document_generated (bool): Whether to set document_generated to True in tickers collection
    
    Returns:
    bool: True if successful, False on error
    """
    try:
        success = save_to_db_robust(recommendations)
        if success:
            if flag_document_generated:
                # Update document_generated flag for tickers
                if 'recommendations' in recommendations and isinstance(recommendations['recommendations'], list):
                    tickers_set = set()
                    for trade in recommendations['recommendations']:
                        ticker = trade.get('ticker')
                        if ticker:
                            tickers_set.add(ticker)
                    
                    if tickers_set:
                        client = DatabaseManager().get_client()
                        db_name = os.getenv("MONGODB_DATABASE", "alphagora")
                        db = client[db_name]
                        tickers_coll = db['tickers']
                        for ticker in tickers_set:
                            tickers_coll.update_one({"ticker": ticker}, {"$set": {"document_generated": True}})
                        print()
                        log_info(f"Updated document_generated flag to True for tickers: {list(tickers_set)}")
                    else:
                        log_warning("No recommendations found in saved document, skipping flag update", "FLAG_UPDATE")
                else:
                    log_warning("No recommendations found in saved document, skipping flag update", "FLAG_UPDATE")
        else:
            log_warning("Database save failed, skipping flag update", "DATABASE_FALLBACK")
            return False
        return success
    except Exception as e:
        log_error("Critical error in database save with fallback", "DATABASE_CRITICAL", e)
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
        if not PYMONGO_AVAILABLE:
            # Skip cache check if pymongo not available
            return None
        
        # Use DatabaseManager for connection pooling
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphagora")]
        collection = db['weight_factors']
        
        # Check if we have weights for today
        today = date.today().isoformat()
        cached_weights = collection.find_one({"date": today})
        
        if cached_weights:
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
                    if PYMONGO_AVAILABLE:
                        collection.insert_one({
                            "date": date.today().isoformat(),
                            "timestamp": datetime.now().isoformat(),
                            "weights": ai_weights
                        })
                        print("Saved new weights to database for caching")
                    else:
                        log_warning("pymongo not available - skipping weight caching", "MONGODB_DEPENDENCY")
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


def get_regions(tickers):
    """
    Get regions for given tickers from database tickers collection.
    
    Parameters:
    tickers (str or list): Ticker symbols to get regions for
    
    Returns:
    list: List of unique regions, or empty list if no regions found or error occurs
    """
    # If tickers is a string, split by comma and strip whitespace
    if isinstance(tickers, str):
        ticker_list = [t.strip() for t in tickers.split(',')]
    else:
        ticker_list = tickers
    
    regions_from_db = []
    
    try:
        if not PYMONGO_AVAILABLE:
            return []
        
        # Use DatabaseManager for connection pooling
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphagora")]
        collection = db['tickers']
        
        # Query database for tickers and get their regions
        ticker_docs = collection.find({"ticker": {"$in": ticker_list}})
        
        for doc in ticker_docs:
            if 'region' in doc and isinstance(doc['region'], list):
                regions_from_db.extend(doc['region'])
        
        # Remove duplicates and return
        if regions_from_db:
            return list(set(regions_from_db))
        else:
            return []
        
    except Exception as e:
        log_error("Error getting regions from database", "DATABASE_REGIONS", e)
        return []


def get_asset_classes(tickers):
    """
    Get asset classes for given tickers from database tickers collection.
    
    Parameters:
    tickers (str or list): Ticker symbols to get asset classes for
    
    Returns:
    list: List of unique asset classes, or empty list if no asset classes found or error occurs
    """
    # If tickers is a string, split by comma and strip whitespace
    if isinstance(tickers, str):
        ticker_list = [t.strip() for t in tickers.split(',')]
    else:
        ticker_list = tickers
    
    asset_classes_from_db = []
    
    try:
        if not PYMONGO_AVAILABLE:
            return []
        
        # Use DatabaseManager for connection pooling
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphagora")]
        collection = db['tickers']
        
        # Query database for tickers and get their asset classes
        ticker_docs = collection.find({"ticker": {"$in": ticker_list}})
        
        for doc in ticker_docs:
            if 'asset_class' in doc and isinstance(doc['asset_class'], str):
                asset_classes_from_db.append(doc['asset_class'])
        
        # Remove duplicates and return
        if asset_classes_from_db:
            return list(set(asset_classes_from_db))
        else:
            return []
        
    except Exception as e:
        log_error("Error getting asset classes from database", "DATABASE_ASSET_CLASSES", e)
        return []


def get_importance(tickers):
    """
    Get importance for given tickers from database tickers collection.
    
    Parameters:
    tickers (str or list): Ticker symbols to get importance for
    
    Returns:
    int: Average importance value (1-5), or 3 (neutral) if no importance values found or error occurs
    """
    # If tickers is a string, split by comma and strip whitespace
    if isinstance(tickers, str):
        ticker_list = [t.strip() for t in tickers.split(',')]
    else:
        ticker_list = tickers
    
    importance_values = []
    
    try:
        if not PYMONGO_AVAILABLE:
            return 5  # Return neutral importance if pymongo not available
        
        # Use DatabaseManager for connection pooling
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphagora")]
        collection = db['tickers']
        
        # Query database for tickers and get their importance values
        ticker_docs = collection.find({"ticker": {"$in": ticker_list}})
        
        for doc in ticker_docs:
            if 'importance' in doc and isinstance(doc['importance'], int):
                importance_values.append(doc['importance'])
        
        # Calculate average importance if we have values
        if importance_values:
            average_importance = sum(importance_values) / len(importance_values)
            return round(average_importance)
        else:
            return 5  # Return neutral importance if no values found
        
    except Exception as e:
        log_error("Error getting importance from database", "DATABASE_IMPORTANCE", e)
        return 5  # Return neutral importance on error


def get_ticker_name(tickers):
    """
    Get name(s) for given ticker(s) from database tickers collection.
    
    Parameters:
    tickers (str or list): Ticker symbol(s) to get names for
    
    Returns:
    str/list: Single name string if single ticker input,
              list of names if multiple tickers input,
              None if ticker not found or error occurs
    """
    # Normalize input to list
    if isinstance(tickers, str):
        ticker_list = [tickers]
        return_single = True
    else:
        ticker_list = tickers
        return_single = False
    
    names = []
    
    try:
        if not PYMONGO_AVAILABLE:
            return None if return_single else []
        
        # Use DatabaseManager for connection pooling
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphagora")]
        collection = db['tickers']
        
        # Query database for tickers and get their names
        ticker_docs = collection.find({"ticker": {"$in": ticker_list}})
        
        # Create mapping of ticker to name
        name_map = {doc['ticker']: doc.get('name') for doc in ticker_docs if 'name' in doc}
        
        # Get names in original order
        for ticker in ticker_list:
            names.append(name_map.get(ticker))
        
        # Return appropriate format based on input type
        if return_single:
            return names[0] if names else None
        else:
            return names
        
    except Exception as e:
        log_error("Error getting ticker names from database", "DATABASE_TICKER_NAMES", e)
        return None if return_single else []


def get_factors(tickers, name=None, current_date=None, prompt=None):
    """
    Get AI-generated factors analysis for given tickers.
    
    Parameters:
    tickers (str or list): Ticker symbols to analyze
    current_date (str): Current date in format "Month Day, Year"
    prompt (str, optional): Custom prompt to use. If None, uses FX_FACTORS_PROMPT from _config
    
    Returns:
    list: Array containing the generated JSON properties as factors
    """
    from _config import FX_FACTORS_PROMPT
    from crypt import decrypt_string
    from genAI.ai_prompt import get_gen_ai_response
    import json
    
    try:
        # Use provided prompt or default to FX_FACTORS_PROMPT
        if prompt is None:
            prompt = FX_FACTORS_PROMPT
        
        # Decrypt the prompt if it's encrypted
        try:
            decrypted_prompt = decrypt_string(prompt)
        except Exception as e:
            log_error("Error decrypting factors prompt", "DECRYPTION", e)
            decrypted_prompt = prompt  # Fallback to encrypted version
        
        # Format the prompt with tickers and current date
        if isinstance(tickers, list):
            tickers_str = ", ".join(tickers)
        else:
            tickers_str = tickers

        # Get Name for instrument_name if provided
        instrument_name = name
            
        formatted_prompt = decrypted_prompt.format(
            tickers_str=tickers_str,
            instrument_name=instrument_name,
            current_date=current_date
        )
        
        # Get AI response
        ai_response = get_gen_ai_response([tickers_str], "factors analysis", formatted_prompt, os.getenv("GEMINI_PRO_MODEL"))
        
        # Remove any markdown code block markers if present
        ai_response = strip_markdown_code_blocks(ai_response)
        # Parse JSON response
        factors_data = json.loads(ai_response)

        factors_array = []

        # Process different response formats
        if isinstance(factors_data, dict) and 'factors' in factors_data:
            # Handle nested factors structure
            factors_data = factors_data['factors']
        
        if isinstance(factors_data, list):
            for item in factors_data:
                # Enforce required structure for each factor
                factor = {
                    "name": str(item.get('name', f"factor_{len(factors_array)+1}")),
                    "value": {
                        "description": "",
                        "bull_bear_score": 0
                    }
                }
                
                # Process value field
                if 'value' in item:
                    if isinstance(item['value'], dict):
                        factor['value']['description'] = str(item['value'].get('description', ''))
                        factor['value']['bull_bear_score'] = int(item['value'].get('bull_bear_score', 0))
                    else:
                        factor['value']['description'] = str(item['value'])
                
                # Skip factor if description is empty
                if not factor['value']['description']:
                    continue
                
                factors_array.append(factor)
                
        elif isinstance(factors_data, dict):
            # Convert key-value pairs to factor objects
            for key, value in factors_data.items():
                factor = {
                    "name": str(key),
                    "value": {
                        "description": "",
                        "bull_bear_score": 0
                    }
                }
                
                if isinstance(value, dict):
                    factor['value']['description'] = str(value.get('description', ''))
                    factor['value']['bull_bear_score'] = int(value.get('bull_bear_score', 0))
                else:
                    factor['value']['description'] = str(value)
                
                # Skip factor if description is empty
                if not factor['value']['description']:
                    continue
                
                factors_array.append(factor)
                
        else:  # Fallback for unexpected formats
            factors_array.append({
                "name": "default_factor",
                "value": {
                    "description": "",
                    "bull_bear_score": 0
                }
            })
        
        return factors_array
        
    except json.JSONDecodeError as e:
        log_error("Error parsing factors response as JSON", "AI_PARSING", e)
        log_warning(f"Raw factors response: {ai_response[:200]}...", "DATA_MISSING")
        return []
    except Exception as e:
        log_error("Error getting factors analysis", "FACTORS_ANALYSIS", e)
        return []

def get_ticker_performance(ticker, period=None):
    """
    Retrieve performance data for a given ticker from the tickers collection.
    
    Parameters:
    ticker (str): The ticker symbol to query
    period (str, optional): Specific period to retrieve (p1y, p6m, p3m, p1m, p1w). 
                            If None, returns all periods.
    
    Returns:
    dict: Performance data for the specified period(s) or None if not found
    """
    try:
        if not PYMONGO_AVAILABLE:
            log_warning("pymongo not available - cannot query performance data", "MONGODB_DEPENDENCY")
            return None

        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphagora")]
        collection = db['tickers']
        
        ticker_data = collection.find_one({"ticker": ticker})
        if not ticker_data:
            return None
            
        performance_data = ticker_data.get('performance', {})
        
        if period:
            value = performance_data.get(period)
            return {period: f"{round(value * 100, 1)}%" if value is not None else None}
        else:
            # Return all periods, formatted as percentage strings
            return {
                'p1y': f"{round(performance_data.get('1y') * 100, 1)}%" if performance_data.get('1y') is not None else None,
                'p6m': f"{round(performance_data.get('6m') * 100, 1)}%" if performance_data.get('6m') is not None else None,
                'p3m': f"{round(performance_data.get('3m') * 100, 1)}%" if performance_data.get('3m') is not None else None,
                'p1m': f"{round(performance_data.get('1m') * 100, 1)}%" if performance_data.get('1m') is not None else None,
                'p1w': f"{round(performance_data.get('1w') * 100, 1)}%" if performance_data.get('1w') is not None else None
            }
            
    except Exception as e:
        log_error("Error retrieving ticker performance data", "TICKER_PERFORMANCE", e)
        return None