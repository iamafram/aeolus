import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import classification_report

from pipeline.features import build_feature_set


def label_overtraining(df: pd.DataFrame) -> pd.Series:
    """
    Labels each row as high risk (1) or low risk (0)
    based on ACWR — the gold standard in sports science.
    ACWR > 1.3 = high injury risk
    ACWR < 0.8 = undertraining
    Sweet spot: 0.8 - 1.3
    """
    acute  = df["distance_m"].rolling(window=7,  min_periods=1).sum()
    chronic = df["distance_m"].rolling(window=28, min_periods=7).sum() / 4
    acwr = acute / chronic.replace(0, np.nan)
    return (acwr > 1.3).astype(int).fillna(0)


FEATURE_COLS = [
    "weekly_km_4w",
    "long_run_pace_3avg",
    "pace_efficiency",
    "elevation_4w",
    "consistency_4w",
    "acwr",
    "pace_trend",
]


def train(data_path: str = "data/processed/activities.csv"):
    # 1. Load & build features
    raw = pd.read_csv(data_path, parse_dates=["date"])
    raw = raw.sort_values("date").copy()

    # Label before feature engineering
    raw["overtraining_risk"] = label_overtraining(raw)

    df = build_feature_set(raw)

    # Align labels with feature rows
    df = df.copy()
    df["overtraining_risk"] = raw.loc[df.index, "overtraining_risk"].values

    X = df[FEATURE_COLS].values
    y = df["overtraining_risk"].values

    print(f"Training on {len(X)} samples")
    print(f"High risk runs: {y.sum()} ({y.mean()*100:.1f}%)")
    print(f"Low risk runs:  {len(y) - y.sum()} ({(1-y.mean())*100:.1f}%)")

    tscv = TimeSeriesSplit(n_splits=5)

    # 2. Baseline: Logistic Regression
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr_scores = cross_val_score(lr, X, y, cv=tscv, scoring="f1_macro")
    print(f"\nLogistic Regression F1: {lr_scores.mean():.2f}")

    # 3. Random Forest
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=4,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    rf_scores = cross_val_score(rf, X, y, cv=tscv, scoring="f1_macro")
    print(f"Random Forest F1:       {rf_scores.mean():.2f}")

    # 4. Final fit on all data
    rf.fit(X, y)

    # 5. Print classification report on full data
    preds = rf.predict(X)
    print("\nClassification report (full data):")
    print(classification_report(y, preds,
          target_names=["Low risk", "High risk"]))

    # 6. Save model
    Path("ml/models").mkdir(parents=True, exist_ok=True)
    joblib.dump(rf, "ml/models/overtraining_classifier.pkl")

    metadata = {
        "feature_cols":    FEATURE_COLS,
        "rf_f1":           round(float(rf_scores.mean()), 2),
        "lr_f1":           round(float(lr_scores.mean()), 2),
        "n_samples":       len(X),
        "high_risk_pct":   round(float(y.mean() * 100), 1),
    }
    with open("ml/models/overtraining_classifier_meta.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nModel saved to ml/models/overtraining_classifier.pkl")
    print(f"Metadata: {metadata}")
    return rf, metadata


if __name__ == "__main__":
    train()