import backtrader as bt
import yfinance as yf
import datetime

class MondayBreakoutStrategy(bt.Strategy):
    """
    Implements a strategy that only enters a trade on Mondays.
    
    Rules:
    1.  **Entry Day:** Trade is only considered on a Monday.
    2.  **Entry Signal:** Monday's daily open > Previous Week's Close.
    3.  **Order Type:** Immediate Market order on the signal day.
    4.  **Stop-Loss:** Entry Price - (2 * ATR(14)).
    5.  **Profit Target:** Entry Price + (3.0 * Risk Amount).
    """
    params = (
        ('atr_period', 14),
        ('atr_multiplier', 2.0),
        ('rr_ratio', 3.0), # Risk-Reward Ratio updated to 3:1
        ('trade_size', 10), # Number of shares to trade
    )

    def __init__(self):
        # Keep a reference to the data lines
        self.daily_open = self.datas[0].open
        self.weekly_close = self.datas[1].close

        # Instantiate indicators
        # ATR is calculated on the daily data for accurate volatility measurement
        self.atr = bt.indicators.AverageTrueRange(
            self.datas[0], period=self.p.atr_period
        )

        # To keep track of pending orders and an exit bracket
        self.buy_order = None
        self.exit_orders = []

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} | {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                
                # Calculate stop-loss and take-profit prices
                risk_amount = self.p.atr_multiplier * self.atr[0]
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
                self.exit_orders = []

            self.buy_order = None
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected: {order.getstatusname()}')
            self.buy_order = None
            self.exit_orders = []

    def next(self):
        # FIX: To get the weekday for the current bar, you must get the datetime object first
        # using .date(0) or .datetime(0) before calling .weekday()
        if self.datas[0].datetime.date(0).weekday() != 0:
            return # If not Monday, do nothing.

        # Check if an order is pending... if yes, we cannot send a 2nd one
        if self.buy_order:
            return

        # Check if we are in the market
        if self.position:
            # If in the market, our bracket orders will handle the exit.
            return

        # Check for our breakout signal: Today's open > last week's close
        is_breakout = self.daily_open[0] > self.weekly_close[-1]

        if is_breakout:
            # All conditions met. Place a Market order for the current day.
            self.log(f"Signal Confirmed on Monday. Open ({self.daily_open[0]:.2f}) > Last Week's Close ({self.weekly_close[-1]:.2f}). Placing Market Order.")
            self.buy_order = self.buy()

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(MondayBreakoutStrategy)

    # Download data
    data_df = yf.download(
        tickers='SPY',
        start='2010-01-01',
        end=datetime.datetime.now().strftime('%Y-%m-%d'),
        progress=False,
        auto_adjust=False, 
        back_adjust=False  
    )
    
    # Flatten column names for backtrader compatibility
    data_df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in data_df.columns]
    
    # Rename 'adj close' to 'adjclose'
    data_df.rename(columns={'adj close': 'adjclose'}, inplace=True)
    
    # The primary data feed is daily
    data = bt.feeds.PandasData(dataname=data_df)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)
    
    # Add a resampled weekly data feed for the breakout signal
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Weeks)


    # Set our desired cash start
    cerebro.broker.setcash(10000.0)

    # Set the commission to zero
    cerebro.broker.setcommission(commission=0.0)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')

    # Print out the starting conditions
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')

    # Run over everything
    results = cerebro.run()
    strat = results[0]

    # Print out the final result
    print(f'\nFinal Portfolio Value: {cerebro.broker.getvalue():.2f}')

    # Print analysis
    print('\n--- Strategy Analysis ---')
    analysis = strat.analyzers
    sharpe = analysis.sharpe_ratio.get_analysis()
    drawdown = analysis.drawdown.get_analysis()
    trade_analysis = analysis.trade_analyzer.get_analysis()

    print(f"Sharpe Ratio: {sharpe.get('sharperatio', 'N/A')}")
    print(f"Max Drawdown: {drawdown.max.drawdown:.2f}%")
    
    # Robustly check for the existence of keys before accessing them
    if trade_analysis and 'total' in trade_analysis and trade_analysis.total.total > 0:
        print(f"Total Trades: {trade_analysis.total.total}")
        
        win_rate = 0.0
        avg_win = 0.0
        if 'won' in trade_analysis and trade_analysis.won.total > 0:
            win_rate = (trade_analysis.won.total / trade_analysis.total.total) * 100
            avg_win = trade_analysis.won.pnl.average
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Average Win: ${avg_win:.2f}")

        avg_loss = 0.0
        if 'lost' in trade_analysis and trade_analysis.lost.total > 0:
            avg_loss = trade_analysis.lost.pnl.average
        print(f"Average Loss: ${avg_loss:.2f}")

        if avg_win > 0 and avg_loss < 0:
            rr_ratio = abs(avg_win / avg_loss)
            print(f"Risk/Reward Ratio (Avg Win / Avg Loss): {rr_ratio:.2f}:1")

    else:
        print("No trades were executed.")


    # Plot the result
    cerebro.plot(style='candlestick')
