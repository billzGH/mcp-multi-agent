"""Tests for spike/engineer-agent/server.py."""

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_engineer(engineer_mod, csv_path: Path):
    """Patch DATA_FILE on the module so it reads from our temp CSV."""
    engineer_mod.DATA_FILE = csv_path
    return engineer_mod


# ---------------------------------------------------------------------------
# load_sales_data
# ---------------------------------------------------------------------------


def test_load_sales_data_returns_rows(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    data = mod.load_sales_data()
    assert len(data) == 5


def test_load_sales_data_missing_file(engineer_mod, tmp_path):
    engineer_mod.DATA_FILE = tmp_path / "nonexistent.csv"
    with pytest.raises(FileNotFoundError):
        engineer_mod.load_sales_data()


# ---------------------------------------------------------------------------
# index_by_transaction
# ---------------------------------------------------------------------------


def test_index_by_transaction_keys(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    data = mod.load_sales_data()
    index = mod.index_by_transaction(data)
    assert "T00001" in index
    assert "T00004" in index
    assert len(index) == 5


def test_index_by_transaction_values(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    data = mod.load_sales_data()
    index = mod.index_by_transaction(data)
    assert index["T00004"]["discount"] == "0.65"


# ---------------------------------------------------------------------------
# index_by_customer
# ---------------------------------------------------------------------------


def test_index_by_customer_groups_correctly(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    data = mod.load_sales_data()
    index = mod.index_by_customer(data)
    # C0001 has T00001 and T00003
    assert len(index["C0001"]) == 2


# ---------------------------------------------------------------------------
# call_tool — get_transaction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_transaction_found(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    result = await mod.call_tool("get_transaction", {"transaction_id": "T00001"})
    text = result[0].text
    assert "T00001" in text
    assert "C0001" in text


@pytest.mark.asyncio
async def test_get_transaction_not_found(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    result = await mod.call_tool("get_transaction", {"transaction_id": "TXXX"})
    assert "not found" in result[0].text.lower()


# ---------------------------------------------------------------------------
# call_tool — investigate_anomaly
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_investigate_anomaly_high_discount(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    result = await mod.call_tool(
        "investigate_anomaly",
        {"transaction_id": "T00004", "anomaly_type": "high_discount"},
    )
    text = result[0].text
    assert "high_discount" in text
    assert "T00004" in text
    assert "Likely cause" in text


@pytest.mark.asyncio
async def test_investigate_anomaly_high_quantity(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    result = await mod.call_tool(
        "investigate_anomaly",
        {"transaction_id": "T00005", "anomaly_type": "high_quantity"},
    )
    text = result[0].text
    assert "high_quantity" in text
    assert "T00005" in text
    # May show "Likely cause" or "No cohort data" depending on sample — both are valid
    assert "get_customer_history" in text


@pytest.mark.asyncio
async def test_investigate_anomaly_not_found(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    result = await mod.call_tool(
        "investigate_anomaly",
        {"transaction_id": "TXXX", "anomaly_type": "high_revenue"},
    )
    assert "not found" in result[0].text.lower()


@pytest.mark.asyncio
async def test_investigate_anomaly_recommends_customer_history(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    result = await mod.call_tool(
        "investigate_anomaly",
        {"transaction_id": "T00004", "anomaly_type": "high_discount"},
    )
    assert "get_customer_history" in result[0].text


# ---------------------------------------------------------------------------
# call_tool — get_customer_history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_customer_history_found(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    result = await mod.call_tool("get_customer_history", {"customer_id": "C0001"})
    text = result[0].text
    assert "C0001" in text
    assert "Total transactions: 2" in text


@pytest.mark.asyncio
async def test_get_customer_history_not_found(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    result = await mod.call_tool("get_customer_history", {"customer_id": "CXXXX"})
    assert "no transactions" in result[0].text.lower()


@pytest.mark.asyncio
async def test_get_customer_history_includes_spend(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    result = await mod.call_tool("get_customer_history", {"customer_id": "C0001"})
    text = result[0].text
    assert "Total spend" in text
    assert "Average order" in text


# ---------------------------------------------------------------------------
# call_tool — unknown tool
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_call_tool_unknown(engineer_mod, sample_csv):
    mod = make_engineer(engineer_mod, sample_csv)
    result = await mod.call_tool("nonexistent_tool", {})
    assert "Error" in result[0].text