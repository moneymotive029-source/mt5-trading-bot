"""
Bitcoin (BTC/USD) Auto-Execution Script
Based on comprehensive trading analysis - April 2, 2026

Signal: BUY LONG (Contrarian play on Extreme Fear)
Entry: ~$66,861
SL: $63,500
TP1: $72,800
TP2: $84,600
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
print('BITCOIN (BTC/USD) - AUTO-EXECUTION')
print('=' * 70)
print()

acc = mt5.account_info()
if acc is None:
    print('[ERROR] Failed to get account info')
    mt5.shutdown()
    exit(1)

print(f'Account: {acc.login} | Balance: ${acc.balance:.2f} | Equity: ${acc.equity:.2f}')
print()

# Select symbol and get price
mt5.symbol_select('BTCUSD', True)
time.sleep(0.5)

tick = mt5.symbol_info_tick('BTCUSD')
if tick is None or tick.bid == 0:
    print('[ERROR] BTCUSD data not available')
    mt5.shutdown()
    exit(1)

print(f'BTC/USD: Bid ${tick.bid:.2f} | Ask ${tick.ask:.2f} | Spread ${tick.ask-tick.bid:.2f}')
print()

# Trade parameters from analysis
ENTRY_PRICE = tick.ask
STOP_LOSS = 63500.00    # Below $65K psychological support
TAKE_PROFIT_1 = 72800.00  # Weekly close resistance
TAKE_PROFIT_2 = 84600.00  # 23-week MA target

# Position sizing: 2% risk
risk_amount = acc.balance * 0.02
risk_points = ENTRY_PRICE - STOP_LOSS
# BTCUSD: ~$1 per 0.01 lot per $1 move (approximate)
position_size = round(risk_amount / risk_points, 2)
position_size = max(0.01, min(position_size, 1.0))

print('TRADE PARAMETERS')
print('-' * 50)
print(f'Direction: BUY LONG')
print(f'Entry: ${ENTRY_PRICE:.2f}')
print(f'Stop Loss: ${STOP_LOSS:.2f} ({risk_points:.2f} points risk)')
print(f'Take Profit 1: ${TAKE_PROFIT_1:.2f}')
print(f'Take Profit 2: ${TAKE_PROFIT_2:.2f}')
print(f'Position Size: {position_size} lots')
print(f'Risk Amount: ${risk_amount:.2f} ({risk_amount/acc.balance*100:.1f}% of balance)')
print(f'Risk/Reward TP1: 1:{(TAKE_PROFIT_1-ENTRY_PRICE)/risk_points:.1f}')
print(f'Risk/Reward TP2: 1:{(TAKE_PROFIT_2-ENTRY_PRICE)/risk_points:.1f}')
print()

# Check existing position
positions = mt5.positions_get(symbol='BTCUSD')
if positions:
    print('[!] Existing BTC position found - skipping duplicate entry')
    for pos in positions:
        print(f'  {"BUY" if pos.type == 0 else "SELL"} {pos.volume} @ ${pos.price_open:.2f} | P/L: ${pos.profit:.2f}')
    mt5.shutdown()
    exit(0)

# Execute BUY order
print('EXECUTING BUY ORDER...')
print()

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
        'symbol': 'BTCUSD',
        'volume': position_size,
        'type': mt5.ORDER_TYPE_BUY,
        'price': ENTRY_PRICE,
        'deviation': 500,  # Higher slippage for crypto volatility
        'magic': 234000,
        'comment': 'Bitcoin Auto-Execution - Contrarian Long',
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
    print(f'  BUY {result.volume} BTC/USD @ ${result.price:.2f}')
    print()

    time.sleep(1)

    # Set SL/TP
    positions = mt5.positions_get(symbol='BTCUSD')
    if positions:
        pos = positions[0]
        sltp_request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'symbol': 'BTCUSD',
            'position': pos.ticket,
            'sl': STOP_LOSS,
            'tp': blended_tp,
        }
        sltp_result = mt5.order_send(sltp_request)

        if sltp_result and sltp_result.retcode == mt5.TRADE_RETCODE_DONE:
            print('[OK] SL/TP SET SUCCESSFULLY!')
            print(f'  Stop Loss: ${STOP_LOSS:.2f}')
            print(f'  Take Profit: ${blended_tp:.2f} (average of TP1/TP2)')
        else:
            print(f'[!] SL/TP pending: {sltp_result.comment if sltp_result else "Unknown"}')

    print()
    print('=' * 70)
    print('TRADE SUMMARY')
    print('=' * 70)
    print(f'BUY {position_size} BTC/USD @ ${ENTRY_PRICE:.2f}')
    print(f'SL: ${STOP_LOSS:.2f} | TP: ${blended_tp:.2f}')
    print(f'Risk: ${risk_amount:.2f} | R/R: 1:{(blended_tp-ENTRY_PRICE)/risk_points:.1f}')
    print('=' * 70)
else:
    print('[ERROR] ORDER FAILED')
    if result:
        print(f'  Retcode: {result.retcode}')
        print(f'  Comment: {result.comment}')

mt5.shutdown()
