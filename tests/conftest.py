"""
Shared fixtures for the mcp-multi-agent test suite.

Each spike server lives in spike/<name>/server.py and is not a proper package,
so we load them via importlib with unique module names to avoid conflicts.
"""

import csv
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


def load_spike_module(agent_name: str, alias: str):
    """Load spike/<agent_name>/server.py as a uniquely named module."""
    path = REPO_ROOT / "spike" / agent_name / "server.py"
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Module fixtures (session-scoped — loaded once per test run)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def monitor_mod():
    return load_spike_module("monitor-agent", "monitor_agent_server")


@pytest.fixture(scope="session")
def engineer_mod():
    return load_spike_module("engineer-agent", "engineer_agent_server")


# ---------------------------------------------------------------------------
# Data fixtures
# ---------------------------------------------------------------------------

SAMPLE_ROWS = [
    {
        "transaction_id": "T00001",
        "transaction_date": "2024-01-10",
        "customer_id": "C0001",
        "product_id": "P001",
        "quantity": "2",
        "unit_price": "45.00",
        "total_amount": "90.00",
        "discount": "0.10",
        "payment_method": "credit_card",
        "status": "completed",
    },
    {
        "transaction_id": "T00002",
        "transaction_date": "2024-02-14",
        "customer_id": "C0002",
        "product_id": "P001",
        "quantity": "1",
        "unit_price": "49.99",
        "total_amount": "49.99",
        "discount": "0.00",
        "payment_method": "paypal",
        "status": "completed",
    },
    {
        "transaction_id": "T00003",
        "transaction_date": "2024-03-01",
        "customer_id": "C0001",
        "product_id": "P002",
        "quantity": "3",
        "unit_price": "120.00",
        "total_amount": "360.00",
        "discount": "0.05",
        "payment_method": "credit_card",
        "status": "completed",
    },
    # Anomalous: high discount
    {
        "transaction_id": "T00004",
        "transaction_date": "2024-04-20",
        "customer_id": "C0003",
        "product_id": "P001",
        "quantity": "1",
        "unit_price": "17.50",
        "total_amount": "17.50",
        "discount": "0.65",
        "payment_method": "paypal",
        "status": "completed",
    },
    # Anomalous: high quantity
    {
        "transaction_id": "T00005",
        "transaction_date": "2024-05-05",
        "customer_id": "C0004",
        "product_id": "P003",
        "quantity": "75",
        "unit_price": "19.99",
        "total_amount": "1499.25",
        "discount": "0.10",
        "payment_method": "bank_transfer",
        "status": "completed",
    },
]


@pytest.fixture()
def sample_csv(tmp_path: Path) -> Path:
    """Write SAMPLE_ROWS to a temp CSV and return the file path."""
    csv_file = tmp_path / "sales.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(SAMPLE_ROWS[0].keys()))
        writer.writeheader()
        writer.writerows(SAMPLE_ROWS)
    return csv_file