"""
Universal Trading Analysis Script
Works with ANY symbol on MetaTrader 5

Usage:
    python gold_analysis.py --symbol GOLD
    python gold_analysis.py --symbol BTCUSD
    python gold_analysis.py --symbol EURUSD
"""

import MetaTrader5 as mt5
import pandas as pd
import argparse

# MT5 Configuration
MT5_CONFIG = {
    "login": 107069198,
    "password": "D@5qZuUd",
    "server": "Ava-Demo 1-MT5"
}

def connect():
    """Initialize MT5 connection with retry"""
    for i in range(3):
        if mt5.initialize(**MT5_CONFIG):
            return True
        time.sleep(1)
    return False

def get_symbol_info(symbol):
    """Get symbol specifications"""
    info = mt5.symbol_info(symbol)
    if info is None:
        return None
    return {
        "name": info.name,
        "digits": info.digits,
        "point": info.point,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "trade_allowed": info.trade_allowed,
        "spread": info.spread,
        "contract_size": info.trade_contract_size,
    }

def calculate_indicators(df):
    """Calculate technical indicators"""
    # ATR
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(14).mean().iloc[-1]

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    macd = exp1 - exp2
    macd_signal = macd.ewm(span=9).mean()

    return {
        'atr': atr,
        'rsi': rsi.iloc[-1],
        'macd': macd.iloc[-1],
        'macd_signal': macd_signal.iloc[-1],
        'macd_hist': macd.iloc[-1] - macd_signal.iloc[-1],
    }

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Universal Trading Analysis")
    parser.add_argument("--symbol", type=str, required=True, help="Trading symbol (e.g., GOLD, BTCUSD, EURUSD)")
    parser.add_argument("--timeframe", type=str, default="H4", help="Timeframe (default: H4)")
    args = parser.parse_args()

    # Connect to MT5
    if not connect():
        print("[ERROR] Failed to connect to MT5")
        return

    # Select symbol
    mt5.symbol_select(args.symbol, True)
    time.sleep(0.5)

    # Get symbol info
    info = get_symbol_info(args.symbol)
    if info is None:
        print(f"[ERROR] Symbol {args.symbol} not found")
        mt5.shutdown()
        return

    # Get current price
    tick = mt5.symbol_info_tick(args.symbol)
    if tick is None or tick.bid == 0:
        print(f"[ERROR] No price data for {args.symbol}")
        mt5.shutdown()
        return

    # Get historical data
    timeframe_map = {
        'M1': mt5.TIMEFRAME_M1, 'M5': mt5.TIMEFRAME_M5, 'M15': mt5.TIMEFRAME_M15,
        'M30': mt5.TIMEFRAME_M30, 'H1': mt5.TIMEFRAME_H1, 'H4': mt5.TIMEFRAME_H4,
        'D1': mt5.TIMEFRAME_D1, 'W1': mt5.TIMEFRAME_W1, 'MN1': mt5.TIMEFRAME_MN1,
    }
    tf = timeframe_map.get(args.timeframe.upper(), mt5.TIMEFRAME_H4)
    df = pd.DataFrame(mt5.copy_rates_from_pos(args.symbol, tf, 0, 200))
    df['time'] = pd.to_datetime(df['time'], unit='s')

    if len(df) == 0:
        print(f"[ERROR] No historical data for {args.symbol}")
        mt5.shutdown()
        return

    price = df['close'].iloc[-1]
    h4_high = df['high'].max()
    h4_low = df['low'].min()

    # Calculate indicators
    indicators = calculate_indicators(df)

    # Moving Averages
    sma20 = df['close'].rolling(20).mean().iloc[-1]
    sma50 = df['close'].rolling(50).mean().iloc[-1]

    # Recent levels
    recent_high = df['high'].rolling(20).max().iloc[-1]
    recent_low = df['low'].rolling(20).min().iloc[-1]

    # Print analysis
    print("=" * 70)
    print(f"TRADING ANALYSIS: {args.symbol}")
    print("=" * 70)
    print()

    print("CURRENT MARKET DATA")
    print("-" * 50)
    print(f"Price: ${price:.{info['digits']}f}")
    print(f"Spread: {info['spread']} points")
    print(f"20-period High: ${recent_high:.{info['digits']}f}")
    print(f"20-period Low: ${recent_low:.{info['digits']}f}")
    print(f"ATR (14): {indicators['atr']:.{info['digits']}f}")
    print()

    print("TECHNICAL INDICATORS")
    print("-" * 50)
    rsi_state = "Overbought" if indicators['rsi'] > 70 else "Oversold" if indicators['rsi'] < 30 else "Neutral"
    print(f"RSI (14): {indicators['rsi']:.2f} - {rsi_state}")
    print(f"MACD: {indicators['macd']:.{info['digits']}f} | Signal: {indicators['macd_signal']:.{info['digits']}f}")
    print(f"MACD Histogram: {indicators['macd_hist']:.{info['digits']}f}")
    print()

    print("KEY LEVELS")
    print("-" * 50)
    print(f"Resistance 1: ${recent_high:.{info['digits']}f}")
    print(f"Resistance 2: ${h4_high:.{info['digits']}f}")
    print(f"Support 1: ${recent_low:.{info['digits']}f}")
    print(f"Support 2: ${h4_low:.{info['digits']}f}")
    print()

    print("TREND ASSESSMENT")
    print("-" * 50)
    print(f"Price vs SMA20: {'Above' if price > sma20 else 'Below'} (${sma20:.{info['digits']}f})")
    print(f"Price vs SMA50: {'Above' if price > sma50 else 'Below'} (${sma50:.{info['digits']}f})")
    print()

    # Signal generation
    bullish = 0
    bearish = 0
    if indicators['rsi'] < 30: bullish += 1
    if indicators['rsi'] > 70: bearish += 1
    if indicators['macd'] > indicators['macd_signal']: bullish += 1
    else: bearish += 1
    if price > sma20: bullish += 1
    else: bearish += 1
    if price > sma50: bullish += 1
    else: bearish += 1

    print("SIGNAL SUMMARY")
    print("-" * 50)
    if bullish > bearish + 1:
        direction = 'BUY'
        confidence = 'High' if bullish >= 3 else 'Medium'
    elif bearish > bullish + 1:
        direction = 'SELL'
        confidence = 'High' if bearish >= 3 else 'Medium'
    else:
        direction = 'BUY' if indicators['macd'] > indicators['macd_signal'] else 'SELL'
        confidence = 'Medium'

    print(f"Direction: {direction}")
    print(f"Confidence: {confidence}")
    print(f"Bullish: {bullish} | Bearish: {bearish}")
    print()

    # Trade setup
    atr = indicators['atr']
    if direction == 'BUY':
        entry = price
        sl = price - (atr * 2)
        tp = price + (atr * 3)
    else:
        entry = price
        sl = price + (atr * 2)
        tp = price - (atr * 3)

    # Account info
    acc = mt5.account_info()
    balance = acc.balance if acc else 10000
    risk_amount = balance * 0.02
    risk_points = abs(entry - sl)

    print("RECOMMENDED TRADE SETUP")
    print("-" * 50)
    print(f"Direction: {direction}")
    print(f"Entry: ${entry:.{info['digits']}f}")
    print(f"Stop Loss: ${sl:.{info['digits']}f} ({abs(entry-sl):.{info['digits']}f} points)")
    print(f"Take Profit: ${tp:.{info['digits']}f} ({abs(tp-entry):.{info['digits']}f} points)")
    risk_reward = abs(tp - entry) / abs(sl - entry)
    print(f"Risk/Reward: 1:{risk_reward:.1f}")
    print()

    print("RISK MANAGEMENT")
    print("-" * 50)
    print(f"Account Balance: ${balance:.2f}")
    print(f"Risk per trade (2%): ${risk_amount:.2f}")
    print()

    # Check existing position
    print("CURRENT POSITION")
    print("-" * 50)
    positions = mt5.positions_get(symbol=args.symbol)
    if positions:
        for pos in positions:
            pos_type = 'BUY' if pos.type == 0 else 'SELL'
            print(f"{pos_type} {pos.volume} @ ${pos.price_open:.{info['digits']}f}")
            print(f"  Current: ${pos.price_current:.{info['digits']}f}")
            print(f"  SL: ${pos.sl:.{info['digits']}f} | TP: ${pos.tp:.{info['digits']}f}")
            print(f"  P/L: ${pos.profit:.2f}")
    else:
        print("No open positions")

    print()
    print("=" * 70)
    print("AUTO-EXECUTION PARAMETERS")
    print("=" * 70)
    print(f"DIRECTION: {direction}")
    print(f"ENTRY: {entry:.{info['digits']}f}")
    print(f"SL: {sl:.{info['digits']}f}")
    print(f"TP: {tp:.{info['digits']}f}")
    print("=" * 70)
    print()
    print("To execute this trade, run:")
    print(f"  python auto_trades/universal_trade.py --symbol {args.symbol} --direction {direction} --volume 0.1 --sl {sl:.{info['digits']}f} --tp {tp:.{info['digits']}f}")
    print()

    mt5.shutdown()

if __name__ == "__main__":
    import time
    main()
