"""
Universal MT5 Auto-Trade Script
Works with ANY symbol on MetaTrader 5

Usage:
    python universal_trade.py --symbol GOLD --direction SELL --volume 0.1 --sl 4762 --tp 4546
    python universal_trade.py --symbol BTCUSD --direction BUY --volume 0.01 --sl 63500 --tp 72800
    python universal_trade.py --symbol EURUSD --direction SELL --volume 0.5 --sl 1.0950 --tp 1.0850
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
        "trade_allowed": info.trade_allowed,
        "spread": info.spread,
    }

def get_tick(symbol):
    """Get current bid/ask prices"""
    return mt5.symbol_info_tick(symbol)

def normalize_volume(symbol, volume):
    """Normalize volume to broker's lot size requirements"""
    info = get_symbol_info(symbol)
    if info is None:
        return volume

    # Round to volume step
    volume = round(volume / info["volume_step"]) * info["volume_step"]
    # Clamp to min/max
    volume = max(info["volume_min"], min(volume, info["volume_max"]))
    return round(volume, 2)

def check_existing_position(symbol):
    """Check if position already exists for symbol"""
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        print(f"[!] Existing position found for {symbol}:")
        for pos in positions:
            pos_type = "BUY" if pos.type == 0 else "SELL"
            print(f"    {pos_type} {pos.volume} @ ${pos.price_open:.{get_symbol_info(symbol)['digits']}f} | P/L: ${pos.profit:.2f}")
        return positions
    return None

def execute_order(symbol, direction, volume, price, deviation=50):
    """
    Execute market order using proven method from Gold/Silver/Bitcoin trades
    Tries multiple filling modes until one succeeds
    """
    order_type = mt5.ORDER_TYPE_SELL if direction == "SELL" else mt5.ORDER_TYPE_BUY

    # Filling modes to try (in order of preference based on broker support)
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
            "type": order_type,
            "price": price,
            "deviation": deviation,
            "magic": 234000,
            "comment": "Universal Auto-Trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        result = mt5.order_send(request)

        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"[OK] {mode_name} filling mode succeeded")
            break
        else:
            retcode = result.retcode if result else "None"
            comment = result.comment if result else "None"
            print(f"  {mode_name}: Retcode {retcode} | {comment}")

    return result

