import numpy as np

def SharpeRatio(
    weights: np.ndarray, 
    asset_returns: np.ndarray, 
    covariance_matrix: np.ndarray, 
    risk_free_rate: float,
) -> float:
    """
    Calculates the Sharpe Ratio for a given portfolio.
    We use 252 trade-day convention
    Args:
        weights (np.ndarray): A 1D numpy array of portfolio weights for each asset.
                              Must sum to 1.0.
        asset_returns (np.ndarray): A 1D numpy array of expected returns for each asset (average daily return)
        covariance_matrix (np.ndarray): A 2D numpy array (NxN) representing the covariance
                                        matrix of the assets.
        risk_free_rate (float): The risk-free rate (annual rate)

    Returns:
        float: The calculated Sharpe Ratio
    """
    # Ensure inputs are numpy arrays for consistent operations
    weights = np.asarray(weights)
    asset_returns = np.asarray(asset_returns)

    # Annualise asset returns (from average daily to annual)
    # Assuming 252 trading days for annualization
    annualised_asset_returns = asset_returns * 252
    
    # Calculate annualised portfolio return
    portfolio_return_annual = np.dot(annualised_asset_returns, weights)
    portfolio_variance_daily = np.dot(weights.T, np.dot(covariance_matrix, weights))

    # annualise the volatility
    portfolio_volatility_annual = np.sqrt(portfolio_variance_daily) * np.sqrt(252)
    excess_return_annual = portfolio_return_annual - risk_free_rate

    sharpe_ratio = excess_return_annual / portfolio_volatility_annual
    return sharpe_ratio