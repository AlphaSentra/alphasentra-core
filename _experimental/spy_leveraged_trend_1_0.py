import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt

# Parameters
symbol = "SPY"
start_date = "2005-01-01"
end_date = "2024-12-31"
risk_reward_ratio = 2
leverage = 2
atr_period = 14
trend_sma_period = 50

# Download SPY data
data = yf.download(symbol, start=start_date, end=end_date, auto_adjust=False)

# Flatten columns if MultiIndex
if isinstance(data.columns, pd.MultiIndex):
    data.columns = [' '.join(col).strip() for col in data.columns.values]

# Remove ticker suffix (e.g. 'Close SPY' -> 'Close'), keep 'Adj Close' intact
new_cols = []
for col in data.columns:
    if col.startswith("Adj Close"):
        new_cols.append("Adj Close")
    else:
        new_cols.append(col.split(' ')[0])
data.columns = new_cols

print(f"Data shape: {data.shape}")
print(f"Columns after renaming: {data.columns.tolist()}")

# Choose price column: prefer 'Close' else 'Adj Close'
if 'Close' in data.columns:
    price_col = 'Close'
elif 'Adj Close' in data.columns:
    price_col = 'Adj Close'
else:
    raise ValueError("Neither 'Close' nor 'Adj Close' columns found in data.")

# Calculate returns, SMA and ATR
data["Return"] = data[price_col].pct_change()
data["SMA"] = data[price_col].rolling(trend_sma_period).mean()
data["ATR"] = (data["High"] - data["Low"]).rolling(atr_period).mean()

# Initialize variables
capital = 100000
position_size = capital * leverage
equity_curve = []
in_trade = False
entry_price = stop_loss = take_profit = 0
position = 0

# For trade logging
trades = []

for i in range(len(data)):
    row = data.iloc[i]
    price = row[price_col]
    date = data.index[i]

    if pd.isna(row["SMA"]) or pd.isna(row["ATR"]):
        equity_curve.append(capital)
        continue

    if not in_trade:
        # Entry: price above SMA
        if price > row["SMA"]:
            entry_price = price
            risk = row["ATR"]
            stop_loss = entry_price - risk
            take_profit = entry_price + risk * risk_reward_ratio
            position = position_size / entry_price
            in_trade = True
            trades.append({
                "Entry Date": date,
                "Entry Price": entry_price,
                "Stop Loss": stop_loss,
                "Take Profit": take_profit
            })
    else:
        # Exit conditions
        if price <= stop_loss or price >= take_profit:
            pnl = (price - entry_price) * position
            capital += pnl
            in_trade = False
            trades[-1].update({
                "Exit Date": date,
                "Exit Price": price,
                "P&L": pnl,
                "Capital After Trade": capital
            })

    equity_curve.append(capital)

# Add equity curve to data
data["Equity"] = equity_curve

# Convert equity and buy & hold to percentage returns
equity_pct = (data["Equity"] / 100000 - 1) * 100
buy_hold_pct = (data[price_col] / data[price_col].iloc[0] - 1) * 100

# Calculate maximum drawdown
running_max = data["Equity"].cummax()
drawdown = (data["Equity"] - running_max) / running_max
max_drawdown = drawdown.min() * 100  # in percentage

# Calculate win rate
wins = [1 for trade in trades if trade.get("P&L", 0) > 0]
win_rate = (len(wins) / len(trades) * 100) if trades else 0

# Plot returns in percentage
plt.figure(figsize=(12,6))
plt.plot(data.index, equity_pct, label="Strategy Return (%)")
plt.plot(data.index, buy_hold_pct, label="Buy & Hold Return (%)")
plt.title("2x Leveraged SPY Breakout Strategy vs Buy & Hold (Returns %)")
plt.ylabel("Return (%)")
plt.xlabel("Date")
plt.legend()
plt.grid(True)
plt.show()

# Final results
final_capital = equity_curve[-1]
total_return = (final_capital / 100000 - 1) * 100

print(f"Final Capital: ${final_capital:.2f}")
print(f"Total Return: {total_return:.2f}%")
print(f"Maximum Drawdown: {max_drawdown:.2f}%")
print(f"Win Rate: {win_rate:.2f}%")
print(f"Total Trades Executed: {len(trades)}")

if trades:
    print("\nAll trades:")
    trades_df = pd.DataFrame(trades)
    print(trades_df)
