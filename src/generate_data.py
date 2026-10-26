"""Generate reproducible synthetic daily demand and inventory snapshots."""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PRODUCTS = [
    ("P-100", "Classic Brick", 22, 3, 0.08),
    ("P-200", "Creative Wheel Set", 15, 4, 0.12),
    ("P-300", "Display Base", 10, 5, 0.10),
    ("P-400", "Mini Figure Pack", 28, 2, 0.15),
]


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    rng = random.Random(7)
    start = date(2025, 1, 1)
    rows: list[dict[str, object]] = []
    for offset in range(210):
        current = start + timedelta(days=offset)
        weekday = current.weekday()
        for sku, name, base, lead_time, volatility in PRODUCTS:
            seasonal = 1.25 if weekday in (5, 6) else 0.9 if weekday == 0 else 1.0
            trend = 1 + offset / 800
            shock = 1.35 if sku == "P-400" and 150 <= offset <= 165 else 1.0
            noise = max(0.4, rng.gauss(1.0, volatility))
            demand = max(0, round(base * seasonal * trend * shock * noise))
            rows.append({"date": current.isoformat(), "sku": sku, "product": name, "demand": demand, "lead_time_days": lead_time})
    with (DATA / "daily_demand.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
