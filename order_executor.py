"""
═══════════════════════════════════════════════════════════════════
ORDER EXECUTOR - Trade Execution & Management
═══════════════════════════════════════════════════════════════════
"""

import MetaTrader5 as mt5
import logging
from typing import Optional, List, Dict
from config import EXECUTION, SYMBOLS
from signal_engine import Signal
from mt5_connector import MT5Connector

logger = logging.getLogger(__name__)


class OrderExecutor:
    """Handles order placement, modification, and position management."""

    def __init__(self, connector: MT5Connector):
        self.connector = connector
        self.executed_trades = []

    def place_order(self, signal: Signal) -> bool:
        """Execute a trading signal by placing an order."""
        symbol = signal.symbol
        symbol_config = SYMBOLS.get(symbol, {})

        # Determine order type
        if signal.action == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = self.connector.get_current_price(symbol)[1]  # Ask
        else:
            order_type = mt5.ORDER_TYPE_SELL
            price = self.connector.get_current_price(symbol)[0]  # Bid

        # Prepare order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": signal.lot_size,
            "type": order_type,
            "price": price,
            "sl": signal.stop_loss,
            "tp": signal.take_profits[0][0],  # Initial TP
            "deviation": EXECUTION.get("slippage_points", 5),
            "magic": EXECUTION.get("magic_number", 20260401),
            "comment": EXECUTION.get("comment", "AI_Signal_Bot"),
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Send order with retries
        for attempt in range(EXECUTION.get("retry_attempts", 3)):
            result = mt5.order_send(request)

            if result is None:
                logger.error(f"Order send failed (attempt {attempt + 1}): {mt5.last_error()}")
                continue

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.warning(f"Order retcode: {result.retcode} - {result.comment}")
                if result.retcode == mt5.TRADE_RETCODE_INVALID_VOLUME:
                    # Adjust volume and retry
                    signal.lot_size = max(0.01, signal.lot_size * 0.5)
                    request["volume"] = signal.lot_size
                    logger.info(f"Adjusted volume to {signal.lot_size}")
                    continue
                elif result.retcode == mt5.TRADE_RETCODE_INVALID_STOPS:
                    # Adjust stops and retry
                    logger.warning("Invalid stops - adjusting to current price")
                    if signal.action == "BUY":
                        signal.stop_loss = price * 0.995  # 0.5% below
                    else:
                        signal.stop_loss = price * 1.005  # 0.5% above
                    request["sl"] = signal.stop_loss
                    continue
            else:
                # Order successful
                logger.info(f"✓ Order executed: {signal.action} {signal.lot_size} {symbol} "
                           f"@ {result.price}, Ticket: {result.order}")
                self.executed_trades.append({
                    "ticket": result.order,
                    "signal": signal,
                    "executed_price": result.price,
                    "executed_volume": signal.lot_size,
                    "timestamp": result.time,
                })
                signal.status = "EXECUTED"
                return True

        logger.error(f"Order execution failed after {EXECUTION.get('retry_attempts', 3)} attempts")
        signal.status = "CANCELLED"
        return False

    def check_take_profit_levels(self) -> List[Dict]:
        """
        Check open positions against take profit levels.
        Returns list of positions that need partial close.
        """
        positions = self.connector.get_positions()
        actions = []

        for pos in positions:
            # Find the original signal for this position
            matching_trade = None
            for trade in self.executed_trades:
                if trade["ticket"] == pos.ticket:
                    matching_trade = trade
                    break

            if not matching_trade:
                continue

            signal = matching_trade["signal"]
            current_price = pos.price_current

            # Check each TP level
            for i, (tp_price, close_pct) in enumerate(signal.take_profits):
                if pos.type == mt5.ORDER_TYPE_BUY:
                    if current_price >= tp_price:
                        actions.append({
                            "position": pos,
                            "action": "PARTIAL_CLOSE",
                            "close_pct": close_pct,
                            "tp_level": i + 1,
                            "reason": f"TP{i+1} hit at {tp_price}",
                        })
                else:  # SELL
                    if current_price <= tp_price:
                        actions.append({
                            "position": pos,
                            "action": "PARTIAL_CLOSE",
                            "close_pct": close_pct,
                            "tp_level": i + 1,
                            "reason": f"TP{i+1} hit at {tp_price}",
                        })

        return actions

    def execute_partial_close(self, position, close_pct: float) -> bool:
        """Execute a partial close of a position."""
        close_volume = position.volume * close_pct
        if close_volume < SYMBOLS.get(position.symbol, {}).get("min_lot", 0.01):
            logger.warning(f"Close volume too small: {close_volume}")
            return False

        # Prepare close order (opposite type)
        if position.type == mt5.ORDER_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = self.connector.get_current_price(position.symbol)[0]  # Bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = self.connector.get_current_price(position.symbol)[1]  # Ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": close_volume,
            "type": order_type,
            "price": price,
            "position": position.ticket,
            "deviation": EXECUTION.get("slippage_points", 5),
            "magic": EXECUTION.get("magic_number", 20260401),
            "comment": f"TP_Level_{close_pct*100:.0f}%",
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✓ Partial close: {close_volume} {position.symbol} @ {result.price}")
            return True
        else:
            logger.error(f"Partial close failed: {result.comment if result else mt5.last_error()}")
            return False

    def move_stop_to_breakeven(self, position, breakeven_price: float) -> bool:
        """Move stop loss to breakeven."""
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": position.ticket,
            "sl": breakeven_price,
            "tp": position.tp,
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✓ Stop moved to breakeven: {breakeven_price}")
            return True
        return False

    def close_all_positions(self, symbol: Optional[str] = None) -> int:
        """Close all positions, optionally filtered by symbol."""
        positions = self.connector.get_positions(symbol)
        closed_count = 0

        for pos in positions:
            if pos.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = self.connector.get_current_price(pos.symbol)[0]
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = self.connector.get_current_price(pos.symbol)[1]

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": order_type,
                "price": price,
                "position": pos.ticket,
                "deviation": EXECUTION.get("slippage_points", 5),
                "magic": EXECUTION.get("magic_number", 20260401),
                "comment": "CLOSE_ALL",
            }

            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                closed_count += 1
                logger.info(f"✓ Closed: {pos.volume} {pos.symbol} @ {result.price}")

        return closed_count

    def get_daily_pnl(self) -> float:
        """Calculate daily P&L from executed trades."""
        daily_pnl = 0.0
        positions = self.connector.get_positions()

        for pos in positions:
            daily_pnl += pos.profit

        return daily_pnl

    def check_risk_limits(self) -> bool:
        """
        Check if we're within risk limits.
        Returns True if trading is allowed, False if limits exceeded.
        """
        from config import RISK_RULES

        # Check daily loss limit
        daily_pnl = self.get_daily_pnl()
        account = self.connector.account_info
        if account:
            daily_loss_pct = abs(daily_pnl) / account.balance if daily_pnl < 0 else 0
            if daily_loss_pct >= RISK_RULES.get("max_daily_loss_pct", 0.05):
                logger.warning(f"Daily loss limit hit: {daily_loss_pct*100:.2f}%")
                return False

        # Check drawdown
        if account:
            drawdown = (account.balance - account.equity) / account.balance
            if drawdown >= RISK_RULES.get("max_drawdown_pct", 0.10):
                logger.warning(f"Max drawdown hit: {drawdown*100:.2f}%")
                return False

        # Check max positions
        total_positions = self.connector.get_total_positions()
        if total_positions >= RISK_RULES.get("max_positions", 5):
            logger.warning(f"Max positions reached: {total_positions}")
            return False

        return True
