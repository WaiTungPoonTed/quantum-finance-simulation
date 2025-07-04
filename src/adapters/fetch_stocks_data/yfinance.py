from datetime import date

import pandas as pd
import yfinance as yf
from entities import *
from use_cases import FetchStocksData


class YFinanceFetchStockData(FetchStocksData):
    def __init__(self, assets: Assets, price_type: str = "Close"):
        super().__init__()
        self.assets = assets
        self.price_type = price_type
        if not self.assets.end_date:
            self.assets.end_date = date.today().isoformat()  # 'YYYY-MM-DD'

    def fetch(self) -> pd.DataFrame:
        data: pd.DataFrame = yf.download(
            tickers=self.assets.tickers,
            start=self.assets.start_date,  # start date (YYYY-MM-DD)
            end=self.assets.end_date,  # end date (YYYY-MM-DD)
        ).xs(
            self.price_type, axis=1
        )  # slide the column in `price_type`
        return data
