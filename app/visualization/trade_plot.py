from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from app.backtesting.trade import Trade


def plot_trade_signals(
    market_data: pd.DataFrame,
    trades: list[Trade],
    title: str = "Trade Signals",
    save_path: Path | str | None = None,
    show: bool = False,
) -> matplotlib.figure.Figure:
    if market_data.empty:
        raise ValueError("Market data cannot be empty.")
    if "close" not in market_data.columns:
        raise ValueError("Market data must contain a 'close' column.")

    fig, ax = plt.subplots(figsize=(12, 6))
    market_data = market_data.sort_index()
    ax.plot(market_data.index, market_data["close"], color="#2ca02c", label="Close Price")

    for trade in trades:
        ax.scatter(trade.entry_dt, trade.entry_price, marker="^", color="#2ca02c", s=80, label="Entry" if trade == trades[0] else "")
        if trade.exit_dt is not None and trade.exit_price is not None:
            ax.scatter(trade.exit_dt, trade.exit_price, marker="v", color="#d62728", s=80, label="Exit" if trade == trades[0] else "")
        if trade.stop_loss is not None and trade.exit_dt is not None:
            ax.hlines(trade.stop_loss, trade.entry_dt, trade.exit_dt, color="#ff7f0e", linestyle="--", linewidth=1, label="Stop Loss" if trade == trades[0] else "")
        if trade.take_profit is not None and trade.exit_dt is not None:
            ax.hlines(trade.take_profit, trade.entry_dt, trade.exit_dt, color="#9467bd", linestyle="--", linewidth=1, label="Take Profit" if trade == trades[0] else "")

    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    fig.tight_layout()
    if save_path is not None:
        fig.savefig(Path(save_path), dpi=150)
    if show:
        plt.show()
    plt.close(fig)
    return fig
