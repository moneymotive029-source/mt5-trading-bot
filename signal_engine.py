"""
═══════════════════════════════════════════════════════════════════
SIGNAL ENGINE - Trading Signal Generation & Monitoring
═══════════════════════════════════════════════════════════════════
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from config import SYMBOLS, ACCOUNT_BALANCE, RISK_PER_TRADE
from mt5_connector import MT5Connector

logger = logging.getLogger(__name__)


class Signal:
    """Represents a trading signal."""

    def __init__(self, symbol: str, action: str, entry_price: float,
                 stop_loss: float, take_profits: List[Tuple[float, float]],
                 lot_size: float, confidence: float, rationale: str):
        self.symbol = symbol
        self.action = action  # BUY or SELL
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profits = take_profits  # [(price, %_to_close), ...]
        self.lot_size = lot_size
        self.confidence = confidence  # 0.0 to 1.0
        self.rationale = rationale
        self.timestamp = datetime.now()
        self.status = "PENDING"  # PENDING, EXECUTED, CANCELLED

    def __str__(self) -> str:
        tp_str = ", ".join([f"{p[0]}({p[1]*100:.0f}%)" for p in self.take_profits])
        return (f"{'[BUY]' if self.action == 'BUY' else '[SELL]'} {self.symbol} @ {self.entry_price}\n"
                f"   SL: {self.stop_loss} | TP: {tp_str}\n"
                f"   Lots: {self.lot_size:.2f} | Confidence: {self.confidence*100:.0f}%\n"
                f"   Rationale: {self.rationale}")


class SignalEngine:
    """Generates and monitors trading signals based on market conditions."""

    def __init__(self, connector: MT5Connector):
        self.connector = connector
        self.active_signals: List[Signal] = []

    def calculate_position_size(self, symbol: str, entry_price: float,
                                stop_loss: float, risk_pct: float = RISK_PER_TRADE) -> float:
        """
        Calculate position size based on risk parameters.

        Formula: Lot Size = (Account Balance × Risk %) / (Stop Distance × Contract Size)
        """
        account = self.connector.account_info
        if account is None:
            return 0.0

        symbol_info = SYMBOLS.get(symbol, {})
        contract_size = symbol_info.get("contract_size", 100)
        min_lot = symbol_info.get("min_lot", 0.01)
        max_lot = symbol_info.get("max_lot", 10.0)
        lot_step = symbol_info.get("lot_step", 0.01)

        # Calculate risk amount
        risk_amount = account.balance * risk_pct

        # Calculate stop distance
        stop_distance = abs(entry_price - stop_loss)
        if stop_distance == 0:
            return 0.0

        # Calculate lot size
        raw_lot = risk_amount / (stop_distance * contract_size)

        # Normalize to lot step
        normalized_lot = round(raw_lot / lot_step) * lot_step

        # Clamp to min/max
        final_lot = max(min_lot, min(max_lot, normalized_lot))

        logger.info(f"Position size calc: Risk ${risk_amount:.2f}, "
                   f"Stop ${stop_distance:.2f}, Contract {contract_size}, "
                   f"→ {final_lot:.2f} lots")

        return final_lot

    def generate_buy_signal(self, symbol: str, entry_price: float,
                           atr: float, confidence: float, rationale: str) -> Optional[Signal]:
        """Generate a BUY signal with proper risk management."""
        symbol_config = SYMBOLS.get(symbol, {})
        atr_mult = symbol_config.get("atr_multiplier_sl", 2.5)

        # Calculate stop loss (ATR-based)
        stop_loss = entry_price - (atr * atr_mult)

        # Calculate take profit levels (multiple targets)
        risk = entry_price - stop_loss
        take_profits = [
            (entry_price + risk * 1.5, 0.25),  # TP1: 1.5R, close 25%
            (entry_price + risk * 2.5, 0.30),  # TP2: 2.5R, close 30%
            (entry_price + risk * 4.0, 0.30),  # TP3: 4R, close 30%
            (entry_price + risk * 6.0, 0.15),  # TP4: 6R, runner 15%
        ]

        # Calculate position size
        lot_size = self.calculate_position_size(symbol, entry_price, stop_loss)
        if lot_size <= 0:
            logger.error(f"Invalid lot size for {symbol}")
            return None

        signal = Signal(
            symbol=symbol,
            action="BUY",
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profits=take_profits,
            lot_size=lot_size,
            confidence=confidence,
            rationale=rationale
        )

        logger.info(f"Generated BUY signal: {symbol} @ {entry_price}, SL: {stop_loss:.2f}, "
                   f"Size: {lot_size:.2f} lots")
        return signal

    def generate_sell_signal(self, symbol: str, entry_price: float,
                            atr: float, confidence: float, rationale: str) -> Optional[Signal]:
        """Generate a SELL signal with proper risk management."""
        symbol_config = SYMBOLS.get(symbol, {})
        atr_mult = symbol_config.get("atr_multiplier_sl", 2.5)

        # Calculate stop loss (ATR-based)
        stop_loss = entry_price + (atr * atr_mult)

        # Calculate take profit levels
        risk = stop_loss - entry_price
        take_profits = [
            (entry_price - risk * 1.5, 0.25),
            (entry_price - risk * 2.5, 0.30),
            (entry_price - risk * 4.0, 0.30),
            (entry_price - risk * 6.0, 0.15),
        ]

        # Calculate position size
        lot_size = self.calculate_position_size(symbol, entry_price, stop_loss)
        if lot_size <= 0:
            logger.error(f"Invalid lot size for {symbol}")
            return None

        signal = Signal(
            symbol=symbol,
            action="SELL",
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profits=take_profits,
            lot_size=lot_size,
            confidence=confidence,
            rationale=rationale
        )

        logger.info(f"Generated SELL signal: {symbol} @ {entry_price}, SL: {stop_loss:.2f}, "
                   f"Size: {lot_size:.2f} lots")
        return signal

    def check_entry_conditions(self, symbol: str) -> Optional[Signal]:
        """
        Check if current market conditions match entry criteria for a symbol.
        Returns a Signal if conditions are met, None otherwise.
        """
        symbol_config = SYMBOLS.get(symbol, {})
        if not symbol_config.get("enabled", False):
            return None

        signal_type = symbol_config.get("signal", "WAIT")
        entry_zones = symbol_config.get("entry_zones", [])
        resistance_zones = symbol_config.get("resistance_zones", [])

        # Get current price
        bid, ask = self.connector.get_current_price(symbol)
        if bid == 0.0:
            return None

        # Get ATR for stop calculation
        atr = self.connector.calculate_atr(symbol)
        if atr == 0:
            logger.warning(f"Could not calculate ATR for {symbol}")
            return None

        mid_price = (bid + ask) / 2

        # Check BUY signals
        if signal_type in ["LONG", "WAIT_LONG"]:
            for entry_low, entry_high in entry_zones:
                if entry_low <= mid_price <= entry_high:
                    # Price is in entry zone
                    confidence = self._calculate_confidence(symbol, "BUY")
                    rationale = f"Price ${mid_price:.2f} in buy zone (${entry_low}-{entry_high})"
                    return self.generate_buy_signal(symbol, mid_price, atr, confidence, rationale)

        # Check SELL signals
        if signal_type in ["SHORT", "WAIT_SHORT"]:
            for entry_low, entry_high in resistance_zones:
                if entry_low <= mid_price <= entry_high:
                    confidence = self._calculate_confidence(symbol, "SELL")
                    rationale = f"Price ${mid_price:.2f} in sell zone (${entry_low}-{entry_high})"
                    return self.generate_sell_signal(symbol, mid_price, atr, confidence, rationale)

        return None

    def _calculate_confidence(self, symbol: str, direction: str) -> float:
        """
        Calculate signal confidence based on technical factors.
        Returns value between 0.0 and 1.0.
        """
        base_confidence = 0.50  # Base 50%

        # Symbol-specific base confidence (from our analysis)
        symbol_confidence = {
            "XAUUSD": 0.60,
            "XAGUSD": 0.55,
            "XPTUSD": 0.72,  # Highest - strong setup
            "XPDUSD": 0.58,
            "COPPER": 0.70,  # Strong setup
        }

        return symbol_confidence.get(symbol, base_confidence)

    def monitor_signals(self) -> List[Signal]:
        """
        Monitor all enabled symbols for entry conditions.
        Returns list of new signals to execute.
        """
        new_signals = []

        for symbol in SYMBOLS.keys():
            if not SYMBOLS[symbol].get("enabled", False):
                continue

            signal = self.check_entry_conditions(symbol)
            if signal:
                # Check correlation risk
                if not self.connector.check_correlation_risk(symbol, signal.action):
                    logger.warning(f"Signal blocked due to correlation risk: {symbol}")
                    continue

                # Check if we already have an active signal for this symbol
                existing = [s for s in self.active_signals if s.symbol == symbol and s.status == "PENDING"]
                if existing:
                    logger.info(f"Already have pending signal for {symbol}")
                    continue

                new_signals.append(signal)
                self.active_signals.append(signal)
                logger.info(f"New signal generated: {signal}")

        return new_signals

    def update_signal_status(self, symbol: str, new_status: str):
        """Update the status of signals for a symbol."""
        for signal in self.active_signals:
            if signal.symbol == symbol:
                signal.status = new_status
