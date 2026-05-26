from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

REQUIRED_COLUMN_LIST = ["open", "high", "low", "close", "volume"]
REQUIRED_COLUMNS = set(REQUIRED_COLUMN_LIST)
COLUMN_SYNONYMS = {
    "o": "open",
    "h": "high",
    "l": "low",
    "c": "close",
    "v": "volume",
    "timestamp": "date",
    "date": "date",
}


class HistoricalMarketDataLoader:
    """Load and validate historical NIFTY market data from local CSV sources."""

    def __init__(self, source: Path | str, symbol: str = "NIFTY", exchange: str = "NSE") -> None:
        self.source = Path(source)
        self.symbol = symbol
        self.exchange = exchange

    def load(self) -> pd.DataFrame:
        """Load the historical market data and return a cleaned OHLCV DataFrame."""
        df = self._load_csv()
        df = self._normalize_columns(df)
        self._validate_dataframe(df)
        return df

    def _load_csv(self) -> pd.DataFrame:
        if not self.source.exists():
            raise FileNotFoundError(f"Market data file not found: {self.source}")

        df = pd.read_csv(self.source)
        if df.empty:
            raise ValueError(f"Market data file is empty: {self.source}")

        df = self._ensure_date_index(df)
        return df

    def _ensure_date_index(self, df: pd.DataFrame) -> pd.DataFrame:
        raw_columns = {col.lower(): col for col in df.columns}
        if "date" in raw_columns:
            df = df.rename(columns={raw_columns["date"]: "date"})
        elif "timestamp" in raw_columns:
            df = df.rename(columns={raw_columns["timestamp"]: "date"})
        else:
            first_col = df.columns[0]
            df = df.rename(columns={first_col: "date"})

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if df["date"].isna().any():
            raise ValueError("Date column contains invalid or missing values.")

        df = df.set_index("date")
        return df

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        mapping = {
            original: COLUMN_SYNONYMS.get(original.lower(), original.lower())
            for original in df.columns
        }
        df = df.rename(columns=mapping)

        for source, target in COLUMN_SYNONYMS.items():
            if source in df.columns and target not in df.columns:
                df = df.rename(columns={source: target})

        missing_columns = REQUIRED_COLUMNS - set(df.columns)
        if missing_columns:
            raise ValueError(
                f"Missing required OHLCV columns: {sorted(missing_columns)}. "
                "Expected open, high, low, close, volume."
            )

        df = df[REQUIRED_COLUMN_LIST]
        return df

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        if df.index.hasnans:
            raise ValueError("Datetime index contains missing values.")

        if df.index.duplicated().any():
            raise ValueError("Datetime index contains duplicate rows.")

        if not df.index.is_monotonic_increasing:
            raise ValueError("Market data must be sorted by ascending date/time.")

        if df[list(REQUIRED_COLUMNS)].isna().any().any():
            raise ValueError("Market data contains missing values in OHLCV columns.")

        for column in REQUIRED_COLUMNS:
            if not pd.api.types.is_numeric_dtype(df[column]):
                df[column] = pd.to_numeric(df[column], errors="coerce")

        if df[list(REQUIRED_COLUMNS)].isna().any().any():
            raise ValueError("Market data contains non-numeric values in OHLCV columns.")

    @classmethod
    def from_csv(cls, source: Path | str, symbol: str = "NIFTY", exchange: str = "NSE") -> pd.DataFrame:
        """Create a loader and return the loaded OHLCV DataFrame."""
        return cls(source=source, symbol=symbol, exchange=exchange).load()
