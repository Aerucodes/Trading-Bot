#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
"""
EMA Crossover Trading Strategy Bot using Backtrader
Copyright (C) 2025 Aerucodes - All Rights Reserved
"""
import datetime
import backtrader as bt
import argparse
from tradelocker_feed import TradeLockerFeed


class EmaCrossStrategy(bt.Strategy):
    """
    A trading strategy that uses EMA-50 and EMA-200 crossovers.
    Buys when EMA-50 crosses above EMA-200 (golden cross)
    Sells when EMA-50 crosses below slow EMA (death cross)
    """
    params = (
        ('fast_ema', 50),   # fast EMA period
        ('slow_ema', 200),  # slow EMA period
    )

    def __init__(self):
        # Keep track of the close price
        self.dataclose = self.datas[0].close
        
        # Add EMAs
        self.fast_ema = bt.indicators.EMA(self.datas[0], period=self.params.fast_ema)
        self.slow_ema = bt.indicators.EMA(self.datas[0], period=self.params.slow_ema)
        
        # Create a CrossOver Signal
        self.crossover = bt.indicators.CrossOver(self.fast_ema, self.slow_ema)
        
        # To keep track of pending orders
        self.order = None
        
        # For logging
        self.log_enabled = True

    def log(self, txt, dt=None):
        """Logging function for the strategy"""
        if self.log_enabled:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        """Called when order status changes"""
        if order.status in [order.Submitted, order.Accepted]:
            # Order submitted/accepted - no action required
            return

        # Report executed order
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, {order.executed.price:.2f}')
            else:
                self.log(f'SELL EXECUTED, {order.executed.price:.2f}')

        # Report failed order
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Reset orders
        self.order = None

    def notify_trade(self, trade):
        """Called when a trade is closed"""
        if not trade.isclosed:
            return

        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def next(self):
        """Main strategy logic executed on each bar"""
        # Check if an order is pending
        if self.order:
            return

        # Log the closing price
        self.log(f'Close: {self.dataclose[0]:.2f}, Fast EMA: {self.fast_ema[0]:.2f}, Slow EMA: {self.slow_ema[0]:.2f}')

        # Check if we are in the market
        if not self.position:
            # Not in the market, look for buy signal
            # Buy when fast EMA crosses above slow EMA (golden cross)
            if self.crossover > 0:
                self.log(f'GOLDEN CROSS - BUY CREATE, {self.dataclose[0]:.2f}')
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:
            # Already in the market, look for sell signal
            # Sell when fast EMA crosses below slow EMA (death cross)
            if self.crossover < 0:
                self.log(f'DEATH CROSS - SELL CREATE, {self.dataclose[0]:.2f}')
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='EMA Crossover Trading Strategy')
    
    parser.add_argument('--data', '-d',
                        default='data.csv',
                        help='Data file to use')
    
    parser.add_argument('--fast', '-f', 
                        default=50, type=int,
                        help='Fast EMA period')
    
    parser.add_argument('--slow', '-s', 
                        default=200, type=int,
                        help='Slow EMA period')
    
    parser.add_argument('--cash', '-c',
                        default=100000.0, type=float,
                        help='Starting cash')
    
    parser.add_argument('--commission', '-comm',
                        default=0.001, type=float,
                        help='Commission rate')
    
    parser.add_argument('--stake', 
                        default=10, type=int,
                        help='Stake size')
    
    parser.add_argument('--plot', '-p',
                        action='store_true',
                        help='Plot the result')
    
    parser.add_argument('--live', '-l',
                        action='store_true',
                        help='Run in live trading mode with TradeLocker')
    
    parser.add_argument('--api-key',
                        default='',
                        help='TradeLocker API key')
    
    parser.add_argument('--symbols',
                        default='AAPL',
                        help='Comma-separated list of symbols to trade')
    
    parser.add_argument('--timeframe',
                        default='1d',
                        help='Timeframe for data feed (e.g., 1m, 5m, 1h, 1d)')
    
    return parser.parse_args()


