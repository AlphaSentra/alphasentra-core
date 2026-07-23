from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class InvestorSearchResult:
    items: list[dict]
    totalItems: Optional[int] = None


@dataclass
class InvestorProfile:
    userName: str
    displayName: Optional[str] = None
    fullName: Optional[str] = None
    copiersGain: Optional[float] = None
    gain: Optional[float] = None
    aumValue: Optional[float] = None
    copiers: Optional[int] = None
    riskScore: Optional[float] = None
    weeklyGain: Optional[float] = None
