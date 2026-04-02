# MT5 Trading Bot - Automated Trading System

MetaTrader 5 automated trading system with comprehensive analysis and auto-execution capabilities for Forex, Commodities, and Cryptocurrencies.

## Features

- **Multi-Asset Trading**: Gold, Silver, Bitcoin, Crude Oil, and more
- **Auto-Execution**: Automatically executes trades after analysis completes
- **Risk Management**: 2% risk per trade with automatic position sizing
- **SL/TP Management**: Automatic stop loss and take profit setting
- **Technical Analysis**: RSI, MACD, Moving Averages, ATR, Bollinger Bands
- **Fundamental Analysis**: Supply/demand, ETF flows, geopolitical factors
- **Sentiment Analysis**: Fear & Greed Index, COT positioning, analyst targets

## Repository Structure

```
mt5-trading-bot/
├── core/
│   └── mt5_trading.py          # Core MT5 trading module
├── auto_trades/
│   ├── universal_trade.py      # Universal script for ANY MT5 symbol
│   ├── gold_trade.py           # Gold script (universal - accepts --symbol)
│   ├── silver_trade.py         # Silver script (universal - accepts --symbol)
│   ├── bitcoin_trade.py        # Bitcoin script (universal - accepts --symbol)
│   └── crudeoil_trade.py       # Crude Oil script (universal - accepts --symbol)
├── analysis/
│   ├── gold_analysis.py        # Universal analysis (accepts --symbol, --timeframe)
│   └── silver_analysis.py      # Universal analysis (accepts --symbol, --timeframe)
├── helpers/
│   ├── mt5_sell_order.py       # Universal SELL order helper (any symbol)
│   ├── execute_buy.py          # Universal BUY order helper (any symbol)
│   └── execute_sell.py         # Universal SELL order helper (any symbol)
├── sltp/
│   ├── silver_sltp.py          # Universal SL/TP setter (any symbol)
│   ├── bitcoin_sltp.py         # Universal SL/TP setter (any symbol)
│   └── crudeoil_sltp.py        # Crude Oil SL/TP setter
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Prerequisites

1. **MetaTrader 5 Terminal** (Windows only)
   - Download from: https://www.metatrader5.com/en/download
   - Install and login with your broker account

2. **Python 3.8+**

3. **Python Packages**:
   ```bash
   pip install MetaTrader5 pandas numpy
   ```

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your MT5 credentials:
   ```
   MT5_LOGIN=107069198
   MT5_PASSWORD=your_password
   MT5_SERVER=Ava-Demo 1-MT5
   ```

## Usage

### Run Core Trading Module

```bash
python core/mt5_trading.py
```

### Execute Auto-Trades

**Universal Script (Recommended - Works with ANY symbol):**

```bash
# Syntax
python auto_trades/universal_trade.py --symbol SYMBOL --direction BUY/SELL --volume LOTS --sl PRICE --tp PRICE

# Examples
python auto_trades/universal_trade.py --symbol GOLD --direction SELL --volume 0.1 --sl 4762 --tp 4546
python auto_trades/universal_trade.py --symbol BTCUSD --direction BUY --volume 0.01 --sl 63500 --tp 72800
python auto_trades/universal_trade.py --symbol EURUSD --direction SELL --volume 0.5 --sl 1.0950 --tp 1.0850
python auto_trades/universal_trade.py --symbol WTICrude --direction BUY --volume 0.1 --sl 76.50 --tp 85.00
```

**Asset-Specific Scripts (Now Universal - Accept CLI Arguments):**

All asset-specific scripts now accept `--symbol`, `--direction`, `--volume`, `--sl`, and `--tp` arguments:

```bash
# Gold (default: GOLD, customizable)
python auto_trades/gold_trade.py --symbol GOLD --direction SELL --volume 0.1 --sl 4762 --tp 4546

# Silver (default: SILVER, customizable)
python auto_trades/silver_trade.py --symbol SILVER --direction BUY --volume 0.5 --sl 28.50 --tp 31.50

# Bitcoin (default: BTCUSD, customizable)
python auto_trades/bitcoin_trade.py --symbol BTCUSD --direction BUY --volume 0.01 --sl 63500 --tp 72800

# Crude Oil (default: WTICrude, customizable)
python auto_trades/crudeoil_trade.py --symbol WTICrude --direction BUY --volume 0.1 --sl 76.50 --tp 85.00
```

### Run Trading Analysis

**Universal Analysis Scripts (Works with ANY symbol):**

```bash
# Gold analysis
python analysis/gold_analysis.py --symbol GOLD

# Bitcoin analysis  
python analysis/gold_analysis.py --symbol BTCUSD

# Forex analysis
python analysis/silver_analysis.py --symbol EURUSD

# Custom timeframe
python analysis/gold_analysis.py --symbol GOLD --timeframe D1
```

### Execute Individual Orders

**Helper Scripts (Universal - Any Symbol):**

```bash
# BUY order
python helpers/execute_buy.py --symbol GOLD --volume 0.1 --sl 4554 --tp 4880

# SELL order
python helpers/execute_sell.py --symbol BTCUSD --volume 0.01 --sl 60000 --tp 72000

