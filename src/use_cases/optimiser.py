from abc import ABC, abstractmethod

from entities import Portfolio


class OptimisePortfolioWeights(ABC):
    @abstractmethod
    def optimise(self) -> Portfolio:
        """find the optimal weights of underlying assets"""
        ...
