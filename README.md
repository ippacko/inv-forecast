# Inventory Demand Forecasting and Reorder Optimization

An end-to-end data-science project that generates realistic daily demand, compares forecasting baselines, and turns the forecast into reorder recommendations.

## What it demonstrates

- Reproducible time-series data generation
- Time-based train/validation splitting
- Baseline comparison instead of assuming a complex model is best
- Forecast metrics: MAE, RMSE, and bias
- Uncertainty-aware reorder points
- Business metrics: service level and stockout risk
- A clear path from model output to an operational decision

## Run

```powershell
python -m src.generate_data
python -m src.forecast
python -m unittest discover -s tests -v
```

Outputs are written to `outputs/`:

- `metrics.json` - model comparison on a held-out 14-day period
- `forecast.csv` - next 14 days by product
- `recommendations.csv` - reorder quantity, safety stock, and stockout risk

## Approach

The project compares:

1. Seasonal-naive forecast: same weekday from the previous week
2. Moving-average forecast: recent 7-day average

The winner is selected per product using validation MAE. Reorder recommendations then combine expected demand, lead time, forecast error, and current stock:

```text
reorder_point = expected_lead_time_demand + safety_stock
reorder_quantity = max(0, demand_until_next_review + safety_stock - current_stock)
```

This is intentionally transparent. A production version could add gradient boosting, hierarchical forecasting, promotions, holidays, and probabilistic intervals.

## Next improvements

- Add MLflow experiment tracking
- Add a Streamlit dashboard
- Add external regressors such as promotions and weather
- Compare against XGBoost or LightGBM
- Add a backtesting framework across multiple forecast windows
