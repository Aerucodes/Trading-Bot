#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
"""
Custom data feed for TradeLocker integration with Backtrader
Copyright (C) 2025 Aerucodes - All Rights Reserved
"""
import datetime
import backtrader as bt
import time
import pandas as pd


class TradeLockerFeed(bt.feeds.DataBase):
    """
    A custom data feed that connects to TradeLocker's API to fetch live price data.
    """
    
    params = (
        ('symbol', None),        # Symbol to fetch data for
        ('timeframe', '1d'),     # Timeframe (e.g., '1m', '5m', '1h', '1d')
        ('fromdate', None),      # Start date for historical data
        ('todate', None),        # End date for historical data
        ('historical', True),    # Whether to load historical data before going live
        ('backfill', True),      # Whether to backfill live data gaps
        ('api', None),           # TradeLocker API instance
        ('ohlcv', True),         # Whether data is in OHLCV format
        ('tz', 'UTC'),           # Timezone for the data
        ('sessionstart', None),  # Session start time (e.g., '09:30')
        ('sessionend', None),    # Session end time (e.g., '16:00')
    )

    def __init__(self):
        super(TradeLockerFeed, self).__init__()
        
        self.api = self.p.api
        if self.api is None:
            raise ValueError("TradeLocker API instance must be provided")
        
        if self.p.symbol is None:
            raise ValueError("Symbol must be provided")
        
        # Initialize variables
        self.intraday = self.p.timeframe[-1] not in ('d', 'w', 'm')
        
        # Define the format for storing dates/times
        self.dtformat = '%Y-%m-%dT%H:%M:%S' if self.intraday else '%Y-%m-%d'
        
        # Set data format
        self.dataformats = {
            'datetime': bt.TimeFrame.Days if not self.intraday else bt.TimeFrame.Minutes,
            'open': float,
            'high': float,
            'low': float,
            'close': float,
            'volume': float,
            'openinterest': float,
        }
        
        # Store historical data
        self.hist_data = None
        self.hist_loaded = False
        
        # Store live data buffer
        self.live_buffer = []
        self.last_bar_time = None
        
        # Keep a reference to the last retrieved bar
        self.last_bar = None

    def start(self):
        """Called when the data feed should start"""
        if not self.api.is_connected:
            if not self.api.connect():
                raise RuntimeError("Failed to connect to TradeLocker API")
        
        # If historical data is requested, fetch it
        if self.p.historical:
            self._load_historical_data()
            
        # Initialize data pointer
        self._idx = -1
            
    def _load_historical_data(self):
        """Load historical data from TradeLocker API"""
        print(f"Loading historical data for {self.p.symbol} ({self.p.timeframe})")
        
        # In a real implementation, you would fetch historical data from TradeLocker API here
        # For this example, we create sample data
        
        # This is a placeholder - replace with actual API call to TradeLocker
        # Example: hist_data = self.api.get_historical_data(self.p.symbol, self.p.timeframe,
        #                                                   self.p.fromdate, self.p.todate)
        
        # Generate dummy data for demonstration purposes
        dates = []
        start_date = self.p.fromdate or datetime.datetime.now() - datetime.timedelta(days=30)
        end_date = self.p.todate or datetime.datetime.now()
        
        current_date = start_date
        while current_date <= end_date:
            if self.intraday:
                # For intraday data, add multiple bars per day during trading hours
                session_start = 9 * 60 + 30  # 9:30 AM in minutes
                session_end = 16 * 60  # 4:00 PM in minutes
                
                if current_date.weekday() < 5:  # Monday to Friday
                    minutes = session_start
                    while minutes < session_end:
                        bar_time = current_date.replace(
                            hour=minutes // 60,
                            minute=minutes % 60,
                            second=0,
                            microsecond=0
                        )
                        dates.append(bar_time)
                        minutes += int(self.p.timeframe[:-1])  # Extract number from timeframe
                
                # Move to next day
                current_date += datetime.timedelta(days=1)
            else:
                # For daily data, add one bar per day
                if current_date.weekday() < 5:  # Monday to Friday
                    dates.append(current_date)
                current_date += datetime.timedelta(days=1)
        
        # Create a dummy DataFrame with OHLCV data
        import numpy as np
        n = len(dates)
        if n == 0:
            print(f"No historical data available for {self.p.symbol}")
            self.hist_data = pd.DataFrame()
            self.hist_loaded = True
            return
            
        # Generate random price data with a slight upward trend
        close_prices = np.cumsum(np.random.normal(0.01, 0.1, n)) + 100
        open_prices = close_prices - np.random.normal(0, 0.1, n)
        high_prices = np.maximum(close_prices, open_prices) + np.random.normal(0.05, 0.05, n)
        low_prices = np.minimum(close_prices, open_prices) - np.random.normal(0.05, 0.05, n)
        volumes = np.random.randint(1000, 10000, n)
        
        self.hist_data = pd.DataFrame({
            'datetime': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes,
            'openinterest': [0] * n
        })
        
        # Store the time of the last historical bar
        if not self.hist_data.empty:
            self.last_bar_time = self.hist_data['datetime'].iloc[-1]
        
        print(f"Loaded {len(self.hist_data)} historical bars for {self.p.symbol}")
        self.hist_loaded = True

    def _fetch_live_bar(self):
        """Fetch the latest live bar from TradeLocker API"""
        # In a real implementation, you would fetch the latest bar data from TradeLocker API here
        # This is a placeholder - replace with actual API call
        
        # For demonstration, create a simulated bar
        now = datetime.datetime.now()
        
        # Only generate a new bar if we're in a trading session
        is_trading_hours = True
        if self.p.sessionstart and self.p.sessionend:
            session_start = datetime.datetime.strptime(self.p.sessionstart, '%H:%M').time()
            session_end = datetime.datetime.strptime(self.p.sessionend, '%H:%M').time()
            current_time = now.time()
            is_trading_hours = session_start <= current_time <= session_end
        
        # Only generate a bar on weekdays (Mon-Fri)
        is_weekday = now.weekday() < 5
        
        if not (is_trading_hours and is_weekday):
            return None
        
        # Calculate the bar's datetime based on the timeframe
        if self.intraday:
            # For intraday timeframes, round down to the nearest bar
            minutes_timeframe = int(self.p.timeframe[:-1])
            total_minutes = now.hour * 60 + now.minute
            bar_minutes = (total_minutes // minutes_timeframe) * minutes_timeframe
            bar_time = now.replace(
                hour=bar_minutes // 60,
                minute=bar_minutes % 60,
                second=0,
                microsecond=0
            )
        else:
            # For daily timeframes, use the date
            bar_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Don't generate duplicate bars
        if self.last_bar_time and bar_time <= self.last_bar_time:
            return None
        
        # Generate a random price change from the last known price
        if self.last_bar:
            last_close = self.last_bar['close']
            open_price = last_close
            close_price = last_close * (1 + (0.001 * (0.5 - float(time.time() % 2))))
            high_price = max(open_price, close_price) + 0.001
            low_price = min(open_price, close_price) - 0.001
        else:
            # First bar
            close_price = 100.0
            open_price = 99.95
            high_price = 100.05
            low_price = 99.90
        
        bar = {
            'datetime': bar_time,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': float(1000 + (time.time() % 1000)),
            'openinterest': 0.0
        }
        
        self.last_bar = bar
        self.last_bar_time = bar_time
        return bar

    def _load_next_live_bar(self):
        """Fetch and queue the next live bar"""
        bar = self._fetch_live_bar()
        if bar:
            self.live_buffer.append(bar)
            return True
        return False

    def _get_bar(self):
        """Get the next bar, either historical or live"""
        if self._idx >= 0 and self._idx < len(self.hist_data):
            # Return historical bar
            bar = self.hist_data.iloc[self._idx].to_dict()
            return bar
        
        # Check if we have any bars in the live buffer
        if not self.live_buffer:
            # Try to fetch a new live bar
            if not self._load_next_live_bar():
                return None
        
        # Return the next live bar if available
        if self.live_buffer:
            return self.live_buffer.pop(0)
        
        return None

    def _load_bar(self):
        """Load the next bar into the data feed"""
        bar = self._get_bar()
        if bar is None:
            return False
        
        # Convert datetime to format expected by backtrader
        dt = bar['datetime']
        
        # Update data lines
        self.lines.datetime[0] = bt.date2num(dt)
        self.lines.open[0] = bar['open']
        self.lines.high[0] = bar['high']
        self.lines.low[0] = bar['low']
        self.lines.close[0] = bar['close']
        self.lines.volume[0] = bar['volume']
        self.lines.openinterest[0] = bar['openinterest']
        
        return True

    def preload(self):
        """Preload all data - required for backtesting but not for live trading"""
        while self.load_next():
            pass
        self.home()

    def _next_historical(self):
        """Move to the next historical data point"""
        self._idx += 1
        return self._idx < len(self.hist_data)

    def _next_live(self):
        """Check for new live data"""
        return self._load_next_live_bar()

    def next(self):
        """Called to advance the data feed iterator"""
        if self._idx >= 0 and self._idx < len(self.hist_data) - 1:
            # Still have historical data to process
            self._next_historical()
            return True
        
        # Check if we've moved from historical to live data
        if self._idx == len(self.hist_data) - 1:
            # Last historical bar, advance to live mode
            self._idx += 1
            
            if not self.p.historical:
                # If we didn't load historical data, create live buffer now
                self.live_buffer = []
                self.last_bar_time = None
            
            # Try to get first live bar
            return self._next_live()
        
        # In live mode
        return self._next_live()

    def load_next(self):
        """Load the next data point into the feed"""
        if not super(TradeLockerFeed, self).next():
            return False
        
        # Update the data point
        return self._load_bar()

    def haslivedata(self):
        """Return whether the feed has live data available"""
        return bool(self.live_buffer) or self._idx >= len(self.hist_data)

    def islive(self):
        """Return whether the feed is in live mode"""
        return True  # Always True for this feed as it's designed for live trading

    def stop(self):
        """Called when the data feed should stop"""
        # Cleanup could be performed here if necessary
        pass 