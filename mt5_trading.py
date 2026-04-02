"""
MT5 Trading Module - Direct Python API Integration
Provides all trading capabilities from the MT5 Trading Bot skill
"""

import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
from typing import Optional, Dict, Any

# MT5 Connection Settings
MT5_CONFIG = {
    "login": 107069198,
    "password": "D@5qZuUd",
    "server": "Ava-Demo 1-MT5"
}

def connect() -> bool:
    """Initialize MT5 connection"""
    if not mt5.initialize(**MT5_CONFIG):
        print(f"Connection failed: {mt5.last_error()}")
        return False
    return True

def disconnect():
    """Shutdown MT5 connection"""
    mt5.shutdown()

def ensure_connected(func):
    """Decorator to ensure MT5 is connected before calling function"""
    def wrapper(*args, **kwargs):
        # Connect if not already connected
        if not mt5.initialize(**MT5_CONFIG):
            if not connect():
                raise Exception("Failed to connect to MT5")
        try:
            return func(*args, **kwargs)
        finally:
            pass  # Keep connection open for subsequent calls
    return wrapper

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
    """Get current bid/ask price for symbol"""
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return {"error": f"Symbol {symbol} not found"}

    return {
        "symbol": symbol,
        "bid": tick.bid,
        "ask": tick.ask,
        "spread": round(tick.ask - tick.bid, 2),
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
            quotes[symbol] = {
                "bid": tick.bid,
                "ask": tick.ask,
                "spread": round(tick.ask - tick.bid, 2),
            }
        else:
            quotes[symbol] = {"error": "Not found"}
    return quotes

@ensure_connected
def get_history(symbol: str, timeframe: str = "H1", bars: int = 100) -> pd.DataFrame:
    """Get historical price data"""
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
    """Get current spread for symbol"""
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        return round(tick.ask - tick.bid, 2)
    return -1

# ============= POSITIONS =============

@ensure_connected
def get_positions(symbol: Optional[str] = None) -> list:
    """Get all open positions or specific symbol position"""
    if symbol:
        positions = mt5.positions_get(symbol=symbol)
    else:
        positions = mt5.positions_get()

    if positions is None:
        return []

    result = []
    for pos in positions:
        result.append({
            "ticket": pos.ticket,
            "symbol": pos.symbol,
            "type": "BUY" if pos.type == 0 else "SELL",
            "volume": pos.volume,
            "price_open": pos.price_open,
            "price_current": pos.price_current,
            "sl": pos.sl,
            "tp": pos.tp,
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

    total = sum(pos.profit for pos in positions)
    return total

# ============= ORDER EXECUTION =============

@ensure_connected
def place_order(symbol: str, order_type: int, volume: float,
                price: float = 0, sl: float = 0, tp: float = 0,
                comment: str = "") -> Dict[str, Any]:
    """
    Place a market or pending order

    order_type: 0=BUY, 1=SELL, 2=BUY_LIMIT, 3=SELL_LIMIT, 4=BUY_STOP, 5=SELL_STOP
    """
    # Get symbol info
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return {"error": f"Symbol {symbol} not found"}

    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            return {"error": f"Cannot select symbol {symbol}"}

    # Determine price
    if order_type in [0, 1]:  # Market order
        tick = mt5.symbol_info_tick(symbol)
        price = tick.ask if order_type == 0 else tick.bid
    elif price == 0:
        return {"error": "Price required for pending order"}

    # Normalize volume
    volume = round(volume, 2)

    # Create order request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 234000,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    # Send order
    result = mt5.order_send(request)

    if result is None:
        return {"error": f"Order failed: {mt5.last_error()}"}

    return {
        "success": result.retcode == mt5.TRADE_RETCODE_DONE,
        "retcode": result.retcode,
        "ticket": result.order if result.order else None,
        "volume": result.volume,
        "price": result.price if hasattr(result, 'price') else price,
        "comment": result.comment,
        "request": request,
    }

def buy(symbol: str, volume: float, sl: float = 0, tp: float = 0, comment: str = "Buy order"):
    """Open BUY position"""
    return place_order(symbol, 0, volume, sl=sl, tp=tp, comment=comment)

def sell(symbol: str, volume: float, sl: float = 0, tp: float = 0, comment: str = "Sell order"):
    """Open SELL position"""
    return place_order(symbol, 1, volume, sl=sl, tp=tp, comment=comment)

def buy_limit(symbol: str, volume: float, price: float, sl: float = 0, tp: float = 0):
    """Place BUY LIMIT order"""
    return place_order(symbol, 2, volume, price=price, sl=sl, tp=tp, comment="Buy Limit")

def sell_limit(symbol: str, volume: float, price: float, sl: float = 0, tp: float = 0):
    """Place SELL LIMIT order"""
    return place_order(symbol, 3, volume, price=price, sl=sl, tp=tp, comment="Sell Limit")

def buy_stop(symbol: str, volume: float, price: float, sl: float = 0, tp: float = 0):
    """Place BUY STOP order"""
    return place_order(symbol, 4, volume, price=price, sl=sl, tp=tp, comment="Buy Stop")

def sell_stop(symbol: str, volume: float, price: float, sl: float = 0, tp: float = 0):
    """Place SELL STOP order"""
    return place_order(symbol, 5, volume, price=price, sl=sl, tp=tp, comment="Sell Stop")

# ============= POSITION MANAGEMENT =============

@ensure_connected
def close_position(symbol: str) -> Dict[str, Any]:
    """Close all positions for a symbol"""
    positions = mt5.positions_get(symbol=symbol)
    if positions is None or len(positions) == 0:
        return {"error": f"No open positions for {symbol}"}

    results = []
    for pos in positions:
        # Create opposite order to close
        order_type = 1 if pos.type == 0 else 0  # SELL if BUY, BUY if SELL
        tick = mt5.symbol_info_tick(symbol)
        price = tick.bid if order_type == 1 else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": order_type,
            "position": pos.ticket,
            "price": price,
            "deviation": 10,
            "magic": 234000,
            "comment": "Close position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        results.append({
            "ticket": pos.ticket,
            "success": result.retcode == mt5.TRADE_RETCODE_DONE if result else False,
            "retcode": result.retcode if result else None,
            "profit": pos.profit,
        })

    return {"closed_positions": results}

@ensure_connected
def close_all_positions() -> Dict[str, Any]:
    """Close all open positions"""
    positions = mt5.positions_get()
    if positions is None or len(positions) == 0:
        return {"message": "No open positions"}

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
            "deviation": 10,
            "magic": 234000,
            "comment": "Close all",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        results.append({
            "symbol": pos.symbol,
            "ticket": pos.ticket,
            "success": result.retcode == mt5.TRADE_RETCODE_DONE if result else False,
            "profit": pos.profit,
        })

    return {"closed_positions": results}

@ensure_connected
def modify_position(symbol: str, sl: float = 0, tp: float = 0) -> Dict[str, Any]:
    """Modify stop loss and take profit for positions"""
    positions = mt5.positions_get(symbol=symbol)
    if positions is None or len(positions) == 0:
        return {"error": f"No open positions for {symbol}"}

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
        })

    return {"modified": results}

