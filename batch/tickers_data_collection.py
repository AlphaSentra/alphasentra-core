"""
This script is responsible for collecting and updating comprehensive ticker data in the MongoDB database.
To initiate the data collection and update process, execute the `update_ticker_data_in_db()` function.
This function orchestrates the retrieval of tickers, fetches various financial and market data points,
and persists the updated information into the database.
"""

import os
from dotenv import load_dotenv
import pymongo
from yahooquery import Ticker
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional
import numpy as np
import time

from helpers import DatabaseManager
from logging_utils import log_error, log_warning, log_info

def get_tickers_from_db() -> list:
    """
    Retrieves a list of ticker symbols from the 'tickers' collection in the MongoDB database.

    Returns:
        list: A list of ticker symbols (strings). Returns an empty list if no tickers
              are found or an error occurs.
    """
    load_dotenv()
    tickers_list = []
    client = None
    try:
        # Get MongoDB connection
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        collection = db["tickers"]

        # Query to get all documents and extract the 'ticker' field
        # We use a projection to only retrieve the 'ticker' field and exclude '_id'
        cursor = collection.find({}, {"ticker": 1, "_id": 0})

        for doc in cursor:
            if 'ticker' in doc:
                tickers_list.append(doc['ticker'])
        
        log_info(f"Successfully retrieved {len(tickers_list)} tickers from the database.")

    except pymongo.errors.ServerSelectionTimeoutError as e:
        log_error("MongoDB server not found. Ensure MongoDB is running on the specified host/port.", "MONGODB_CONNECTION", e)
    except pymongo.errors.OperationFailure as e:
        log_error(f"MongoDB operation failed: {e}", "MONGODB_OPERATION", e)
    except Exception as e:
        log_error(f"An unexpected error occurred while fetching tickers from DB: {e}", "DATA_FETCHING", e)
    finally:
        if client:
            DatabaseManager().close_connection() # Using the singleton instance to close connection
    return tickers_list

