from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd


@dataclass
class PriceUpdate:
    symbol: str
    timestamp: pd.Timestamp
    open_price: float
    high: float
    low: float
    close: float
    volume: int


class LiveFeed:
    def __init__(self) -> None:
        self.subscriptions: dict[str, list[Callable[[PriceUpdate], None]]] = {}
        self.price_history: list[PriceUpdate] = []

    def subscribe(self, symbol: str, callback: Callable[[PriceUpdate], None]) -> None:
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = []
        self.subscriptions[symbol].append(callback)

    def unsubscribe(self, symbol: str, callback: Callable[[PriceUpdate], None]) -> None:
        if symbol in self.subscriptions:
            self.subscriptions[symbol] = [cb for cb in self.subscriptions[symbol] if cb != callback]

    def publish_update(self, update: PriceUpdate) -> None:
        self.price_history.append(update)
        if update.symbol in self.subscriptions:
            for callback in self.subscriptions[update.symbol]:
                callback(update)

    def simulate_from_dataframe(
        self,
        market_data: pd.DataFrame,
        symbol: str = "NIFTY",
        speed: float = 1.0,
    ) -> None:
        for idx, (timestamp, row) in enumerate(market_data.iterrows()):
            update = PriceUpdate(
                symbol=symbol,
                timestamp=pd.Timestamp(timestamp),
                open_price=float(row.get("open", row["close"])),
                high=float(row.get("high", row["close"])),
                low=float(row.get("low", row["close"])),
                close=float(row["close"]),
                volume=int(row.get("volume", 0)),
            )
            self.publish_update(update)

    def get_latest_price(self, symbol: str) -> float | None:
        for update in reversed(self.price_history):
            if update.symbol == symbol:
                return update.close
        return None

    def get_price_history(self, symbol: str, limit: int = 100) -> list[PriceUpdate]:
        return [update for update in self.price_history[-limit:] if update.symbol == symbol]

    def summary(self) -> dict[str, object]:
        subscribed_symbols = list(self.subscriptions.keys())
        latest_prices: dict[str, float | None] = {}
        for symbol in subscribed_symbols:
            latest_prices[symbol] = self.get_latest_price(symbol)
        return {
            "subscribed_symbols": subscribed_symbols,
            "subscription_count": len(subscribed_symbols),
            "price_update_count": len(self.price_history),
            "latest_prices": latest_prices,
        }