# ============= RISK MANAGEMENT =============

def calculate_position_size(entry_price: float, stop_loss: float, risk_percent: float,
                            account_balance: float = None) -> float:
    """
    Calculate position size based on risk parameters

    Returns lot size that risks exactly risk_percent of account
    """
    if account_balance is None:
        account_balance = get_balance()

    risk_amount = account_balance * (risk_percent / 100)
    price_diff = abs(entry_price - stop_loss)

    if price_diff == 0:
        return 0

    # For forex/CFD: 1 lot = 100,000 units, profit/loss per pip depends on symbol
    # Simplified: lots = risk_amount / (price_diff * 100000)
    lot_size = risk_amount / (price_diff * 1000)  # Approximate

    # Round to 2 decimal places, minimum 0.01
    lot_size = round(max(0.01, lot_size), 2)

    return lot_size

@ensure_connected
def get_symbol_info(symbol: str) -> Dict[str, Any]:
    """Get detailed symbol information"""
    info = mt5.symbol_info(symbol)
    if info is None:
        return {"error": f"Symbol {symbol} not found"}

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
    }

# ============= TECHNICAL ANALYSIS =============

@ensure_connected
def analyze_symbol(symbol: str, bars: int = 100) -> Dict[str, Any]:
    """Full technical analysis for a symbol"""
    # Get price data
    df = get_history(symbol, "H1", bars)
    if df.empty:
        return {"error": "No data available"}

    current_price = df['close'].iloc[-1]

    # Calculate indicators
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

    # Support/Resistance (simplified - recent highs/lows)
    resistance = df['high'].rolling(window=20).max().iloc[-1]
    support = df['low'].rolling(window=20).min().iloc[-1]

    # Generate signals
    rsi_signal = "Overbought" if rsi.iloc[-1] > 70 else "Oversold" if rsi.iloc[-1] < 30 else "Neutral"
    trend_signal = "Bullish" if current_price > sma_50 else "Bearish"
    macd_signal = "Buy" if macd_line.iloc[-1] > signal_line.iloc[-1] else "Sell"

    return {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "rsi": round(rsi.iloc[-1], 2),
        "rsi_signal": rsi_signal,
        "sma_20": round(sma_20, 2),
        "sma_50": round(sma_50, 2),
        "ema_20": round(ema_20, 2),
        "trend": trend_signal,
        "macd_signal": macd_signal,
        "resistance": round(resistance, 2),
        "support": round(support, 2),
        "recommendation": "BUY" if (macd_signal == "Buy" and trend_signal == "Bullish") else "SELL" if (macd_signal == "Sell" and trend_signal == "Bearish") else "NEUTRAL",
    }

# ============= HELPER FUNCTIONS =============

def list_available_symbols() -> list:
    """List all available trading symbols"""
    if not mt5.initialize(**MT5_CONFIG):
        return []

    symbols = mt5.symbols_get()
    if symbols is None:
        return []

    result = [s.name for s in symbols if s.visible]
    mt5.shutdown()
    return sorted(result)

# ============= CLI INTERFACE =============

if __name__ == "__main__":
    import sys

    print("MT5 Trading Module - Direct Python API")
    print("=" * 50)

    # Test connection
    if connect():
        print("[OK] Connected to MT5")

        # Show account info
        info = get_account_info()
        print(f"\nAccount: {info['name']} ({info['login']})")
        print(f"Balance: ${info['balance']:.2f}")
        print(f"Equity: ${info['equity']:.2f}")

        # Show positions
        positions = get_positions()
        if positions:
            print(f"\nOpen Positions: {len(positions)}")
            for pos in positions:
                print(f"  {pos['type']} {pos['volume']} {pos['symbol']} @ {pos['price_open']} (P/L: ${pos['profit']:.2f})")
        else:
            print("\nNo open positions")

        disconnect()
        print("\n[OK] Disconnected")
    else:
        print("[ERROR] Failed to connect to MT5")
        sys.exit(1)
