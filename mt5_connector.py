"""
═══════════════════════════════════════════════════════════════════
MT5 CONNECTOR - Core MT5 Integration Module
═══════════════════════════════════════════════════════════════════
"""

import MetaTrader5 as mt5
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from config import MT5_LOGIN, MT5_PASSWORD, MT5_SERVER, MT5_PATH, SYMBOLS

logger = logging.getLogger(__name__)


class MT5Connector:
    """Handles all MetaTrader 5 connectivity and data operations."""

    def __init__(self):
        self.connected = False
        self.account_info = None
        self.positions = []
        self.orders = []

    def connect(self) -> bool:
        """Initialize connection to MT5."""
        try:
            # Initialize MT5
            if MT5_PATH:
                if not mt5.initialize(path=MT5_PATH, login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
                    logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                    return False
            else:
                if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
                    logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                    return False

            # Get account info
            self.account_info = mt5.account_info()
            if self.account_info is None:
                logger.error("Failed to get account info")
                return False

            self.connected = True
            logger.info(f"[OK] Connected to MT5 - Account: {self.account_info.login}, "
                       f"Balance: ${self.account_info.balance:.2f}, "
                       f"Server: {self.account_info.server}")
            return True

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Close MT5 connection."""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")

    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """Get symbol information."""
        info = mt5.symbol_info(symbol)
        if info is None:
            logger.warning(f"Symbol {symbol} not found")
            return None
        return {
            "name": info.name,
            "bid": info.bid,
            "ask": info.ask,
            "spread": info.ask - info.bid,
            "volume_min": info.volume_min,
            "volume_max": info.volume_max,
            "volume_step": info.volume_step,
            "contract_size": info.trade_contract_size,
        }

    def get_current_price(self, symbol: str) -> Tuple[float, float]:
        """Get current bid/ask prices."""
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return 0.0, 0.0
        return tick.bid, tick.ask

    def get_historical_data(self, symbol: str, timeframe: int = mt5.TIMEFRAME_H1,
                           bars: int = 100) -> Optional[pd.DataFrame]:
        """Get historical OHLCV data."""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        if rates is None or len(rates) == 0:
            return None

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def calculate_atr(self, symbol: str, period: int = 14, timeframe: int = mt5.TIMEFRAME_H1) -> float:
        """Calculate ATR (Average True Range)."""
        df = self.get_historical_data(symbol, timeframe, period + 10)
        if df is None:
            return 0.0

        # Calculate True Range
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = abs(df['high'] - df['close'].shift(1))
        df['low_close'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)

        # ATR is average of last 'period' TR values
        atr = df['tr'].iloc[-period:].mean()
        return atr

    def get_positions(self, symbol: Optional[str] = None) -> List[dict]:
        """Get open positions, optionally filtered by symbol."""
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
                "type": "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                "volume": pos.volume,
                "price_open": pos.price_open,
                "price_current": pos.price_current,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": pos.profit,
                "time": datetime.fromtimestamp(pos.time),
            })
        return result

    def get_account_balance(self) -> float:
        """Get current account balance."""
        info = mt5.account_info()
        return info.balance if info else 0.0

    def get_account_equity(self) -> float:
        """Get current account equity."""
        info = mt5.account_info()
        return info.equity if info else 0.0

    def get_free_margin(self) -> float:
        """Get free margin available."""
        info = mt5.account_info()
        return info.margin_free if info else 0.0

    def get_total_positions(self) -> int:
        """Get total number of open positions."""
        positions = mt5.positions_get()
        return len(positions) if positions else 0

    def check_correlation_risk(self, new_symbol: str, new_type: str) -> bool:
        """
        Check if adding this position would violate correlation rules.
        Returns True if position is allowed, False if it violates correlation rules.
        """
        from config import RISK_RULES

        if new_type != "BUY":  # Only check for long positions
            return True

        positions = self.get_positions()
        correlation_pairs = RISK_RULES.get("max_correlated_positions", 2)

        # Check each correlation pair
        for pair in RISK_RULES.get("correlation_pairs", []):
            if new_symbol in pair:
                correlated_symbol = pair[0] if pair[1] == new_symbol else pair[1]
                correlated_longs = [p for p in positions if p["symbol"] == correlated_symbol and p["type"] == "BUY"]
                if len(correlated_longs) >= correlation_pairs:
                    logger.warning(f"Correlation risk: Already have {len(correlated_longs)} "
                                 f"{correlated_symbol} long position(s)")
                    return False

        return True

    def __str__(self) -> str:
        if not self.connected:
            return "MT5Connector: Not connected"
        return f"MT5Connector: {self.account_info.login}@{self.account_info.server}"
