import unittest
from datetime import datetime, timedelta, date

from app.dashboard import (
    EquityMonitor,
    PositionPanel,
    SignalMonitor,
    SessionView,
    LiveDashboard,
    SignalSide,
    MarketSessionState,
)


class TestDashboardComponents(unittest.TestCase):
    def test_equity_monitor_records_updates_and_snapshot(self):
        monitor = EquityMonitor(100000.0)
        now = datetime.now()
        monitor.record_equity_update(now + timedelta(minutes=1), 100500.0)
        snapshot = monitor.get_equity_snapshot()

        self.assertEqual(snapshot.opening_equity, 100000.0)
        self.assertEqual(snapshot.current_equity, 100500.0)
        self.assertGreaterEqual(snapshot.session_pnl, 500.0)
        self.assertGreaterEqual(snapshot.max_drawdown_pct, 0.0)
        self.assertGreaterEqual(snapshot.smoothness_score, 0.0)

    def test_position_panel_updates_open_and_closing_positions(self):
        panel = PositionPanel(100000.0)
        entry_time = datetime.now() - timedelta(minutes=30)
        panel.record_position_update("ABC", 100, 100.0, 105.0, entry_time)
        snapshot = panel.get_position_snapshot("ABC")

        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.symbol, "ABC")
        self.assertTrue(snapshot.unrealized_pnl > 0)

        exposure = panel.get_portfolio_exposure()
        self.assertEqual(exposure.open_positions_count, 1)
        self.assertGreater(exposure.total_unrealized_pnl, 0)

        panel.record_position_update("ABC", 0, 100.0, 105.0, entry_time)
        self.assertIsNone(panel.get_position_snapshot("ABC"))

    def test_signal_monitor_records_signals_and_execution(self):
        monitor = SignalMonitor()
        signal = monitor.record_signal(
            strategy_name="test",
            symbol="XYZ",
            side=SignalSide.BUY,
            quantity=10,
            reason="test entry",
        )
        self.assertEqual(signal.status.name, "GENERATED")

        monitor.record_execution(signal, 10, 50.0)
        self.assertEqual(signal.status.name, "EXECUTED")
        self.assertEqual(signal.filled_quantity, 10)

        dist = monitor.get_signal_distribution()
        self.assertEqual(dist.total_signals, 1)
        self.assertEqual(dist.buy_signals, 1)
        self.assertEqual(dist.sell_signals_count, 0)
        self.assertEqual(dist.execution_rate, 1.0)

    def test_session_view_updates_and_summary(self):
        session = SessionView(date.today())
        session.initialize_session(50000.0)
        session.record_signal(executed=True)
        session.record_trade_result(True)
        session.record_trade_result(False)
        session.flag_quality_issue("overtrading")
        session.add_daily_note("test note")

        snapshot = session.get_session_snapshot(MarketSessionState.OPEN)
        self.assertEqual(snapshot.signals_generated, 1)
        self.assertEqual(snapshot.signals_executed, 1)
        self.assertEqual(snapshot.winning_trades, 1)
        self.assertEqual(snapshot.losing_trades, 1)
        self.assertIn("overtrading", snapshot.has_quality_issues)

        summary = session.generate_end_of_day_summary()
        self.assertIn("DAILY SESSION REVIEW", summary)
        self.assertIn("test note", summary)

    def test_live_dashboard_aggregates_views(self):
        dashboard = LiveDashboard(100000.0)
        dashboard.set_market_state(MarketSessionState.OPEN)
        dashboard.record_equity_update(100200.0)
        dashboard.record_position_update(
            symbol="ABC",
            quantity=50,
            entry_price=200.0,
            current_price=202.0,
            entry_time=datetime.now() - timedelta(minutes=10),
        )
        dashboard.record_signal(
            strategy_name="test",
            symbol="ABC",
            side=SignalSide.BUY,
            quantity=50,
            reason="initial",
            executed=True,
        )
        dashboard.record_signal_execution("ABC", 50, 202.0)
        dashboard.record_trade_result(True)

        snapshot = dashboard.get_dashboard_snapshot()
        self.assertEqual(snapshot.session_snapshot.market_state, MarketSessionState.OPEN)
        self.assertGreaterEqual(snapshot.equity_snapshot.current_equity, 100000.0)
        self.assertGreaterEqual(snapshot.portfolio_exposure.open_positions_count, 1)
        self.assertGreaterEqual(snapshot.signal_distribution.total_signals, 1)
        self.assertGreaterEqual(snapshot.operational_health_score, 0)

        output = dashboard.print_dashboard()
        self.assertIn("LIVE DASHBOARD", output)


if __name__ == "__main__":
    unittest.main()
