#!/usr/bin/env python3
"""
Generate sample sales data for the Phase 0 spike.

Creates spike/data/sales.csv with ~200 transactions including deliberate anomalies
so the monitor-agent has something interesting to detect.

Usage:
    uv run spike/data/generate_data.py
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_FILE = Path(__file__).parent / "sales.csv"

random.seed(42)

PRODUCTS = [
    ("P001", "Widget Pro", 49.99),
    ("P002", "Gadget Plus", 129.99),
    ("P003", "Doohickey", 19.99),
    ("P004", "Thingamajig", 79.99),
    ("P005", "Whatsit Deluxe", 249.99),
]

CUSTOMERS = [f"C{str(i).zfill(4)}" for i in range(1, 51)]
PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "bank_transfer"]
STATUSES = ["completed", "completed", "completed", "pending", "refunded"]

START_DATE = datetime(2024, 1, 1)


def random_date() -> str:
    delta = random.randint(0, 364)
    return (START_DATE + timedelta(days=delta)).strftime("%Y-%m-%d")


def generate_transactions(n: int = 200) -> list:
    rows = []
    for i in range(1, n + 1):
        product_id, _, base_price = random.choice(PRODUCTS)
        quantity = random.randint(1, 10)
        discount = round(random.uniform(0.0, 0.20), 3)   # normal: 0–20%
        unit_price = round(base_price * (1 - discount), 2)
        total = round(unit_price * quantity, 2)

        rows.append({
            "transaction_id": f"T{str(i).zfill(5)}",
            "transaction_date": random_date(),
            "customer_id": random.choice(CUSTOMERS),
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": total,
            "discount": discount,
            "payment_method": random.choice(PAYMENT_METHODS),
            "status": random.choice(STATUSES),
        })

    # ---- inject deliberate anomalies ----

    # 1. High-revenue critical: huge quantity
    rows.append({
        "transaction_id": "T99901",
        "transaction_date": "2024-06-15",
        "customer_id": "C0001",
        "product_id": "P002",
        "quantity": 80,
        "unit_price": 129.99,
        "total_amount": round(129.99 * 80, 2),
        "discount": 0.05,
        "payment_method": "bank_transfer",
        "status": "completed",
    })

    # 2. High-revenue warning: very expensive single item
    rows.append({
        "transaction_id": "T99902",
        "transaction_date": "2024-08-20",
        "customer_id": "C0007",
        "product_id": "P005",
        "quantity": 3,
        "unit_price": 999.99,
        "total_amount": round(999.99 * 3, 2),
        "discount": 0.0,
        "payment_method": "credit_card",
        "status": "pending",
    })

    # 3. High-discount critical
    rows.append({
        "transaction_id": "T99903",
        "transaction_date": "2024-03-10",
        "customer_id": "C0023",
        "product_id": "P001",
        "quantity": 2,
        "unit_price": round(49.99 * 0.35, 2),
        "total_amount": round(49.99 * 0.35 * 2, 2),
        "discount": 0.65,
        "payment_method": "paypal",
        "status": "completed",
    })

    # 4. High-quantity warning
    rows.append({
        "transaction_id": "T99904",
        "transaction_date": "2024-11-05",
        "customer_id": "C0042",
        "product_id": "P003",
        "quantity": 60,
        "unit_price": 19.99,
        "total_amount": round(19.99 * 60, 2),
        "discount": 0.10,
        "payment_method": "credit_card",
        "status": "completed",
    })

    return rows


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_transactions()
    fieldnames = [
        "transaction_id", "transaction_date", "customer_id", "product_id",
        "quantity", "unit_price", "total_amount", "discount",
        "payment_method", "status",
    ]
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} transactions → {OUTPUT_FILE}")
    print("Anomalies injected: T99901 (high_revenue/critical), T99902 (high_revenue/warning),")
    print("                    T99903 (high_discount/critical), T99904 (high_quantity/warning)")


if __name__ == "__main__":
    main()