"""
Project:     Alphagora
File:        helpers.py
Author:      Daiviet Huynh
Created:     2025-07-22
License:     MIT License
Repository:  https://github.com/daivieth/Alphagora

Description:
Helper functions for the Alphagora.
"""



# --- HELPER FUNCTIONS ---
import yfinance as yf
import backtrader as bt
from backtrader.indicators import ATR, ADX
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import sys
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from genAI.ai_prompt import get_gen_ai_response

# Load environment variables
load_dotenv()

# Load AI model prompt for target price from environment variables
TARGET_PRICE_PROMPT = os.getenv("TARGET_PRICE")


def calculate_trade_levels(tickers, trade_direction, period=14, gemini_model=None, decimal_digits=2, recommendation_narrative=None):
    """
    Calculate appropriate stop loss and target price levels based on ADX and ATR indicators.
    
    Parameters:
    tickers (list): List of ticker symbols as strings
    trade_direction (str): Trade direction, either "LONG" or "SHORT"
    period (int): Period for ADX and ATR calculations (default: 14)
    gemini_model (str, optional): The Gemini model to use for analysis
    decimal_digits (int): Number of decimal digits for rounding prices (default: 2)
    recommendation_narrative (list, optional): List of recommendation narrative paragraphs
    
    Returns:
    dict: Dictionary with ticker as key and dict with 'stop_loss' and 'target_price' as values
    """
    
    try:
        # Debug: Print the function parameters
        
        # Validate trade direction
        if trade_direction not in ["LONG", "SHORT"]:
            raise ValueError("Trade direction must be either 'LONG' or 'SHORT'")
        
        # Dictionary to store stop loss prices
        stop_loss_prices = {}

        print()
        print("Calculating stop loss prices...")

        # Fetch data for all tickers
        for ticker in tickers:
            try:
                # Fetch historical data for the last 60 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=60)
                data = yf.download(ticker, start=start_date, end=end_date, progress=False, multi_level_index=False)
                
                if data.empty:
                    print(f"No data available for {ticker}")
                    continue
                
                # Prepare data for backtrader
                data_feed = bt.feeds.PandasData(dataname=data)
                
                # Create a cerebro instance
                cerebro = bt.Cerebro()
                
                # Add data to cerebro
                cerebro.adddata(data_feed)
                
                # Create a strategy to calculate indicators
                class IndicatorStrategy(bt.Strategy):
                    def __init__(self):
                        self.atr = ATR(period=period)
                        self.adx = ADX(period=period)
                    
                    def next(self):
                        pass  # We don't need to do anything in next()
                
                # Add strategy to cerebro
                cerebro.addstrategy(IndicatorStrategy)
                
                # Run cerebro to calculate indicators
                results = cerebro.run()
                
                # Get the strategy instance
                strategy = results[0]
                
                # Get the latest values of indicators
                current_atr = strategy.atr[0]
                current_adx = strategy.adx[0]
                current_close = data['Close'].iloc[-1]
                
                # Calculate stop loss based on ADX strength and ATR
                # Higher ADX means stronger trend, so we can place stop loss further away
                # Lower ADX means weaker trend, so we place stop loss closer
                
                # Normalize ADX (typically ranges from 0 to 100)
                adx_strength = min(current_adx / 100, 1.0)  # Cap at 1.0
                
                # Use ATR as the base for stop loss distance
                # Multiply by a factor that depends on ADX strength
                # For stronger trends (high ADX), use 1.5x ATR
                # For weaker trends (low ADX), use 2.5x ATR
                atr_multiplier = 2.5 - (adx_strength * 1.0)  # Ranges from 2.5 to 1.5
                
                # Calculate stop loss distance
                stop_loss_distance = current_atr * atr_multiplier
                
                # Calculate stop loss price based on trade direction
                if trade_direction == "LONG":
                    stop_loss_price = current_close - stop_loss_distance
                else:  # SHORT
                    stop_loss_price = current_close + stop_loss_distance
                
                # Calculate entry price for this ticker
                entry_prices = calculate_entry_price([ticker], trade_direction)
                entry_price = entry_prices.get(ticker, current_close)  # Fallback to current close if entry price calculation fails
                
                # Get target price from AI model if prompt is available
                if TARGET_PRICE_PROMPT:
                    try:
                        # Prepare recommendation narrative string
                        recommendation_narrative_str = ""
                        if recommendation_narrative:
                            recommendation_narrative_str = " ".join(recommendation_narrative)
                        
                        # Format the prompt with the required variables
                        formatted_prompt = TARGET_PRICE_PROMPT.format(
                            trade_direction=trade_direction,
                            ticker_str=ticker,
                            entry_price=round(entry_price, decimal_digits),
                            stop_loss=round(stop_loss_price, decimal_digits),
                            recommendation_narrative_str=recommendation_narrative_str
                        )
                        
                        # Get AI-generated target price
                        ai_response = get_gen_ai_response([ticker], "target price", formatted_prompt, gemini_model)
                        
                        # Try to parse the response as a float
                        try:
                            target_price = float(ai_response.strip())
                        except ValueError:
                            print(f"Warning: Could not parse AI response '{ai_response}' as a number for {ticker}. Using fallback calculation.")
                            # Fallback to original calculation if AI response is not a valid number
                            if trade_direction == "LONG":
                                target_price = current_close + (2 * stop_loss_distance)
                            else:  # SHORT
                                target_price = current_close - (2 * stop_loss_distance)
                    except Exception as e:
                        print(f"Warning: Error getting AI target price for {ticker}: {e}. Using fallback calculation.")
                        # Fallback to original calculation if there's any error
                        if trade_direction == "LONG":
                            target_price = current_close + (2 * stop_loss_distance)
                        else:  # SHORT
                            target_price = current_close - (2 * stop_loss_distance)
                else:
                    # Fallback to original calculation if prompt is not available
                    if trade_direction == "LONG":
                        target_price = current_close + (2 * stop_loss_distance)
                    else:  # SHORT
                        target_price = current_close - (2 * stop_loss_distance)
                
                # Store the result
                stop_loss_prices[ticker] = {
                    'stop_loss': max(0, stop_loss_price),  # Ensure non-negative
                    'target_price': max(0, target_price)   # Ensure non-negative
                }
                
                
            except Exception as e:
                print(f"Error calculating stop loss for {ticker}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return stop_loss_prices
    except Exception as e:
        print(f"ERROR in calculate_trade_levels: {e}")
        import traceback
        traceback.print_exc()
        return {}


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
        # Debug: Print the recommendations structure
        
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
            recommendation_narrative = recommendations.get('market_outlook_narrative')
            long_stop_losses = calculate_trade_levels(long_tickers, 'LONG', gemini_model=gemini_model, decimal_digits=decimal_digits, recommendation_narrative=recommendation_narrative)
            
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
            recommendation_narrative = recommendations.get('market_outlook_narrative')
            short_stop_losses = calculate_trade_levels(short_tickers, 'SHORT', gemini_model=gemini_model, decimal_digits=decimal_digits, recommendation_narrative=recommendation_narrative)
            
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
        print(f"ERROR in add_trade_levels_to_recommendations: {e}")
        import traceback
        traceback.print_exc()
        return recommendations


def calculate_entry_price(tickers, trade_direction, period=5):
    """
    Calculate an appropriate entry price based on past week's high and low.
    
    For LONG positions: Entry price is set at the high since the past week to now
    For SHORT positions: Entry price is set at the low since the past week to now
    
    Parameters:
    tickers (list): List of ticker symbols as strings
    trade_direction (str): Trade direction, either "LONG" or "SHORT"
    period (int): Period for high/low calculations in days (default: 5 for one week)
    
    Returns:
    dict: Dictionary with ticker as key and entry price as value
    """
    
    try:
        # Debug: Print the function parameters
        
        # Validate trade direction
        if trade_direction not in ["LONG", "SHORT"]:
            raise ValueError("Trade direction must be either 'LONG' or 'SHORT'")
        
        # Dictionary to store entry prices
        entry_prices = {}

        print()
        print("Calculating entry prices...")

        # Fetch data for all tickers
        for ticker in tickers:
            try:
                # Fetch historical data for the last 30 days (to ensure we have enough data for weekly calculations)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                data = yf.download(ticker, start=start_date, end=end_date, progress=False, multi_level_index=False)
                
                if data.empty:
                    print(f"No data available for {ticker}")
                    continue
                
                # Get data for the past week only (last 5 trading days)
                week_data = data.tail(period)
                
                if len(week_data) < period:
                    print(f"Not enough data for {ticker} to calculate weekly high/low")
                    continue
                
                # Calculate weekly high and low
                week_high = week_data['High'].max()
                week_low = week_data['Low'].min()
                
                # Calculate entry price based on trade direction
                # For LONG positions, entry price is at the high since past week to now
                # For SHORT positions, entry price is at the low since past week to now
                if trade_direction == "LONG":
                    # Enter at the high since past week to now
                    entry_price = week_high
                else:  # SHORT
                    # Enter at the low since past week to now
                    entry_price = week_low
                
                # Store the result
                entry_prices[ticker] = max(0, entry_price)  # Ensure non-negative
                
                
            except Exception as e:
                print(f"Error calculating entry price for {ticker}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return entry_prices
    except Exception as e:
        print(f"ERROR in calculate_entry_price: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_entry_price_recommendations(tickers_with_direction, decimal_digits=2):
    """
    Return entry prices in the specified JSON format.

    Parameters:
    tickers_with_direction (list): List of dictionaries with 'ticker' and 'trade_direction' keys
    decimal_digits (int): Number of decimal digits for rounding prices (default: 2)

    Returns:
    list: Array of objects with 'ticker', 'trade_direction', and 'entry_price' keys
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
    
    # Calculate entry prices for LONG positions
    long_entry_prices = {}
    if long_tickers:
        long_entry_prices = calculate_entry_price(long_tickers, 'LONG')
    
    # Calculate entry prices for SHORT positions
    short_entry_prices = {}
    if short_tickers:
        short_entry_prices = calculate_entry_price(short_tickers, 'SHORT')
    
    # Combine all results in the required format
    recommendations = []
    
    for item in tickers_with_direction:
        ticker = item.get('ticker')
        direction = item.get('trade_direction', '').upper()
        
        if ticker and direction:
            entry_price = None
            if direction == 'LONG' and ticker in long_entry_prices:
                entry_price = round(long_entry_prices[ticker], decimal_digits)
            elif direction == 'SHORT' and ticker in short_entry_prices:
                entry_price = round(short_entry_prices[ticker], decimal_digits)
            
            recommendations.append({
                'ticker': ticker,
                'trade_direction': direction,
                'entry_price': entry_price if entry_price is not None else 'N/A'
            })
    
    return recommendations
def add_entry_price_to_recommendations(recommendations, gemini_model=None, decimal_digits=2):
    """
    Add entry prices to recommendations.

    Parameters:
    recommendations (dict): The AI recommendations dictionary
    gemini_model (str, optional): The Gemini model to use for analysis
    decimal_digits (int): Number of decimal digits for rounding prices (default: 2)

    Returns:
    dict: The recommendations dictionary with entry prices added
    """
        
    try:
        # Debug: Print the recommendations structure
        
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
        print(f"ERROR in add_entry_price_to_recommendations: {e}")
        import traceback
        traceback.print_exc()
        return recommendations

def factcheck_market_outlook(market_outlook_narrative, gemini_model=None):
    """
    Factcheck the market outlook narrative using the AI model.
    
    Args:
        market_outlook_narrative (list): List of paragraphs in the market outlook narrative
        gemini_model (str, optional): The Gemini model to use for analysis
    
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
    

    # Create current date in the format "September 6, 2025"
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Join the narrative paragraphs into a single string
    market_outlook_narrative_str = " ".join(market_outlook_narrative)
    
    # Format the prompt with the market outlook narrative
    factcheck_prompt = FACTCHECK_AI_RESPONSE.format(
        market_outlook_narrative_str=market_outlook_narrative_str,
        current_date=current_date
    )
    
    try:
        # Get AI factcheck response
        factcheck_response = get_gen_ai_response([], "factcheck", factcheck_prompt, gemini_model)
        
        # Try to parse the response as JSON
        try:
            # Remove any markdown code block markers if present
            factcheck_response_clean = factcheck_response.strip()
            if factcheck_response_clean.startswith("```json"):
                factcheck_response_clean = factcheck_response_clean[7:]
            elif factcheck_response_clean.startswith("```"):
                factcheck_response_clean = factcheck_response_clean[3:]
            if factcheck_response_clean.endswith("```"):
                factcheck_response_clean = factcheck_response_clean[:-3]
            
            # Strip whitespace
            factcheck_response_clean = factcheck_response_clean.strip()
            
            # Additional cleaning for common AI response issues
            # Remove leading/trailing quotes if present
            if factcheck_response_clean.startswith("'") and factcheck_response_clean.endswith("'"):
                factcheck_response_clean = factcheck_response_clean[1:-1]
            elif factcheck_response_clean.startswith('"') and factcheck_response_clean.endswith('"'):
                factcheck_response_clean = factcheck_response_clean[1:-1]
            
            # Try to parse as JSON
            factcheck_result = json.loads(factcheck_response_clean)

            # Debug output for factcheck result
            print(f"Factcheck result: {factcheck_result}")
            
            # Return the factcheck result
            return factcheck_result.get("factcheck", "accurate")
        except json.JSONDecodeError as json_error:
            print(f"Error parsing factcheck response as JSON: {factcheck_response}")
            print(f"JSON decode error: {str(json_error)}")
            # Try to extract factcheck value from string response
            response_lower = factcheck_response_clean.lower()
            if "inaccurate" in response_lower:
                return "inaccurate"
            elif "accurate" in response_lower:
                return "accurate"

    except Exception as e:
        print(f"Error factchecking market outlook: {e}")
        return "accurate"  # Default to accurate if there's any error
    
def encrypt_string(plaintext, secret_key=None):
    """
    Encrypt a string using a secret key from environment variables.
    
    Parameters:
    plaintext (str): The string to encrypt
    secret_key (str, optional): The secret key to use for encryption. 
                               If None, uses ENCRYPTION_SECRET from .env
    
    Returns:
    str: Base64 encoded encrypted string, or None if encryption fails
    """
    try:
        # Get secret key from environment if not provided
        if secret_key is None:
            secret_key = os.getenv("ENCRYPTION_SECRET")
            if not secret_key:
                raise ValueError("ENCRYPTION_SECRET not found in environment variables")
        
        # Derive a 32-byte key from the secret using PBKDF2
        salt = b'AlphagoraSalt_'  # Fixed salt for simplicity (in production, use random salt)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        
        # Create Fernet instance with the derived key
        fernet = Fernet(key)
        
        # Encrypt the plaintext
        encrypted = fernet.encrypt(plaintext.encode())
        
        return encrypted.decode()
        
    except ImportError:
        # Fallback to simple encryption if cryptography is not available
        print("Warning: cryptography library not installed. Using simple base64 encoding.")
        return base64.urlsafe_b64encode(plaintext.encode()).decode()
        
    except Exception as e:
        print(f"Error encrypting string: {e}")
        return None


def decrypt_string(encrypted_text, secret_key=None):
    """
    Decrypt a string that was encrypted with encrypt_string.
    
    Parameters:
    encrypted_text (str): The encrypted string to decrypt
    secret_key (str, optional): The secret key to use for decryption.
                               If None, uses ENCRYPTION_SECRET from .env
    
    Returns:
    str: Decrypted plaintext string, or None if decryption fails
    """
    try:
        # Get secret key from environment if not provided
        if secret_key is None:
            secret_key = os.getenv("ENCRYPTION_SECRET")
            if not secret_key:
                raise ValueError("ENCRYPTION_SECRET not found in environment variables")
        
        # Derive a 32-byte key from the secret using PBKDF2
        salt = b'AlphagoraSalt_'  # Fixed salt for simplicity (in production, use random salt)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        
        # Create Fernet instance with the derived key
        fernet = Fernet(key)
        
        # Decrypt the encrypted text
        decrypted = fernet.decrypt(encrypted_text.encode())
        
        return decrypted.decode()
        
    except ImportError:
        # Fallback to simple decryption if cryptography is not available
        print("Warning: cryptography library not installed. Using simple base64 decoding.")
        return base64.urlsafe_b64decode(encrypted_text.encode()).decode()
        
    except Exception as e:
        print(f"Error decrypting string: {e}")
        return None
