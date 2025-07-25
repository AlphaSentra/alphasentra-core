import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def calculate_drawdown(cum_returns: pd.Series) -> pd.Series:
    """Calculate drawdown series from cumulative returns."""
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak) / peak
    return drawdown

def backtest_strategy_ticker_vs_alt_on_dma(
    ticker='SSO',
    alt_ticker='GLD',
    benchmark_ticker='SPY',
    dma_period=200,
    start_date='2015-01-01',
    end_date='2025-01-01'
):
    # Download data
    benchmark = yf.download(benchmark_ticker, start=start_date, end=end_date, auto_adjust=False)
    asset = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)
    alt_asset = yf.download(alt_ticker, start=start_date, end=end_date, auto_adjust=False)
    spy = yf.download('SPY', start=start_date, end=end_date, auto_adjust=False)

    if benchmark.empty or asset.empty or alt_asset.empty or spy.empty:
        raise ValueError("Data download failed. Check tickers and date range.")

    # Calculate benchmark DMA
    dma_col = f'{dma_period}DMA'
    benchmark[dma_col] = benchmark['Close'].rolling(window=dma_period).mean()

    # Buy & Hold benchmark returns
    benchmark['BuyHold_Returns'] = benchmark['Close'].pct_change()
    benchmark['BuyHold_CumReturns'] = (1 + benchmark['BuyHold_Returns']).cumprod()

    # Buy & Hold SPY returns
    spy['BuyHold_Returns'] = spy['Close'].pct_change()
    spy['BuyHold_CumReturns'] = (1 + spy['BuyHold_Returns']).cumprod()

    # Daily returns for tickers
    asset['Returns'] = asset['Close'].pct_change()
    alt_asset['Returns'] = alt_asset['Close'].pct_change()

    # Align benchmark close and DMA (ensure both are Series)
    benchmark_close = benchmark['Close'].squeeze()
    benchmark_dma = benchmark[dma_col].squeeze()
    benchmark_close, benchmark_dma = benchmark_close.align(benchmark_dma, join='inner', axis=0)

    # Signal: 1 if benchmark close > DMA else 0
    signal = (benchmark_close > benchmark_dma).astype(int)

    # Align returns
    asset_returns = asset['Returns'].reindex(signal.index).fillna(0)
    alt_returns = alt_asset['Returns'].reindex(signal.index).fillna(0)

    # Strategy logic
    shifted_signal = signal.shift(1).fillna(0)
    strategy_returns = shifted_signal * asset_returns + (1 - shifted_signal) * alt_returns
    strategy_cum_returns = (1 + strategy_returns).cumprod()

    # Combine cumulative returns including SPY buy & hold
    combined = pd.DataFrame({
        f'BuyHold_{benchmark_ticker}': benchmark['BuyHold_CumReturns'].reindex(strategy_cum_returns.index).fillna(method='ffill'),
        f'Strategy_{ticker}_vs_{alt_ticker}_on_{benchmark_ticker}_{dma_period}DMA': strategy_cum_returns,
        'BuyHold_SPY': spy['BuyHold_CumReturns'].reindex(strategy_cum_returns.index).fillna(method='ffill'),
    })

    # Drawdowns
    dd_benchmark = calculate_drawdown(combined[f'BuyHold_{benchmark_ticker}'])
    dd_strategy = calculate_drawdown(combined.iloc[:, 1])
    dd_spy = calculate_drawdown(combined['BuyHold_SPY'])

    # Plot cumulative returns (Strategy and SPY only)
    plt.figure(figsize=(12, 6))
    plt.plot(combined.index, combined.iloc[:, 1], label=combined.columns[1])  # Strategy
    plt.plot(combined.index, combined['BuyHold_SPY'], label='Buy & Hold SPY')
    plt.title(f'Cumulative Returns: {ticker} vs {alt_ticker} (DMA on {benchmark_ticker}) + SPY Benchmark')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns')
    plt.legend()
    plt.grid(True)
    plt.show()

    # Plot drawdowns (Strategy and SPY only)
    plt.figure(figsize=(12, 6))
    plt.plot(dd_strategy.index, dd_strategy, label='Strategy Drawdown')
    plt.plot(dd_spy.index, dd_spy, label='SPY Drawdown')
    plt.title(f'Drawdowns: {ticker} vs {alt_ticker} (DMA on {benchmark_ticker}) + SPY Benchmark')
    plt.xlabel('Date')
    plt.ylabel('Drawdown')
    plt.legend()
    plt.grid(True)
    plt.show()

    # Summary
    buyhold_return = (combined[f'BuyHold_{benchmark_ticker}'].iloc[-1] - 1) * 100
    strategy_return = (combined.iloc[-1, 1] - 1) * 100
    spy_return = (combined['BuyHold_SPY'].iloc[-1] - 1) * 100

    max_dd_benchmark = dd_benchmark.min() * 100
    max_dd_strategy = dd_strategy.min() * 100
    max_dd_spy = dd_spy.min() * 100

    print(f"Period: {start_date} to {end_date}")
    print(f"Buy & Hold {benchmark_ticker} return: {buyhold_return:.2f}%")
    print(f"Strategy return: {strategy_return:.2f}%")
    print(f"Buy & Hold SPY return: {spy_return:.2f}%")
    print(f"{benchmark_ticker} max drawdown: {max_dd_benchmark:.2f}%")
    print(f"Strategy max drawdown: {max_dd_strategy:.2f}%")
    print(f"SPY max drawdown: {max_dd_spy:.2f}%")

    return combined

if __name__ == "__main__":
    ticker_input = input("Enter main ticker to trade when DMA signal is bullish (e.g., SSO): ").strip().upper()
    alt_ticker_input = input("Enter alternative ticker when signal is bearish (default GLD): ").strip().upper()
    alt_ticker = alt_ticker_input if alt_ticker_input else 'GLD'

    dma_input = input("Enter DMA period (default 200): ").strip()
    dma_period = int(dma_input) if dma_input.isdigit() else 200

    benchmark_input = input("Enter benchmark ticker for DMA signal (default SPY): ").strip().upper()
    benchmark_ticker = benchmark_input if benchmark_input else 'SPY'

    df_results = backtest_strategy_ticker_vs_alt_on_dma(
        ticker=ticker_input,
        alt_ticker=alt_ticker,
        benchmark_ticker=benchmark_ticker,
        dma_period=dma_period
    )