def collect_ticker_data(tickers: list) -> dict:
    """
    Collects various data points for a list of tickers using YahooQuery,
    including market capitalization, forward P/E ratio, and EPS growth.

    Args:
        tickers (list): A list of ticker symbols (e.g., ['AAPL', 'MSFT']).

    Returns:
        dict: A dictionary where keys are ticker symbols and values are dictionaries
              containing collected data (e.g., {'market_cap': 12345, 'forward_pe': 25.5, 'eps_growth': 0.15}).
              Returns None for a data point if not available for a ticker.
    """
    if not tickers:
        log_warning(
            "No tickers provided for data collection. Skipping market cap, forward P/E ratio, and EPS growth collection."
        )
        return {}

    ticker_data = {}
    yq_tickers = Ticker(tickers)

    try:
        data = yq_tickers.all_modules

        for ticker_symbol in tickers:
            market_cap = None
            forward_pe = None
            eps_growth = None
            dilution_proxy = None # Initialize dilution_proxy
            average_daily_range_pips = None # Initialize average_daily_range_pips
            momentum_spread = None # Initialize momentum_spread
            average_daily_volume = None # Initialize average_daily_volume
            thirty_day_volume_change = None # Initialize 30-day volume change
            one_week_performance = None # Initialize 1-week percentage performance
            one_month_performance = None # Initialize 1-month percentage performance
            three_month_performance = None # Initialize 3-month percentage performance
            
            if ticker_symbol in data and 'summaryDetail' in data[ticker_symbol]:
                summary_detail = data[ticker_symbol]['summaryDetail']
                market_cap = summary_detail.get('marketCap')
                forward_pe = summary_detail.get('forwardPE')
                
                # Collect circulatingSupply and maxSupply for dilution_proxy calculation
                circulating_supply = summary_detail.get('circulatingSupply')
                max_supply = summary_detail.get('maxSupply')

                if circulating_supply is not None and max_supply is not None and max_supply > 0:
                    dilution_proxy = circulating_supply / max_supply
                    log_info(f"Collected dilution proxy for {ticker_symbol}: {dilution_proxy}")
                else:
                    log_warning(f"Circulating supply or max supply not found or max supply is zero for {ticker_symbol}. Cannot calculate dilution proxy.")

                if market_cap is not None:
                    log_info(f"Collected market cap for {ticker_symbol}: {market_cap}")
                else:
                    log_warning(f"Market cap not found for {ticker_symbol}.")
                
                if forward_pe is not None:
                    log_info(f"Collected forward P/E for {ticker_symbol}: {forward_pe}")
                else:
                    log_warning(f"Forward P/E not found for {ticker_symbol}.")
            else:
                log_warning(f"No data or 'summaryDetail' found for {ticker_symbol}.")
            
            # Collect 30-day average daily range in pips for FX pairs
            if ticker_symbol.endswith('=X'): # Assuming FX pairs end with '=X'
                average_daily_range_pips = _calculate_30d_average_daily_range_in_pips(ticker_symbol)
                if average_daily_range_pips is not None:
                    log_info(f"Collected 30-day average daily range for {ticker_symbol}: {average_daily_range_pips} pips.")
                else:
                    log_warning(f"Could not collect 30-day average daily range for FX pair {ticker_symbol}.")

            # Collect momentum spread
            momentum_spread = _calculate_momentum_spread(ticker_symbol)
            if momentum_spread is not None:
                log_info(f"Collected momentum spread for {ticker_symbol}: {momentum_spread:.2f}.")
            else:
                log_warning(f"Could not collect momentum spread for {ticker_symbol}.")

            # Collect average daily volume
            average_daily_volume = _calculate_average_daily_volume(ticker_symbol)
            if average_daily_volume is not None:
                log_info(f"Collected average daily volume for {ticker_symbol}: {average_daily_volume:.2f}.")
            else:
                log_warning(f"Could not collect average daily volume for {ticker_symbol}.")

            # Collect 30-day volume change
            thirty_day_volume_change = _calculate_30d_volume_change(ticker_symbol)
            if thirty_day_volume_change is not None:
                log_info(f"Collected 30-day volume change for {ticker_symbol}: {thirty_day_volume_change:.2f}%")
            else:
                log_warning(f"Could not collect 30-day volume change for {ticker_symbol}.")

            # Collect 1-week percentage performance
            one_week_performance = _calculate_percentage_performance(ticker_symbol, 7)
            if one_week_performance is not None:
                log_info(f"Collected 1-week performance for {ticker_symbol}: {one_week_performance:.2f}%")
            else:
                log_warning(f"Could not collect 1-week performance for {ticker_symbol}.")
            
            # Collect 1-month percentage performance
            one_month_performance = _calculate_percentage_performance(ticker_symbol, 30)
            if one_month_performance is not None:
                log_info(f"Collected 1-month performance for {ticker_symbol}: {one_month_performance:.2f}%")
            else:
                log_warning(f"Could not collect 1-month performance for {ticker_symbol}.")

            # Collect 3-month percentage performance
            three_month_performance = _calculate_percentage_performance(ticker_symbol, 90)
            if three_month_performance is not None:
                log_info(f"Collected 3-month performance for {ticker_symbol}: {three_month_performance:.2f}%")
            else:
                log_warning(f"Could not collect 3-month performance for {ticker_symbol}.")

            # Attempt to get EPS growth from 'financialData' or 'earningsTrend'
            if ticker_symbol in data and 'financialData' in data[ticker_symbol]:
                financial_data = data[ticker_symbol]['financialData']
                eps_growth = financial_data.get('earningsGrowth') # Example key
                if eps_growth is not None:
                    log_info(f"Collected EPS growth for {ticker_symbol}: {eps_growth}")
                else:
                    log_warning(f"EPS growth not found in financialData for {ticker_symbol}.")
            elif ticker_symbol in data and 'earningsTrend' in data[ticker_symbol]:
                # Earnings trend might have a list of trends, we might need to pick the latest or average
                earnings_trend_list = data[ticker_symbol]['earningsTrend'].get('trend', [])
                if earnings_trend_list:
                    # Assuming we want the latest annual EPS growth
                    for trend_item in earnings_trend_list:
                        if trend_item.get('period') == '+1y': # Next year's estimate
                            eps_growth = trend_item.get('earningsEstimate', {}).get('growth')
                            break
                    if eps_growth is not None:
                        log_info(f"Collected EPS growth from earningsTrend for {ticker_symbol}: {eps_growth}")
                    else:
                        log_warning(f"EPS growth not found in earningsTrend for {ticker_symbol}.")
            else:
                log_warning(f"No financialData or earningsTrend found for {ticker_symbol} to get EPS growth.")

            ticker_data[ticker_symbol] = {
                'market_cap': market_cap,
                'forward_pe': forward_pe,
                'eps_growth': eps_growth,
                'dilution_proxy': dilution_proxy, # Add dilution_proxy
                '30d_average_daily_range_pips': average_daily_range_pips, # Add 30-day average daily range in pips
                'momentum_spread': momentum_spread, # Add momentum_spread
                'average_daily_volume': average_daily_volume, # Add average_daily_volume
                '30d_volume_change': thirty_day_volume_change, # Add 30-day volume change
                '1w': one_week_performance,
                '1m': one_month_performance,
                '3m': three_month_performance
            }

    except Exception as e:
        log_error(f"An error occurred while fetching ticker data: {e}", "YAHOOQUERY_ERROR", e)
        for ticker_symbol in tickers:
            if ticker_symbol not in ticker_data:
                ticker_data[ticker_symbol] = {'market_cap': None, 'forward_pe': None, 'eps_growth': None, 'dilution_proxy': None, '30d_average_daily_range_pips': None, 'momentum_spread': None, 'average_daily_volume': None, '30d_volume_change': None}

    return ticker_data

