import MetaTrader5 as mt5
import pandas as pd

# Connect to AvaTrade MT5
mt5.initialize(login=107069198, password='D@5qZuUd', server='Ava-Demo 1-MT5')
mt5.symbol_select('SILVER', True)

print('=' * 60)
print('SILVER (XAGUSD) COMPREHENSIVE TRADING ANALYSIS')
print('=' * 60)
print()

# Get current price
tick = mt5.symbol_info_tick('SILVER')
print(f'Current Price: Bid ${tick.bid:.2f} | Ask ${tick.ask:.2f} | Spread ${tick.ask-tick.bid:.3f}')
print()

# Get H4 historical data
df = pd.DataFrame(mt5.copy_rates_from_pos('SILVER', mt5.TIMEFRAME_H4, 0, 200))
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
rsi_val = rsi.iloc[-1]

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
rsi_state = "Overbought" if rsi_val > 70 else "Oversold" if rsi_val < 30 else "Neutral"
print(f'RSI (14): {rsi_val:.2f} - {rsi_state}')
print(f'MACD: {macd.iloc[-1]:.2f} | Signal: {macd_signal.iloc[-1]:.2f}')
print(f'MACD Histogram: {macd.iloc[-1] - macd_signal.iloc[-1]:.2f}')
print()

print('KEY LEVELS')
print('-' * 40)
print(f'Resistance: ${recent_high:.2f}')
print(f'Support: ${recent_low:.2f}')
print()

print('TREND')
print('-' * 40)
print(f'vs SMA20: {"Above" if price > sma20 else "Below"} (${sma20:.2f})')
print(f'vs SMA50: {"Above" if price > sma50 else "Below"} (${sma50:.2f})')
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

if bullish > bearish + 1:
    direction = 'BUY'
elif bearish > bullish + 1:
    direction = 'SELL'
else:
    direction = 'BUY' if macd.iloc[-1] > macd_signal.iloc[-1] else 'SELL'

# Trade setup
if direction == 'BUY':
    sl = price - (atr * 2)
    tp = price + (atr * 3)
else:
    sl = price + (atr * 2)
    tp = price - (atr * 3)

# Account info
acc = mt5.account_info()
balance = acc.balance
risk_amount = balance * 0.02
risk_points = abs(price - sl)
# Silver: ~$0.01 move = ~$10 per standard lot
position_size = round(risk_amount / (risk_points * 1000), 2)
position_size = max(0.1, min(position_size, 5.0))

print('SIGNAL SUMMARY')
print('-' * 40)
print(f'Direction: {direction}')
print(f'Confidence: {"High" if abs(bullish-bearish) >= 2 else "Medium"}')
print(f'Bullish: {bullish} | Bearish: {bearish}')
print()

print('RECOMMENDED TRADE')
print('-' * 40)
print(f'{direction} {position_size} lots SILVER')
print(f'Entry: ${price:.2f}')
print(f'SL: ${sl:.2f}')
print(f'TP: ${tp:.2f}')
print(f'Risk/Reward: 1:{abs(tp-price)/abs(price-sl):.1f}')
print()

# FUNDAMENTAL CONTEXT
print('FUNDAMENTAL CONTEXT')
print('-' * 40)
print('Silver/Gold Ratio: ~52 (historically bullish for silver)')
print('Industrial Demand: Solar panels, EVs, electronics growing')
print('Supply Deficit: 3rd year of structural deficit')
print('Green Energy: Major driver for future demand')
print()

print('=' * 60)
print('AUTO-EXECUTION')
print('=' * 60)
print(f'DIRECTION: {direction}')
print(f'VOLUME: {position_size} lots')
print(f'ENTRY: {tick.bid if direction == "SELL" else tick.ask}')
print(f'SL: {sl:.2f}')
print(f'TP: {tp:.2f}')
print('=' * 60)

# EXECUTE THE TRADE
print()
print('EXECUTING TRADE...')

# Place order
order_type = mt5.ORDER_TYPE_SELL if direction == 'SELL' else mt5.ORDER_TYPE_BUY
exec_price = tick.bid if direction == 'SELL' else tick.ask

request = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': 'SILVER',
    'volume': position_size,
    'type': order_type,
    'price': exec_price,
    'deviation': 50,
    'magic': 234000,
    'comment': 'Auto-executed after analysis',
    'type_time': mt5.ORDER_TIME_GTC,
    'type_filling': mt5.ORDER_FILLING_FOK,
}

result = mt5.order_send(request)

if result and result.retcode == mt5.TRADE_RETCODE_DONE:
    print(f'[OK] ORDER FILLED!')
    print(f'  Ticket: {result.order}')
    print(f'  {direction} {result.volume} @ ${result.price:.2f}')

    # Set SL/TP
    import time
    time.sleep(0.5)

    sl_request = {
        'action': mt5.TRADE_ACTION_SLTP,
        'symbol': 'SILVER',
        'position': result.position,
        'sl': sl,
        'tp': tp,
    }

    sl_result = mt5.order_send(sl_request)

    if sl_result and sl_result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f'[OK] SL/TP SET!')
        print(f'  Stop Loss: ${sl:.2f}')
        print(f'  Take Profit: ${tp:.2f}')
    else:
        print(f'⚠ SL/TP pending: {sl_result.comment if sl_result else "Unknown"}')

    print()
    print('TRADE SUMMARY')
    print('-' * 40)
    print(f'{direction} {result.volume} SILVER @ ${result.price:.2f}')
    print(f'SL: ${sl:.2f} (Risk: ${risk_amount:.2f})')
    print(f'TP: ${tp:.2f} (Reward: ${risk_amount * 1.5:.2f})')
else:
    print(f'❌ ORDER FAILED')
    print(f'  Retcode: {result.retcode if result else "None"}')
    print(f'  Comment: {result.comment if result else "None"}')

mt5.shutdown()
