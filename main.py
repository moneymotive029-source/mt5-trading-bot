"""
=====================================================================
MT5 TRADING BOT - Main Entry Point
=====================================================================

Metals Trading Signal Bot for MetaTrader 5
Based on comprehensive CFD metals analysis (April 2026)

TOP SIGNALS:
1. COPPER (HG/USD)   - LONG @ $4.35-4.45/lb -> Target $5.00-6.00
2. PLATINUM (XPT/USD) - LONG @ $1,850-1,890 -> Target $2,000-2,200
3. GOLD (XAU/USD)    - WAIT->LONG @ $4,420-4,480 -> Target $4,620-5,050

Run this bot on your local machine with MT5 installed.
"""

import logging
import time
import sys
from datetime import datetime, timedelta
from typing import List

# Set UTF-8 encoding for Windows console compatibility
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from config import LOG_LEVEL, LOG_FILE, ENABLE_TELEGRAM, EXECUTION
from mt5_connector import MT5Connector
from signal_engine import SignalEngine
from order_executor import OrderExecutor

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TradingBot:
    """Main trading bot orchestrator."""

    def __init__(self):
        self.connector = MT5Connector()
        self.signal_engine = SignalEngine(self.connector)
        self.order_executor = OrderExecutor(self.connector)
        self.running = False
        self.last_check = None
        self.signals_generated = 0
        self.trades_executed = 0

    def start(self):
        """Start the trading bot."""
        # Connect to MT5 first
        if not self.connector.connect():
            logger.error("Failed to connect to MT5. Exiting.")
            return False

        logger.info("=" * 70)
        logger.info("MT5 TRADING BOT STARTING")
        logger.info("=" * 70)
        logger.info(f"Account: {self.connector.account_info.login}")
        logger.info(f"Balance: ${self.connector.get_account_balance():.2f}")
        logger.info(f"Risk per trade: ${self.connector.account_info.balance * 0.02:.2f} (2%)")
        logger.info("=" * 70)

        self.running = True
        self.last_check = datetime.now()

        # Main trading loop
        try:
            while self.running:
                self._trading_cycle()
                time.sleep(5)  # Check every 5 seconds
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}", exc_info=True)
        finally:
            self.shutdown()

        return True

    def _trading_cycle(self):
        """Execute one trading cycle."""
        now = datetime.now()

        # Check if we should run (avoid news events, market hours, etc.)
        if not self._should_trade():
            return

        # Check risk limits
        if not self.order_executor.check_risk_limits():
            logger.warning("Risk limits exceeded - skipping trade cycle")
            return

        # Check for take profit actions
        tp_actions = self.order_executor.check_take_profit_levels()
        for action in tp_actions:
            if action["action"] == "PARTIAL_CLOSE":
                self.order_executor.execute_partial_close(action["position"], action["close_pct"])
                logger.info(f"TP Level {action['tp_level']} hit - Closed {action['close_pct']*100:.0f}%")

        # Move stops to breakeven where appropriate
        self._manage_stops()

        # Check for new signals
        new_signals = self.signal_engine.monitor_signals()

        # Execute signals
        for signal in new_signals:
            logger.info(f"Executing signal: {signal}")
            if self.order_executor.place_order(signal):
                self.trades_executed += 1
                self.signals_generated += 1

        # Log status every minute
        if (now - self.last_check).total_seconds() >= 60:
            self._log_status()
            self.last_check = now

    def _should_trade(self) -> bool:
        """Check if we should be trading right now."""
        from config import NEWS_EVENTS

        now = datetime.now()

        # Check market hours (forex/metals typically 24/5)
        if now.weekday() >= 5:  # Weekend
            return False

        # Check news blackout periods
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")

        if date_str in NEWS_EVENTS:
            for event_time, event_name, blackout_min in NEWS_EVENTS[date_str]:
                event_dt = datetime.strptime(f"{date_str} {event_time}", "%Y-%m-%d %H:%M")
                blackout_start = event_dt - timedelta(minutes=blackout_min)
                blackout_end = event_dt + timedelta(minutes=blackout_min)

                if blackout_start <= now <= blackout_end:
                    logger.info(f"News blackout: {event_name} at {event_time}")
                    return False

        return True

    def _manage_stops(self):
        """Manage stop losses - move to breakeven when profitable."""
        positions = self.connector.get_positions()

        for pos in positions:
            # Find entry price from executed trades
            for trade in self.order_executor.executed_trades:
                if trade["ticket"] == pos.ticket:
                    entry = trade["executed_price"]
                    current = pos.price_current

                    # Move to breakeven if profitable by 1R
                    if pos.type == 0:  # BUY
                        risk = entry - pos.sl
                        if current >= entry + risk:
                            self.order_executor.move_stop_to_breakeven(pos, entry + 0.01)
                    else:  # SELL
                        risk = pos.sl - entry
                        if current <= entry - risk:
                            self.order_executor.move_stop_to_breakeven(pos, entry - 0.01)
                    break

    def _log_status(self):
        """Log current bot status."""
        positions = self.connector.get_positions()
        equity = self.connector.get_account_equity()
        balance = self.connector.get_account_balance()
        daily_pnl = self.order_executor.get_daily_pnl()

        logger.info("-" * 50)
        logger.info(f"Status: {len(positions)} positions | "
                   f"Equity: ${equity:.2f} | Balance: ${balance:.2f} | "
                   f"Daily P&L: ${daily_pnl:.2f}")
        logger.info(f"Signals: {self.signals_generated} | Trades: {self.trades_executed}")

        for pos in positions:
            logger.info(f"  → {pos.symbol} {pos.type} {pos.volume} @ {pos.price_open:.2f} "
                       f"| P&L: ${pos.profit:.2f}")

    def shutdown(self):
        """Gracefully shutdown the bot."""
        logger.info("Shutting down...")
        self.running = False
        self.connector.disconnect()
        logger.info("Bot shutdown complete")


def main():
    """Main entry point."""
    bot = TradingBot()

    # Show welcome message
    print(r"""
=====================================================================
           MT5 METALS TRADING BOT - April 2026 Signals
=====================================================================

TOP TRADES:
  [1] COPPER (HG/USD)    -> LONG @ $4.35-4.45/lb -> TP: $5.00-6.00
  [2] PLATINUM (XPT/USD) -> LONG @ $1,850-1,890 -> TP: $2,000-2,200
  [3] GOLD (XAU/USD)     -> WAIT->LONG @ $4,420-4,480 -> TP: $4,620-5,050

=====================================================================
  REMINDER: Change your MT5 password in config.py!
    Your credentials were exposed in the chat.
=====================================================================
    """)

    # Start the bot
    bot.start()


if __name__ == "__main__":
    main()
