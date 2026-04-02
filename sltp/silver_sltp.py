"""
Set Stop Loss and Take Profit for SILVER position
Using the exact same method that worked for GOLD
"""

import MetaTrader5 as mt5

# Connect to AvaTrade MT5
mt5.initialize(login=107069198, password='D@5qZuUd', server='Ava-Demo 1-MT5')

print('=' * 60)
print('SETTING SL/TP FOR SILVER POSITION')
print('=' * 60)
print()

# Get SILVER position
positions = mt5.positions_get(symbol='SILVER')

if positions is None or len(positions) == 0:
    print('No open SILVER position found')
    mt5.shutdown()
    exit(1)

pos = positions[0]
print(f'Position Found:')
print(f'  Ticket: {pos.ticket}')
print(f'  Type: {"BUY" if pos.type == 0 else "SELL"}')
print(f'  Volume: {pos.volume} lots')
print(f'  Entry Price: ${pos.price_open:.3f}')
print(f'  Current Price: ${pos.price_current:.3f}')
print(f'  P/L: ${pos.profit:.2f}')
print(f'  Current SL: ${pos.sl:.3f}')
print(f'  Current TP: ${pos.tp:.3f}')
print()

# Get current tick data for reference
tick = mt5.symbol_info_tick('SILVER')
print(f'Current Market: Bid ${tick.bid:.3f} | Ask ${tick.ask:.3f}')
print()

# Calculate SL/TP levels based on entry price
# For SELL position: SL above entry, TP below entry
entry = pos.price_open

if pos.type == 1:  # SELL position
    # SL above entry (wider for SILVER volatility)
    sl = entry + 3.0  # 3 points above = ~75.95
    tp = entry - 5.0  # 5 points below = ~67.95
    print(f'SELL Position - Stops calculated:')
    print(f'  SL: ${sl:.3f} (above entry by {sl-entry:.3f})')
    print(f'  TP: ${tp:.3f} (below entry by {entry-tp:.3f})')
    print(f'  Risk/Reward: 1:{(entry-tp)/(sl-entry):.1f}')
else:  # BUY position
    # SL below entry, TP above entry
    sl = entry - 3.0
    tp = entry + 5.0
    print(f'BUY Position - Stops calculated:')
    print(f'  SL: ${sl:.3f} (below entry by {entry-sl:.3f})')
    print(f'  TP: ${tp:.3f} (above entry by {tp-entry:.3f})')
    print(f'  Risk/Reward: 1:{(tp-entry)/(entry-sl):.1f}')

print()
print('Attempting to set SL/TP...')
print()

# Use TRADE_ACTION_SLTP with position ticket (same as GOLD success)
mod_request = {
    'action': mt5.TRADE_ACTION_SLTP,
    'symbol': 'SILVER',
    'position': pos.ticket,
    'sl': sl,
    'tp': tp,
}

print(f'Request details:')
print(f'  Action: TRADE_ACTION_SLTP')
print(f'  Symbol: SILVER')
print(f'  Position Ticket: {pos.ticket}')
print(f'  SL: ${sl:.3f}')
print(f'  TP: ${tp:.3f}')
print()

result = mt5.order_send(mod_request)

print('Result:')
print(f'  Retcode: {result.retcode if result else "None"}')
print(f'  Comment: {result.comment if result else "None"}')
print()

if result and result.retcode == mt5.TRADE_RETCODE_DONE:
    print('[OK] SL/TP SET SUCCESSFULLY!')

    # Verify by re-reading position
    import time
    time.sleep(0.5)
    positions = mt5.positions_get(symbol='SILVER')
    if positions:
        pos = positions[0]
        print(f'  Verified SL: ${pos.sl:.3f}')
        print(f'  Verified TP: ${pos.tp:.3f}')
else:
    print('[FAILED] SL/TP not set')
    if result:
        print(f'  Error code: {result.retcode}')
        print(f'  Error comment: {result.comment}')

print()
print('=' * 60)

mt5.shutdown()
