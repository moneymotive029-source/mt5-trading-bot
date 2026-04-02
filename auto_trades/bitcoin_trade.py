"""
Bitcoin (BTC/USD) Auto-Execution Script
Based on comprehensive trading analysis

Signal: BUY LONG (Contrarian play on Extreme Fear)
Entry: ~$66,861
SL: $63,500
TP1: $72,800
TP2: $84,600

Usage:
    python bitcoin_trade.py [--symbol BTCUSD] [--direction BUY] [--volume 0.01] [--sl 63500] [--tp 72800]
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

def normalize_volume(symbol, volume):
    """Normalize volume to broker's lot size requirements"""
    info = get_symbol_info(symbol)
    if info is None:
        return volume
    volume = round(volume / info["volume_step"]) * info["volume_step"]
    volume = max(info["volume_min"], min(volume, info["volume_max"]))
    return round(volume, 2)

def execute_order(symbol, direction, volume, price, deviation=500):
    """Execute order with multiple filling mode fallback"""
    order_type = mt5.ORDER_TYPE_SELL if direction == "SELL" else mt5.ORDER_TYPE_BUY
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
            "deviation": deviation,  # Higher slippage for crypto volatility
            "magic": 234000,
            "comment": "Bitcoin Auto-Execution",
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
    """Set Stop Loss and Take Profit"""
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
    parser = argparse.ArgumentParser(description="Bitcoin Auto-Execution Script")
    parser.add_argument("--symbol", type=str, default="BTCUSD", help="Trading symbol (default: BTCUSD)")
    parser.add_argument("--direction", type=str, default="BUY", choices=["BUY", "SELL"], help="Trade direction")
    parser.add_argument("--volume", type=float, default=0.01, help="Lot size")
    parser.add_argument("--sl", type=float, default=None, help="Stop Loss price")
    parser.add_argument("--tp", type=float, default=None, help="Take Profit price")
    parser.add_argument("--deviation", type=int, default=500, help="Max slippage in points (crypto)")
    args = parser.parse_args()

    # Connect to MT5
    print("=" * 70)
    print(f"BITCOIN AUTO-EXECUTION: {args.symbol}")
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
    tick = mt5.symbol_info_tick(args.symbol)
    if tick is None or tick.bid == 0:
        print(f"[ERROR] No price data for {args.symbol}")
        mt5.shutdown()
        return

    print(f"Current Price: Bid ${tick.bid:.{info['digits']}f} | Ask ${tick.ask:.{info['digits']}f}")
    print()

    # Check existing position
    positions = mt5.positions_get(symbol=args.symbol)
    if positions:
        print(f"[!] Existing position found for {args.symbol} - skipping duplicate entry")
        for pos in positions:
            pos_type = "BUY" if pos.type == 0 else "SELL"
            print(f"    {pos_type} {pos.volume} @ ${pos.price_open:.{info['digits']}f} | P/L: ${pos.profit:.2f}")
        mt5.shutdown()
        return

    # Trade parameters from analysis
    DIRECTION = args.direction
    ENTRY_PRICE = tick.ask if DIRECTION == "BUY" else tick.bid

    # Default SL/TP if not provided (based on BTC volatility)
    if args.sl is None:
        STOP_LOSS = 63500.00 if DIRECTION == "BUY" else ENTRY_PRICE + 3500
    else:
        STOP_LOSS = args.sl

    if args.tp is None:
        TAKE_PROFIT_1 = 72800.00 if DIRECTION == "BUY" else ENTRY_PRICE - 6000
        TAKE_PROFIT_2 = 84600.00 if DIRECTION == "BUY" else ENTRY_PRICE - 12000
    else:
        TAKE_PROFIT_1 = args.tp
        TAKE_PROFIT_2 = args.tp + (args.tp - ENTRY_PRICE) * 0.5  # Secondary TP

    # Position sizing: 2% risk
    risk_amount = acc.balance * 0.02
    risk_points = abs(ENTRY_PRICE - STOP_LOSS)
    position_size = round(risk_amount / risk_points, 2)  # BTCUSD: ~$1 per 0.01 lot per $1
    position_size = max(0.01, min(position_size, 1.0))

    # Use blended TP for single TP value
    blended_tp = (TAKE_PROFIT_1 + TAKE_PROFIT_2) / 2

    print("TRADE PARAMETERS")
    print("-" * 50)
    print(f"Direction: {DIRECTION}")
    print(f"Entry: ${ENTRY_PRICE:.{info['digits']}f}")
    print(f"Stop Loss: ${STOP_LOSS:.{info['digits']}f}")
    print(f"Take Profit 1: ${TAKE_PROFIT_1:.{info['digits']}f}")
    print(f"Take Profit 2: ${TAKE_PROFIT_2:.{info['digits']}f}")
    print(f"Blended TP: ${blended_tp:.{info['digits']}f}")
    print(f"Position Size: {position_size} lots")
    print(f"Risk Amount: ${risk_amount:.2f}")
    print(f"Risk/Reward TP1: 1:{abs(TAKE_PROFIT_1-ENTRY_PRICE)/risk_points:.1f}")
    print(f"Risk/Reward TP2: 1:{abs(TAKE_PROFIT_2-ENTRY_PRICE)/risk_points:.1f}")
    print()

    # Execute order
    print(f"EXECUTING {DIRECTION} ORDER...")
    result = execute_order(args.symbol, DIRECTION, position_size, ENTRY_PRICE, args.deviation)
    print()

    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        print("[OK] ORDER FILLED!")
        print(f"  Ticket: {result.order}")
        print(f"  {DIRECTION} {result.volume} {args.symbol} @ ${result.price:.{info['digits']}f}")
        print()

        time.sleep(1)

        # Set SL/TP
        positions = mt5.positions_get(symbol=args.symbol)
        if positions:
            pos = positions[0]
            print("SETTING SL/TP...")
            sltp_result = set_sltp(args.symbol, pos.ticket, STOP_LOSS, blended_tp)

            if sltp_result and sltp_result.retcode == mt5.TRADE_RETCODE_DONE:
                print("[OK] SL/TP SET SUCCESSFULLY!")
                print(f"  Stop Loss: ${STOP_LOSS:.{info['digits']}f}")
                print(f"  Take Profit: ${blended_tp:.{info['digits']}f} (average of TP1/TP2)")
            else:
                print(f"[!] SL/TP pending: {sltp_result.comment if sltp_result else 'Unknown'}")

        print()
        print("=" * 70)
        print("TRADE SUMMARY")
        print("=" * 70)
        print(f"{DIRECTION} {position_size} {args.symbol} @ ${ENTRY_PRICE:.{info['digits']}f}")
        print(f"SL: ${STOP_LOSS:.{info['digits']}f} | TP: ${blended_tp:.{info['digits']}f}")
        print(f"Risk: ${risk_amount:.2f} | R/R: 1:{abs(blended_tp-ENTRY_PRICE)/risk_points:.1f}")
        print("=" * 70)
    else:
        print("[ERROR] ORDER FAILED")
        if result:
            print(f"  Retcode: {result.retcode}")
            print(f"  Comment: {result.comment}")

    mt5.shutdown()

if __name__ == "__main__":
    main()
