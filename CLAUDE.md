# MT5 Trading Bot - Claude Code Context

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure settings (edit config.py)
# - MT5_LOGIN, MT5_PASSWORD, MT5_SERVER
# - Risk settings, entry zones, etc.

# Run the bot
python main.py
```

## Project Structure

- `config.py` - MT5 credentials, symbol configs, risk rules
- `mt5_connector.py` - MT5 API integration
- `signal_engine.py` - Signal generation with position sizing
- `order_executor.py` - Order placement & management
- `main.py` - Main entry point
- `requirements.txt` - Python dependencies

## Key Commands

| Command | Description |
|---------|-------------|
| `python main.py` | Start the trading bot |
| `pip install -r requirements.txt` | Install dependencies |
| `python -c "import MetaTrader5 as mt5; mt5.initialize(...); print(mt5.account_info().trade_mode)"` | Check trade mode |

## Trading Configuration

Edit `config.py` to customize:
- MT5 credentials (login, password, server)
- Entry zones for each metal
- Risk per trade (default 2%)
- Stop loss ATR multiplier
- Take profit levels

## Current Symbols

| Symbol | Signal | Entry Zone | Contract Size |
|--------|--------|------------|---------------|
| GOLD | WAIT→LONG | $4,420-4,480 | 100 oz |
| SILVER | WAIT→SHORT | $68.50-70.00 | 10,000 oz |
| PLATINUM | LONG | $1,850-1,890 | 100 oz |
| PALLADIUM | WAIT→SHORT | $1,420-1,460 | 100 oz |
| COPPER | LONG | $4.35-4.45/lb | 10,000 lbs |

## Requirements

- MetaTrader 5 installed and running
- Active MT5 account (demo or live)
- Python 3.8+
- AutoTrading enabled in MT5 (F4)
- Account trade mode = 2 (Full Trading)