def set_sltp(symbol, position_ticket, sl, tp):
    """
    Set Stop Loss and Take Profit using the exact method that worked for Gold/Silver/Bitcoin
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
    parser = argparse.ArgumentParser(description="Universal MT5 Auto-Trade")
    parser.add_argument("--symbol", type=str, required=True, help="Trading symbol (e.g., GOLD, BTCUSD, EURUSD)")
    parser.add_argument("--direction", type=str, required=True, choices=["BUY", "SELL"], help="Trade direction")
    parser.add_argument("--volume", type=float, required=True, help="Lot size")
    parser.add_argument("--sl", type=float, required=True, help="Stop Loss price")
    parser.add_argument("--tp", type=float, required=True, help="Take Profit price")
    parser.add_argument("--deviation", type=int, default=50, help="Max slippage in points (default: 50)")
    args = parser.parse_args()

    # Connect to MT5
    print("=" * 70)
    print(f"UNIVERSAL MT5 AUTO-TRADE: {args.symbol}")
    print("=" * 70)
    print()

    if not connect():
        print("[ERROR] Failed to connect to MT5")
        return

    # Get account info
    acc = mt5.account_info()
    if acc is None:
        print("[ERROR] Failed to get account info")
        mt5.shutdown()
        return

    print(f"Account: {acc.login} | Balance: ${acc.balance:.2f} | Equity: ${acc.equity:.2f}")
    print()

    # Select symbol
    mt5.symbol_select(args.symbol, True)
    time.sleep(0.5)

    # Get symbol info
    info = get_symbol_info(args.symbol)
    if info is None:
        print(f"[ERROR] Symbol {args.symbol} not found")
        mt5.shutdown()
        return

    print(f"Symbol: {info['name']} | Digits: {info['digits']} | Spread: {info['spread']} points")
    print(f"Min Lot: {info['volume_min']} | Max Lot: {info['volume_max']} | Step: {info['volume_step']}")
    print()

    # Get current price
    tick = get_tick(args.symbol)
    if tick is None or tick.bid == 0:
        print(f"[ERROR] No price data for {args.symbol}")
        mt5.shutdown()
        return

    print(f"Current Price: Bid ${tick.bid:.{info['digits']}f} | Ask ${tick.ask:.{info['digits']}f}")
    print()

    # Check existing position
    if check_existing_position(args.symbol):
        print("Skipping duplicate entry.")
        mt5.shutdown()
        return

    # Validate SL/TP for direction
    if args.direction == "BUY":
        if args.sl >= tick.ask:
            print(f"[ERROR] Stop Loss ({args.sl}) must be BELOW entry price ({tick.ask}) for BUY")
            mt5.shutdown()
            return
        if args.tp <= tick.ask:
            print(f"[ERROR] Take Profit ({args.tp}) must be ABOVE entry price ({tick.ask}) for BUY")
            mt5.shutdown()
            return
    else:  # SELL
        if args.sl <= tick.bid:
            print(f"[ERROR] Stop Loss ({args.sl}) must be ABOVE entry price ({tick.bid}) for SELL")
            mt5.shutdown()
            return
        if args.tp >= tick.bid:
            print(f"[ERROR] Take Profit ({args.tp}) must be BELOW entry price ({tick.bid}) for SELL")
            mt5.shutdown()
            return

    # Normalize volume
    volume = normalize_volume(args.symbol, args.volume)
    print(f"Normalized Volume: {volume} lots (requested: {args.volume})")
    print()

    # Trade parameters
    entry_price = tick.ask if args.direction == "BUY" else tick.bid
    risk = abs(entry_price - args.sl)
    reward = abs(args.tp - entry_price)
    rr_ratio = reward / risk if risk > 0 else 0

    print("TRADE PARAMETERS")
    print("-" * 50)
    print(f"Direction: {args.direction}")
    print(f"Symbol: {args.symbol}")
    print(f"Entry: ${entry_price:.{info['digits']}f}")
    print(f"Stop Loss: ${args.sl:.{info['digits']}f}")
    print(f"Take Profit: ${args.tp:.{info['digits']}f}")
    print(f"Volume: {volume} lots")
    print(f"Risk/Reward: 1:{rr_ratio:.1f}")
    print()

    # Execute order
    print(f"EXECUTING {args.direction} ORDER...")
    result = execute_order(args.symbol, args.direction, volume, entry_price, args.deviation)
    print()

    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        print("[OK] ORDER FILLED!")
        print(f"  Ticket: {result.order}")
        print(f"  {args.direction} {result.volume} {args.symbol} @ ${result.price:.{info['digits']}f}")
        print()

        # Wait for position to be established
        time.sleep(1)

        # Set SL/TP using proven method
        positions = mt5.positions_get(symbol=args.symbol)
        if positions:
            pos = positions[0]
            print("SETTING SL/TP...")

            sltp_result = set_sltp(args.symbol, pos.ticket, args.sl, args.tp)

            if sltp_result and sltp_result.retcode == mt5.TRADE_RETCODE_DONE:
                print("[OK] SL/TP SET SUCCESSFULLY!")
                print(f"  Stop Loss: ${args.sl:.{info['digits']}f}")
                print(f"  Take Profit: ${args.tp:.{info['digits']}f}")

                # Verify
                time.sleep(0.5)
                positions = mt5.positions_get(symbol=args.symbol)
                if positions:
                    pos = positions[0]
                    print()
                    print("POSITION VERIFIED:")
                    print(f"  Ticket: {pos.ticket}")
                    print(f"  SL: ${pos.sl:.{info['digits']}f}")
                    print(f"  TP: ${pos.tp:.{info['digits']}f}")
            else:
                print(f"[!] SL/TP pending: {sltp_result.comment if sltp_result else 'Unknown'}")

        print()
        print("=" * 70)
        print("TRADE SUMMARY")
        print("=" * 70)
        print(f"{args.direction} {volume} {args.symbol} @ ${entry_price:.{info['digits']}f}")
        print(f"SL: ${args.sl:.{info['digits']}f} | TP: ${args.tp:.{info['digits']}f}")
        print(f"Risk/Reward: 1:{rr_ratio:.1f}")
        print("=" * 70)
    else:
        print("[ERROR] ORDER FAILED")
        if result:
            print(f"  Retcode: {result.retcode}")
            print(f"  Comment: {result.comment}")

            # Common retcodes
            if result.retcode == 10006:
                print("  -> Request rejected (check Auto-Trading is enabled)")
            elif result.retcode == 10013:
                print("  -> Invalid request (check symbol, volume, prices)")
            elif result.retcode == 10014:
                print("  -> Invalid volume (check min/max lot size)")
            elif result.retcode == 10015:
                print("  -> Invalid price (check market is open)")
            elif result.retcode == 10016:
                print("  -> Invalid stops (SL/TP too close or invalid levels)")
            elif result.retcode == 10018:
                print("  -> Market closed")
            elif result.retcode == 10030:
                print("  -> Unsupported filling mode (tried alternatives)")

    mt5.shutdown()

if __name__ == "__main__":
    main()
