import pandas as pd
import numpy as np


def build_feature_set(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("date").copy()
    df["date"] = pd.to_datetime(df["date"])

    # 1. Average weekly mileage over last 4 weeks
    df["weekly_km_4w"] = (
        df["distance_m"]
        .rolling(window=28, min_periods=7)
        .sum() / 1000 / 4
    )

    # 2. Average long run pace (last 3 runs > 10km — lowered from 18km)
    long_runs = df[df["distance_m"] > 10_000]["avg_pace_s_per_km"]
    df["long_run_pace_3avg"] = long_runs.rolling(window=3, min_periods=1).mean()
    df["long_run_pace_3avg"] = df["long_run_pace_3avg"].ffill()

    # 3. Heart rate efficiency — skipped, no HR data
    # Using pace efficiency proxy instead: pace / distance
    df["pace_efficiency"] = df["avg_pace_s_per_km"] / (df["distance_m"] / 1000)

    # 4. Cumulative elevation last 4 weeks
    df["elevation_4w"] = (
        df["elevation_m"]
        .rolling(window=28, min_periods=1)
        .sum()
    )

    # 5. Training consistency (% of days with a run, last 28 days)
    df["has_run"] = 1
    df["consistency_4w"] = (
        df["has_run"]
        .rolling(window=28, min_periods=1)
        .sum() / 28
    )

    # 6. ACWR — injury risk ratio
    acute   = df["distance_m"].rolling(window=7,  min_periods=1).sum()
    chronic = df["distance_m"].rolling(window=28, min_periods=7).sum() / 4
    df["acwr"] = acute / chronic.replace(0, np.nan)

    # 7. Pace trend (are you getting faster?)
    def pace_slope(series):
        if len(series) < 3:
            return 0
        x = np.arange(len(series))
        slope, _ = np.polyfit(x, series, 1)
        return slope

    df["pace_trend"] = (
        df["avg_pace_s_per_km"]
        .rolling(window=28, min_periods=3)
        .apply(pace_slope, raw=True)
    )

    feature_cols = [
        "weekly_km_4w",
        "long_run_pace_3avg",
        "pace_efficiency",
        "elevation_4w",
        "consistency_4w",
        "acwr",
        "pace_trend",
    ]

    return df[feature_cols + ["avg_pace_s_per_km", "date"]].dropna()