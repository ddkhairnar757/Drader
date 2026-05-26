import unittest
from datetime import datetime, timezone

import pandas as pd

from app.paper_trading.daily_journal import DailyJournal
from app.paper_trading.live_feed import LiveFeed, PriceUpdate
from app.paper_trading.paper_broker import PaperBroker
from app.paper_trading.position_tracker import PositionTracker
from app.paper_trading.session_manager import SessionConfig, SessionManager
from app.paper_trading.signal_router import SignalRouter


class TestPaperBroker(unittest.TestCase):
    def setUp(self) -> None:
        self.broker = PaperBroker(starting_capital=100000.0, commission_per_trade=1.0, slippage_pct=0.0005)

    def test_buy_order_execution(self) -> None:
        order = self.broker.submit_order(
            order_id="ORD-001",
            symbol="NIFTY",
            side="buy",
            quantity=10,
            current_price=100.0,
            timestamp=pd.Timestamp("2025-01-01"),
        )
        self.assertEqual(order.status.value, "filled")
        self.assertEqual(len(self.broker.positions), 1)
        self.assertEqual(self.broker.positions["NIFTY"].quantity, 10)

    def test_buy_order_insufficient_funds(self) -> None:
        self.broker.cash = 100.0
        order = self.broker.submit_order(
            order_id="ORD-002",
            symbol="NIFTY",
            side="buy",
            quantity=10000,
            current_price=100.0,
            timestamp=pd.Timestamp("2025-01-01"),
        )
        self.assertEqual(order.status.value, "cancelled")
        self.assertEqual(len(self.broker.positions), 0)

    def test_sell_order_execution(self) -> None:
        self.broker.submit_order(
            order_id="ORD-003",
            symbol="NIFTY",
            side="buy",
            quantity=10,
            current_price=100.0,
            timestamp=pd.Timestamp("2025-01-01"),
        )
        self.broker.submit_order(
            order_id="ORD-004",
            symbol="NIFTY",
            side="sell",
            quantity=10,
            current_price=102.0,
            timestamp=pd.Timestamp("2025-01-02"),
        )
        self.assertEqual(len(self.broker.positions), 0)
        self.assertEqual(len(self.broker.closed_trades), 1)

    def test_total_equity_tracking(self) -> None:
        initial_equity = self.broker.total_equity
        self.broker.submit_order(
            order_id="ORD-005",
            symbol="NIFTY",
            side="buy",
            quantity=10,
            current_price=100.0,
            timestamp=pd.Timestamp("2025-01-01"),
        )
        self.broker.update_position_values(105.0, "NIFTY")
        unrealized_pnl = self.broker.positions["NIFTY"].unrealized_pnl
        self.assertGreater(unrealized_pnl, 0)


class TestPositionTracker(unittest.TestCase):
    def setUp(self) -> None:
        self.broker = PaperBroker(starting_capital=100000.0)
        self.tracker = PositionTracker(self.broker)
        self.broker.submit_order(
            order_id="ORD-006",
            symbol="NIFTY",
            side="buy",
            quantity=10,
            current_price=100.0,
            timestamp=pd.Timestamp("2025-01-01"),
        )

    def test_position_snapshot(self) -> None:
        self.tracker.capture_snapshot({"NIFTY": 105.0}, pd.Timestamp("2025-01-01"))
        positions = self.tracker.get_current_positions()
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0].symbol, "NIFTY")

    def test_unrealized_pnl_tracking(self) -> None:
        self.tracker.capture_snapshot({"NIFTY": 105.0}, pd.Timestamp("2025-01-01"))
        pnl = self.tracker.get_total_unrealized_pnl()
        self.assertGreater(pnl, 0)


class TestSignalRouter(unittest.TestCase):
    def setUp(self) -> None:
        self.broker = PaperBroker(starting_capital=100000.0)
        self.router = SignalRouter(self.broker)

    def test_signal_emission(self) -> None:
        signal = self.router.emit_signal(
            strategy_name="EMA",
            symbol="NIFTY",
            side="buy",
            quantity=10,
            signal_price=100.0,
            timestamp=pd.Timestamp("2025-01-01"),
            reason="crossover",
        )
        self.assertEqual(len(self.router.signals), 1)
        self.assertEqual(signal.strategy_name, "EMA")

    def test_signal_execution(self) -> None:
        signal = self.router.emit_signal(
            strategy_name="EMA",
            symbol="NIFTY",
            side="buy",
            quantity=10,
            signal_price=100.0,
            timestamp=pd.Timestamp("2025-01-01"),
        )
        execution = self.router.execute_signal(signal, current_price=100.0)
        self.assertIsNotNone(execution)
        self.assertEqual(execution.symbol, "NIFTY")


class TestSessionManager(unittest.TestCase):
    def test_market_open_close_states(self) -> None:
        manager = SessionManager()
        open_time = datetime(2025, 1, 1, 9, 15, tzinfo=timezone.utc)
        close_time = datetime(2025, 1, 1, 15, 30, tzinfo=timezone.utc)
        after_close = datetime(2025, 1, 1, 16, 0, tzinfo=timezone.utc)

        self.assertTrue(manager.is_market_open(open_time))
        self.assertTrue(manager.is_market_open(close_time))
        self.assertFalse(manager.is_market_open(after_close))


class TestLiveFeed(unittest.TestCase):
    def test_subscription_and_publishing(self) -> None:
        feed = LiveFeed()
        updates_received = []

        def callback(update: PriceUpdate) -> None:
            updates_received.append(update)

        feed.subscribe("NIFTY", callback)
        update = PriceUpdate(
            symbol="NIFTY",
            timestamp=pd.Timestamp("2025-01-01"),
            open_price=100.0,
            high=105.0,
            low=99.0,
            close=104.0,
            volume=1000,
        )
        feed.publish_update(update)
        self.assertEqual(len(updates_received), 1)
        self.assertEqual(updates_received[0].close, 104.0)

    def test_price_history(self) -> None:
        feed = LiveFeed()
        for i in range(5):
            update = PriceUpdate(
                symbol="NIFTY",
                timestamp=pd.Timestamp("2025-01-01") + pd.Timedelta(days=i),
                open_price=100.0,
                high=105.0,
                low=99.0,
                close=100.0 + i,
                volume=1000,
            )
            feed.publish_update(update)
        history = feed.get_price_history("NIFTY")
        self.assertEqual(len(history), 5)


class TestDailyJournal(unittest.TestCase):
    def test_session_recording(self) -> None:
        broker = PaperBroker(starting_capital=100000.0)
        tracker = PositionTracker(broker)
        router = SignalRouter(broker)
        journal = DailyJournal()

        session_start = datetime(2025, 1, 1, 9, 15, tzinfo=timezone.utc)
        session_end = datetime(2025, 1, 1, 15, 30, tzinfo=timezone.utc)

        entry = journal.record_session(
            session_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            session_start=session_start,
            session_end=session_end,
            broker=broker,
            position_tracker=tracker,
            signal_router=router,
            starting_equity=100000.0,
        )

        self.assertIsNotNone(entry)
        self.assertEqual(entry.daily_pnl, 0.0)
        self.assertEqual(len(journal.entries), 1)


if __name__ == "__main__":
    unittest.main()
