"""
Gold (XAUUSD) Auto-Execution Script
Based on comprehensive trading analysis

Signal: SELL (contrarian on geopolitical easing) or BUY (on safe-haven demand)
"""

import MetaTrader5 as mt5
import time

# Connect with retry
connected = False
for i in range(3):
    if mt5.initialize(login=107069198, password='D@5qZuUd', server='Ava-Demo 1-MT5'):
        connected = True
        break
    time.sleep(1)

if not connected:
    print('[ERROR] Failed to connect to MT5')
    exit(1)

print('=' * 70)
print('GOLD (XAUUSD) - AUTO-EXECUTION')
print('=' * 70)
print()

acc = mt5.account_info()
if acc is None:
    print('[ERROR] Failed to get account info')
    mt5.shutdown()
    exit(1)

print(f'Account: {acc.login} | Balance: ${acc.balance:.2f} | Equity: ${acc.equity:.2f}')
print()

# Select symbol
mt5.symbol_select('GOLD', True)
time.sleep(0.5)

tick = mt5.symbol_info_tick('GOLD')
if tick is None or tick.bid == 0:
    print('[ERROR] GOLD data not available')
    mt5.shutdown()
    exit(1)

print(f'GOLD: Bid ${tick.bid:.2f} | Ask ${tick.ask:.2f} | Spread ${tick.ask-tick.bid:.2f}')
print()

# Check existing position
positions = mt5.positions_get(symbol='GOLD')
if positions:
    print('[!] Existing GOLD position found - skipping duplicate entry')
    for pos in positions:
        print(f'  {"BUY" if pos.type == 0 else "SELL"} {pos.volume} @ ${pos.price_open:.2f} | P/L: ${pos.profit:.2f}')
    mt5.shutdown()
    exit(0)

# Trade parameters - update based on analysis
DIRECTION = 'SELL'  # or 'BUY'
ENTRY_PRICE = tick.bid if DIRECTION == 'SELL' else tick.ask
STOP_LOSS = ENTRY_PRICE + 86 if DIRECTION == 'SELL' else ENTRY_PRICE - 86
TAKE_PROFIT = ENTRY_PRICE - 130 if DIRECTION == 'SELL' else ENTRY_PRICE + 130

# Position sizing: 2% risk
risk_amount = acc.balance * 0.02
risk_points = abs(ENTRY_PRICE - STOP_LOSS)
position_size = round(risk_amount / (risk_points * 10), 2)  # Gold: ~$10 per 0.01 lot per $1
position_size = max(0.01, min(position_size, 1.0))

print('TRADE PARAMETERS')
print('-' * 50)
print(f'Direction: {DIRECTION}')
print(f'Entry: ${ENTRY_PRICE:.2f}')
print(f'Stop Loss: ${STOP_LOSS:.2f}')
print(f'Take Profit: ${TAKE_PROFIT:.2f}')
print(f'Position Size: {position_size} lots')
print(f'Risk Amount: ${risk_amount:.2f}')
print(f'Risk/Reward: 1:{abs(TAKE_PROFIT-ENTRY_PRICE)/risk_points:.1f}')
print()

# Execute order
print(f'EXECUTING {DIRECTION} ORDER...')

order_type = mt5.ORDER_TYPE_SELL if DIRECTION == 'SELL' else mt5.ORDER_TYPE_BUY

# Try different filling modes
filling_modes = [
    (mt5.ORDER_FILLING_FOK, "FOK"),
    (mt5.ORDER_FILLING_RETURN, "RETURN"),
]

result = None
for filling_mode, mode_name in filling_modes:
    print(f'Trying {mode_name} filling mode...')

    order_request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': 'GOLD',
        'volume': position_size,
        'type': order_type,
        'price': ENTRY_PRICE,
        'deviation': 50,
        'magic': 234000,
        'comment': 'Gold Auto-Execution',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': filling_mode,
    }

    result = mt5.order_send(order_request)

    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f'[OK] {mode_name} succeeded!')
        break
    else:
        print(f'  Retcode: {result.retcode if result else "None"} | Comment: {result.comment if result else "None"}')

print()

if result and result.retcode == mt5.TRADE_RETCODE_DONE:
    print('[OK] ORDER FILLED!')
    print(f'  Ticket: {result.order}')
    print(f'  {DIRECTION} {result.volume} GOLD @ ${result.price:.2f}')
    print()

    time.sleep(1)

    # Set SL/TP
    positions = mt5.positions_get(symbol='GOLD')
    if positions:
        pos = positions[0]
        sltp_request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'symbol': 'GOLD',
            'position': pos.ticket,
            'sl': STOP_LOSS,
            'tp': TAKE_PROFIT,
        }
        sltp_result = mt5.order_send(sltp_request)

        if sltp_result and sltp_result.retcode == mt5.TRADE_RETCODE_DONE:
            print('[OK] SL/TP SET SUCCESSFULLY!')
            print(f'  Stop Loss: ${STOP_LOSS:.2f}')
            print(f'  Take Profit: ${TAKE_PROFIT:.2f}')
        else:
            print(f'[!] SL/TP pending: {sltp_result.comment if sltp_result else "Unknown"}')

    print()
    print('=' * 70)
    print('TRADE SUMMARY')
    print('=' * 70)
    print(f'{DIRECTION} {position_size} GOLD @ ${ENTRY_PRICE:.2f}')
    print(f'SL: ${STOP_LOSS:.2f} | TP: ${TAKE_PROFIT:.2f}')
    print(f'Risk: ${risk_amount:.2f} | R/R: 1:{abs(TAKE_PROFIT-ENTRY_PRICE)/risk_points:.1f}')
    print('=' * 70)
else:
    print('[ERROR] ORDER FAILED')
    if result:
        print(f'  Retcode: {result.retcode}')
        print(f'  Comment: {result.comment}')

mt5.shutdown()
