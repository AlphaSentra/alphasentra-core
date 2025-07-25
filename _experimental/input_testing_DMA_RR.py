import yfinance as yf
import pandas as pd
import numpy as np

def calculate_returns(prices):
    return (prices.pct_change().dropna() + 1).cumprod()

def calculate_drawdown(cumulative_returns):
    roll_max = cumulative_returns.cummax()
    drawdown = cumulative_returns / roll_max - 1
    return drawdown.min()

def backtest_strategy(spy_ticker, long_ticker, alt_ticker, dma_period):
    # Download historical data
    spy = yf.download(spy_ticker, start='2000-01-01', progress=False)['Close']
    long = yf.download(long_ticker, start='2000-01-01', progress=False)['Close']
    alt = yf.download(alt_ticker, start='2000-01-01', progress=False)['Close']

    # Combine and align
    df = pd.DataFrame({
        'SPY': spy,
        'LONG': long,
        'ALT': alt
    }).dropna()

    # Calculate DMA
    df['DMA'] = df['SPY'].rolling(window=dma_period).mean()
    df = df.dropna()

    # Signal: SPY above DMA -> buy long; else buy alt
    df['Signal'] = np.where(df['SPY'] > df['DMA'], 'LONG', 'ALT')

    # Simulated strategy returns
    df['Strategy_Price'] = np.where(df['Signal'] == 'LONG', df['LONG'], df['ALT'])
    df['Strategy_Return'] = df['Strategy_Price'].pct_change().fillna(0)
    df['Strategy_Cum'] = (1 + df['Strategy_Return']).cumprod()

    # Risk-reward logic: simplified entry-exit tracking
    df['Trade_Entry'] = df['Signal'].ne(df['Signal'].shift())
    df['Trade_Peak'] = df['Strategy_Cum'].where(df['Trade_Entry']).ffill()
    df['Trade_Drawdown'] = df['Strategy_Cum'] / df['Trade_Peak'] - 1

    # SPY buy and hold
    spy_cum = calculate_returns(df['SPY'])
    strategy_cum = df['Strategy_Cum']

    # Final outputs
    spy_return = spy_cum.iloc[-1] - 1
    strat_return = strategy_cum.iloc[-1] - 1
    spy_dd = calculate_drawdown(spy_cum)
    strat_dd = calculate_drawdown(strategy_cum)

    print("\nPerformance Summary:")
    print(f"SPY Buy & Hold Return: {spy_return:.2%}")
    print(f"Strategy Return       : {strat_return:.2%}")
    print(f"SPY Max Drawdown      : {spy_dd:.2%}")
    print(f"Strategy Max Drawdown : {strat_dd:.2%}")

    return df

if __name__ == "__main__":
    spy_ticker = input("Enter SPY ticker (e.g., SPY): ").strip().upper()
    long_ticker = input("Enter LONG ticker when above DMA (e.g., QQQ): ").strip().upper()
    alt_ticker = input("Enter ALT ticker when below DMA (e.g., GLD): ").strip().upper()
    dma_period = int(input("Enter DMA period (e.g., 200): "))

    results = backtest_strategy(
        spy_ticker=spy_ticker,
        long_ticker=long_ticker,
        alt_ticker=alt_ticker,
        dma_period=dma_period
    )
