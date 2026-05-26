from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from app.backtesting.trade import Trade


@dataclass
class MonteCarloResult:
    simulation_index: int
    total_return: float
    max_drawdown: float


class MonteCarloSimulator:
    def __init__(self, seed: int | None = None) -> None:
        self.random_state = np.random.default_rng(seed)

    @staticmethod
    def _max_drawdown(equity_curve: np.ndarray) -> float:
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak
        return float(np.min(drawdown))

    def simulate(
        self,
        trades: Iterable[Trade],
        starting_capital: float = 100_000.0,
        n_simulations: int = 500,
    ) -> list[MonteCarloResult]:
        trade_pnls = np.array([trade.realized_pnl for trade in trades], dtype=float)
        if trade_pnls.size == 0:
            raise ValueError("Monte Carlo simulation requires at least one closed trade")

        results: list[MonteCarloResult] = []
        for idx in range(n_simulations):
            sampled = self.random_state.choice(trade_pnls, size=trade_pnls.size, replace=True)
            equity_curve = starting_capital + np.cumsum(sampled)
            total_return = float(equity_curve[-1] / starting_capital - 1.0)
            max_drawdown = self._max_drawdown(equity_curve)
            results.append(MonteCarloResult(idx, total_return, max_drawdown))
        return results
