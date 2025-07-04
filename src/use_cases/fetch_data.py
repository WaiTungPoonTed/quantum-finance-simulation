from abc import ABC, abstractmethod

import pandas as pd


class FetchStocksData(ABC):
    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        """fetch price data of underlying assets"""
        ...
