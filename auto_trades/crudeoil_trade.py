"""
Crude Oil (WTI) Auto-Execution Script
Based on comprehensive trading analysis - April 2, 2026

Signal: BUY LONG
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
    print(f'Last error: {mt5.last_error()}')
    exit(1)

print('=' * 70)
print('CRUDE OIL (WTI) - AUTO-EXECUTION')
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
mt5.symbol_select('WTICrude', True)
time.sleep(0.5)

tick = mt5.symbol_info_tick('WTICrude')
if tick is None or tick.bid == 0:
    print('[ERROR] WTI Crude data not available')
    mt5.shutdown()
    exit(1)

print(f'WTI Crude: Bid ${tick.bid:.2f} | Ask ${tick.ask:.2f}')
print()

ENTRY_PRICE = tick.ask
STOP_LOSS = 76.50
TAKE_PROFIT_1 = 85.00
TAKE_PROFIT_2 = 91.50

risk_amount = acc.balance * 0.02
risk_points = ENTRY_PRICE - STOP_LOSS
position_size = round(risk_amount / (risk_points * 1000), 2)
position_size = max(0.05, min(position_size, 1.0))

print(f'Direction: BUY LONG | Entry: ${ENTRY_PRICE:.2f}')
print(f'SL: ${STOP_LOSS:.2f} | TP1: ${TAKE_PROFIT_1:.2f} | TP2: ${TAKE_PROFIT_2:.2f}')
print(f'Position: {position_size} lots')
print()

# Check existing position
positions = mt5.positions_get(symbol='WTICrude')
if positions:
    print('[!] Existing position found - skipping')
    for pos in positions:
        print(f'  {"BUY" if pos.type == 0 else "SELL"} {pos.volume} @ ${pos.price_open:.2f} | P/L: ${pos.profit:.2f}')
    mt5.shutdown()
    exit(0)

# Try different filling modes
filling_modes = [
    (mt5.ORDER_FILLING_FOK, "FOK"),
    (mt5.ORDER_FILLING_RETURN, "RETURN"),
]

result = None
for filling_mode, mode_name in filling_modes:
    print(f'Trying {mode_name} filling mode...')

    buy_request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': 'WTICrude',
        'volume': position_size,
        'type': mt5.ORDER_TYPE_BUY,
        'price': ENTRY_PRICE,
        'deviation': 50,
        'magic': 234000,
        'comment': 'Crude Oil Auto-Execution',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': filling_mode,
    }

    result = mt5.order_send(buy_request)

    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f'[OK] {mode_name} succeeded!')
        break
    else:
        print(f'  Retcode: {result.retcode if result else "None"} | Comment: {result.comment if result else "None"}')

print()

blended_tp = (TAKE_PROFIT_1 + TAKE_PROFIT_2) / 2

if result and result.retcode == mt5.TRADE_RETCODE_DONE:
    print('[OK] ORDER FILLED!')
    print(f'  Ticket: {result.order}')
    print(f'  BUY {result.volume} WTI @ ${result.price:.2f}')
    print()

    time.sleep(1)

    positions = mt5.positions_get(symbol='WTICrude')
    if positions:
        pos = positions[0]
        sltp_request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'symbol': 'WTICrude',
            'position': pos.ticket,
            'sl': STOP_LOSS,
            'tp': blended_tp,
        }
        sltp_result = mt5.order_send(sltp_request)

        if sltp_result and sltp_result.retcode == mt5.TRADE_RETCODE_DONE:
            print('[OK] SL/TP SET!')
            print(f'  SL: ${STOP_LOSS:.2f} | TP: ${blended_tp:.2f}')
        else:
            print(f'[!] SL/TP pending: {sltp_result.comment if sltp_result else "Unknown"}')

    print()
    print('=' * 70)
    print(f'BUY {position_size} WTI @ ${ENTRY_PRICE:.2f}')
    print(f'SL: ${STOP_LOSS:.2f} | TP: ${blended_tp:.2f}')
    print('=' * 70)
else:
    print('[ERROR] ALL FILLING MODES FAILED')
    print(f'Final Retcode: {result.retcode if result else "None"}')
    print(f'Final Comment: {result.comment if result else "None"}')

mt5.shutdown()
