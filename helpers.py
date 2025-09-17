"""
Description:
Helper functions for calculating trade levels, entry prices, and integrating with AI model.
"""



# --- HELPER FUNCTIONS ---
import yfinance as yf
import backtrader as bt
from backtrader.indicators import ATR, ADX
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import sys


# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from genAI.ai_prompt import get_gen_ai_response

# Load environment variables
load_dotenv()


def calculate_trade_levels(tickers, trade_direction, period=14, decimal_digits=2):
    """
    Calculate appropriate stop loss and target price levels based on ADX and ATR indicators.
    
    Parameters:
    tickers (list): List of ticker symbols as strings
    trade_direction (str): Trade direction, either "LONG" or "SHORT"
    period (int): Period for ADX and ATR calculations (default: 14)
    decimal_digits (int): Number of decimal digits for rounding prices (default: 2)
    
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
                
                # Calculate target price as 2.5x stop loss distance
                if trade_direction == "LONG":
                    target_price = current_close + (2.5 * stop_loss_distance)
                else:  # SHORT
                    target_price = current_close - (2.5 * stop_loss_distance)
                
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
    
def strip_markdown_code_blocks(text):
    """
    Remove markdown code block markers from text.
    Handles various formats including ```json, ```, and variations with whitespace.
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
    
    # If no full code block found, try to remove partial markers
    # Remove starting ``` with optional language and whitespace
    text = re.sub(r'^```\w*\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    
    # Remove ending ``` with optional whitespace
    text = re.sub(r'\n?```\s*$', '', text)
    text = re.sub(r'\s*```\s*$', '', text)
    
    return text.strip()
    

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
