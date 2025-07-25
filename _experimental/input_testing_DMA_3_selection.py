import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def calculate_drawdown(cum_returns: pd.Series) -> pd.Series:
    """Calculates the drawdown for a series of cumulative returns."""
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak) / peak
    return drawdown

def backtest_strategy_ticker_vs_alt_on_dma(
    ticker='QQQ',
    alt_ticker='SPY',
    safe_ticker='TLT',
    safe_pct=0.5,
    benchmark_ticker='QQQ',
    dma_period=200,
    start_date='2015-01-01',
    end_date='2025-01-01'
):
    """
    Backtests a strategy that switches between two assets based on a benchmark's moving average,
    while holding a constant percentage in a safe asset.
    """
    # 1. Efficiently download all required data
    all_tickers = list(set([benchmark_ticker, ticker, alt_ticker, safe_ticker, 'SPY']))
    try:
        data = yf.download(all_tickers, start=start_date, end=end_date, auto_adjust=False)
        if data.empty:
            raise ValueError("Failed to download any data.")
        close_data = data['Close'].dropna(axis=0, how='all') # Drop rows where all prices are NaN
    except Exception as e:
        print(f"Error downloading data: {e}")
        return

    # 2. Calculate DMA and handle resulting NaNs (CRITICAL FIX)
    dma_col = f'{dma_period}DMA'
    close_data[dma_col] = close_data[benchmark_ticker].rolling(window=dma_period).mean()
    close_data.dropna(inplace=True) # Remove rows with NaN to align all data

    if close_data.empty:
        print(f"Not enough data for DMA period of {dma_period}. Try an earlier start date or shorter period.")
        return

    # 3. Calculate daily and cumulative returns
    daily_returns = close_data[[ticker, alt_ticker, safe_ticker]].pct_change().fillna(0)
    close_data['BuyHold_SPY'] = (1 + close_data['SPY'].pct_change()).cumprod()
    close_data[f'BuyHold_{benchmark_ticker}'] = (1 + close_data[benchmark_ticker].pct_change()).cumprod()

    # 4. Generate the trading signal
    # Signal is 1 (bullish) if benchmark > DMA, else 0 (bearish)
    # .shift(1) prevents lookahead bias
    signal = (close_data[benchmark_ticker] > close_data[dma_col]).astype(int).shift(1).fillna(0)

    # 5. Calculate strategy returns
    equity_weight = 1 - safe_pct
    strategy_returns = equity_weight * (signal * daily_returns[ticker] + (1 - signal) * daily_returns[alt_ticker]) + safe_pct * daily_returns[safe_ticker]
    strategy_cum_returns = (1 + strategy_returns).cumprod()

    # 6. Combine results for analysis, avoiding duplicate columns (CRITICAL FIX)
    strategy_label = f'Strategy_{int(safe_pct*100)}%_{safe_ticker}_{ticker}_vs_{alt_ticker}'
    results_dict = {
        strategy_label: strategy_cum_returns,
        f'BuyHold_{benchmark_ticker}': close_data[f'BuyHold_{benchmark_ticker}']
    }
    if benchmark_ticker != 'SPY':
        results_dict['BuyHold_SPY'] = close_data['BuyHold_SPY']
    
    combined = pd.DataFrame(results_dict).dropna()

    # 7. Calculate drawdowns
    dd_strategy = calculate_drawdown(combined[strategy_label])
    dd_benchmark = calculate_drawdown(combined[f'BuyHold_{benchmark_ticker}'])
    dd_spy = calculate_drawdown(combined['BuyHold_SPY']) if 'BuyHold_SPY' in combined else None

    # 8. Plotting (Revised for clarity)
    # Plot Cumulative Returns
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(14, 7))
    plt.plot(combined.index, combined[strategy_label], label=strategy_label, linewidth=2)
    plt.plot(combined.index, combined[f'BuyHold_{benchmark_ticker}'], label=f'Buy & Hold {benchmark_ticker}', linestyle='--')
    if dd_spy is not None:
        plt.plot(combined.index, combined['BuyHold_SPY'], label='Buy & Hold SPY', linestyle=':', color='gray')
    plt.title(f'Cumulative Returns: Strategy vs. Benchmarks ({benchmark_ticker} {dma_period}-DMA)', fontsize=16)
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns')
    plt.legend()
    plt.show()

    # Plot Drawdowns
    plt.figure(figsize=(14, 7))
    plt.fill_between(dd_strategy.index, dd_strategy, 0, alpha=0.3, label=f'Strategy Drawdown')
    plt.plot(dd_benchmark.index, dd_benchmark, label=f'{benchmark_ticker} Drawdown', linestyle='--')
    if dd_spy is not None:
        plt.plot(dd_spy.index, dd_spy, label='SPY Drawdown', linestyle=':', color='gray')
    plt.title('Drawdowns: Strategy vs. Benchmarks', fontsize=16)
    plt.xlabel('Date')
    plt.ylabel('Drawdown')
    plt.legend()
    plt.show()

    # 9. Print Summary Statistics
    final_strategy_return = (combined[strategy_label].iloc[-1] - 1) * 100
    final_benchmark_return = (combined[f'BuyHold_{benchmark_ticker}'].iloc[-1] - 1) * 100
    
    print("\n--- Backtest Summary ---")
    print(f"Period: {combined.index.min().date()} to {combined.index.max().date()}")
    print(f"DMA Signal: {benchmark_ticker} vs. {dma_period}-Day Moving Average")
    print("-" * 26)
    print(f"Strategy Return: {final_strategy_return:.2f}%")
    print(f"Strategy Max Drawdown: {dd_strategy.min() * 100:.2f}%")
    print("-" * 26)
    print(f"Buy & Hold {benchmark_ticker} Return: {final_benchmark_return:.2f}%")
    print(f"Buy & Hold {benchmark_ticker} Max Drawdown: {dd_benchmark.min() * 100:.2f}%")
    if dd_spy is not None:
        final_spy_return = (combined['BuyHold_SPY'].iloc[-1] - 1) * 100
        print("-" * 26)
        print(f"Buy & Hold SPY Return: {final_spy_return:.2f}%")
        print(f"Buy & Hold SPY Max Drawdown: {dd_spy.min() * 100:.2f}%")
    print("--- End Summary ---\n")

    return combined

