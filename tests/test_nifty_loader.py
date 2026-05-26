import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app.market_data.nifty_loader import HistoricalMarketDataLoader


class TestHistoricalMarketDataLoader(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_rows = [
            "date,open,high,low,close,volume",
            "2025-01-01,19700,19850,19620,19800,240000",
            "2025-01-02,19810,19900,19750,19870,210000",
        ]

    def _write_sample_csv(self, filename: Path) -> None:
        filename.write_text("\n".join(self.sample_rows), encoding="utf-8")

    def test_loads_valid_nifty_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "nifty_sample.csv"
            self._write_sample_csv(source)

            loader = HistoricalMarketDataLoader(source)
            df = loader.load()

            self.assertEqual(len(df), 2)
            self.assertListEqual(list(df.columns), ["open", "high", "low", "close", "volume"])
            self.assertEqual(df.index.name, "date")
            self.assertTrue((df["volume"] > 0).all())

    def test_missing_column_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "nifty_missing.csv"
            source.write_text("date,open,high,low,close\n2025-01-01,19700,19850,19620,19800", encoding="utf-8")

            loader = HistoricalMarketDataLoader(source)
            with self.assertRaises(ValueError):
                loader.load()

    def test_unsorted_dates_raise(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "nifty_unsorted.csv"
            source.write_text(
                "date,open,high,low,close,volume\n2025-01-02,19810,19900,19750,19870,210000\n2025-01-01,19700,19850,19620,19800,240000",
                encoding="utf-8",
            )

            loader = HistoricalMarketDataLoader(source)
            with self.assertRaises(ValueError):
                loader.load()


if __name__ == "__main__":
    unittest.main()
