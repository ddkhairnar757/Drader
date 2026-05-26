from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd

from .trade import Trade


class PerformanceMetrics:
    @staticmethod
    def calculate(
        equity_curve: pd.DataFrame,
        trades: Iterable[Trade],
        starting_capital: float,
    ) -> dict[str, float]:
        if equity_curve.empty:
            raise ValueError("Equity curve must contain at least one point.")

        returns = equity_curve["equity"].pct_change().fillna(0.0)
        total_return = float(equity_curve["equity"].iloc[-1] / starting_capital - 1.0)
        cumulative_max = equity_curve["equity"].cummax()
        drawdown = (equity_curve["equity"] - cumulative_max) / cumulative_max
        max_drawdown = float(drawdown.min())

        trade_list = [trade for trade in trades if trade.realized_pnl is not None]
        wins = [trade.realized_pnl for trade in trade_list if trade.realized_pnl and trade.realized_pnl > 0]
        losses = [-trade.realized_pnl for trade in trade_list if trade.realized_pnl and trade.realized_pnl < 0]

        win_rate = float(len(wins) / len(trade_list)) if trade_list else 0.0
        gross_profit = float(sum(wins))
        gross_loss = float(sum(losses))
        profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)
        average_trade = float(sum(trade.realized_pnl for trade in trade_list) / len(trade_list)) if trade_list else 0.0

        volatility = float(returns.std(ddof=0))
        annualized_return = float((1.0 + total_return) ** (252.0 / max(len(equity_curve), 1)) - 1.0)
        sharpe_ratio = float((returns.mean() / volatility) * math.sqrt(252.0)) if volatility > 0 else 0.0

        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "average_trade": average_trade,
            "sharpe_ratio": sharpe_ratio,
            "trade_count": float(len(trade_list)),
        }
