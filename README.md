# quantum-finance-simulation

```bash
.
├── LICENSE
├── README.md
├── environment.yml
├── requirements.txt
└── src
    ├── adapters
    │   ├── __init__.py
    │   ├── execute_quantum_algorithm
    │   │   └── grover_search.py
    │   ├── fetch_stocks_data
    │   │   └── yfinance.py
    │   └── optimiser
    │       └── qubo.py
    ├── data
    │   └── df.pkl
    ├── deployments
    │   └── web_api
    │       └── main.py
    ├── entities
    │   ├── __init__.py
    │   ├── assets.py
    │   └── grover.py
    ├── playground.ipynb
    ├── use_cases
    │   ├── __init__.py
    │   ├── execute_grover_search.py
    │   ├── fetch_data.py
    │   └── optimiser.py
    └── utils
        ├── __pycache__
        │   └── finance.cpython-312.pyc
        ├── finance.py
        └── quantum_tools.py
```

go to the path `./quantum-finance-simulation/src`. Then run

```bash
uvicorn deployments.web_api.main:app
```

to open the backend FastAPI server
