# MT5 Metals Trading Bot

Automated trading bot for MetaTrader 5 based on comprehensive CFD metals analysis.

> **Warning:** Trading CFDs and Forex involves significant risk of loss. This bot is provided for educational purposes only. Always test on a demo account first.

## Features

- **Automated Signal Execution** - Monitors entry zones and executes trades automatically
- **Risk-Based Position Sizing** - Calculates lot sizes based on 2% risk per trade
- **ATR-Based Stop Losses** - Volatility-adjusted stops (2.5-3x ATR)
- **4-Tier Take Profit Scaling** - 25% @ 1.5R, 30% @ 2.5R, 30% @ 4R, 15% runner
- **Breakeven Stop Management** - Auto-moves stops when profitable by 1R
- **Correlation Risk Management** - Avoids holding correlated longs (Gold+Silver, Pt+Pd)
- **News Blackout Periods** - Avoids trading during NFP, CPI, FOMC events

## Requirements

- **MetaTrader 5** installed on Windows
- **Active MT5 account** (demo or live) with a broker
- **Python 3.8+**
- **AutoTrading enabled** in MT5 (press F4)
- **Account trade mode = 2** (Full Trading - contact broker if disabled)

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd mt5-trading-bot

# Install Python dependencies
pip install -r requirements.txt
```

## Configuration

Edit `config.py` with your settings:

```python
# MT5 Credentials
MT5_LOGIN = 12345678  # Your login ID
MT5_PASSWORD = "your_password"  # Your MT5 password
MT5_SERVER = "YourBroker-Server"  # e.g., "ICMarkets-Live02"
MT5_PATH = r"C:\Program Files\Your Broker\terminal64.exe"  # MT5 path

# Trading Settings
ACCOUNT_BALANCE = 10000  # Your account balance
RISK_PER_TRADE = 0.02  # 2% risk per trade
MAX_POSITIONS = 5  # Maximum concurrent positions
```

### Symbol Configuration

Each metal has configurable entry zones, contract sizes, and signals:

```python
SYMBOLS = {
    "GOLD": {
        "enabled": True,
        "contract_size": 100,  # 100 oz per lot
        "entry_zones": [(4420, 4480)],  # Buy zone
        "signal": "WAIT_LONG",  # LONG, SHORT, WAIT_LONG, WAIT_SHORT
    },
    "PLATINUM": {
        "enabled": True,
        "contract_size": 100,
        "entry_zones": [(1850, 1890)],
        "signal": "LONG",
    },
    "COPPER": {
        "enabled": True,
        "contract_size": 10000,  # 10,000 lbs per lot
        "entry_zones": [(4.35, 4.45)],
        "signal": "LONG",
    },
}
```

## Usage

### Start the Bot

```bash
python main.py
```

The bot will:
1. Connect to your MT5 terminal
2. Monitor entry zones every 5 seconds
3. Execute trades when conditions are met
4. Manage stop losses and take profits automatically

### Stop the Bot

Press `Ctrl+C` in the terminal.

### Check Logs

Activity is logged to `mt5_bot.log` and displayed in the console.

## Trading Strategy

### Position Sizing Formula

```
Lot Size = (Account Balance × Risk %) / (Stop Distance × Contract Size)
```

Example for Copper on $10K account (2% risk):
- Entry: $4.40/lb
- Stop: $4.20/lb ($0.20 risk)
- Contract: 10,000 lbs
- Lot Size = $200 / ($0.20 × 10,000) = **0.1 lots**

### Take Profit Structure

| Level | Target | Close % | Remaining |
|-------|--------|---------|-----------|
| TP1 | 1.5R | 25% | 75% |
| TP2 | 2.5R | 30% | 45% |
| TP3 | 4.0R | 30% | 15% |
| TP4 | 6.0R | 15% | 0% |

### Risk Management Rules

- **Max risk per trade:** 2% (configurable)
- **Max daily loss:** 5% (stops trading for the day)
- **Max drawdown:** 10% (stops trading)
- **Max correlated positions:** 2 (avoids Gold+Silver both long)
- **News blackout:** 30-120 min around high-impact events

## Current Trading Signals

| Symbol | Signal | Entry Zone | Target | Stop | Confidence |
|--------|--------|------------|--------|------|------------|
| **COPPER** | LONG | $4.35-4.45/lb | $5.00-6.00 | ATR-based | 70% |
| **PLATINUM** | LONG | $1,850-1,890 | $2,000-2,200 | ATR-based | 72% |
| **GOLD** | WAIT→LONG | $4,420-4,480 | $4,620-5,050 | ATR-based | 60% |

## Troubleshooting

### "AutoTrading disabled by client"

1. Press **F4** in MT5 to toggle AutoTrading ON (button turns green)
2. Go to `Tools → Options → Expert Advisors`
3. Check "Allow algorithmic trading"
4. Restart MT5

### "Account trade mode: 0 (DISABLED)"

Your broker has disabled trading on the account. Contact support to enable **full trading** (trade mode 2). Common causes:
- Weekend market closure (forex closed Fri evening - Sun 5PM ET)
- New demo account pending activation
- Verification required

### "Symbol not available"

Symbol names vary by broker. Check available symbols:

```python
import MetaTrader5 as mt5
mt5.initialize(...)
symbols = mt5.symbols_get()
for s in symbols:
    if 'GOLD' in s.name or 'XAU' in s.name:
        print(s.name)
```

Update `config.py` with your broker's symbol names.

### "Failed to connect to MT5"

1. Ensure MT5 terminal is running
2. Verify credentials in `config.py`
3. Set `MT5_PATH` to your terminal executable:
   ```python
   MT5_PATH = r"C:\Program Files\Broker\terminal64.exe"
   ```

## File Structure

```
mt5-trading-bot/
├── config.py           # Configuration & trading settings
├── mt5_connector.py    # MT5 API integration
├── signal_engine.py    # Signal generation logic
├── order_executor.py   # Order placement & management
├── main.py             # Main entry point
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── CLAUDE.md           # Claude Code quick reference
└── .gitignore          # Git ignore rules
```

## Disclaimer

**Trading CFDs and Forex involves significant risk of loss.** This bot is provided for educational purposes only. Past performance does not guarantee future results.

1. Test thoroughly on a demo account first
2. Start with small position sizes
3. Never risk more than you can afford to lose
4. Consult with a licensed financial advisor

## License

MIT License - See [LICENSE](LICENSE) file.
