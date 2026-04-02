"""
Universal MT5 BUY Order Helper
Works with ANY symbol on MetaTrader 5

Usage:
    python execute_buy.py --symbol GOLD --volume 0.1 --sl 4554 --tp 4880
    python execute_buy.py --symbol EURUSD --volume 0.5 --sl 1.0850 --tp 1.0950
"""

import MetaTrader5 as mt5
import time
import argparse

# MT5 Configuration
MT5_CONFIG = {
    "login": 107069198,
    "password": "D@5qZuUd",
    "server": "Ava-Demo 1-MT5"
}

def connect():
    """Initialize MT5 connection with retry"""
    for i in range(3):
        if mt5.initialize(**MT5_CONFIG):
            return True
        time.sleep(1)
    return False

def get_symbol_info(symbol):
    """Get symbol specifications"""
    info = mt5.symbol_info(symbol)
    if info is None:
        return None
    return {
        "name": info.name,
        "digits": info.digits,
        "point": info.point,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
    }

def execute_buy(symbol, volume, sl=0, tp=0, deviation=50, comment="BUY order"):
    """
    Execute BUY order with multiple filling mode fallback
    Returns the result dict if successful, None otherwise
    """
    tick = mt5.symbol_info_tick(symbol)
    if tick is None or tick.ask == 0:
        print(f"[ERROR] No price data for {symbol}")
        return None

    filling_modes = [
        (mt5.ORDER_FILLING_FOK, "FOK"),
        (mt5.ORDER_FILLING_RETURN, "RETURN"),
        (mt5.ORDER_FILLING_IOC, "IOC"),
    ]

    result = None
    for filling_mode, mode_name in filling_modes:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY,
            "price": tick.ask,
            "sl": sl,
            "tp": tp,
            "deviation": deviation,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        result = mt5.order_send(request)

        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"[OK] {mode_name} filling mode succeeded")
            return result
        else:
            retcode = result.retcode if result else "None"
            comment = result.comment if result else "None"
            print(f"  {mode_name}: Retcode {retcode} | {comment}")

    return result

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Universal MT5 BUY Order Helper")
    parser.add_argument("--symbol", type=str, required=True, help="Trading symbol")
    parser.add_argument("--volume", type=float, default=0.1, help="Lot size (default: 0.1)")
    parser.add_argument("--sl", type=float, default=0, help="Stop Loss price (default: 0)")
    parser.add_argument("--tp", type=float, default=0, help="Take Profit price (default: 0)")
    parser.add_argument("--deviation", type=int, default=50, help="Max slippage (default: 50)")
    parser.add_argument("--comment", type=str, default="BUY order", help="Order comment")
    args = parser.parse_args()

    # Connect to MT5
    print("=" * 70)
    print(f"EXECUTING BUY ORDER: {args.symbol}")
    print("=" * 70)
    print()

    if not connect():
        print("[ERROR] Failed to connect to MT5")
        return

    # Get symbol info
    info = get_symbol_info(args.symbol)
    if info is None:
        print(f"[ERROR] Symbol {args.symbol} not found")
        mt5.shutdown()
        return

    print(f"Symbol: {info['name']} | Digits: {info['digits']}")

    # Get tick data
    tick = mt5.symbol_info_tick(args.symbol)
    if tick is None:
        print("[ERROR] Failed to get tick data")
        mt5.shutdown()
        return

    print(f"Current Ask: ${tick.ask:.{info['digits']}f}")
    print(f"Order: BUY {args.volume} lots")
    print()

    # Check account
    acc = mt5.account_info()
    if acc:
        print(f"Account: {acc.login} ({acc.name})")
        print(f"Balance: ${acc.balance:.2f}")
        print(f"Trade Allowed: {acc.trade_allowed}")
    print()

    # Execute order
    result = execute_buy(args.symbol, args.volume, args.sl, args.tp, args.deviation, args.comment)

    print()

    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        print("[OK] BUY order executed successfully!")
        print(f"  Ticket: {result.order}")
        print(f"  Volume: {result.volume} lots")
        print(f"  Price: ${result.price:.{info['digits']}f}")

        if args.sl > 0 or args.tp > 0:
            print(f"  SL: ${args.sl:.{info['digits']}f}")
            print(f"  TP: ${args.tp:.{info['digits']}f}")
    else:
        print("[ERROR] Order execution failed")
        if result:
            print(f"  Retcode: {result.retcode}")
            print(f"  Comment: {result.comment}")

    mt5.shutdown()
    print()
    print("Disconnected from MT5")

if __name__ == "__main__":
    main()
