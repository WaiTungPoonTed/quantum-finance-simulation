from typing import Optional  # Optional is clearer in older Python versions

from pydantic import BaseModel


class Assets(BaseModel):
    tickers: list[str]  # list of tickers of stocks
    start_date: str  # e.g. 2015-07-04
    end_date: Optional[str] = None  # e.g. , 2025-07-04


class Portfolio(BaseModel):
    tickers: list[str]
    weights: list[float]  # weights of each asset, sum to one
