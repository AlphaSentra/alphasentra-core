"""YFinance data provider adapter.

Maps BaseDataProvider interface to yfinance calls.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from data.provider_factory import register
from data.provider_interface import BaseDataProvider

try:
    import yfinance as yf
except ModuleNotFoundError as exc:
    raise RuntimeError("yfinance is required for the default data provider") from exc

logger = logging.getLogger(__name__)


@register("yfinance")
class YFinanceProvider(BaseDataProvider):
    """Default data provider backed by Yahoo Finance via yfinance."""

    def _ticker(self, symbol: str) -> yf.Ticker:
        """Return a yfinance Ticker instance for the given symbol."""
        return yf.Ticker(symbol)

    def get_price(self, ticker: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        """Fetch OHLCV data for a date range."""
        try:
            return yf.download(
                ticker,
                start=start,
                end=end,
                interval=interval,
                progress=False,
                multi_level_index=False,
                auto_adjust=False,
            )
        except Exception as exc:
            logger.debug("get_price failed for %s: %s", ticker, exc)
            return pd.DataFrame()

    def get_latest_price(self, ticker: str) -> Optional[float]:
        """Return the latest closing price for a ticker."""
        try:
            hist = self._ticker(ticker).history(period="1d")
            if not hist.empty:
                return float(hist["Close"].iloc[-1])
            return None
        except Exception as exc:
            logger.debug("latest price failed for %s: %s", ticker, exc)
            return None

    def get_info(self, ticker: str) -> dict:
        """Return the info dict for a ticker."""
        try:
            return self._ticker(ticker).info or {}
        except Exception as exc:
            logger.debug("get_info failed for %s: %s", ticker, exc)
            return {}

    def get_history(self, ticker: str, period: str) -> pd.DataFrame:
        """Return historical OHLCV data for a period string (e.g. '5d', '3mo')."""
        try:
            return self._ticker(ticker).history(period=period)
        except Exception as exc:
            logger.debug("get_history failed for %s: %s", ticker, exc)
            return pd.DataFrame()

    def get_financials(self, ticker: str) -> Optional[pd.DataFrame]:
        """Return annual financials as a DataFrame."""
        try:
            df = self._ticker(ticker).financials
            return df.T if df is not None and not df.empty else None
        except Exception as exc:
            logger.debug("get_financials failed for %s: %s", ticker, exc)
            return None

    def get_quarterly_financials(self, ticker: str) -> Optional[pd.DataFrame]:
        """Return quarterly financials as a DataFrame."""
        try:
            df = self._ticker(ticker).quarterly_financials
            return df.T if df is not None and not df.empty else None
        except Exception as exc:
            logger.debug("get_quarterly_financials failed for %s: %s", ticker, exc)
            return None

    def get_balance_sheet(self, ticker: str, quarterly: bool = False) -> Optional[pd.DataFrame]:
        """Return balance-sheet data, quarterly or annual."""
        try:
            if quarterly:
                return self._ticker(ticker).quarterly_balance_sheet
            return self._ticker(ticker).balance_sheet
        except Exception as exc:
            logger.debug("get_balance_sheet failed for %s: %s", ticker, exc)
            return None

    def get_cashflow(self, ticker: str, quarterly: bool = False) -> Optional[pd.DataFrame]:
        """Return cash-flow data, quarterly or annual."""
        try:
            if quarterly:
                return self._ticker(ticker).quarterly_cashflow
            return self._ticker(ticker).cashflow
        except Exception as exc:
            logger.debug("get_cashflow failed for %s: %s", ticker, exc)
            return None

    def get_dividends(self, ticker: str, period: Optional[str] = None) -> Optional[pd.Series]:
        """Return dividends as a Series. The period arg is accepted for interface compatibility."""
        try:
            series = self._ticker(ticker).dividends
            return series if series is not None and not series.empty else None
        except Exception as exc:
            logger.debug("get_dividends failed for %s: %s", ticker, exc)
            return None

    def ticker_exists(self, ticker: str) -> bool:
        """Return True if the ticker symbol is valid and resolvable."""
        try:
            info = self._ticker(ticker).info or {}
            return bool(info.get("symbol") == ticker)
        except Exception as exc:
            logger.debug("ticker_exists failed for %s: %s", ticker, exc)
            return False
