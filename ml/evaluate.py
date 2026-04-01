import pandas as pd
import numpy as np
import joblib
import json
import shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

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

FEATURE_LABELS = {
    "weekly_km_4w":        "Weekly mileage (4w avg)",
    "long_run_pace_3avg":  "Long run pace",
    "pace_efficiency":     "Pace efficiency",
    "elevation_4w":        "Elevation (4w total)",
    "consistency_4w":      "Training consistency",
    "acwr":                "Workload ratio (ACWR)",
    "pace_trend":          "Pace trend",
}


def explain_prediction(data_path: str = "data/processed/activities.csv"):
    """
    Generates SHAP explanation for the latest prediction.
    Returns the top factor and all shap values.
    """
    model    = joblib.load("ml/models/race_predictor.pkl")
    raw      = pd.read_csv(data_path, parse_dates=["date"])
    features = build_feature_set(raw)

    X      = features[FEATURE_COLS].values
    latest = X[-1].reshape(1, -1)

    # SHAP values
    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # Top feature for latest prediction
    latest_shap  = shap_values[-1]
    top_idx      = int(np.argmax(np.abs(latest_shap)))
    top_feature  = FEATURE_COLS[top_idx]
    top_label    = FEATURE_LABELS[top_feature]
    top_impact   = latest_shap[top_idx]

    direction = "slower" if top_impact > 0 else "faster"
    print(f"\nTop factor in your prediction: {top_label}")
    print(f"Impact: pushing your time {direction} by {abs(top_impact):.1f} minutes")

    # All shap values for latest prediction
    shap_dict = {
        FEATURE_LABELS[f]: round(float(v), 2)
        for f, v in zip(FEATURE_COLS, latest_shap)
    }
    print("\nFull breakdown (positive = slower, negative = faster):")
    for label, val in sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True):
        direction = "+" if val > 0 else ""
        print(f"  {label:<30} {direction}{val:.1f} min")

    # Save SHAP summary plot
    Path("ml/models").mkdir(parents=True, exist_ok=True)
    shap.summary_plot(
        shap_values, X,
        feature_names=[FEATURE_LABELS[f] for f in FEATURE_COLS],
        show=False
    )
    plt.tight_layout()
    plt.savefig("ml/models/shap_summary.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\nSHAP summary plot saved to ml/models/shap_summary.png")

    return {
        "top_factor":  top_label,
        "top_impact":  round(float(top_impact), 2),
        "shap_values": shap_dict,
    }


def predict_with_explanation(athlete_id: int = None,
                             data_path: str = "data/processed/activities.csv") -> dict:
    """
    Called by FastAPI — returns prediction + explanation in one call.
    """
    race_model = joblib.load("ml/models/race_predictor.pkl")
    risk_model = joblib.load("ml/models/overtraining_classifier.pkl")

    raw      = pd.read_csv(data_path, parse_dates=["date"])
    features = build_feature_set(raw)
    latest   = features[FEATURE_COLS].iloc[-1].values.reshape(1, -1)

    # Race prediction
    pred_minutes = float(race_model.predict(latest)[0])
    hours        = int(pred_minutes // 60)
    mins         = int(pred_minutes % 60)

    # Risk prediction
    risk_pred = risk_model.predict(latest)[0]
    risk_prob = max(risk_model.predict_proba(latest)[0])
    risk_label = "High" if risk_pred == 1 else "Low"

    # SHAP explanation
    explainer   = shap.TreeExplainer(race_model)
    shap_values = explainer.shap_values(latest)[0]
    top_idx     = int(np.argmax(np.abs(shap_values)))
    top_feature = FEATURE_LABELS[FEATURE_COLS[top_idx]]
    top_impact  = float(shap_values[top_idx])
    direction   = "slower" if top_impact > 0 else "faster"

    return {
        "predicted_finish":  f"{hours}:{mins:02d}",
        "predicted_minutes": round(pred_minutes, 1),
        "overtraining_risk": risk_label,
        "risk_confidence":   round(risk_prob * 100, 1),
        "top_factor":        top_feature,
        "insight":           f"{top_feature} is pushing your time {direction} by {abs(top_impact):.1f} min",
        "shap_values": {
            FEATURE_LABELS[f]: round(float(v), 2)
            for f, v in zip(FEATURE_COLS, shap_values)
        },
    }


if __name__ == "__main__":
    explain_prediction()