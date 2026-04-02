import MetaTrader5 as mt5
import time

print("=" * 60)
print("EXECUTING SELL ORDER - GOLD")
print("=" * 60)
print()

# Initialize with longer timeout
if not mt5.initialize(login=107069198, password='D@5qZuUd', server='Ava-Demo 1-MT5', timeout=5000):
    print("Failed to initialize MT5")
    print(f"Error: {mt5.last_error()}")
    exit(1)

print("Connected to MT5")

# Select symbol
if not mt5.symbol_select('GOLD', True):
    print("Failed to select GOLD")
    mt5.shutdown()
    exit(1)

print("GOLD symbol selected")
print()

# Get tick data
tick = mt5.symbol_info_tick('GOLD')
if tick is None:
    print("Failed to get tick data")
    mt5.shutdown()
    exit(1)

print(f"Current Bid: {tick.bid}")
print(f"Order: SELL 0.15 lots GOLD")
print()

# Check account
acc = mt5.account_info()
if acc:
    print(f"Account: {acc.login} ({acc.name})")
    print(f"Balance: ${acc.balance:.2f}")
    print(f"Trade Allowed: {acc.trade_allowed}")
print()

# Try different filling modes based on broker capabilities
filling_modes = [
    (mt5.ORDER_FILLING_FOK, "FOK"),
    (mt5.ORDER_FILLING_IOC, "IOC"),
]

result = None
for filling_mode, mode_name in filling_modes:
    print(f"Attempting {mode_name} filling mode...")

    # Build request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "GOLD",
        "volume": 0.15,
        "type": mt5.ORDER_TYPE_SELL,
        "price": tick.bid,
        "deviation": 50,
        "magic": 234000,
        "comment": "SELL signal - Trading analysis",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": filling_mode,
    }

    # Send order
    result = mt5.order_send(request)

    if result is None:
        print(f"  Result: None (terminal not responding)")
    elif result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"  SUCCESS!")
        break
    else:
        print(f"  Retcode {result.retcode}: {result.comment}")

    time.sleep(1)

print()

if result and result.retcode == mt5.TRADE_RETCODE_DONE:
    print("[OK] SELL order executed successfully!")
    print(f"  Ticket: {result.order}")
    print(f"  Volume: {result.volume} lots")
    print(f"  Price: ${result.price:.2f}")
    print()

    # Set SL and TP
    print("Setting Stop Loss and Take Profit...")
    time.sleep(0.5)

    sl_result = mt5.order_send({
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": "GOLD",
        "position": result.position,
        "sl": 4762.00,
        "tp": 4546.00,
    })

    if sl_result and sl_result.retcode == mt5.TRADE_RETCODE_DONE:
        print("SL/TP set successfully!")
        print(f"  Stop Loss: $4,762.00")
        print(f"  Take Profit: $4,546.00")
    else:
        print(f"SL/TP: {sl_result.comment if sl_result else 'Failed'}")

    print()
    print("Trade Summary:")
    print(f"  SELL {result.volume} @ ${result.price:.2f}")
    print(f"  Stop Loss: $4,762.00")
    print(f"  Take Profit: $4,546.00")
    print(f"  Risk: ~$162 | Reward: ~$162")
else:
    print("[ERROR] Order execution failed")
    print(f"  Result: {result}")
    print()
    print("TROUBLESHOOTING:")
    print("  1. Ensure MT5 terminal is running and logged in")
    print("  2. Enable Auto-Trading (green play button in toolbar)")
    print("  3. Check Tools > Options > Expert Advisors > Allow algo trading")

# Show positions
print()
print("Current GOLD Positions:")
positions = mt5.positions_get(symbol='GOLD')
if positions:
    for pos in positions:
        ptype = 'SELL' if pos.type == 1 else 'BUY'
        print(f"  {ptype} {pos.volume} @ ${pos.price_open:.2f}")
        print(f"    SL: ${pos.sl:.2f} | TP: ${pos.tp:.2f}")
        print(f"    P/L: ${pos.profit:.2f}")
else:
    print("  No open positions")

mt5.shutdown()
print()
print("Disconnected from MT5")