def run_backtest(args=None):
    """Set up and run the backtest"""
    if args is None:
        args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(EmaCrossStrategy, 
                         fast_ema=args.fast,
                         slow_ema=args.slow)

    # Load data
    print(f'Loading data from {args.data}')
    data = bt.feeds.GenericCSVData(
        dataname=args.data,
        datetime=0,  # Column containing datetime
        open=1,      # Column containing open
        high=2,      # Column containing high
        low=3,       # Column containing low
        close=4,     # Column containing close
        volume=5,    # Column containing volume
        openinterest=-1,  # Column containing open interest (-1 means not available)
        dtformat='%Y-%m-%d',  # Format of datetime
        timeframe=bt.TimeFrame.Days  # Daily timeframe
    )

    # Add the data to cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(args.cash)

    # Set the commission
    cerebro.broker.setcommission(commission=args.commission)

    # Set the stake size
    cerebro.addsizer(bt.sizers.FixedSize, stake=args.stake)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    # Print out the starting conditions
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')

    # Run the backtest
    results = cerebro.run()
    strat = results[0]

    # Print out the final result
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f}')
    
    # Print performance metrics
    print(f'Sharpe Ratio: {strat.analyzers.sharpe.get_analysis()["sharperatio"]:.3f}')
    print(f'Max Drawdown: {strat.analyzers.drawdown.get_analysis()["max"]["drawdown"]:.2f}%')
    print(f'Annual Return: {strat.analyzers.returns.get_analysis()["rtot"] * 100:.2f}%')

    # Plot the result if requested
    if args.plot:
        cerebro.plot(style='candle')
    
    return results


class TradeLockerAPI:
    """Simple wrapper for TradeLocker API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.is_connected = False
    
    def connect(self):
        """Connect to TradeLocker API"""
        print("Connecting to TradeLocker API...")
        # In a real implementation, you would establish a connection here
        # using TradeLocker's API documentation and authentication methods
        self.is_connected = True
        print("Connected to TradeLocker successfully.")
        return self.is_connected
    
    def get_market_data(self, symbol, timeframe='1d', bars=500):
        """Get market data for the specified symbol"""
        print(f"Fetching market data for {symbol} ({timeframe})")
        # In a real implementation, you would fetch actual market data here
        # This is a placeholder
        return None
    
    def place_order(self, symbol, order_type, quantity, side, price=None, stop_price=None):
        """Place an order via TradeLocker"""
        print(f"Placing {side} order for {quantity} {symbol} at {price}")
        # In a real implementation, you would submit the order to TradeLocker
        # and return an order ID or similar
        order_id = "12345"  # Placeholder
        return order_id
    
    def get_account_info(self):
        """Get account information"""
        print("Fetching account information")
        # In a real implementation, you would fetch actual account data
        return {"balance": 100000, "positions": []}
    
    def disconnect(self):
        """Disconnect from TradeLocker API"""
        print("Disconnecting from TradeLocker API")
        self.is_connected = False
        return True


def run_live_trading(args):
    """
    Set up live trading using TradeLocker
    """
    if not args.api_key:
        print("ERROR: API key is required for live trading. Use --api-key parameter.")
        return
    
    print("Setting up live trading with TradeLocker...")
    
    # Initialize TradeLocker API
    trade_api = TradeLockerAPI(args.api_key)
    
    # Connect to TradeLocker
    if not trade_api.connect():
        print("Failed to connect to TradeLocker. Exiting.")
        return
    
    try:
        # Create a cerebro instance for live trading
        cerebro = bt.Cerebro()
        
        # Add our strategy
        cerebro.addstrategy(EmaCrossStrategy, 
                           fast_ema=args.fast,
                           slow_ema=args.slow)
        
        # Parse symbols
        symbols = args.symbols.split(',')
        print(f"Trading symbols: {symbols}")
        
        # Session times (market hours)
        session_start = "09:30"
        session_end = "16:00"
        
        # Add data feeds for each symbol using our custom TradeLocker feed
        for symbol in symbols:
            print(f"Setting up data feed for {symbol}")
            
            # Calculate fromdate as 1 year ago to have enough data for EMAs
            fromdate = datetime.datetime.now() - datetime.timedelta(days=365)
            
            data = TradeLockerFeed(
                symbol=symbol,
                timeframe=args.timeframe,
                fromdate=fromdate,
                historical=True,  # Load historical data first
                api=trade_api,
                sessionstart=session_start,
                sessionend=session_end
            )
            
            cerebro.adddata(data)
        
        # Set broker parameters
        account_info = trade_api.get_account_info()
        cerebro.broker.setcash(account_info["balance"])
        cerebro.broker.setcommission(commission=args.commission)
        
        # Set position size
        cerebro.addsizer(bt.sizers.FixedSize, stake=args.stake)
        
        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        
        print(f"Starting live trading with TradeLocker...")
        print(f"Initial portfolio value: {cerebro.broker.getvalue():.2f}")
        
        # Run the strategy
        cerebro.run()
        
    except Exception as e:
        print(f"An error occurred during live trading: {e}")
    
    finally:
        # Disconnect from TradeLocker
        trade_api.disconnect()
        print("Live trading session ended.")


if __name__ == '__main__':
    args = parse_args()
    
    if args.live:
        run_live_trading(args)
    else:
        run_backtest(args) 