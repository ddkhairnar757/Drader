from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_equity_curve(
    equity_curve: pd.DataFrame,
    title: str = "Equity Curve",
    save_path: Path | str | None = None,
    show: bool = False,
) -> matplotlib.figure.Figure:
    if equity_curve.empty:
        raise ValueError("Equity curve data cannot be empty.")
    if "equity" not in equity_curve.columns:
        raise ValueError("Equity curve must contain an 'equity' column.")

    fig, ax = plt.subplots(figsize=(10, 5))
    equity_curve = equity_curve.sort_index()
    ax.plot(equity_curve.index, equity_curve["equity"], label="Equity", color="#1f77b4")
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity")
    ax.grid(True, alpha=0.3)
    ax.legend()

    drawdown = equity_curve["equity"] / equity_curve["equity"].cummax() - 1.0
    ax2 = ax.twinx()
    ax2.fill_between(
        equity_curve.index,
        drawdown,
        0,
        color="#ff7f0e",
        alpha=0.2,
        label="Drawdown",
    )
    ax2.set_ylabel("Drawdown")
    ax2.set_ylim(min(drawdown.min(), -0.05), 0.05)
    ax2.legend(loc="upper left")

    fig.tight_layout()
    if save_path is not None:
        fig.savefig(Path(save_path), dpi=150)
    if show:
        plt.show()
    plt.close(fig)
    return fig