if __name__ == "__main__":
    ticker_input = input("Enter main ticker (e.g., QQQ): ").strip().upper() or 'QQQ'
    alt_ticker_input = input("Enter alternative ticker (e.g., SPY): ").strip().upper() or 'SPY'
    safe_ticker_input = input("Enter safe asset ticker (e.g., TLT): ").strip().upper() or 'TLT'
    benchmark_input = input(f"Enter benchmark for DMA signal (e.g., {ticker_input}): ").strip().upper() or ticker_input
    
    try:
        safe_pct_input = input("Enter safe asset allocation % (e.g., 50): ").strip()
        safe_pct = float(safe_pct_input) / 100 if safe_pct_input else 0.5
    except ValueError:
        print("Invalid percentage. Defaulting to 50%.")
        safe_pct = 0.5

    try:
        dma_input = input("Enter DMA period (e.g., 200): ").strip()
        dma_period = int(dma_input) if dma_input else 200
    except ValueError:
        print("Invalid period. Defaulting to 200.")
        dma_period = 200
        
    start_date_input = input("Enter start date (YYYY-MM-DD): ").strip() or '2015-01-01'
    end_date_input = input("Enter end date (YYYY-MM-DD): ").strip() or pd.Timestamp.now().strftime('%Y-%m-%d')


    df_results = backtest_strategy_ticker_vs_alt_on_dma(
        ticker=ticker_input,
        alt_ticker=alt_ticker_input,
        safe_ticker=safe_ticker_input,
        benchmark_ticker=benchmark_input,
        safe_pct=safe_pct,
        dma_period=dma_period,
        start_date=start_date_input,
        end_date=end_date_input
    )