# Alternative SELL helper
python helpers/mt5_sell_order.py --symbol SILVER --volume 0.5 --sl 28.00 --tp 31.00
```

### Set Stop Loss / Take Profit

**Universal SL/TP Setter (Works with ANY symbol):**

```bash
# Silver position
python sltp/silver_sltp.py --symbol SILVER --sl 28.50 --tp 31.50

# Bitcoin position
python sltp/bitcoin_sltp.py --symbol BTCUSD --sl 63500 --tp 72800

# Gold position
python sltp/silver_sltp.py --symbol GOLD --sl 4600 --tp 4750

# Any MT5 symbol
python sltp/silver_sltp.py --symbol EURUSD --sl 1.0850 --tp 1.0950
```

## Auto-Execution Workflow

1. **Analysis Phase**: Comprehensive technical, fundamental, and sentiment analysis
2. **Signal Generation**: BUY/SELL/NEUTRAL signal with confidence level
3. **Risk Calculation**: Position size based on 2% risk and stop distance
4. **Order Execution**: Market order with appropriate filling mode
5. **SL/TP Setting**: Automatic stop loss and take profit placement

## Risk Management

| Parameter | Value |
|-----------|-------|
| Risk per trade | 2% of account balance |
| Maximum position | 1.0 lots (capped) |
| Minimum position | 0.01 lots |
| Default R/R | 1:1.5 to 1:3.0 |
| Slippage tolerance | 50-500 points (asset-dependent) |

## Supported Assets

**All scripts now work with ANY symbol available on your MT5 broker:**

| Category | Examples | Symbols |
|----------|----------|---------|
| **Forex** | EUR/USD, GBP/USD, USD/JPY | EURUSD, GBPUSD, USDJPY |
| **Metals** | Gold, Silver, Platinum | GOLD, SILVER, XPTUSD |
| **Crypto** | Bitcoin, Ethereum | BTCUSD, ETHUSD |
| **Energy** | WTI Crude, Brent Oil | WTICrude, BRENT_OIL |
| **Indices** | US30, NAS100, SPX500 | US30, NAS100, SPX500 |
| **Stocks** | Apple, Tesla, Microsoft | AAPL, TSLA, MSFT |

Use `python core/mt5_trading.py --list-symbols` to see all available symbols on your broker.

## Trading Signals

Each auto-trade script includes:
- **Direction**: BUY or SELL
- **Entry**: Market or limit price
- **Stop Loss**: Based on technical levels
- **Take Profit**: Multiple targets (TP1, TP2)
- **Position Size**: Calculated via Kelly Criterion (fractional)
- **Risk/Reward**: Minimum 1:1.5

## Universal Trade Script

The `universal_trade.py` script uses the exact same proven method that successfully executed trades for Gold, Silver, and Bitcoin. It works with **ANY** symbol on MT5:

### Features

- **Auto-detects symbol specifications** (digits, point value, min/max lots)
- **Validates SL/TP** for the trade direction (SL above entry for SELL, below for BUY)
- **Tries multiple filling modes** (FOK, RETURN, IOC) until one succeeds
- **Sets SL/TP automatically** using `TRADE_ACTION_SLTP`
- **Verifies position** after execution

### Command Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--symbol` | Yes | Trading symbol (e.g., GOLD, BTCUSD, EURUSD, WTICrude) |
| `--direction` | Yes | BUY or SELL |
| `--volume` | Yes | Lot size (will be normalized to broker's requirements) |
| `--sl` | Yes | Stop Loss price |
| `--tp` | Yes | Take Profit price |
| `--deviation` | No | Max slippage in points (default: 50) |

### Examples

```bash
# Forex - EUR/USD SELL
python auto_trades/universal_trade.py --symbol EURUSD --direction SELL --volume 0.5 --sl 1.0950 --tp 1.0850

# Metals - Gold BUY
python auto_trades/universal_trade.py --symbol GOLD --direction BUY --volume 0.1 --sl 4600 --tp 4750

# Crypto - Bitcoin SELL
python auto_trades/universal_trade.py --symbol BTCUSD --direction SELL --volume 0.05 --sl 70000 --tp 60000

# Energy - WTI Crude BUY
python auto_trades/universal_trade.py --symbol WTICrude --direction BUY --volume 0.1 --sl 76.50 --tp 85.00

# Indices - US30 BUY
python auto_trades/universal_trade.py --symbol US30 --direction BUY --volume 0.01 --sl 42000 --tp 44000
```

### SL/TP Validation

The script automatically validates that your stops are correct for the trade direction:

| Direction | Stop Loss | Take Profit |
|-----------|-----------|-------------|
| **BUY** | Must be **BELOW** entry | Must be **ABOVE** entry |
| **SELL** | Must be **ABOVE** entry | Must be **BELOW** entry |

## Disclaimer

**This software is for educational purposes only.**

Trading Forex, Commodities, and Cryptocurrencies involves substantial risk of loss. Past performance does not guarantee future results. Always test thoroughly on a demo account before using live funds.

The authors are not responsible for any financial losses. Use at your own risk.

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For issues and questions:
- GitHub Issues: https://github.com/moneymotive029-source/mt5-trading-bot/issues
