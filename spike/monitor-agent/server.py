#!/usr/bin/env python3
"""
Monitor Agent MCP Server

Detects anomalies in sales data. Part of the Phase 0 multi-agent coordination spike.
Works alongside engineer-agent — Claude Desktop orchestrates both without custom code.

Tools:
  - check_data_health: overall health summary with anomaly count
  - list_anomalies:    list each detected anomaly with severity and context
  - get_metric_stats:  baseline stats for a metric (used by engineer-agent for context)
"""

import asyncio
import csv
import json
import statistics
from pathlib import Path
from typing import Any, List

from mcp.server import Server
from mcp.types import TextContent, Tool

server = Server("monitor-agent")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

DATA_FILE = Path(__file__).parent.parent / "data" / "sales.csv"


def load_sales_data() -> List[dict]:
    """Load the spike sample dataset."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Sample data not found at {DATA_FILE}. "
            "Run spike/data/generate_data.py first."
        )
    with open(DATA_FILE, newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Anomaly detection logic
# ---------------------------------------------------------------------------

ANOMALY_THRESHOLDS = {
    "revenue_zscore": 2.5,   # flag transactions > 2.5 std devs above mean
    "discount_pct": 0.40,    # flag discounts > 40%
    "quantity": 50,          # flag single-transaction quantities > 50 units
}


def _zscore(value: float, mean: float, stdev: float) -> float:
    if stdev == 0:
        return 0.0
    return (value - mean) / stdev


def detect_anomalies(data: List[dict]) -> List[dict]:
    """
    Return a list of anomaly dicts, each with:
      - transaction_id
      - anomaly_type  (high_revenue | high_discount | high_quantity)
      - severity      (warning | critical)
      - value         (the offending value)
      - context       (human-readable explanation)
    """
    amounts = [float(r["total_amount"]) for r in data if r.get("total_amount")]
    mean_amount = statistics.mean(amounts)
    stdev_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0.0

    anomalies = []

    for row in data:
        tid = row.get("transaction_id", "unknown")

        # High revenue
        try:
            amount = float(row["total_amount"])
            z = _zscore(amount, mean_amount, stdev_amount)
            if z > ANOMALY_THRESHOLDS["revenue_zscore"]:
                anomalies.append({
                    "transaction_id": tid,
                    "anomaly_type": "high_revenue",
                    "severity": "critical" if z > 4.0 else "warning",
                    "value": round(amount, 2),
                    "context": (
                        f"Transaction amount ${amount:.2f} is {z:.1f} std devs above "
                        f"mean (${mean_amount:.2f})"
                    ),
                })
        except (ValueError, KeyError):
            pass

        # High discount
        try:
            discount = float(row["discount"])
            if discount > ANOMALY_THRESHOLDS["discount_pct"]:
                anomalies.append({
                    "transaction_id": tid,
                    "anomaly_type": "high_discount",
                    "severity": "critical" if discount > 0.60 else "warning",
                    "value": round(discount, 3),
                    "context": (
                        f"Discount {discount*100:.1f}% exceeds threshold "
                        f"({ANOMALY_THRESHOLDS['discount_pct']*100:.0f}%)"
                    ),
                })
        except (ValueError, KeyError):
            pass

        # High quantity
        try:
            qty = int(row["quantity"])
            if qty > ANOMALY_THRESHOLDS["quantity"]:
                anomalies.append({
                    "transaction_id": tid,
                    "anomaly_type": "high_quantity",
                    "severity": "warning",
                    "value": qty,
                    "context": (
                        f"Quantity {qty} exceeds single-transaction threshold "
                        f"({ANOMALY_THRESHOLDS['quantity']} units)"
                    ),
                })
        except (ValueError, KeyError):
            pass

    return anomalies


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="check_data_health",
            description=(
                "Run a health check on the sales dataset. Returns an overall health "
                "status (healthy / degraded / critical), total transaction count, "
                "anomaly count, and a brief summary. Call this first to get an overview "
                "before calling list_anomalies."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="list_anomalies",
            description=(
                "List all detected anomalies in the sales dataset with their type, "
                "severity, value, and context. Use after check_data_health. "
                "Optionally filter by anomaly_type or severity."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "anomaly_type": {
                        "type": "string",
                        "enum": ["high_revenue", "high_discount", "high_quantity"],
                        "description": "Filter to a specific anomaly type (optional)",
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["warning", "critical"],
                        "description": "Filter to a specific severity level (optional)",
                    },
                },
            },
        ),
        Tool(
            name="get_metric_stats",
            description=(
                "Get baseline statistics (mean, median, stdev, min, max) for a numeric "
                "metric across all transactions. Useful context for the engineer-agent "
                "when investigating anomalies."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "enum": ["total_amount", "discount", "quantity"],
                        "description": "The metric to summarise",
                    }
                },
                "required": ["metric"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@server.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    try:
        data = load_sales_data()

        if name == "check_data_health":
            anomalies = detect_anomalies(data)
            critical = [a for a in anomalies if a["severity"] == "critical"]
            warnings = [a for a in anomalies if a["severity"] == "warning"]

            if critical:
                status = "🔴 CRITICAL"
            elif warnings:
                status = "🟡 DEGRADED"
            else:
                status = "🟢 HEALTHY"

            msg = (
                f"Data Health: {status}\n\n"
                f"Transactions analysed: {len(data)}\n"
                f"Anomalies detected:    {len(anomalies)} "
                f"({len(critical)} critical, {len(warnings)} warnings)\n\n"
            )
            if anomalies:
                type_counts: dict = {}
                for a in anomalies:
                    type_counts[a["anomaly_type"]] = type_counts.get(a["anomaly_type"], 0) + 1
                msg += "Breakdown by type:\n"
                for atype, count in type_counts.items():
                    msg += f"  • {atype}: {count}\n"
                msg += "\nCall list_anomalies for full details."
            return [TextContent(type="text", text=msg)]

        elif name == "list_anomalies":
            anomalies = detect_anomalies(data)

            # Apply filters
            if arguments.get("anomaly_type"):
                anomalies = [a for a in anomalies if a["anomaly_type"] == arguments["anomaly_type"]]
            if arguments.get("severity"):
                anomalies = [a for a in anomalies if a["severity"] == arguments["severity"]]

            if not anomalies:
                return [TextContent(type="text", text="No anomalies found matching the criteria.")]

            lines = [f"Found {len(anomalies)} anomalie(s):\n"]
            for a in anomalies:
                icon = "🔴" if a["severity"] == "critical" else "🟡"
                lines.append(
                    f"{icon} [{a['severity'].upper()}] {a['anomaly_type']}\n"
                    f"   Transaction: {a['transaction_id']}\n"
                    f"   Value:       {a['value']}\n"
                    f"   Context:     {a['context']}\n"
                )
            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "get_metric_stats":
            metric = arguments["metric"]
            values = []
            for row in data:
                try:
                    values.append(float(row[metric]))
                except (ValueError, KeyError):
                    pass

            if not values:
                return [TextContent(type="text", text=f"No numeric values found for '{metric}'.")]

            msg = (
                f"Baseline stats for '{metric}' ({len(values)} transactions):\n\n"
                f"  Mean:   {statistics.mean(values):.2f}\n"
                f"  Median: {statistics.median(values):.2f}\n"
                f"  Stdev:  {statistics.stdev(values):.2f}\n"
                f"  Min:    {min(values):.2f}\n"
                f"  Max:    {max(values):.2f}\n"
            )
            return [TextContent(type="text", text=msg)]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())