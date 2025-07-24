import backtrader as bt
import yfinance as yf
import datetime

class DonchianBreakoutStrategy(bt.Strategy):
    """
    Implements the Donchian Channel Breakout Strategy as detailed in the report.
    
    Rules:
    1.  **Entry Signal:** Daily close > 20-Day Donchian Channel Upper Band.
    2.  **Trend Filter:** Daily close > 100-Day Simple Moving Average (SMA).
    3.  **Volume Filter:** Volume on breakout day > 20-Day Simple Moving Average of Volume.
    4.  **Order Type:** Pending Buy Stop order placed on the day *after* the signal
        at the prior day's Donchian high level.
    5.  **Stop-Loss:** Entry Price - (2 * ATR(14)).
    6.  **Profit Target:** Entry Price + (1.5 * Risk Amount).
    """
    params = (
        ('donchian_period', 20),
        ('trend_sma_period', 100),
        ('volume_sma_period', 20),
        ('atr_period', 14),
        ('atr_multiplier', 2.0),
        ('rr_ratio', 1.5),
        ('trade_size', 100), # Number of shares to trade
    )

    def __init__(self):
        # Keep a reference to the "close" line in the data dataseries
        self.close = self.datas.close
        self.volume = self.datas.volume

        # Instantiate indicators
        self.donchian = bt.indicators.DonchianChannels(
            self.datas, period=self.p.donchian_period
        )
        self.sma_trend = bt.indicators.SimpleMovingAverage(
            self.datas, period=self.p.trend_sma_period
        )
        self.sma_volume = bt.indicators.SimpleMovingAverage(
            self.datas.volume, period=self.p.volume_sma_period
        )
        self.atr = bt.indicators.AverageTrueRange(
            self.datas, period=self.p.atr_period
        )

        # To keep track of pending orders and an exit bracket
        self.buy_order = None
        self.exit_orders =

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas.datetime.date(0)
        print(f'{dt.isoformat()} | {txt}')

    def notify_order(self, order):
        if order.status in:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                
                # Calculate stop-loss and take-profit prices
                risk_amount = self.p.atr_multiplier * self.atr
                stop_price = order.executed.price - risk_amount
                profit_target_price = order.executed.price + (self.p.rr_ratio * risk_amount)

                # Place bracket orders (OCO - One-Cancels-Other)
                stop_order = self.sell(exectype=bt.Order.Stop, price=stop_price)
                limit_order = self.sell(exectype=bt.Order.Limit, price=profit_target_price)
                self.exit_orders = [stop_order, limit_order]
                
                self.log(f'Placed Stop-Loss at {stop_price:.2f} and Take-Profit at {profit_target_price:.2f}')

            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                # Reset exit orders list
                self.exit_orders =

            self.buy_order = None

        elif order.status in:
            self.log(f'Order Canceled/Margin/Rejected: {order.getstatusname()}')
            self.buy_order = None
            self.exit_orders =

    def next(self):
        # Check if an order is pending... if yes, we cannot send a 2nd one
        if self.buy_order:
            return

        # Check if we are in the market
        if self.position:
            # If in the market, our bracket orders will handle the exit.
            # We could add trailing stop logic here if desired.
            return

        # Check for our breakout signal on the PREVIOUS day's close
        # Using [-1] index to avoid look-ahead bias
        is_breakout = self.close[-1] > self.donchian.dch[-1]
        is_uptrend = self.close[-1] > self.sma_trend[-1]
        is_volume_confirmed = self.volume[-1] > self.sma_volume[-1]

        if is_breakout and is_uptrend and is_volume_confirmed:
            # All conditions met. Place a pending Buy Stop order for the current day.
            # The entry price is the Donchian high from the signal day.
            entry_price = self.donchian.dch[-1]
            
            self.log(f'Signal Confirmed. Placing Buy Stop order at {entry_price:.2f}')
            self.buy_order = self.buy(exectype=bt.Order.Stop, price=entry_price, size=self.p.trade_size)

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(DonchianBreakoutStrategy)

    # Download data
    data_df = yf.download(
        'SPY',
        start='2010-01-01',
        end=datetime.datetime.now().strftime('%Y-%m-%d'),
        progress=False
    )
    data = bt.feeds.PandasData(dataname=data_df)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Set the commission - 0.50% total cost is 0.25% per trade (buy/sell)
    # backtrader's commission is a percentage, so 0.0025 = 0.25%
    cerebro.broker.setcommission(commission=0.0025)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')

    # Print out the starting conditions
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')

    # Run over everything
    results = cerebro.run()
    strat = results

    # Print out the final result
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f}')

    # Print analysis
    print('\n--- Strategy Analysis ---')
    sharpe = strat.analyzers.sharpe_ratio.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    trade_analysis = strat.analyzers.trade_analyzer.get_analysis()

    print(f"Sharpe Ratio: {sharpe.get('sharperatio', 'N/A')}")
    print(f"Max Drawdown: {drawdown.max.drawdown:.2f}%")
    print(f"Total Trades: {trade_analysis.total.total}")
    if trade_analysis.total.total > 0:
        print(f"Win Rate: {(trade_analysis.won.total / trade_analysis.total.total) * 100:.2f}%")
        print(f"Average Win: ${trade_analysis.won.pnl.average:.2f}")
        print(f"Average Loss: ${trade_analysis.lost.pnl.average:.2f}")
        print(f"Risk/Reward Ratio (Avg Win / Avg Loss): {abs(trade_analysis.won.pnl.average / trade_analysis.lost.pnl.average):.2f}:1")

    # Plot the result
    cerebro.plot(style='candlestick')