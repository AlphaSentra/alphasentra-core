import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def calculate_atr(data, period=14):
    """Calculates the Average True Range (ATR) using the standard EMA method."""
    data['high-low'] = data['High'] - data['Low']
    data['high-prev_close'] = np.abs(data['High'] - data['Close'].shift(1))
    data['low-prev_close'] = np.abs(data['Low'] - data['Close'].shift(1))
    
    # The True Range is the greatest of the three values.
    data['true_range'] = data[['high-low', 'high-prev_close', 'low-prev_close']].max(axis=1)
    
    # Calculate the ATR using an Exponential Moving Average (EMA)
    data['atr'] = data['true_range'].ewm(span=period, adjust=False).mean()
    
    # Clean up the temporary columns
    data.drop(['high-low', 'high-prev_close', 'low-prev_close', 'true_range'], axis=1, inplace=True)
    return data

def run_backtest(
    ticker='SPY',
    filter_ticker='SPY',
    start_date='2020-01-01',
    end_date='2024-01-01',
    initial_capital=10000.0,
    long_ma_period=200, # Period for the long-term trend filter
    atr_period=14,
    atr_multiplier=2.0, # Stop loss will be 2 * ATR below entry
    risk_reward_ratio=2.0
):
    """
    Runs a backtest for a strategy that trades a ticker based on the 200 DMA of a filter ticker.

    Args:
        ticker (str): The stock ticker to trade (e.g., 'SSO').
        filter_ticker (str): The ticker to use for the 200 DMA filter (e.g., 'SPY').
        start_date (str): The start date for historical data (YYYY-MM-DD).
        end_date (str): The end date for historical data (YYYY-MM-DD).
        initial_capital (float): The starting capital for the backtest.
        long_ma_period (int): The period for the long-term trend-following moving average.
        atr_period (int): The period for the Average True Range (ATR) calculation.
        atr_multiplier (float): The multiplier for the ATR to set the stop loss.
        risk_reward_ratio (float): The ratio of potential reward to risk.
    """

    # --- 1. Data Fetching and Indicator Calculation ---
    print(f"Fetching data for trading ticker {ticker} and filter ticker {filter_ticker}...")
    try:
        # Download data for the asset to be traded
        data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)
        # Download data for the filter asset
        filter_data = yf.download(filter_ticker, start=start_date, end=end_date, auto_adjust=True)

        if data.empty or filter_data.empty:
            print(f"No data found for one of the tickers. Please check the symbols.")
            return
    except Exception as e:
        print(f"An error occurred while fetching data: {e}")
        return

    # --- Calculate Indicators and Combine Data ---
    # ATR for the traded asset
    data = calculate_atr(data, period=atr_period)
    # 200 DMA for the filter asset
    filter_data['filter_ma'] = filter_data['Close'].rolling(window=long_ma_period).mean()
    
    # Prepare filter data with a specific column name for joining
    filter_data.rename(columns={'Close': 'filter_close'}, inplace=True)
    # Join the two dataframes on their index. 'how=inner' ensures we only use dates where both assets have data.
    data = data.join(filter_data[['filter_ma', 'filter_close']], how='inner')

    # Drop any remaining NA values after indicators and join
    data.dropna(inplace=True)

    # --- 2. Backtesting Logic ---
    print(f"Running backtest: Trading {ticker} using {filter_ticker} 200 DMA as filter...")
    trades = []
    in_position = False
    entry_price = 0
    entry_date = None
    stop_loss_price = 0
    take_profit_price = 0

    # Get integer locations for columns for faster access
    open_col = data.columns.get_loc('Open')
    high_col = data.columns.get_loc('High')
    low_col = data.columns.get_loc('Low')
    close_col = data.columns.get_loc('Close')
    filter_ma_col = data.columns.get_loc('filter_ma')
    filter_close_col = data.columns.get_loc('filter_close')
    atr_col = data.columns.get_loc('atr')
    
    # Convert dataframe to numpy array for faster, non-indexed access in loop
    data_np = data.to_numpy()
    data_index = data.index

    # Iterate through each day in the historical data, starting from the second element
    for i in range(1, len(data_np)):
        # --- Exit Logic: Check before entry logic ---
        if in_position:
            current_high = data_np[i, high_col]
            current_low = data_np[i, low_col]

            # Check for Take Profit hit
            if current_high >= take_profit_price:
                trades.append({
                    'entry_date': entry_date, 'entry_price': entry_price,
                    'exit_date': data_index[i], 'exit_price': take_profit_price,
                    'reason': 'Take Profit'
                })
                in_position = False

            # Check for Stop Loss hit
            elif current_low <= stop_loss_price:
                trades.append({
                    'entry_date': entry_date, 'entry_price': entry_price,
                    'exit_date': data_index[i], 'exit_price': stop_loss_price,
                    'reason': 'Stop Loss'
                })
                in_position = False

        # --- Entry Logic ---
        # If not in a position, check filter and then enter at the open of the current day.
        if not in_position:
            # Check the filter ticker's 200 DMA from the previous day
            prev_filter_close = data_np[i-1, filter_close_col]
            prev_filter_ma = data_np[i-1, filter_ma_col]

            if prev_filter_close > prev_filter_ma:
                # If filter passes, enter the trade in the main ticker at today's open
                in_position = True
                entry_price = data_np[i, open_col] # Enter at today's open
                entry_date = data_index[i]
                # Use ATR from the previous day of the traded ticker to set the stop
                atr_from_prev_day = data_np[i-1, atr_col]
                
                # Calculate Stop Loss and Take Profit based on ATR
                stop_loss_price = entry_price - (atr_from_prev_day * atr_multiplier)
                risk_amount = entry_price - stop_loss_price
                take_profit_price = entry_price + (risk_amount * risk_reward_ratio)

    # --- Close any open trade at the end of the backtest ---
    if in_position:
        trades.append({
            'entry_date': entry_date, 'entry_price': entry_price,
            'exit_date': data_index[-1], 'exit_price': data_np[-1, close_col],
            'reason': 'End of Backtest'
        })

    # --- 3. Performance Analysis ---
    if not trades:
        print("\nNo trades were executed during the backtest period.")
        return

    print("Analyzing performance...")
    # --- FIX: Create the DataFrame AFTER all trades (including the final one) are logged ---
    trades_df = pd.DataFrame(trades)
    trades_df['pnl'] = trades_df['exit_price'] - trades_df['entry_price']
    trades_df['equity'] = initial_capital + trades_df['pnl'].cumsum()
    
    # Calculate statistics
    total_trades = len(trades_df)
    winning_trades = trades_df[trades_df['pnl'] > 0]
    losing_trades = trades_df[trades_df['pnl'] <= 0]
    
    win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
    total_pnl = trades_df['pnl'].sum()
    final_equity = trades_df['equity'].iloc[-1] if not trades_df.empty else initial_capital
    strategy_return_pct = (final_equity / initial_capital - 1) * 100
    average_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
    average_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
    
    if abs(average_loss) > 0: realized_rr = abs(average_win / average_loss)
    else: realized_rr = float('inf')

    # --- Calculate Buy & Hold Performance for the filter ticker (SPY) ---
    spy_data_in_period = filter_data.loc[data.index]
    spy_start_price = spy_data_in_period['filter_close'].iloc[0]
    spy_end_price = spy_data_in_period['filter_close'].iloc[-1]
    spy_return_pct = (spy_end_price / spy_start_price - 1) * 100
    spy_buy_and_hold_equity = initial_capital * (1 + spy_return_pct / 100)


    # --- 4. Display Results ---
    print("\n--- Backtest Results ---")
    print(f"Period: {data.index[0].date()} to {data.index[-1].date()}")
    print(f"Strategy: Trade {ticker} using {filter_ticker}'s {long_ma_period} DMA as a filter.")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print("-" * 26)
    print(f"Total Trades: {total_trades}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Average Winning Trade: ${float(average_win):.2f}")
    print(f"Average Losing Trade: ${float(average_loss):.2f}")
    print(f"Realized Reward/Risk Ratio: {float(realized_rr):.2f}:1")
    print("-" * 26)
    print("--- Performance Comparison ---")
    print(f"Strategy Final Equity: ${float(final_equity):,.2f} ({float(strategy_return_pct):.2f}%)")
    print(f"Buy & Hold {filter_ticker} Final Equity: ${float(spy_buy_and_hold_equity):,.2f} ({float(spy_return_pct):.2f}%)")
    print("-" * 26)


    print("\n--- Trade Log ---")
    print(trades_df[['entry_date', 'entry_price', 'exit_date', 'exit_price', 'reason', 'pnl', 'equity']].round(2))
    
    # --- 5. Visualization ---
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
    fig.suptitle(f'{ticker} Trading Strategy Backtest (Filtered by {filter_ticker} 200DMA)', fontsize=16)

    # --- Plot 1: Price and Trades ---
    ax1.plot(data['Close'], label=f'{ticker} Close', color='skyblue', alpha=0.7)
    
    if not trades_df.empty:
        ax1.plot(trades_df['entry_date'], trades_df['entry_price'], '^', markersize=10, color='green', label='Buy Signal')
        tp_exits = trades_df[trades_df['reason'] == 'Take Profit']
        sl_exits = trades_df[trades_df['reason'] == 'Stop Loss']
        ax1.plot(tp_exits['exit_date'], tp_exits['exit_price'], 'v', markersize=10, color='blue', label='Take Profit Exit')
        ax1.plot(sl_exits['exit_date'], sl_exits['exit_price'], 'v', markersize=10, color='red', label='Stop Loss Exit')
    
    ax1.set_ylabel('Price ($)')
    ax1.legend()
    ax1.grid(True)

    # --- Plot 2: Equity Curve ---
    if not trades_df.empty:
        ax2.plot(trades_df['exit_date'], trades_df['equity'], label='Strategy Equity Curve', color='green', marker='o', linestyle='-')
        # Add Buy & Hold curve for comparison
        ax2.plot(spy_data_in_period.index, initial_capital * (spy_data_in_period['filter_close'] / spy_start_price), label=f'{filter_ticker} Buy & Hold', color='orange', linestyle='--')
        ax2.axhline(y=initial_capital, color='grey', linestyle=':', label=f'Initial Capital (${initial_capital:,.0f})')
    
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Portfolio Value ($)')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    plt.show()


if __name__ == '__main__':
    # You can customize the parameters here
    run_backtest(
        ticker='SPY',
        filter_ticker='SPY',
        start_date='2020-01-01',
        end_date='2024-01-01',
        initial_capital=10000.0,
        long_ma_period=200,
        atr_period=14,
        atr_multiplier=2.0, # Stop is 2x ATR value
        risk_reward_ratio=2.0 # Target profit is 2x the risk
    )
    print("\nDisclaimer: This script is for educational purposes only. Past performance is not indicative of future results.")