def _calculate_30d_average_daily_range_in_pips(ticker_symbol: str) -> Optional[float]:
    """
    Calculates the 30-day average daily range in pips for a given FX ticker using yahooquery.
    Handles JPY pairs differently for pip calculation.

    Args:
        ticker_symbol (str): The FX ticker symbol (e.g., 'EURUSD=X', 'USDJPY=X').

    Returns:
        float: The 30-day average daily range in pips, or None if data is unavailable or an error occurs.
    """
    try:
        # Fetch historical data for the last 45 days to ensure 30 trading days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=45)
        
        # Using yahooquery to get historical data
        yq_ticker = Ticker(ticker_symbol)
        data = yq_ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
        
        if data.empty or ticker_symbol not in data.index.get_level_values('symbol'):
            log_warning(f"No historical data available for {ticker_symbol} to calculate 30-day average daily range using yahooquery.", "AVG_DAILY_RANGE_CALCULATION")
            return None

        # Extract data for the specific ticker
        ticker_data = data.loc[ticker_symbol]

        # Ensure we have at least 30 days of data
        if len(ticker_data) < 30:
            log_warning(f"Less than 30 days of historical data for {ticker_symbol}. Cannot accurately calculate 30-day average daily range.", "AVG_DAILY_RANGE_CALCULATION")
            return None

        # Get the last 30 trading days
        ticker_data = ticker_data.tail(30)

        daily_ranges_in_pips = []
        is_jpy_pair = "JPY" in ticker_symbol.upper()

        for index, row in ticker_data.iterrows():
            high = row["high"]
            low = row["low"]
            daily_range = high - low

            # Convert to pips
            if is_jpy_pair:
                # For JPY pairs, 1 pip is 0.01
                daily_range_pips = daily_range * 100
            else:
                # For most other pairs, 1 pip is 0.0001
                daily_range_pips = daily_range * 10000
            
            daily_ranges_in_pips.append(daily_range_pips)

        if not daily_ranges_in_pips:
            return None

        average_daily_range_pips = sum(daily_ranges_in_pips) / len(daily_ranges_in_pips)
        log_info(f"Calculated 30-day average daily range for {ticker_symbol}: {average_daily_range_pips:.2f} pips using yahooquery.", "AVG_DAILY_RANGE_CALCULATION")
        return round(average_daily_range_pips, 2)

    except Exception as e:
        log_error(f"Error calculating 30-day average daily range for {ticker_symbol} using yahooquery: {e}", "AVG_DAILY_RANGE_CALCULATION", e)
        return None


