from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd


class BaseDataProvider(ABC):
    @abstractmethod
    def get_price(self, ticker: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        pass

    @abstractmethod
    def get_latest_price(self, ticker: str) -> Optional[float]:
        pass

    @abstractmethod
    def get_info(self, ticker: str) -> dict:
        pass

    @abstractmethod
    def get_history(self, ticker: str, period: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_financials(self, ticker: str) -> Optional[pd.DataFrame]:
        pass

    @abstractmethod
    def get_quarterly_financials(self, ticker: str) -> Optional[pd.DataFrame]:
        pass

    @abstractmethod
    def get_balance_sheet(self, ticker: str, quarterly: bool = False) -> Optional[pd.DataFrame]:
        pass

    @abstractmethod
    def get_cashflow(self, ticker: str, quarterly: bool = False) -> Optional[pd.DataFrame]:
        pass

    @abstractmethod
    def get_dividends(self, ticker: str, period: Optional[str] = None) -> Optional[pd.Series]:
        pass

    @abstractmethod
    def ticker_exists(self, ticker: str) -> bool:
        pass
