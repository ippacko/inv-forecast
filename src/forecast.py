"""Compare transparent forecasting baselines and create reorder recommendations."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "daily_demand.csv"
OUTPUTS = ROOT / "outputs"
HOLDOUT = 14


def read_data() -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    with DATA.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            grouped[row["sku"]].append(
                {
                    "date": date.fromisoformat(row["date"]),
                    "product": row["product"],
                    "demand": int(row["demand"]),
                    "lead_time_days": int(row["lead_time_days"]),
                }
            )
    return grouped


def seasonal_naive(history: list[int], horizon: int, period: int = 7) -> list[float]:
    if len(history) < period:
        return [mean(history)] * horizon
    return [history[-period + index % period] for index in range(horizon)]


def moving_average(history: list[int], horizon: int, window: int = 7) -> list[float]:
    baseline = mean(history[-window:])
    return [baseline] * horizon


def metrics(actual: list[int], predicted: list[float]) -> dict[str, float]:
    errors = [actual_value - predicted_value for actual_value, predicted_value in zip(actual, predicted)]
    return {
        "mae": round(mean(abs(error) for error in errors), 3),
        "rmse": round(math.sqrt(mean(error * error for error in errors)), 3),
        "bias": round(mean(errors), 3),
    }


def main() -> dict[str, object]:
    grouped = read_data()
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    all_metrics: dict[str, dict[str, object]] = {}
    forecasts: list[dict[str, object]] = []
    recommendations: list[dict[str, object]] = []

    for sku, rows in grouped.items():
        train = rows[:-HOLDOUT]
        actual = [int(row["demand"]) for row in rows[-HOLDOUT:]]
        history = [int(row["demand"]) for row in train]
        candidates = {
            "seasonal_naive": seasonal_naive(history, HOLDOUT),
            "moving_average": moving_average(history, HOLDOUT),
        }
        scored = {name: metrics(actual, prediction) for name, prediction in candidates.items()}
        winner = min(scored, key=lambda name: scored[name]["mae"])
        all_metrics[sku] = {"product": rows[0]["product"], "models": scored, "selected_model": winner}

        full_history = [int(row["demand"]) for row in rows]
        next_dates = [rows[-1]["date"] + timedelta(days=index) for index in range(1, HOLDOUT + 1)]
        prediction = seasonal_naive(full_history, HOLDOUT) if winner == "seasonal_naive" else moving_average(full_history, HOLDOUT)
        for forecast_date, value in zip(next_dates, prediction):
            forecasts.append({"date": forecast_date.isoformat(), "sku": sku, "product": rows[0]["product"], "forecast_demand": round(value, 2)})

        lead_time = int(rows[0]["lead_time_days"])
        recent = full_history[-28:]
        daily_error = pstdev(recent) if len(recent) > 1 else 0
        lead_demand = sum(prediction[:lead_time])
        safety_stock = math.ceil(1.28 * daily_error * math.sqrt(lead_time))
        current_stock = round(mean(full_history[-7:]) * lead_time * 1.15)
        reorder_quantity = max(0, math.ceil(sum(prediction[:7]) + safety_stock - current_stock))
        recommendations.append(
            {
                "sku": sku,
                "product": rows[0]["product"],
                "current_stock": current_stock,
                "lead_time_days": lead_time,
                "expected_lead_time_demand": round(lead_demand, 2),
                "safety_stock": safety_stock,
                "reorder_quantity": reorder_quantity,
                "stockout_risk": "high" if current_stock < lead_demand else "low",
            }
        )

    with (OUTPUTS / "metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(all_metrics, handle, indent=2)
    write_csv(OUTPUTS / "forecast.csv", forecasts)
    write_csv(OUTPUTS / "recommendations.csv", recommendations)
    return {"metrics": all_metrics, "recommendations": recommendations}


def write_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    rows = list(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    result = main()
    print(json.dumps({"products": len(result["metrics"]), "recommendations": result["recommendations"]}, indent=2))