def _calculate_momentum_spread(ticker_symbol: str) -> Optional[float]:
    """
    Calculates the momentum spread for a given ticker using yahooquery data.

    Args:
        ticker_symbol (str): The ticker symbol (e.g., 'AAPL').

    Returns:
        float: The momentum spread, or None if data is unavailable or an error occurs.
    """
    try:
        lookback_momentum = 20  # Approximately 1 month of trading days
        lookback_range = 20     # For average daily range calculation

        end_date = datetime.now()
        # Fetch enough data for both lookback periods
        start_date = end_date - timedelta(days=max(lookback_momentum, lookback_range) * 2) # Get more days to be safe
        
        yq_ticker = Ticker(ticker_symbol)
        data = yq_ticker.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))

        if data.empty or ticker_symbol not in data.index.get_level_values("symbol"):
            log_warning(f"No historical data available for {ticker_symbol} to calculate momentum spread.", "MOMENTUM_SPREAD_CALCULATION")
            return None

        ticker_data = data.loc[ticker_symbol]

        if len(ticker_data) < max(lookback_momentum, lookback_range):
            log_warning(f"Not enough historical data for {ticker_symbol} to calculate momentum spread.", "MOMENTUM_SPREAD_CALCULATION")
            return None

        close = ticker_data["close"]
        high = ticker_data["high"]
        low = ticker_data["low"]

        # 1M Momentum (%)
        momentum = close.pct_change(lookback_momentum).iloc[-1] * 100

        # Average daily range as % of price (spread proxy)
        range_pct = ((high - low) / close).rolling(lookback_range).mean().iloc[-1] * 100

        # Avoid divide-by-zero
        if range_pct == 0:
            range_pct = np.nan # Use numpy.nan for consistency

        # Momentum per unit of friction
        if pd.isna(momentum) or pd.isna(range_pct):
            momentum_spread = None
        else:
            momentum_spread = momentum / range_pct

        log_info(f"Calculated momentum spread for {ticker_symbol}: {momentum_spread:.2f}", "MOMENTUM_SPREAD_CALCULATION")
        return momentum_spread

    except Exception as e:
        log_error(f"Error calculating momentum spread for {ticker_symbol}: {e}", "MOMENTUM_SPREAD_CALCULATION", e)
        return None


