import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

# Connect to AvaTrade MT5
mt5.initialize(login=107069198, password='D@5qZuUd', server='Ava-Demo 1-MT5')
mt5.symbol_select('SILVER', True)

print('=' * 60)
print('SILVER (XAGUSD) COMPREHENSIVE TRADING ANALYSIS')
print('=' * 60)
print()

# Get current price
tick = mt5.symbol_info_tick('SILVER')
if tick is None:
    print('SILVER not available on this broker')
    print('Checking available symbols...')
    symbols = mt5.symbols_get()
    precious = [s.name for s in symbols if s and any(m in s.name.lower() for m in ['silver', 'xag', 'plat', 'pall'])]
    print('Precious metals available:', precious)
    mt5.shutdown()
    exit(1)

print(f'Current Price: Bid ${tick.bid:.2f} | Ask ${tick.ask:.2f} | Spread ${tick.ask-tick.bid:.2f}')
print()

# Get historical data (H4)
df = pd.DataFrame(mt5.copy_rates_from_pos('SILVER', mt5.TIMEFRAME_H4, 0, 200))
df['time'] = pd.to_datetime(df['time'], unit='s')

if len(df) == 0:
    print('No historical data available')
    mt5.shutdown()
    exit(1)

price = df['close'].iloc[-1]
h4_high = df['high'].max()
h4_low = df['low'].min()

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

# Moving Averages
sma20 = df['close'].rolling(20).mean().iloc[-1]
sma50 = df['close'].rolling(50).mean().iloc[-1]

# Recent levels
recent_high = df['high'].rolling(20).max().iloc[-1]
recent_low = df['low'].rolling(20).min().iloc[-1]

print('CURRENT MARKET DATA')
print('-' * 40)
print(f'Price: ${price:.2f}')
print(f'H4 Range: ${h4_low:.2f} - ${h4_high:.2f}')
print(f'ATR (14): ${atr:.2f}')
print()

print('TECHNICAL INDICATORS')
print('-' * 40)
rsi_val = rsi.iloc[-1]
rsi_state = "Overbought" if rsi_val > 70 else "Oversold" if rsi_val < 30 else "Neutral"
print(f'RSI (14): {rsi_val:.2f} - {rsi_state}')
print(f'MACD: {macd.iloc[-1]:.2f} | Signal: {macd_signal.iloc[-1]:.2f}')
macd_hist = macd.iloc[-1] - macd_signal.iloc[-1]
print(f'MACD Histogram: {macd_hist:.2f}')
print()

print('KEY LEVELS')
print('-' * 40)
print(f'Resistance 1: ${recent_high:.2f}')
print(f'Resistance 2: ${h4_high:.2f}')
print(f'Support 1: ${recent_low:.2f}')
print(f'Support 2: ${h4_low:.2f}')
print()

print('TREND ASSESSMENT')
print('-' * 40)
print(f'Price vs SMA20: ${price:.2f} vs ${sma20:.2f} - {"Above" if price > sma20 else "Below"}')
print(f'Price vs SMA50: ${price:.2f} vs ${sma50:.2f} - {"Above" if price > sma50 else "Below"}')
print()

# Signal generation
bullish = 0
bearish = 0
if rsi_val < 30: bullish += 1
if rsi_val > 70: bearish += 1
if macd.iloc[-1] > macd_signal.iloc[-1]: bullish += 1
else: bearish += 1
if price > sma20: bullish += 1
else: bearish += 1
if price > sma50: bullish += 1
else: bearish += 1

print('SIGNAL SUMMARY')
print('-' * 40)
if bullish > bearish + 1:
    direction = 'BUY'
    confidence = 'High' if bullish >= 3 else 'Medium'
elif bearish > bullish + 1:
    direction = 'SELL'
    confidence = 'High' if bearish >= 3 else 'Medium'
else:
    direction = 'NEUTRAL'
    confidence = 'Medium'

print(f'Direction: {direction}')
print(f'Confidence: {confidence}')
print(f'Bullish: {bullish} | Bearish: {bearish}')
print()

# Trade setup
if direction == 'BUY':
    entry = price
    sl = price - (atr * 2)
    tp = price + (atr * 3)
elif direction == 'SELL':
    entry = price
    sl = price + (atr * 2)
    tp = price - (atr * 3)
else:
    # Default to last signal
    if macd.iloc[-1] > macd_signal.iloc[-1]:
        direction = 'BUY'
        entry = price
        sl = price - (atr * 2)
        tp = price + (atr * 3)
    else:
        direction = 'SELL'
        entry = price
        sl = price + (atr * 2)
        tp = price - (atr * 3)

print('RECOMMENDED TRADE SETUP')
print('-' * 40)
print(f'Direction: {direction}')
print(f'Entry: ${entry:.2f}')
print(f'Stop Loss: ${sl:.2f} ({abs(entry-sl):.2f} points)')
print(f'Take Profit: ${tp:.2f} ({abs(tp-entry):.2f} points)')
risk_reward = abs(tp - entry) / abs(sl - entry)
print(f'Risk/Reward: 1:{risk_reward:.1f}')
print()

# Account info
acc = mt5.account_info()
balance = acc.balance if acc else 10000
risk_amount = balance * 0.02
risk_points = abs(entry - sl)
position_size = round(risk_amount / (risk_points * 50), 2) if risk_points > 0 else 0.01  # Silver: ~50 per point per lot
position_size = max(0.01, min(position_size, 1.0))  # Cap at 1 lot

print('RISK MANAGEMENT')
print('-' * 40)
print(f'Account Balance: ${balance:.2f}')
print(f'Risk per trade (2%): ${risk_amount:.2f}')
print(f'Recommended Position: {position_size} lots')
print()

# Store for execution
print('=' * 60)
print('AUTO-EXECUTION PARAMETERS')
print('=' * 60)
print(f'DIRECTION: {direction}')
print(f'ENTRY: {entry:.2f}')
print(f'SL: {sl:.2f}')
print(f'TP: {tp:.2f}')
print(f'VOLUME: {position_size} lots')
print('=' * 60)

mt5.shutdown()
