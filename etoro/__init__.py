"""eToro API client package."""

from .client import ETPublicClient, EToroClientError, get_public_client_from_env
from .models import (
    EToroAggregatedPosition,
    EToroGainHistory,
    EToroGainPoint,
    EToroInvestorPortfolio,
    EToroPortfolioPosition,
    EToroSocialTrade,
    EToroTradeHistory,
    EToroTradeRecord,
    EToroUser,
    EToroUserLookupResult,
)

__all__ = [
    "ETPublicClient",
    "get_public_client_from_env",
    "EToroClientError",
    "EToroAggregatedPosition",
    "EToroGainHistory",
    "EToroGainPoint",
    "EToroInvestorPortfolio",
    "EToroPortfolioPosition",
    "EToroSocialTrade",
    "EToroTradeHistory",
    "EToroTradeRecord",
    "EToroUser",
    "EToroUserLookupResult",
]
