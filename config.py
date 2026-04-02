"""
═══════════════════════════════════════════════════════════════════
MT5 TRADING BOT - CONFIGURATION
═══════════════════════════════════════════════════════════════════
"""

# ─────────────────────────────────────────────────────────────────
# MT5 CREDENTIALS (CHANGE THESE - Your credentials were exposed!)
# ─────────────────────────────────────────────────────────────────
MT5_LOGIN = 107069198  # Your login ID
MT5_PASSWORD = "D@5qZuUd"  # ⚠️ CHANGE THIS - credentials were exposed!
MT5_SERVER = "Ava-Demo 1-MT5"  # Your broker server
MT5_PATH = r"C:\Program Files\Ava Trade MT5 Terminal\terminal64.exe"  # MT5 terminal path

# ─────────────────────────────────────────────────────────────────
# TRADING SETTINGS
# ─────────────────────────────────────────────────────────────────
ACCOUNT_BALANCE = 100000  # Your account balance in USD
RISK_PER_TRADE = 0.02  # 2% risk per trade (0.01 = 1%, 0.02 = 2%)
MAX_POSITIONS = 5  # Maximum concurrent positions
USE_LEVERAGE = True  # Use margin/leverage

# ─────────────────────────────────────────────────────────────────
# SYMBOL CONFIGURATION
# ─────────────────────────────────────────────────────────────────
SYMBOLS = {
    "GOLD": {  # Gold (100 Troy Oz)
        "enabled": True,
        "contract_size": 100,  # 100 oz per lot
        "min_lot": 0.01,
        "max_lot": 10.0,
        "lot_step": 0.01,
        "typical_spread": 50,  # $50 per oz spread
        "atr_multiplier_sl": 2.5,
        "entry_zones": [(4420, 4480)],  # Buy zones
        "resistance_zones": [(4600, 4640)],  # Sell/take profit zones
        "signal": "WAIT_LONG",  # WAIT_LONG, LONG, SHORT, WAIT_SHORT
    },
    "SILVER": {  # Silver (10,000 Troy Oz)
        "enabled": True,
        "contract_size": 10000,  # 10000 oz per lot
        "min_lot": 0.01,
        "max_lot": 5.0,
        "lot_step": 0.01,
        "typical_spread": 0.12,  # 12 cents
        "atr_multiplier_sl": 3.0,
        "entry_zones": [(68.50, 70.00)],
        "resistance_zones": [(73.50, 75.00)],
        "signal": "WAIT_SHORT",
    },
    "PLATINUM": {  # Platinum - BEST SETUP (100 Troy Oz)
        "enabled": True,
        "contract_size": 100,  # 100 oz per lot
        "min_lot": 0.01,
        "max_lot": 5.0,
        "lot_step": 0.01,
        "typical_spread": 20,  # $20 per oz
        "atr_multiplier_sl": 2.5,
        "entry_zones": [(1850, 1890)],  # STRONG BUY ZONE
        "resistance_zones": [(1950, 2020), (2120, 2200)],
        "signal": "LONG",
    },
    "PALLADIUM": {  # Palladium (100 Troy Oz)
        "enabled": True,
        "contract_size": 100,
        "min_lot": 0.01,
        "max_lot": 3.0,
        "lot_step": 0.01,
        "typical_spread": 30,
        "atr_multiplier_sl": 3.0,
        "entry_zones": [(1420, 1460)],
        "resistance_zones": [(1340, 1280), (1200, 1150)],
        "signal": "WAIT_SHORT",
    },
    "COPPER": {  # Copper (HG) - STRONGEST BUY (10,000 lbs)
        "enabled": True,
        "contract_size": 10000,  # 10000 lbs per lot
        "min_lot": 0.01,
        "max_lot": 5.0,
        "lot_step": 0.01,
        "typical_spread": 0.06,  # 6 cents
        "atr_multiplier_sl": 2.5,
        "entry_zones": [(4.35, 4.45)],  # STRONG BUY ZONE (USD/lb)
        "resistance_zones": [(4.75, 5.10), (5.50, 6.00)],
        "signal": "LONG",
    },
}

# ─────────────────────────────────────────────────────────────────
# RISK MANAGEMENT
# ─────────────────────────────────────────────────────────────────
RISK_RULES = {
    "max_daily_loss_pct": 0.05,  # Stop trading after 5% daily loss
    "max_drawdown_pct": 0.10,  # Stop trading after 10% drawdown
    "max_correlated_positions": 2,  # Max positions in correlated metals
    "correlation_pairs": [
        ("GOLD", "SILVER"),  # Don't hold both long
        ("PLATINUM", "PALLADIUM"),  # PGM correlation
    ],
    "news_blackout_minutes": 30,  # Don't trade 30min before/after high-impact news
}

# ─────────────────────────────────────────────────────────────────
# HIGH-IMPACT NEWS TIMES (ET) - AVOID TRADING
# ─────────────────────────────────────────────────────────────────
NEWS_EVENTS = {
    "2026-04-03": [("08:30", "NFP", 60)],  # 60 min blackout
    "2026-04-10": [("08:30", "CPI", 60)],
    "2026-04-29": [("14:00", "FOMC", 120)],
    "2026-04-30": [("14:30", "Fed Presser", 90)],
}

# ─────────────────────────────────────────────────────────────────
# LOGGING & ALERTS
# ─────────────────────────────────────────────────────────────────
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "mt5_bot.log"
ENABLE_TELEGRAM = False  # Set True for Telegram alerts
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
ENABLE_EMAIL = False  # Set True for email alerts
SMTP_SERVER = ""
SMTP_PORT = 587
EMAIL_USER = ""
EMAIL_PASSWORD = ""
EMAIL_RECIPIENT = ""

# ─────────────────────────────────────────────────────────────────
# EXECUTION SETTINGS
# ─────────────────────────────────────────────────────────────────
EXECUTION = {
    "use_market_orders": True,  # True = Market, False = Limit
    "slippage_points": 5,  # Max slippage in points
    "magic_number": 20260401,  # EA identifier
    "comment": "AI_Signal_Bot",
    "retry_attempts": 3,
    "retry_delay_ms": 500,
}
