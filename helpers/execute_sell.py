import MetaTrader5 as mt5

mt5.initialize(login=107069198, password='D@5qZuUd', server='Ava-Demo 1-MT5')
mt5.symbol_select('GOLD', True)

tick = mt5.symbol_info_tick('GOLD')

print('=' * 60)
print('EXECUTING SELL ORDER - GOLD')
print('=' * 60)
print()

if tick is None:
    print('[ERROR] Could not get GOLD price')
    mt5.shutdown()
    exit(1)

print(f'Current Bid: {tick.bid}')
print(f'Order: SELL 0.15 lots GOLD')
print()

# Place SELL order with IOC filling
request = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': 'GOLD',
    'volume': 0.15,
    'type': mt5.ORDER_TYPE_SELL,
    'price': tick.bid,
    'sl': 4762.00,
    'tp': 4546.00,
    'deviation': 20,
    'magic': 234000,
    'comment': 'SELL signal - Trading analysis',
    'type_time': mt5.ORDER_TIME_GTC,
    'type_filling': mt5.ORDER_FILLING_IOC,
}

print('Sending order...')
result = mt5.order_send(request)

if result:
    print(f'Retcode: {result.retcode}')
    print(f'Comment: {result.comment}')
    print(f'Ticket: {result.order}')

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print()
        print('[OK] SELL order executed successfully!')
        print(f'  Volume: {result.volume} lots')
        print(f'  Price: ${result.price:.2f}')
        print(f'  Stop Loss: $4,762.00')
        print(f'  Take Profit: $4,546.00')
        print()
        print('Trade Summary:')
        print(f'  Entry: ${result.price:.2f}')
        print(f'  Risk: 108 points (~$162)')
        print(f'  Reward: 216 points (~$324)')
        print(f'  R/R: 1:2.0')
    else:
        print()
        print(f'[ERROR] Order failed')
        print(f'Full result: {result}')
else:
    print('[ERROR] order_send returned None')

mt5.shutdown()
