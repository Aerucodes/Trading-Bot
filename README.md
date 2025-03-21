# EMA Crossover Trading Bot

A Python-based automated trading bot that implements the EMA crossover strategy using the Backtrader framework with TradeLocker integration.

## Strategy Overview

The EMA crossover strategy in this bot:
1. Uses 50-period EMA (fast) and 200-period EMA (slow)
2. Generates a buy signal when fast EMA crosses above slow EMA (Golden Cross)
3. Generates a sell signal when fast EMA crosses below slow EMA (Death Cross)
4. Includes performance metrics like Sharpe Ratio, Drawdown, and Returns

## Requirements

```
backtrader>=1.9.76.123
matplotlib>=3.3.0
numpy>=1.19.0
pandas>=1.1.0
```

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd ema-trading-bot
```

2. Install the required packages:
```
pip install -r requirements.txt
```

## Usage

### Backtesting

To run a backtest with default parameters:

```
python momentum_bot.py
```

### Command Line Arguments

The script accepts various command line arguments for customization:

- `--data, -d`: Data file to use (default: data.csv)
- `--fast, -f`: Fast EMA period (default: 50)
- `--slow, -s`: Slow EMA period (default: 200)
- `--cash, -c`: Starting cash (default: 100000.0)
- `--commission, -comm`: Commission rate (default: 0.001)
- `--stake`: Stake size (default: 10)
- `--plot, -p`: Plot the backtest results

Example with custom parameters:

```
python momentum_bot.py --data=my_data.csv --fast=20 --slow=50 --cash=50000 --plot
```

## Data Format

The bot expects CSV files with the following columns:
- Date (in YYYY-MM-DD format)
- Open
- High
- Low
- Close
- Volume

A sample data file is included in the repository.

## Performance Metrics

The strategy calculates and displays the following performance metrics:
- Final Portfolio Value
- Sharpe Ratio
- Maximum Drawdown
- Annual Return

## Live Trading with TradeLocker

This bot includes integration with TradeLocker for live trading. To run the bot in live trading mode:

```
python momentum_bot.py --live --api-key=YOUR_API_KEY --symbols=AAPL,MSFT,GOOG
```

### TradeLocker-specific Arguments

- `--live, -l`: Enable live trading mode with TradeLocker
- `--api-key`: Your TradeLocker API key (required for live trading)
- `--symbols`: Comma-separated list of symbols to trade (default: AAPL)

### TradeLocker Integration Features

The integration with TradeLocker provides:
1. Real-time market data from TradeLocker
2. Automatic order execution through TradeLocker
3. Account and portfolio management
4. Multi-symbol trading support

### Implementation Notes

The current TradeLocker implementation is a placeholder framework. To use it in a production environment:

1. Update the `TradeLockerAPI` class with the actual TradeLocker API endpoints according to their documentation
2. Implement a custom data feed class to connect to TradeLocker's market data stream
3. Test thoroughly in a paper trading environment before using with real money

## Disclaimer

This trading bot is for educational purposes only. Use it at your own risk. Trading involves substantial risk of loss and is not suitable for every investor.

---

Copyright © 2025 Aerucodes. All rights reserved. 