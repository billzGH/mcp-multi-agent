#!/usr/bin/env python3
"""
Engineer Agent MCP Server

Investigates anomalies identified by the monitor-agent. Part of the Phase 0
multi-agent coordination spike. Claude Desktop orchestrates both servers —
it calls monitor-agent to detect anomalies, then calls this server to dig in.

Tools:
  - get_transaction:       fetch a single transaction by ID
  - investigate_anomaly:   deep-dive on one anomaly — pulls context, compares
                           to cohort, and surfaces likely cause
  - get_customer_history:  summarise all transactions for a customer
"""

import asyncio
import csv
import statistics
from pathlib import Path
from typing import Any, List

from mcp.server import Server
from mcp.types import TextContent, Tool

server = Server("engineer-agent")

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


def index_by_transaction(data: List[dict]) -> dict:
    return {row["transaction_id"]: row for row in data if row.get("transaction_id")}


def index_by_customer(data: List[dict]) -> dict:
    idx: dict = {}
    for row in data:
        cid = row.get("customer_id", "unknown")
        idx.setdefault(cid, []).append(row)
    return idx


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_transaction",
            description=(
                "Fetch full details of a single transaction by its ID. "
                "Use this to inspect a specific transaction flagged by monitor-agent."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "The transaction ID to look up",
                    }
                },
                "required": ["transaction_id"],
            },
        ),
        Tool(
            name="investigate_anomaly",
            description=(
                "Deep-dive investigation of a flagged transaction. Compares the "
                "transaction to others of the same product and payment method, "
                "computes how far it deviates from the cohort, and identifies "
                "the most likely cause of the anomaly. Provide the transaction_id "
                "and the anomaly_type reported by monitor-agent."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "Transaction ID flagged by monitor-agent",
                    },
                    "anomaly_type": {
                        "type": "string",
                        "enum": ["high_revenue", "high_discount", "high_quantity"],
                        "description": "The anomaly type reported by monitor-agent",
                    },
                },
                "required": ["transaction_id", "anomaly_type"],
            },
        ),
        Tool(
            name="get_customer_history",
            description=(
                "Summarise all transactions for a customer: total spend, average order "
                "value, order count, and most recent transactions. Useful for determining "
                "whether an anomalous transaction is out of character for this customer."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer ID to look up",
                    }
                },
                "required": ["customer_id"],
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

        if name == "get_transaction":
            tid = arguments["transaction_id"]
            tx_index = index_by_transaction(data)
            row = tx_index.get(tid)
            if not row:
                return [TextContent(type="text", text=f"Transaction '{tid}' not found.")]

            lines = [f"Transaction: {tid}\n"]
            for k, v in row.items():
                lines.append(f"  {k}: {v}")
            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "investigate_anomaly":
            tid = arguments["transaction_id"]
            anomaly_type = arguments["anomaly_type"]
            tx_index = index_by_transaction(data)
            row = tx_index.get(tid)

            if not row:
                return [TextContent(type="text", text=f"Transaction '{tid}' not found.")]

            # Build cohort: same product_id and payment_method
            product_id = row.get("product_id", "")
            payment = row.get("payment_method", "")
            cohort = [
                r for r in data
                if r.get("product_id") == product_id
                and r.get("payment_method") == payment
                and r.get("transaction_id") != tid
            ]

            # Metric to investigate
            metric_map = {
                "high_revenue": "total_amount",
                "high_discount": "discount",
                "high_quantity": "quantity",
            }
            metric = metric_map[anomaly_type]

            try:
                flagged_val = float(row[metric])
            except (ValueError, KeyError):
                return [TextContent(
                    type="text",
                    text=f"Cannot read metric '{metric}' from transaction {tid}."
                )]

            cohort_vals = []
            for r in cohort:
                try:
                    cohort_vals.append(float(r[metric]))
                except (ValueError, KeyError):
                    pass

            msg = f"Investigation: {anomaly_type} on transaction {tid}\n\n"
            msg += f"Transaction details:\n"
            msg += f"  product_id:     {product_id}\n"
            msg += f"  payment_method: {payment}\n"
            msg += f"  customer_id:    {row.get('customer_id', 'unknown')}\n"
            msg += f"  {metric}: {flagged_val}\n"
            msg += f"  status:         {row.get('status', 'unknown')}\n\n"

            if cohort_vals:
                cohort_mean = statistics.mean(cohort_vals)
                cohort_stdev = statistics.stdev(cohort_vals) if len(cohort_vals) > 1 else 0.0
                z = (flagged_val - cohort_mean) / cohort_stdev if cohort_stdev else 0.0

                msg += f"Cohort comparison (same product + payment method, n={len(cohort_vals)}):\n"
                msg += f"  Cohort mean:  {cohort_mean:.2f}\n"
                msg += f"  Cohort stdev: {cohort_stdev:.2f}\n"
                msg += f"  Z-score:      {z:.2f}\n\n"

                # Likely cause heuristics
                msg += "Likely cause:\n"
                if anomaly_type == "high_revenue":
                    if float(row.get("quantity", 1)) > 10:
                        msg += "  → High quantity order driving elevated total\n"
                    elif float(row.get("unit_price", 0)) > cohort_mean:
                        msg += "  → Unit price above cohort average — possible pricing error\n"
                    else:
                        msg += "  → Unusual combination of quantity and price\n"
                elif anomaly_type == "high_discount":
                    msg += f"  → Discount {float(row.get('discount',0))*100:.1f}% "
                    msg += f"vs cohort avg {statistics.mean([float(r.get('discount',0)) for r in cohort if r.get('discount')])*100:.1f}%\n"
                    msg += "  → May indicate manual override or promotional error\n"
                elif anomaly_type == "high_quantity":
                    msg += "  → Bulk order; verify this is an intentional B2B purchase\n"
            else:
                msg += "No cohort data available for comparison (unique product/payment combination).\n"

            msg += "\nRecommendation: call get_customer_history to check if this is "
            msg += "consistent with this customer's normal behaviour."
            return [TextContent(type="text", text=msg)]

        elif name == "get_customer_history":
            cid = arguments["customer_id"]
            cust_index = index_by_customer(data)
            transactions = cust_index.get(cid)

            if not transactions:
                return [TextContent(type="text", text=f"No transactions found for customer '{cid}'.")]

            amounts = []
            for t in transactions:
                try:
                    amounts.append(float(t["total_amount"]))
                except (ValueError, KeyError):
                    pass

            msg = f"Customer history: {cid}\n\n"
            msg += f"  Total transactions: {len(transactions)}\n"
            if amounts:
                msg += f"  Total spend:        ${sum(amounts):.2f}\n"
                msg += f"  Average order:      ${statistics.mean(amounts):.2f}\n"
                msg += f"  Largest order:      ${max(amounts):.2f}\n"
                msg += f"  Smallest order:     ${min(amounts):.2f}\n"

            msg += f"\nMost recent transactions (up to 5):\n"
            recent = sorted(
                transactions,
                key=lambda r: r.get("transaction_date", ""),
                reverse=True,
            )[:5]
            for t in recent:
                msg += (
                    f"  {t.get('transaction_date','?')}  "
                    f"{t.get('transaction_id','?')}  "
                    f"${float(t.get('total_amount', 0)):.2f}  "
                    f"{t.get('status','?')}\n"
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