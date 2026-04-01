import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path

from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_absolute_error

from pipeline.features import build_feature_set

FEATURE_COLS = [
    "weekly_km_4w",
    "long_run_pace_3avg",
    "pace_efficiency",
    "elevation_4w",
    "consistency_4w",
    "acwr",
    "pace_trend",
]


def pace_to_marathon_minutes(pace_s_per_km: float) -> float:
    """Riegel formula: predicts marathon time from current pace."""
    ref_distance_km = 10
    marathon_km = 42.195
    time_ref_s = pace_s_per_km * ref_distance_km
    predicted_s = time_ref_s * (marathon_km / ref_distance_km) ** 1.06
    return predicted_s / 60


def train(data_path: str = "data/processed/activities.csv"):
    # 1. Load & build features
    raw = pd.read_csv(data_path, parse_dates=["date"])
    df  = build_feature_set(raw)

    X = df[FEATURE_COLS].values
    y = df["long_run_pace_3avg"].apply(pace_to_marathon_minutes).values

    print(f"Training on {len(X)} samples")
    print(f"Target range: {y.min():.1f} – {y.max():.1f} minutes")

    # 2. TimeSeriesSplit — never random split on time data
    tscv = TimeSeriesSplit(n_splits=5)

    # 3. Baseline: predict the mean
    baseline_mae = np.mean([
        mean_absolute_error(y[test], np.full(len(test), y[train].mean()))
        for train, test in tscv.split(X)
    ])
    print(f"\nBaseline MAE (predict mean): {baseline_mae:.1f} minutes")

    # 4. Train XGBoost
    model = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        base_score=0.5,
        random_state=42,
        n_jobs=-1,
    )

    cv_scores = cross_val_score(
        model, X, y,
        cv=tscv,
        scoring="neg_mean_absolute_error",
    )
    cv_mae = -cv_scores.mean()
    print(f"XGBoost CV MAE:              {cv_mae:.1f} minutes")
    print(f"Improvement over baseline:   {baseline_mae - cv_mae:.1f} minutes")

    # 5. Final fit on all data
    model.fit(X, y)

    # 6. Save model + metadata
    Path("ml/models").mkdir(parents=True, exist_ok=True)
    joblib.dump(model, "ml/models/race_predictor.pkl")

    metadata = {
        "feature_cols":        FEATURE_COLS,
        "cv_mae_minutes":      round(cv_mae, 2),
        "baseline_mae":        round(baseline_mae, 2),
        "n_samples":           len(X),
        "target_mean_minutes": round(float(y.mean()), 1),
    }
    with open("ml/models/race_predictor_meta.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nModel saved to ml/models/race_predictor.pkl")
    print(f"Metadata: {metadata}")
    return model, metadata


if __name__ == "__main__":
    train()