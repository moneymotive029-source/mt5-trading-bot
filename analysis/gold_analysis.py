import MetaTrader5 as mt5
import pandas as pd

mt5.initialize(login=107069198, password='D@5qZuUd', server='Ava-Demo 1-MT5')

# Get H4 data for broader context
df = pd.DataFrame(mt5.copy_rates_from_pos('GOLD', mt5.TIMEFRAME_H4, 0, 100))
df['time'] = pd.to_datetime(df['time'], unit='s')

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

print('=' * 60)
print('GOLD (XAUUSD) COMPREHENSIVE TRADING ANALYSIS')
print('=' * 60)
print()
print('CURRENT MARKET DATA')
print('-' * 40)
print(f'Price: ${price:.2f}')
print(f'H4 Range: ${h4_low:.2f} - ${h4_high:.2f}')
print(f'ATR (14): {atr:.2f} points')
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
print(f'Resistance 1: ${recent_high:.2f} (recent high)')
print(f'Resistance 2: ${h4_high:.2f} (H4 high)')
print(f'Support 1: ${recent_low:.2f} (recent low)')
print(f'Support 2: ${h4_low:.2f} (H4 low)')
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
if bullish > bearish:
    direction = 'BUY'
    confidence = 'High' if bullish >= 3 else 'Medium'
elif bearish > bullish:
    direction = 'SELL'
    confidence = 'High' if bearish >= 3 else 'Medium'
else:
    direction = 'NEUTRAL'
    confidence = 'Medium'

print(f'Direction: {direction}')
print(f'Confidence: {confidence}')
print(f'Bullish: {bullish} | Bearish: {bearish}')
print()

# Current position
print('CURRENT POSITION')
print('-' * 40)
positions = mt5.positions_get(symbol='GOLD')
if positions:
    for pos in positions:
        pos_type = 'BUY' if pos.type == 0 else 'SELL'
        print(f'{pos_type} {pos.volume} @ ${pos.price_open:.2f}')
        print(f'Current: ${pos.price_current:.2f}')
        print(f'SL: ${pos.sl:.2f} | TP: ${pos.tp:.2f}')
        print(f'P/L: +${pos.profit:.2f}')
else:
    print('No open positions')
print()

# Trade recommendation
print('RECOMMENDED ACTION')
print('-' * 40)
if direction == 'NEUTRAL':
    print('Recommendation: HOLD existing position')
    print('- Market is consolidating, no clear directional bias')
    print('- Keep current SL at $4650.00')
    print('- Consider setting TP at $4700-4720 to lock in gains')
    tp_entry = price + (atr * 2)
    print(f'- Suggested TP: ${tp_entry:.2f} (+{atr*2:.1f} points)')
elif direction == 'BUY':
    print('Recommendation: ADD to position or open new BUY')
    entry = price
    sl = price - (atr * 1.5)
    tp = price + (atr * 3)
    print(f'- Entry: ${entry:.2f}')
    print(f'- SL: ${sl:.2f} (-{atr*1.5:.1f} points)')
    print(f'- TP: ${tp:.2f} (+{atr*3:.1f} points)')
    print(f'- Risk/Reward: 1:{(atr*3)/(atr*1.5):.1f}')
else:
    print('Recommendation: Consider closing long position')
    print(f'- If price breaks below ${recent_low:.2f}, SELL signal strengthens')
    print(f'- Wait for confirmation before opening short')

print()
print('=' * 60)
print('DISCLAIMER: This analysis is for informational purposes only.')
print('Trading involves substantial risk. Past performance does not')
print('guarantee future results.')
print('=' * 60)

mt5.shutdown()
