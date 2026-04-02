"""
MT5 Trading Module - Universal Python API Integration
Works with ANY symbol/market on MetaTrader 5 (Forex, Metals, Crypto, Indices, Energies, Stocks, Bonds)
"""

import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
from typing import Optional, Dict, Any, List

# MT5 Connection Settings
MT5_CONFIG = {
    "login": 107069198,
    "password": "D@5qZuUd",
    "server": "Ava-Demo 1-MT5"
}

def connect() -> bool:
    """Initialize MT5 connection with retry"""
    for i in range(3):
        if mt5.initialize(**MT5_CONFIG):
            return True
        time.sleep(1)
    return False

def disconnect():
    """Shutdown MT5 connection"""
    mt5.shutdown()

def ensure_connected(func):
    """Decorator to ensure MT5 is connected before calling function"""
    def wrapper(*args, **kwargs):
        if not mt5.initialize(**MT5_CONFIG):
            if not connect():
                raise Exception("Failed to connect to MT5")
        try:
            return func(*args, **kwargs)
        finally:
            pass
    return wrapper

# ============= SYMBOL INFO =============

@ensure_connected
def get_symbol_info(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed symbol information for ANY MT5 symbol

    Returns:
        dict with name, digits, point, volume_min/max/step, spread, contract_size, etc.
    """
    info = mt5.symbol_info(symbol)
    if info is None:
        return None

    return {
        "name": info.name,
        "visible": info.visible,
        "trade_allowed": info.trade_allowed,
        "trade_mode": info.trade_mode,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "spread": info.spread,
        "digits": info.digits,
        "point": info.point,
        "trade_contract_size": info.trade_contract_size,
        "swap_long": info.swap_long,
        "swap_short": info.swap_short,
        "session_auction": info.session_auction,
    }

def list_available_symbols(category: str = None) -> List[str]:
    """
    List all available trading symbols, optionally filtered by category

    Args:
        category: Filter by category ('forex', 'metal', 'crypto', 'index', 'energy', 'stock', 'bond')

    Returns:
        List of symbol names
    """
    if not mt5.initialize(**MT5_CONFIG):
        return []

    symbols = mt5.symbols_get()
    if symbols is None:
        mt5.shutdown()
        return []

    if category:
        category = category.upper()
        category_map = {
            'FOREX': ['FOREX'],
            'FX': ['FOREX'],
            'METAL': ['METAL'],
            'METALS': ['METAL'],
            'CRYPTO': ['CRYPTO'],
            'INDEX': ['INDEX'],
            'INDICES': ['INDEX'],
            'ENERGY': ['ENERGY'],
            'ENERGIES': ['ENERGY'],
            'STOCK': ['STOCK'],
            'STOCKS': ['STOCK'],
            'BOND': ['BOND'],
            'BONDS': ['BOND'],
        }
        categories = category_map.get(category, [category])
        result = [s.name for s in symbols if s.visible and any(c in (s.path or '').upper() for c in categories)]
    else:
        result = [s.name for s in symbols if s.visible]

    mt5.shutdown()
    return sorted(result)

# ============= ACCOUNT INFO =============

@ensure_connected
def get_account_info() -> Dict[str, Any]:
    """Get full account information"""
    account = mt5.account_info()
    if account is None:
        return {"error": "Failed to get account info"}

    return {
        "login": account.login,
        "name": account.name,
        "server": account.server,
        "balance": account.balance,
        "equity": account.equity,
        "margin": account.margin,
        "margin_free": account.margin_free,
        "margin_level": account.margin_level,
        "currency": account.currency,
        "leverage": account.leverage,
        "profit": account.profit,
        "trade_allowed": account.trade_allowed,
        "trade_expert": account.trade_expert,
    }

@ensure_connected
def get_balance() -> float:
    """Get account balance"""
    account = mt5.account_info()
    return account.balance if account else 0.0

@ensure_connected
def get_equity() -> float:
    """Get account equity"""
    account = mt5.account_info()
    return account.equity if account else 0.0

# ============= MARKET DATA =============

@ensure_connected
def get_price(symbol: str) -> Dict[str, Any]:
    """Get current bid/ask price for ANY symbol"""
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return {"error": f"Symbol {symbol} not found"}

    info = get_symbol_info(symbol)
    digits = info['digits'] if info else 2

    return {
        "symbol": symbol,
        "bid": round(tick.bid, digits),
        "ask": round(tick.ask, digits),
        "spread": round(tick.ask - tick.bid, digits),
        "time": datetime.fromtimestamp(tick.time),
        "volume": tick.volume,
    }

@ensure_connected
def get_quotes(symbols: list) -> Dict[str, Dict]:
    """Get quotes for multiple symbols"""
    quotes = {}
    for symbol in symbols:
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            info = get_symbol_info(symbol)
            digits = info['digits'] if info else 2
            quotes[symbol] = {
                "bid": round(tick.bid, digits),
                "ask": round(tick.ask, digits),
                "spread": round(tick.ask - tick.bid, digits),
            }
        else:
            quotes[symbol] = {"error": "Not found"}
    return quotes

@ensure_connected
def get_history(symbol: str, timeframe: str = "H1", bars: int = 100) -> pd.DataFrame:
    """Get historical price data for ANY symbol"""
    tf_map = {
        "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15, "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1, "W1": mt5.TIMEFRAME_W1, "MN1": mt5.TIMEFRAME_MN1
    }

    tf = tf_map.get(timeframe.upper(), mt5.TIMEFRAME_H1)
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)

    if rates is None or len(rates) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df[['time', 'open', 'high', 'low', 'close', 'volume']]

@ensure_connected
def get_spread(symbol: str) -> float:
    """Get current spread for ANY symbol"""
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        info = get_symbol_info(symbol)
        digits = info['digits'] if info else 2
        return round(tick.ask - tick.bid, digits)
    return -1

# ============= POSITIONS =============

@ensure_connected
def get_positions(symbol: str = None) -> list:
    """Get all open positions or specific symbol position"""
    if symbol:
        positions = mt5.positions_get(symbol=symbol)
    else:
        positions = mt5.positions_get()

    if positions is None:
        return []

    result = []
    for pos in positions:
        sym_info = get_symbol_info(pos.symbol)
        digits = sym_info['digits'] if sym_info else 2
        result.append({
            "ticket": pos.ticket,
            "symbol": pos.symbol,
            "type": "BUY" if pos.type == 0 else "SELL",
            "volume": pos.volume,
            "price_open": round(pos.price_open, digits),
            "price_current": round(pos.price_current, digits),
            "sl": round(pos.sl, digits) if pos.sl > 0 else 0,
            "tp": round(pos.tp, digits) if pos.tp > 0 else 0,
            "profit": pos.profit,
            "time": datetime.fromtimestamp(pos.time),
            "comment": pos.comment,
        })
    return result

@ensure_connected
def get_total_profit() -> float:
    """Get total profit/loss from all positions"""
    positions = mt5.positions_get()
    if positions is None:
        return 0.0
    return sum(pos.profit for pos in positions)

# ============= ORDER EXECUTION (Universal Method) =============

def _try_execute_order(request: dict) -> tuple:
    """
    Try to execute order with multiple filling modes (proven method from Gold/Silver/Bitcoin trades)

    Returns:
        (result, success)
    """
    # Filling modes to try in order
    filling_modes = [
        (mt5.ORDER_FILLING_FOK, "FOK"),
        (mt5.ORDER_FILLING_RETURN, "RETURN"),
        (mt5.ORDER_FILLING_IOC, "IOC"),
    ]

    original_filling = request.get('type_filling', mt5.ORDER_FILLING_FOK)

    for filling_mode, mode_name in filling_modes:
        request['type_filling'] = filling_mode
        result = mt5.order_send(request)

        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            return result, True

    # If all failed, return last result
    return result, False

@ensure_connected
def place_order(symbol: str, order_type: int, volume: float,
                price: float = 0, sl: float = 0, tp: float = 0,
                comment: str = "", deviation: int = 50) -> Dict[str, Any]:
    """
    Place a market or pending order for ANY symbol

    Args:
        symbol: Trading symbol
        order_type: 0=BUY, 1=SELL, 2=BUY_LIMIT, 3=SELL_LIMIT, 4=BUY_STOP, 5=SELL_STOP
        volume: Lot size
        price: Entry price (for pending orders, or 0 for market)
        sl: Stop Loss price
        tp: Take Profit price
        comment: Order comment
        deviation: Max slippage in points

    Returns:
        dict with success, retcode, ticket, volume, price, comment
    """
    # Get symbol info
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return {"error": f"Symbol {symbol} not found", "success": False}

    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            return {"error": f"Cannot select symbol {symbol}", "success": False}

    # Normalize volume to broker's requirements
    volume = round(volume / symbol_info.volume_step) * symbol_info.volume_step
    volume = max(symbol_info.volume_min, min(volume, symbol_info.volume_max))
    volume = round(volume, 2)

    # Determine price for market orders
    if order_type in [0, 1]:  # Market order
        tick = mt5.symbol_info_tick(symbol)
        price = tick.ask if order_type == 0 else tick.bid
    elif price == 0:
        return {"error": "Price required for pending order", "success": False}

    # Create order request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": deviation,
        "magic": 234000,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,  # Will be overridden by _try_execute_order
    }

    # Execute with multiple filling modes
    result, success = _try_execute_order(request)

    if result is None:
        return {"error": f"Order failed: {mt5.last_error()}", "success": False}

    digits = symbol_info.digits

    return {
        "success": result.retcode == mt5.TRADE_RETCODE_DONE,
        "retcode": result.retcode,
        "ticket": result.order if result.order else None,
        "volume": result.volume,
        "price": round(result.price, digits) if hasattr(result, 'price') else price,
        "comment": result.comment,
    }

def buy(symbol: str, volume: float, sl: float = 0, tp: float = 0, comment: str = "Buy order"):
    """Open BUY position for ANY symbol"""
    return place_order(symbol, 0, volume, sl=sl, tp=tp, comment=comment)

def sell(symbol: str, volume: float, sl: float = 0, tp: float = 0, comment: str = "Sell order"):
    """Open SELL position for ANY symbol"""
    return place_order(symbol, 1, volume, sl=sl, tp=tp, comment=comment)

def buy_limit(symbol: str, volume: float, price: float, sl: float = 0, tp: float = 0):
    """Place BUY LIMIT order for ANY symbol"""
    return place_order(symbol, 2, volume, price=price, sl=sl, tp=tp, comment="Buy Limit")

def sell_limit(symbol: str, volume: float, price: float, sl: float = 0, tp: float = 0):
    """Place SELL LIMIT order for ANY symbol"""
    return place_order(symbol, 3, volume, price=price, sl=sl, tp=tp, comment="Sell Limit")

def buy_stop(symbol: str, volume: float, price: float, sl: float = 0, tp: float = 0):
    """Place BUY STOP order for ANY symbol"""
    return place_order(symbol, 4, volume, price=price, sl=sl, tp=tp, comment="Buy Stop")

def sell_stop(symbol: str, volume: float, price: float, sl: float = 0, tp: float = 0):
    """Place SELL STOP order for ANY symbol"""
    return place_order(symbol, 5, volume, price=price, sl=sl, tp=tp, comment="Sell Stop")

# ============= POSITION MANAGEMENT =============

@ensure_connected
def close_position(symbol: str) -> Dict[str, Any]:
    """Close all positions for a symbol"""
    positions = mt5.positions_get(symbol=symbol)
    if positions is None or len(positions) == 0:
        return {"error": f"No open positions for {symbol}", "success": False}

    results = []
    for pos in positions:
        order_type = 1 if pos.type == 0 else 0
        tick = mt5.symbol_info_tick(symbol)
        price = tick.bid if order_type == 1 else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": order_type,
            "position": pos.ticket,
            "price": price,
            "deviation": 50,
            "magic": 234000,
            "comment": "Close position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result, success = _try_execute_order(request)
        results.append({
            "ticket": pos.ticket,
            "success": result.retcode == mt5.TRADE_RETCODE_DONE if result else False,
            "retcode": result.retcode if result else None,
            "profit": pos.profit,
        })

    return {"closed_positions": results, "success": all(r["success"] for r in results)}

@ensure_connected
def close_all_positions() -> Dict[str, Any]:
    """Close all open positions"""
    positions = mt5.positions_get()
    if positions is None or len(positions) == 0:
        return {"message": "No open positions", "success": True}

    results = []
    for pos in positions:
        order_type = 1 if pos.type == 0 else 0
        tick = mt5.symbol_info_tick(pos.symbol)
        price = tick.bid if order_type == 1 else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": order_type,
            "position": pos.ticket,
            "price": price,
            "deviation": 50,
            "magic": 234000,
            "comment": "Close all",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result, success = _try_execute_order(request)
        results.append({
            "symbol": pos.symbol,
            "ticket": pos.ticket,
            "success": result.retcode == mt5.TRADE_RETCODE_DONE if result else False,
            "profit": pos.profit,
        })

    return {"closed_positions": results, "success": all(r["success"] for r in results)}

@ensure_connected
def modify_position(symbol: str, sl: float = 0, tp: float = 0) -> Dict[str, Any]:
    """
    Modify stop loss and take profit for positions (proven method from Gold/Silver/Bitcoin)

    Uses TRADE_ACTION_SLTP with position ticket
    """
    positions = mt5.positions_get(symbol=symbol)
    if positions is None or len(positions) == 0:
        return {"error": f"No open positions for {symbol}", "success": False}

    results = []
    for pos in positions:
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": symbol,
            "position": pos.ticket,
            "sl": sl,
            "tp": tp,
        }

        result = mt5.order_send(request)
        results.append({
            "ticket": pos.ticket,
            "success": result.retcode == mt5.TRADE_RETCODE_DONE if result else False,
            "retcode": result.retcode if result else None,
            "comment": result.comment if result else "Unknown",
        })

    return {"modified": results, "success": all(r["success"] for r in results)}

@ensure_connected
def set_stop_loss(symbol: str, sl: float) -> Dict[str, Any]:
    """Set only stop loss for position"""
    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return {"error": f"No open positions for {symbol}", "success": False}

    pos = positions[0]
    return modify_position(symbol, sl=sl, tp=pos.tp)

@ensure_connected
def set_take_profit(symbol: str, tp: float) -> Dict[str, Any]:
    """Set only take profit for position"""
    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return {"error": f"No open positions for {symbol}", "success": False}

    pos = positions[0]
    return modify_position(symbol, sl=pos.sl, tp=tp)

# ============= RISK MANAGEMENT =============

def calculate_position_size(symbol: str, entry_price: float, stop_loss: float,
                            risk_percent: float = 2.0, account_balance: float = None) -> float:
    """
    Calculate position size for ANY symbol based on risk parameters

    Formula: lots = risk_amount / (price_diff * contract_size * point_value)

    Args:
        symbol: Trading symbol
        entry_price: Entry price
        stop_loss: Stop loss price
        risk_percent: Risk as % of account (default 2%)
        account_balance: Account balance (uses current if None)

    Returns:
        Lot size normalized to broker's requirements
    """
    if account_balance is None:
        account_balance = get_balance()

    risk_amount = account_balance * (risk_percent / 100)
    price_diff = abs(entry_price - stop_loss)

    if price_diff == 0:
        return 0

    # Get symbol info for contract size
    info = get_symbol_info(symbol)
    if info is None:
        # Fallback: approximate calculation
        lot_size = risk_amount / (price_diff * 1000)
    else:
        contract_size = info.get('trade_contract_size', 100)
        # Simplified: adjust based on price magnitude
        if price_diff < 0.01:  # Forex-like (small moves)
            multiplier = 100000
        elif price_diff < 1:  # Metals-like
            multiplier = 1000
        else:  # Crypto/Indices-like (large moves)
            multiplier = 10

        lot_size = risk_amount / (price_diff * contract_size * multiplier / 100)

    # Normalize to broker's volume requirements
    if info:
        lot_size = round(lot_size / info['volume_step']) * info['volume_step']
        lot_size = max(info['volume_min'], min(lot_size, info['volume_max']))

    return round(max(0.01, lot_size), 2)

# ============= TECHNICAL ANALYSIS =============

@ensure_connected
def analyze_symbol(symbol: str, bars: int = 100) -> Dict[str, Any]:
    """Full technical analysis for ANY symbol"""
    df = get_history(symbol, "H1", bars)
    if df.empty:
        return {"error": "No data available", "success": False}

    info = get_symbol_info(symbol)
    digits = info['digits'] if info else 2

    current_price = df['close'].iloc[-1]

    # RSI (14 period)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Moving Averages
    sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
    sma_50 = df['close'].rolling(window=50).mean().iloc[-1]
    ema_20 = df['close'].ewm(span=20).mean().iloc[-1]

    # MACD
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9).mean()

    # Support/Resistance
    resistance = df['high'].rolling(window=20).max().iloc[-1]
    support = df['low'].rolling(window=20).min().iloc[-1]

    # ATR (volatility)
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(14).mean().iloc[-1]

    # Signals
    rsi_val = rsi.iloc[-1]
    rsi_signal = "Overbought" if rsi_val > 70 else "Oversold" if rsi_val < 30 else "Neutral"
    trend_signal = "Bullish" if current_price > sma_50 else "Bearish"
    macd_sig = "Buy" if macd_line.iloc[-1] > signal_line.iloc[-1] else "Sell"

    # Overall recommendation
    bullish = sum([rsi_val < 50, current_price > sma_20, current_price > sma_50, macd_line.iloc[-1] > signal_line.iloc[-1]])
    bearish = sum([rsi_val > 50, current_price < sma_20, current_price < sma_50, macd_line.iloc[-1] < signal_line.iloc[-1]])

    if bullish > bearish + 1:
        recommendation = "BUY"
    elif bearish > bullish + 1:
        recommendation = "SELL"
    else:
        recommendation = "NEUTRAL"

    return {
        "symbol": symbol,
        "current_price": round(current_price, digits),
        "rsi": round(rsi_val, 2),
        "rsi_signal": rsi_signal,
        "sma_20": round(sma_20, digits),
        "sma_50": round(sma_50, digits),
        "ema_20": round(ema_20, digits),
        "trend": trend_signal,
        "macd_signal": macd_sig,
        "resistance": round(resistance, digits),
        "support": round(support, digits),
        "atr": round(atr, digits),
        "recommendation": recommendation,
        "bullish_signals": bullish,
        "bearish_signals": bearish,
    }

# ============= HELPER FUNCTIONS =============

def validate_sl_tp(symbol: str, direction: str, entry: float, sl: float, tp: float) -> tuple:
    """
    Validate Stop Loss and Take Profit prices for a trade direction

    Returns:
        (is_valid, error_message)
    """
    if direction.upper() == "BUY":
        if sl >= entry:
            return False, f"Stop Loss ({sl}) must be BELOW entry price ({entry}) for BUY"
        if tp <= entry:
            return False, f"Take Profit ({tp}) must be ABOVE entry price ({entry}) for BUY"
    else:  # SELL
        if sl <= entry:
            return False, f"Stop Loss ({sl}) must be ABOVE entry price ({entry}) for SELL"
        if tp >= entry:
            return False, f"Take Profit ({tp}) must be BELOW entry price ({entry}) for SELL"

    return True, None

# ============= CLI INTERFACE =============

if __name__ == "__main__":
    import sys

    print("MT5 Trading Module - Universal Python API")
    print("Works with ANY symbol: Forex, Metals, Crypto, Indices, Energies, Stocks, Bonds")
    print("=" * 70)

    if connect():
        print("[OK] Connected to MT5\n")

        # Account info
        info = get_account_info()
        print(f"Account: {info['name']} ({info['login']})")
        print(f"Balance: ${info['balance']:.2f}")
        print(f"Equity: ${info['equity']:.2f}\n")

        # List available symbols by category
        print("Available symbols by category:")
        for cat in ['forex', 'metal', 'crypto', 'index', 'energy']:
            syms = list_available_symbols(cat)
            if syms:
                print(f"  {cat.upper()}: {', '.join(syms[:5])}{'...' if len(syms) > 5 else ''}")
        print()

        # Positions
        positions = get_positions()
        if positions:
            print(f"Open Positions: {len(positions)}")
            for pos in positions:
                print(f"  {pos['type']} {pos['volume']} {pos['symbol']} @ {pos['price_open']} (P/L: ${pos['profit']:.2f})")
        else:
            print("No open positions")

        disconnect()
        print("\n[OK] Disconnected")
    else:
        print("[ERROR] Failed to connect to MT5")
        sys.exit(1)
