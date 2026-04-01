from fastapi import APIRouter
from ml.evaluate import predict_with_explanation
import pandas as pd
from pipeline.features import build_feature_set

router = APIRouter(prefix="/athlete", tags=["athlete"])

FEATURE_COLS = [
    "weekly_km_4w",
    "long_run_pace_3avg",
    "pace_efficiency",
    "elevation_4w",
    "consistency_4w",
    "acwr",
    "pace_trend",
]


@router.get("/fitness")
def get_fitness():
    return predict_with_explanation()


@router.get("/trends")
def get_trends():
    df       = pd.read_csv("data/processed/activities.csv",
                           parse_dates=["date"])
    features = build_feature_set(df)

    last_8_weeks = features.tail(8)[
        ["date", "avg_pace_s_per_km", "weekly_km_4w", "acwr"]
    ].copy()

    def fmt_pace(s):
        m = int(s // 60)
        sec = int(s % 60)
        return f"{m}:{sec:02d}"

    rows = []
    for _, row in last_8_weeks.iterrows():
        rows.append({
            "date":      row["date"].strftime("%Y-%m-%d"),
            "pace":      fmt_pace(row["avg_pace_s_per_km"]),
            "pace_s":    round(row["avg_pace_s_per_km"], 1),
            "weekly_km": round(row["weekly_km_4w"], 1),
            "acwr":      round(row["acwr"], 2),
        })

    return {
        "trends":        rows,
        "best_pace":     fmt_pace(last_8_weeks["avg_pace_s_per_km"].min()),
        "worst_pace":    fmt_pace(last_8_weeks["avg_pace_s_per_km"].max()),
        "avg_weekly_km": round(last_8_weeks["weekly_km_4w"].mean(), 1),
    }