def _calculate_average_daily_volume(ticker_symbol: str, lookback_days: int = 30) -> Optional[float]:
    """
    Calculates the average daily volume for a given ticker over a specified lookback period using yahooquery.

    Args:
        ticker_symbol (str): The ticker symbol (e.g., 'AAPL').
        lookback_days (int): The number of days to look back for calculating the average volume.

    Returns:
        float: The average daily volume, or None if data is unavailable or an error occurs.
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days * 2) # Fetch more data to ensure enough trading days
        
        yq_ticker = Ticker(ticker_symbol)
        data = yq_ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))

        if data.empty or ticker_symbol not in data.index.get_level_values('symbol'):
            log_warning(f"No historical data available for {ticker_symbol} to calculate average daily volume.", "AVG_DAILY_VOLUME_CALCULATION")
            return None

        ticker_data = data.loc[ticker_symbol]

        if len(ticker_data) < lookback_days:
            log_warning(f"Less than {lookback_days} days of historical data for {ticker_symbol}. Cannot accurately calculate average daily volume.", "AVG_DAILY_VOLUME_CALCULATION")
            return None

        # Get the volume for the specified lookback days
        recent_volume = ticker_data['volume'].tail(lookback_days)

        average_volume = recent_volume.mean()

        log_info(f"Calculated {lookback_days}-day average daily volume for {ticker_symbol}: {average_volume:.2f}", "AVG_DAILY_VOLUME_CALCULATION")
        return round(average_volume, 2)

    except Exception as e:
        log_error(f"Error calculating average daily volume for {ticker_symbol}: {e}", "AVG_DAILY_VOLUME_CALCULATION", e)
        return None


def _calculate_30d_volume_change(ticker_symbol: str) -> Optional[float]:
    """
    Calculates the 30-day volume change for a given ticker using yahooquery.
    This is the percentage change of the last 30-day average volume compared to the previous 30-day average volume.

    Args:
        ticker_symbol (str): The ticker symbol (e.g., 'AAPL').

    Returns:
        float: The 30-day volume change percentage, or None if data is unavailable or an error occurs.
    """
    try:
        lookback_days = 30
        total_days_needed = lookback_days * 2 + 10 # Get a bit more data to ensure two full 30-day periods

        end_date = datetime.now()
        start_date = end_date - timedelta(days=total_days_needed)
        
        yq_ticker = Ticker(ticker_symbol)
        data = yq_ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))

        if data.empty or ticker_symbol not in data.index.get_level_values('symbol'):
            log_warning(f"No historical data available for {ticker_symbol} to calculate 30-day volume change.", "30D_VOLUME_CHANGE_CALCULATION")
            return None

        ticker_data = data.loc[ticker_symbol]

        if len(ticker_data) < lookback_days * 2:
            log_warning(f"Less than {lookback_days * 2} days of historical data for {ticker_symbol}. Cannot accurately calculate 30-day volume change.", "30D_VOLUME_CHANGE_CALCULATION")
            return None

        # Get the volume for the last two 30-day periods
        recent_60_days_volume = ticker_data['volume'].tail(lookback_days * 2)

        current_30d_avg_volume = recent_60_days_volume.iloc[-lookback_days:].mean()
        previous_30d_avg_volume = recent_60_days_volume.iloc[:-lookback_days].mean()

        if previous_30d_avg_volume == 0:
            log_warning(f"Previous 30-day average volume is zero for {ticker_symbol}. Cannot calculate 30-day volume change.", "30D_VOLUME_CHANGE_CALCULATION")
            return None
        
        thirty_day_volume_change = ((current_30d_avg_volume - previous_30d_avg_volume) / previous_30d_avg_volume) * 100

        log_info(f"Calculated 30-day volume change for {ticker_symbol}: {thirty_day_volume_change:.2f}%", "30D_VOLUME_CHANGE_CALCULATION")
        return round(thirty_day_volume_change, 2)

    except Exception as e:
        log_error(f"Error calculating 30-day volume change for {ticker_symbol}: {e}", "30D_VOLUME_CHANGE_CALCULATION", e)
        return None


def _calculate_percentage_performance(ticker_symbol: str, lookback_days: int) -> Optional[float]:
    """
    Calculates the percentage performance of a ticker over a specified number of lookback days.

    Args:
        ticker_symbol (str): The ticker symbol (e.g., 'AAPL').
        lookback_days (int): The number of days to look back for calculating the percentage change.

    Returns:
        float: The percentage performance, or None if data is unavailable or an error occurs.
    """
    try:
        end_date = datetime.now()
        # Fetch enough data to cover the lookback period, adding a buffer for non-trading days.
        start_date = end_date - timedelta(days=lookback_days * 2) # Get more days to be safe
        
        yq_ticker = Ticker(ticker_symbol)
        data = yq_ticker.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))

        if data.empty or ticker_symbol not in data.index.get_level_values("symbol"):
            log_warning(f"No historical data available for {ticker_symbol} to calculate {lookback_days}-day percentage performance.", "PERFORMANCE_CALCULATION")
            return None

        ticker_data = data.loc[ticker_symbol]

        # Ensure we have enough data points for the lookback period
        if len(ticker_data) < lookback_days:
            log_warning(f"Less than {lookback_days} days of historical data for {ticker_symbol}. Cannot accurately calculate {lookback_days}-day performance.", "PERFORMANCE_CALCULATION")
            return None

        # Get the closing prices for the relevant period
        close_prices = ticker_data["close"].tail(lookback_days + 1) # Need current day and 'lookback_days' previous days

        if len(close_prices) < lookback_days + 1:
            log_warning(f"Not enough closing prices for {ticker_symbol} to calculate {lookback_days}-day performance.", "PERFORMANCE_CALCULATION")
            return None

        initial_price = close_prices.iloc[0]
        final_price = close_prices.iloc[-1]

        if initial_price == 0:
            log_warning(f"Initial price is zero for {ticker_symbol}. Cannot calculate {lookback_days}-day percentage performance.", "PERFORMANCE_CALCULATION")
            return None

        percentage_performance = ((final_price - initial_price) / initial_price) * 100

        log_info(f"Calculated {lookback_days}-day percentage performance for {ticker_symbol}: {percentage_performance:.2f}%", "PERFORMANCE_CALCULATION")
        return round(percentage_performance, 2)

    except Exception as e:
        log_error(f"Error calculating {lookback_days}-day percentage performance for {ticker_symbol}: {e}", "PERFORMANCE_CALCULATION", e)
        return None


def update_ticker_data_in_db():
    """
    Orchestrates the complete process of fetching all active ticker symbols from the MongoDB database,
    collecting a comprehensive suite of financial and market data points for each ticker,
    and subsequently updating these data points in the database.

    The collected data includes:
    - Market capitalization (`market_cap`)
    - Forward Price-to-Earnings ratio (`forward_pe`)
    - Earnings Per Share growth (`eps_growth`)
    - Dilution proxy (`dilution_proxy`), calculated from circulating and max supply for cryptocurrencies.
    - 30-day average daily range in pips (`30d_average_daily_range_pips`) for FX pairs.
    - Momentum spread (`momentum_spread`), indicating momentum per unit of price friction.
    - Average daily volume (`average_daily_volume`)
    - 30-day volume change (`30d_volume_change`), reflecting recent volume trends.
    - 1-week percentage performance (`1w`).
    - 1-month percentage performance (`1m`).
    - 3-month percentage performance (`3m`).

    This function ensures that the ticker data in the database is current and comprehensive,
    handling potential errors during data collection and database operations with robust logging.
    """
    load_dotenv()
    log_info("Starting ticker data update process...")

    tickers_from_db = get_tickers_from_db()

    if not tickers_from_db:
        log_warning("No tickers found in the database to update data.")
        return

    log_info(f"Total {len(tickers_from_db)} tickers to process in batches.")
    
    batch_size = 100
    all_ticker_data = {}

    for i in range(0, len(tickers_from_db), batch_size):
        ticker_batch = tickers_from_db[i:i + batch_size]
        log_info(f"Processing batch {int(i/batch_size) + 1}/{(len(tickers_from_db) + batch_size - 1) // batch_size} with {len(ticker_batch)} tickers.")
        
        batch_data = collect_ticker_data(ticker_batch)
        all_ticker_data.update(batch_data)
        
        if (i + batch_size) < len(tickers_from_db):
            log_info("Pausing for 60 seconds before next batch...")
            time.sleep(60) # Pause for 60 seconds between batches

    if not all_ticker_data:
        log_warning("No ticker data collected for any tickers.")
        return

    client = None
    try:
        client = DatabaseManager().get_client()
        db = client[os.getenv("MONGODB_DATABASE", "alphasentra-core")]
        collection = db["tickers"]
        
        updated_count = 0
        for ticker_symbol, data in all_ticker_data.items():
            update_fields = {}
            if data["market_cap"] is not None:
                update_fields["market_cap"] = data["market_cap"]
            if data["forward_pe"] is not None:
                update_fields["forward_pe"] = data["forward_pe"]
            if data["eps_growth"] is not None:
                update_fields["eps_growth"] = data["eps_growth"]
            if data["dilution_proxy"] is not None:
                update_fields["dilution_proxy"] = data["dilution_proxy"]
            if data["30d_average_daily_range_pips"] is not None: # Add 30-day average daily range in pips to update fields
                update_fields["30d_average_daily_range_pips"] = data["30d_average_daily_range_pips"]
            if data["momentum_spread"] is not None:
                update_fields["momentum_spread"] = data["momentum_spread"]
            if data["average_daily_volume"] is not None:
                update_fields["average_daily_volume"] = data["average_daily_volume"]
            if data["30d_volume_change"] is not None:
                update_fields["30d_volume_change"] = data["30d_volume_change"]
            if data["1w_performance"] is not None:
                update_fields["1w"] = data["1w_performance"]
            if data["1m_performance"] is not None:
                update_fields["1m"] = data["1m_performance"]
            if data["3m_performance"] is not None:
                update_fields["3m"] = data["3m_performance"]

            if update_fields:
                result = collection.update_one(
                    {"ticker": ticker_symbol},
                    {"$set": update_fields}
                )
                if result.modified_count > 0:
                    log_info(f"Updated data for {ticker_symbol}: {update_fields}.")
                    updated_count += 1
                elif result.upserted_id is not None:
                    log_warning(f"Inserted data for new ticker {ticker_symbol}: {update_fields}.")
                    updated_count += 1
                else:
                    log_info(f"Data for {ticker_symbol} already up-to-date or no change.")
            else:
                log_warning(f"No valid data to update for {ticker_symbol}. Skipping.")

        log_info(f"Finished updating ticker data. Total {updated_count} tickers updated/inserted.")

    except pymongo.errors.ServerSelectionTimeoutError as e:
        log_error("MongoDB server not found. Ensure MongoDB is running on the specified host/port.", "MONGODB_CONNECTION", e)
    except pymongo.errors.OperationFailure as e:
        log_error(f"MongoDB operation failed during ticker data update: {e}", "MONGODB_OPERATION", e)
    except Exception as e:
        log_error(f"An unexpected error occurred during ticker data update: {e}", "DATA_UPDATE_ERROR", e)
    finally:
        if client:
            DatabaseManager().close_connection()


if __name__ == '__main__':
    update_ticker_data_in_db()
