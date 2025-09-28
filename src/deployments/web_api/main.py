from entities.assets import Assets, Portfolio
from fastapi import FastAPI
from deployments.handler.app import handle_optimise_portfolio


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
    # FastAPI automatically validates the incoming request body against the Assets model.
    # If the data is invalid, FastAPI will automatically return a 422 Unprocessable Entity error.

    # print("--- FastAPI Service ---")
    # print(f"Received valid assets payload: {payload}", type(payload))

    # # --- MOCK LOGIC ---
    # # In the future, this is where you will call your use_cases and adapters.
    # # For now, we return a hardcoded JSON response.
    # mock_response = {
    #     "message": "Data processed successfully by the REAL FastAPI service",
    #     "input_parameters": payload,
    #     "optimised_weights": {
    #         "assets.tickers[0]": 0.55,  # Use different numbers to prove it's from Python
    #         "assets.tickers[1]": 0.45,
    #     },
    #     "expected_return": 0.28,
    #     "expected_risk": 0.15,
    # }

    # print("Sending mock response from FastAPI.")
    
    print("--- FastAPI Service ---")
    print(f"Received valid assets payload: {payload}", type(payload))
    mock_response: Portfolio = handle_optimise_portfolio(payload)
    print("Sending response from FastAPI.")
    # print(f'Response: {mock_response}')
    return mock_response
