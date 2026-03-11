"""Tests for spike/monitor-agent/server.py."""

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_monitor(monitor_mod, csv_path: Path):
    """Patch DATA_FILE on the module so it reads from our temp CSV."""
    monitor_mod.DATA_FILE = csv_path
    return monitor_mod


# ---------------------------------------------------------------------------
# load_sales_data
# ---------------------------------------------------------------------------


def test_load_sales_data_returns_rows(monitor_mod, sample_csv):
    mod = make_monitor(monitor_mod, sample_csv)
    data = mod.load_sales_data()
    assert len(data) == 5


def test_load_sales_data_missing_file(monitor_mod, tmp_path):
    monitor_mod.DATA_FILE = tmp_path / "nonexistent.csv"
    with pytest.raises(FileNotFoundError):
        monitor_mod.load_sales_data()


# ---------------------------------------------------------------------------
# detect_anomalies
# ---------------------------------------------------------------------------


def test_detect_anomalies_finds_high_discount(monitor_mod, sample_csv):
    mod = make_monitor(monitor_mod, sample_csv)
    data = mod.load_sales_data()
    anomalies = mod.detect_anomalies(data)
    types = [a["anomaly_type"] for a in anomalies]
    assert "high_discount" in types


def test_detect_anomalies_high_discount_is_critical(monitor_mod, sample_csv):
    mod = make_monitor(monitor_mod, sample_csv)
    data = mod.load_sales_data()
    anomalies = mod.detect_anomalies(data)
    discount_anomaly = next(a for a in anomalies if a["anomaly_type"] == "high_discount")
    assert discount_anomaly["severity"] == "critical"
    assert discount_anomaly["transaction_id"] == "T00004"


def test_detect_anomalies_finds_high_quantity(monitor_mod, sample_csv):
    mod = make_monitor(monitor_mod, sample_csv)
    data = mod.load_sales_data()
    anomalies = mod.detect_anomalies(data)
    types = [a["anomaly_type"] for a in anomalies]
    assert "high_quantity" in types


def test_detect_anomalies_high_quantity_transaction(monitor_mod, sample_csv):
    mod = make_monitor(monitor_mod, sample_csv)
    data = mod.load_sales_data()
    anomalies = mod.detect_anomalies(data)
    qty_anomaly = next(a for a in anomalies if a["anomaly_type"] == "high_quantity")
    assert qty_anomaly["transaction_id"] == "T00005"


def test_detect_anomalies_anomaly_has_required_fields(monitor_mod, sample_csv):
    mod = make_monitor(monitor_mod, sample_csv)
    data = mod.load_sales_data()
    anomalies = mod.detect_anomalies(data)
    assert anomalies, "Expected at least one anomaly in sample data"
    for a in anomalies:
        assert "transaction_id" in a
        assert "anomaly_type" in a
        assert "severity" in a
        assert "value" in a
        assert "context" in a


def test_detect_anomalies_no_anomalies_in_clean_data(monitor_mod, sample_csv, tmp_path):
    """Dataset with all normal transactions should return no anomalies."""
    import csv

    clean_rows = [
        {
            "transaction_id": f"T{i:05d}",
            "transaction_date": "2024-01-01",
            "customer_id": "C0001",
            "product_id": "P001",
            "quantity": "2",
            "unit_price": "50.00",
            "total_amount": "100.00",
            "discount": "0.05",
            "payment_method": "credit_card",
            "status": "completed",
        }
        for i in range(1, 20)
    ]
    clean_file = tmp_path / "clean.csv"
    with open(clean_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(clean_rows[0].keys()))
        writer.writeheader()
        writer.writerows(clean_rows)

    monitor_mod.DATA_FILE = clean_file
    data = monitor_mod.load_sales_data()
    anomalies = monitor_mod.detect_anomalies(data)
    revenue_anomalies = [a for a in anomalies if a["anomaly_type"] == "high_revenue"]
    assert len(revenue_anomalies) == 0


# ---------------------------------------------------------------------------
# get_metric_stats (via call_tool)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_call_tool_get_metric_stats(monitor_mod, sample_csv):
    mod = make_monitor(monitor_mod, sample_csv)
    result = await mod.call_tool("get_metric_stats", {"metric": "total_amount"})
    assert len(result) == 1
    text = result[0].text
    assert "Mean" in text
    assert "Stdev" in text


@pytest.mark.asyncio
async def test_call_tool_check_data_health(monitor_mod, sample_csv):
    mod = make_monitor(monitor_mod, sample_csv)
    result = await mod.call_tool("check_data_health", {})
    text = result[0].text
    assert "Transactions analysed" in text
    assert "Anomalies detected" in text


@pytest.mark.asyncio
async def test_call_tool_list_anomalies(monitor_mod, sample_csv):
    mod = make_monitor(monitor_mod, sample_csv)
    result = await mod.call_tool("list_anomalies", {})
    text = result[0].text
    assert "anomalie" in text.lower()


@pytest.mark.asyncio
async def test_call_tool_list_anomalies_filter_by_type(monitor_mod, sample_csv):
    mod = make_monitor(monitor_mod, sample_csv)
    result = await mod.call_tool(
        "list_anomalies", {"anomaly_type": "high_discount"}
    )
    text = result[0].text
    assert "high_discount" in text


@pytest.mark.asyncio
async def test_call_tool_unknown_tool(monitor_mod, sample_csv):
    mod = make_monitor(monitor_mod, sample_csv)
    result = await mod.call_tool("nonexistent_tool", {})
    assert "Error" in result[0].text