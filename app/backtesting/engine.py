from __future__ import annotations

import pandas as pd

from app.config.settings import BacktestSettings
from app.strategies.base_strategy import BaseStrategy
from .metrics import PerformanceMetrics
from .portfolio import Portfolio
from .trade import Trade


class BacktestResult:
    def __init__(self, trades: list[Trade], equity_curve: pd.DataFrame, metrics: dict[str, float]) -> None:
        self.trades = trades
        self.equity_curve = equity_curve
        self.metrics = metrics


class BacktestEngine:
    def __init__(self, settings: BacktestSettings | None = None) -> None:
        self.settings = settings or BacktestSettings.from_env()

    def run(self, strategy: BaseStrategy, market_data: pd.DataFrame) -> BacktestResult:
        prepared_data = strategy.prepare_data(market_data)
        raw_signals = strategy.generate_signals(prepared_data)
        validated_signals = strategy.validate_signals(raw_signals)
        sized_signals = strategy.position_size(
            validated_signals,
            balance=self.settings.starting_capital,
            risk_per_trade=self.settings.risk_per_trade,
        )
        stop_data = strategy.stop_loss(validated_signals, prepared_data)
        profit_data = strategy.take_profit(validated_signals, prepared_data)

        portfolio = Portfolio(
            starting_capital=self.settings.starting_capital,
            commission_per_trade=self.settings.commission_per_trade,
            slippage_pct=self.settings.slippage_pct,
        )

        for current_dt, row in market_data.iterrows():
            close_price = float(row["close"])
            signal = int(validated_signals.loc[current_dt, "signal"]) if current_dt in validated_signals.index else 0
            size = int(sized_signals.loc[current_dt, "position_size"]) if current_dt in sized_signals.index else 0
            stop_loss = float(stop_data.loc[current_dt, "stop_loss"]) if current_dt in stop_data.index and pd.notna(stop_data.loc[current_dt, "stop_loss"]) else None
            take_profit = float(profit_data.loc[current_dt, "take_profit"]) if current_dt in profit_data.index and pd.notna(profit_data.loc[current_dt, "take_profit"]) else None

            if portfolio.has_open_position():
                current_trade = portfolio.open_trade
                if current_trade is not None:
                    if current_trade.stop_loss is not None and close_price <= current_trade.stop_loss:
                        portfolio.close_position(exit_dt=current_dt, exit_price=close_price)
                    elif current_trade.take_profit is not None and close_price >= current_trade.take_profit:
                        portfolio.close_position(exit_dt=current_dt, exit_price=close_price)
                    elif signal == -1:
                        portfolio.close_position(exit_dt=current_dt, exit_price=close_price)

            if not portfolio.has_open_position() and signal == 1 and size > 0:
                portfolio.open_position(
                    entry_dt=current_dt,
                    entry_price=close_price,
                    quantity=size,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )

            portfolio.record_equity(current_dt, close_price)

        if portfolio.has_open_position() and portfolio.open_trade is not None:
            last_price = float(market_data.iloc[-1]["close"])
            portfolio.close_position(exit_dt=market_data.index[-1], exit_price=last_price)
            if portfolio.equity_history and portfolio.equity_history[-1]["date"] == market_data.index[-1]:
                portfolio.equity_history.pop()
            portfolio.record_equity(market_data.index[-1], last_price)

        equity_curve = portfolio.to_equity_curve()
        metrics = PerformanceMetrics.calculate(equity_curve, portfolio.closed_trades, self.settings.starting_capital)
        return BacktestResult(trades=portfolio.closed_trades, equity_curve=equity_curve, metrics=metrics)
