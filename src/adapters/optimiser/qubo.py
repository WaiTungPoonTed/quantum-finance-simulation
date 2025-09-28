from functools import lru_cache
from typing import Optional

import numpy as np
import pandas as pd
from docplex.mp.model import Model
from qiskit.primitives import Sampler
from qiskit_optimization.algorithms import GroverOptimizer
from qiskit_optimization.algorithms.optimization_algorithm import (
    OptimizationResultStatus,
)
from qiskit_optimization.translators import from_docplex_mp
from use_cases import OptimisePortfolioWeights


class QuboTwoAssetsOptimiser(OptimisePortfolioWeights):
    """
    QUBO Problem for two assets optimiastion
    """

    def __init__(
        self,
        data: pd.DataFrame,
        risk_free_rate: float,
        n_qubits: int = 4,
        scale: int = 1000,
        grover_iteration: int = 5,
        mu: float | int = 1,
        value_qubits: Optional[int] = None,  # The number of qubits to encode the result
    ):
        super().__init__()
        self.data = data
        self.risk_free_rate = risk_free_rate
        self.n_qubits = n_qubits
        self.mu = mu
        # approximate the decimal numbers by integers
        self._scale = (
            scale * (2**n_qubits) ** 2
        )  # (2**n_qubits)**2 for the weight normalisation factor
        self.grover_iteration = grover_iteration
        if value_qubits:
            self._value_qubits = value_qubits
        else:
            self._value_qubits = 2**n_qubits

    @property
    @lru_cache(maxsize=None)  # Caches the result after the first computation
    def annual_returns(self) -> np.array:
        """Calculates and returns the expected annual returns for each asset."""
        # annual return and default trade-day = 252
        return np.array(self.data.pct_change().dropna().mean()) * 252

    @property
    @lru_cache(maxsize=None)  # Caches the result after the first computation
    def cov_matrix(self) -> np.array:
        """Calculates and returns the covariance matrix of daily returns."""
        # annual covariance and default trade-day = 252
        return np.array(self.data.pct_change().dropna().cov()) * 252

    def QuadraticProgram(self):
        model = Model()
        """
        Utility := E(r) - mu*Var(r)
        """
        # define integer variables in 0..2^n -1 instead of binary_var
        x0 = model.integer_var(lb=0, ub=2**self.n_qubits - 1, name="x0")
        sigma_1 = self.cov_matrix[0][0]
        sigma_2 = self.cov_matrix[1][1]
        cov_12 = self.cov_matrix[0][1]
        ret_1 = self.annual_returns[0]
        ret_2 = self.annual_returns[1]

        a: float = -self.mu * (sigma_1**2 - 2 * cov_12 + sigma_2**2)
        b: float = ret_1 - ret_2 - self.mu * (2 * cov_12 - 2 * sigma_2**2)
        c: float = ret_2 - self.mu * sigma_2**2

        # rescale and take the integer parts
        A: int = int(self._scale * a / (2**self.n_qubits - 1) ** 2)
        B: int = int(self._scale * b / (2**self.n_qubits - 1))
        C: int = int(self._scale * c)
        # Maximise the utility: E(r) - mu*Var(r)
        model.maximize((A * x0**2 + B * x0 + C))
        qp = from_docplex_mp(model)

        """Uses Grover Adaptive Search (GAS) to find the minimum of a QUBO function."""
        grover_optimizer = GroverOptimizer(
            self._value_qubits, num_iterations=self.grover_iteration, sampler=Sampler()
        )
        results = grover_optimizer.solve(qp)
        return results

    def optimise(self) -> tuple[float]:
        result = self.QuadraticProgram()
        if OptimizationResultStatus.SUCCESS != result.status:
            print(result.status)
        w1 = result.x
        weight_1 = w1 / (2**self.n_qubits - 1)
        weight_2 = 1 - weight_1
        return (weight_1, weight_2)
