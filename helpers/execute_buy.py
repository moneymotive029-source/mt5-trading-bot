import MetaTrader5 as mt5

mt5.initialize(login=107069198, password='D@5qZuUd', server='Ava-Demo 1-MT5')

# Get current tick
tick = mt5.symbol_info_tick('GOLD')
print('=== EXECUTING BUY ORDER BASED ON TRADING ANALYSIS ===')
print()
print(f'Current Ask: {tick.ask}')
print(f'Order: BUY 0.1 lots GOLD')
print()

# Place BUY order
request = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': 'GOLD',
    'volume': 0.1,
    'type': mt5.ORDER_TYPE_BUY,
    'price': tick.ask,
    'sl': 0.0,
    'tp': 0.0,
    'deviation': 10,
    'magic': 234000,
    'comment': 'BUY signal - Trading analysis',
    'type_time': mt5.ORDER_TIME_GTC,
    'type_filling': mt5.ORDER_FILLING_FOK,
}

result = mt5.order_send(request)

if result and result.retcode == mt5.TRADE_RETCODE_DONE:
    print('[OK] Order executed successfully!')
    print(f'  Ticket: {result.order}')
    print(f'  Volume: {result.volume} lots')
    print(f'  Price: ${result.price:.2f}')
    print()
    print('Next steps:')
    print('  - Set SL at 4554.84 (per analysis)')
    print('  - Set TP at 4879.64 (per analysis)')
else:
    print(f'[ERROR] Order failed: {result.comment if result else "Unknown"}')

mt5.shutdown()
