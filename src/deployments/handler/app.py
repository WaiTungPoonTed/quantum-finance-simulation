import numpy as np
import pandas as pd
from adapters import QuboTwoAssetsOptimiser, YFinanceFetchStockData
from entities import Assets, Portfolio


def handle_optimise_portfolio(payload: Assets) -> dict:
    """
    Accepts a list of assets and optimisation parameters,
    and will eventually return the optimised portfolio weights.
    """
    print("--- FastAPI Service ---")
    print(f"Received valid assets payload: {payload}", type(payload))

    # --- Fetch Data ---
    assets = YFinanceFetchStockData(payload)
    stock_data = assets.fetch()
    print(f"Fetched stock data: {stock_data}")

    qubo_two_assets_optimiser = QuboTwoAssetsOptimiser(
        data=stock_data,
        risk_free_rate=0,
        grover_iteration=2,
        mu=1,
        value_qubits=13,
        n_qubits=4,
    )

    # --- Optimise Portfolio ---
    optimised_portfolio = qubo_two_assets_optimiser.optimise()
    print(f"Optimised portfolio: {optimised_portfolio}")

    weights: list[np.float] = [stock[0] for stock in optimised_portfolio]

    portfolio = stock_data.pct_change() * np.array(weights)
    # first day fill NaN with 0
    portfolio = portfolio.fillna(0).sum(axis=1)

    ret = stock_data.pct_change().fillna(0)
    ret["Quantum_Portfolio"] = portfolio
    # Convert into price
    df = (1 + ret).cumprod()
    mock_response = {
        "portfolio": Portfolio(
            tickers=payload.tickers,
            weights=weights,  # Use different numbers to prove it's from Python
        ),
        "stock_data": df.to_dict(),
    }
    print("Sending mock response from FastAPI.")
    return mock_response
