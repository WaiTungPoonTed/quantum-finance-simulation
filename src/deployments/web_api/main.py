from deployments.handler.app import handle_optimise_portfolio
from entities.assets import Assets, Portfolio
from fastapi import FastAPI

# Create an instance of the FastAPI application
app = FastAPI(
    title="Quantum Portfolio Optimiser API",
    description="An API for running quantum portfolio optimisation tasks.",
    version="0.1.0",
)


# A simple "health check" endpoint at the root URL
@app.get("/")
def read_root():
    """Returns the status of the API."""
    return {"status": "FastAPI server is running."}


# This is our main optimisation endpoint
@app.post("/optimise")
def optimise_portfolio(payload: Assets):
    """
    Accepts a list of assets and optimisation parameters,
    and will eventually return the optimised portfolio weights.
    """
    print("--- FastAPI Service ---")
    print(f"Received valid assets payload: {payload}", type(payload))
    mock_response: Portfolio = handle_optimise_portfolio(payload)
    print("Sending response from FastAPI.")
    # print(f'Response: {mock_response}')
    return mock_response
