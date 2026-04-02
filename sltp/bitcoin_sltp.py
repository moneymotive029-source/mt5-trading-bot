"""
Universal MT5 SL/TP Setter
Works with ANY symbol on MetaTrader 5

Usage:
    python bitcoin_sltp.py --symbol BTCUSD --sl 63500 --tp 72800
    python bitcoin_sltp.py --symbol GOLD --sl 4600 --tp 4750
    python bitcoin_sltp.py --symbol ETHUSD --sl 2800 --tp 3200
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
    }

def set_sltp(symbol, position_ticket, sl, tp):
    """
    Set Stop Loss and Take Profit for an existing position
    Uses TRADE_ACTION_SLTP with position ticket
    """
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": symbol,
        "position": position_ticket,
        "sl": sl,
        "tp": tp,
    }
    result = mt5.order_send(request)
    return result

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Universal MT5 SL/TP Setter")
    parser.add_argument("--symbol", type=str, required=True, help="Trading symbol")
    parser.add_argument("--sl", type=float, required=True, help="Stop Loss price")
    parser.add_argument("--tp", type=float, required=True, help="Take Profit price")
    args = parser.parse_args()

    # Connect to MT5
    print("=" * 70)
    print(f"SETTING SL/TP FOR: {args.symbol}")
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

    # Get position
    positions = mt5.positions_get(symbol=args.symbol)

    if positions is None or len(positions) == 0:
        print(f"[ERROR] No open position found for {args.symbol}")
        mt5.shutdown()
        return

    pos = positions[0]
    digits = info['digits']

    print(f"Position Found:")
    print(f"  Ticket: {pos.ticket}")
    print(f"  Type: {'BUY' if pos.type == 0 else 'SELL'}")
    print(f"  Volume: {pos.volume} lots")
    print(f"  Entry Price: ${pos.price_open:.{digits}f}")
    print(f"  Current Price: ${pos.price_current:.{digits}f}")
    print(f"  P/L: ${pos.profit:.2f}")
    print(f"  Current SL: ${pos.sl:.{digits}f}")
    print(f"  Current TP: ${pos.tp:.{digits}f}")
    print()

    # Get current tick data
    tick = mt5.symbol_info_tick(args.symbol)
    print(f"Current Market: Bid ${tick.bid:.{digits}f} | Ask ${tick.ask:.{digits}f}")
    print()

    # Validate SL/TP for position type
    entry = pos.price_open
    valid = True

    if pos.type == 0:  # BUY position
        if args.sl >= entry:
            print(f"[ERROR] SL ({args.sl}) must be BELOW entry ({entry}) for BUY position")
            valid = False
        if args.tp <= entry:
            print(f"[ERROR] TP ({args.tp}) must be ABOVE entry ({entry}) for BUY position")
            valid = False
    else:  # SELL position
        if args.sl <= entry:
            print(f"[ERROR] SL ({args.sl}) must be ABOVE entry ({entry}) for SELL position")
            valid = False
        if args.tp >= entry:
            print(f"[ERROR] TP ({args.tp}) must be BELOW entry ({entry}) for SELL position")
            valid = False

    if not valid:
        mt5.shutdown()
        return

    print(f"New SL/TP Levels:")
    print(f"  Stop Loss: ${args.sl:.{digits}f}")
    print(f"  Take Profit: ${args.tp:.{digits}f}")

    if pos.type == 0:  # BUY
        risk = entry - args.sl
        reward = args.tp - entry
    else:  # SELL
        risk = args.sl - entry
        reward = entry - args.tp

    print(f"  Risk/Reward: 1:{reward/risk:.1f}" if risk > 0 else "")
    print()

    print("Setting SL/TP...")
    print()

    # Set SL/TP using position ticket
    result = set_sltp(args.symbol, pos.ticket, args.sl, args.tp)

    print("Result:")
    print(f"  Retcode: {result.retcode if result else 'None'}")
    print(f"  Comment: {result.comment if result else 'None'}")
    print()

    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        print("[OK] SL/TP SET SUCCESSFULLY!")

        # Verify by re-reading position
        time.sleep(0.5)
        positions = mt5.positions_get(symbol=args.symbol)
        if positions:
            pos = positions[0]
            print(f"  Verified SL: ${pos.sl:.{digits}f}")
            print(f"  Verified TP: ${pos.tp:.{digits}f}")
    else:
        print("[FAILED] SL/TP not set")
        if result:
            print(f"  Error code: {result.retcode}")
            print(f"  Error comment: {result.comment}")

            # Common retcodes
            if result.retcode == 10016:
                print("  -> Invalid stops (SL/TP too close or invalid levels)")
            elif result.retcode == 10014:
                print("  -> Invalid request (check position exists)")

    print()
    print("=" * 70)

    mt5.shutdown()

if __name__ == "__main__":
    main()
