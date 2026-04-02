"""
Set Stop Loss and Take Profit for Bitcoin position
Using the exact same method that worked for GOLD and SILVER
"""

import MetaTrader5 as mt5
import time

# Connect to MT5
mt5.initialize(login=107069198, password='D@5qZuUd', server='Ava-Demo 1-MT5')

print('=' * 70)
print('BITCOIN - SETTING SL/TP')
print('=' * 70)
print()

# Get BTC position
positions = mt5.positions_get(symbol='BTCUSD')

if positions is None or len(positions) == 0:
    print('No open BTC position found')
    mt5.shutdown()
    exit(1)

pos = positions[0]
print(f'Position Found:')
print(f'  Ticket: {pos.ticket}')
print(f'  Type: {"BUY" if pos.type == 0 else "SELL"}')
print(f'  Volume: {pos.volume} lots')
print(f'  Entry Price: ${pos.price_open:.2f}')
print(f'  Current Price: ${pos.price_current:.2f}')
print(f'  P/L: ${pos.profit:.2f}')
print(f'  Current SL: ${pos.sl:.2f}')
print(f'  Current TP: ${pos.tp:.2f}')
print()

# For SELL position: SL above entry, TP below entry
entry = pos.price_open

if pos.type == 1:  # SELL position
    # SL above entry (wider for BTC volatility)
    sl = entry + 3500  # ~$70,340
    tp = entry - 6000  # ~$60,840
    print(f'SELL Position - Stops calculated:')
    print(f'  SL: ${sl:.2f} (above entry by {sl-entry:.2f})')
    print(f'  TP: ${tp:.2f} (below entry by {entry-tp:.2f})')
    print(f'  Risk/Reward: 1:{(entry-tp)/(sl-entry):.1f}')

print()
print('Setting SL/TP...')

# Use TRADE_ACTION_SLTP with position ticket (same as GOLD/SILVER success)
mod_request = {
    'action': mt5.TRADE_ACTION_SLTP,
    'symbol': 'BTCUSD',
    'position': pos.ticket,
    'sl': sl,
    'tp': tp,
}

result = mt5.order_send(mod_request)

print(f'Result: Retcode {result.retcode if result else "None"}')
print(f'Comment: {result.comment if result else "None"}')
print()

if result and result.retcode == mt5.TRADE_RETCODE_DONE:
    print('[OK] SL/TP SET SUCCESSFULLY!')

    # Verify
    time.sleep(0.5)
    positions = mt5.positions_get(symbol='BTCUSD')
    if positions:
        pos = positions[0]
        print(f'  Verified SL: ${pos.sl:.2f}')
        print(f'  Verified TP: ${pos.tp:.2f}')
else:
    print('[FAILED] SL/TP not set')
    if result:
        print(f'  Error: {result.retcode} - {result.comment}')

print()
print('=' * 70)

mt5.shutdown()
