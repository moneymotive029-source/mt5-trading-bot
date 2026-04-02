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
│   ├── gold_trade.py           # Gold auto-execution script
│   ├── silver_trade.py         # Silver auto-execution script
│   ├── bitcoin_trade.py        # Bitcoin auto-execution script
│   └── crudeoil_trade.py       # Crude Oil auto-execution script
├── analysis/
│   ├── gold_analysis.py        # Gold analysis script
│   └── silver_analysis.py      # Silver analysis script
├── helpers/
│   ├── mt5_sell_order.py       # SELL order helper
│   ├── execute_buy.py          # BUY order helper
│   └── execute_sell.py         # SELL order helper
├── sltp/
│   ├── silver_sltp.py          # Silver SL/TP setter
│   ├── bitcoin_sltp.py         # Bitcoin SL/TP setter
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

```bash
# Gold
python auto_trades/gold_trade.py

# Silver
python auto_trades/silver_trade.py

# Bitcoin
python auto_trades/bitcoin_trade.py

# Crude Oil
python auto_trades/crudeoil_trade.py
```

### Set Stop Loss / Take Profit

```bash
# Silver
python sltp/silver_sltp.py

# Bitcoin
python sltp/bitcoin_sltp.py
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

| Asset | Symbol | Typical Spread | Digits |
|-------|--------|----------------|--------|
| Gold | GOLD | ~0.40 | 2 |
| Silver | SILVER | ~0.03 | 3 |
| Bitcoin | BTCUSD | ~25-30 | 2 |
| WTI Crude | WTICrude | ~0.03 | 2 |
| Brent Oil | BRENT_OIL | ~0.05 | 2 |

## Trading Signals

Each auto-trade script includes:
- **Direction**: BUY or SELL
- **Entry**: Market or limit price
- **Stop Loss**: Based on technical levels
- **Take Profit**: Multiple targets (TP1, TP2)
- **Position Size**: Calculated via Kelly Criterion (fractional)
- **Risk/Reward**: Minimum 1:1.5

## Example: Gold Trade Output

```
======================================================================
GOLD (XAUUSD) - AUTO-EXECUTION
======================================================================

Account: 107069198 | Balance: $9531.41 | Equity: $9393.79

GOLD: Bid $4675.84 | Ask $4676.24 | Spread $0.40

TRADE PARAMETERS
--------------------------------------------------
Direction: SELL
Entry: $4676.24
Stop Loss: $4762.00
Take Profit 1: $4546.00
Position Size: 0.15 lots
Risk/Reward: 1:1.5

[OK] ORDER FILLED!
  Ticket: 57970123
  SELL 0.15 GOLD @ $4675.84

[OK] SL/TP SET SUCCESSFULLY!
  Stop Loss: $4762.00
  Take Profit: $4546.00
```

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
- Email: moneymotive029-source@github
