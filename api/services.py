from datetime import date, timedelta
from ml.evaluate import predict_with_explanation


PHASES = {
    "taper": range(0, 3),
    "peak":  range(3, 7),
    "build": range(7, 14),
    "base":  range(14, 100),
}

WEEKLY_TEMPLATES = {
    "base": [
        {"day": "Monday",    "type": "Easy",     "km": 8,  "pace_offset": +30},
        {"day": "Tuesday",   "type": "Rest",      "km": 0,  "pace_offset": 0},
        {"day": "Wednesday", "type": "Easy",      "km": 10, "pace_offset": +30},
        {"day": "Thursday",  "type": "Rest",      "km": 0,  "pace_offset": 0},
        {"day": "Friday",    "type": "Easy",      "km": 8,  "pace_offset": +30},
        {"day": "Saturday",  "type": "Rest",      "km": 0,  "pace_offset": 0},
        {"day": "Sunday",    "type": "Long run",  "km": 18, "pace_offset": +45},
    ],
    "build": [
        {"day": "Monday",    "type": "Easy",     "km": 10, "pace_offset": +30},
        {"day": "Tuesday",   "type": "Rest",      "km": 0,  "pace_offset": 0},
        {"day": "Wednesday", "type": "Tempo",     "km": 10, "pace_offset": -15},
        {"day": "Thursday",  "type": "Easy",      "km": 8,  "pace_offset": +30},
        {"day": "Friday",    "type": "Rest",      "km": 0,  "pace_offset": 0},
        {"day": "Saturday",  "type": "Easy",      "km": 10, "pace_offset": +30},
        {"day": "Sunday",    "type": "Long run",  "km": 24, "pace_offset": +45},
    ],
    "peak": [
        {"day": "Monday",    "type": "Easy",     "km": 10, "pace_offset": +30},
        {"day": "Tuesday",   "type": "Tempo",     "km": 12, "pace_offset": -20},
        {"day": "Wednesday", "type": "Rest",      "km": 0,  "pace_offset": 0},
        {"day": "Thursday",  "type": "Tempo",     "km": 10, "pace_offset": -20},
        {"day": "Friday",    "type": "Easy",      "km": 8,  "pace_offset": +30},
        {"day": "Saturday",  "type": "Rest",      "km": 0,  "pace_offset": 0},
        {"day": "Sunday",    "type": "Long run",  "km": 32, "pace_offset": +45},
    ],
    "taper": [
        {"day": "Monday",    "type": "Easy",     "km": 6,  "pace_offset": +20},
        {"day": "Tuesday",   "type": "Rest",      "km": 0,  "pace_offset": 0},
        {"day": "Wednesday", "type": "Easy",      "km": 6,  "pace_offset": +20},
        {"day": "Thursday",  "type": "Rest",      "km": 0,  "pace_offset": 0},
        {"day": "Friday",    "type": "Easy",      "km": 4,  "pace_offset": +10},
        {"day": "Saturday",  "type": "Rest",      "km": 0,  "pace_offset": 0},
        {"day": "Sunday",    "type": "Easy",      "km": 3,  "pace_offset": +10},
    ],
    "recovery": [
        {"day": "Monday",    "type": "Rest",      "km": 0,  "pace_offset": 0},
        {"day": "Tuesday",   "type": "Easy",      "km": 5,  "pace_offset": +40},
        {"day": "Wednesday", "type": "Rest",      "km": 0,  "pace_offset": 0},
        {"day": "Thursday",  "type": "Easy",      "km": 5,  "pace_offset": +40},
        {"day": "Friday",    "type": "Rest",      "km": 0,  "pace_offset": 0},
        {"day": "Saturday",  "type": "Easy",      "km": 6,  "pace_offset": +40},
        {"day": "Sunday",    "type": "Rest",      "km": 0,  "pace_offset": 0},
    ],
}


def get_phase(weeks_to_race: int) -> str:
    for phase, week_range in PHASES.items():
        if weeks_to_race in week_range:
            return phase
    return "base"


def format_pace(pace_s_per_km: float) -> str:
    """Convert seconds per km to mm:ss string."""
    mins = int(pace_s_per_km // 60)
    secs = int(pace_s_per_km % 60)
    return f"{mins}:{secs:02d}"


def generate_weekly_plan(race_date: date,
                         data_path: str = "data/processed/activities.csv") -> dict:
    """
    Main function — generates this week's training plan.
    Uses model outputs to adapt the plan automatically.
    """
    today = date.today()
    weeks_to_race = max(0, (race_date - today).days // 7)

    # Get model predictions
    prediction = predict_with_explanation(data_path=data_path)
    risk        = prediction["overtraining_risk"]
    base_pace   = prediction["predicted_minutes"] * 60 / 42.195

    # Override with recovery week if high risk
    if risk == "High":
        phase    = "recovery"
        template = WEEKLY_TEMPLATES["recovery"]
    else:
        phase    = get_phase(weeks_to_race)
        template = WEEKLY_TEMPLATES[phase]

    # Build daily schedule
    schedule = []
    for day in template:
        if day["type"] == "Rest":
            schedule.append({
                "day":   day["day"],
                "type":  "Rest",
                "km":    0,
                "pace":  None,
                "note":  "Rest or light cross-training",
            })
        else:
            target_pace = base_pace + day["pace_offset"]
            pace_low    = format_pace(target_pace - 10)
            pace_high   = format_pace(target_pace + 10)
            schedule.append({
                "day":   day["day"],
                "type":  day["type"],
                "km":    day["km"],
                "pace":  f"{pace_low} – {pace_high} /km",
                "note":  "",
            })

    total_km = sum(d["km"] for d in schedule)

    return {
        "phase":          phase,
        "weeks_to_race":  weeks_to_race,
        "overtraining_risk": risk,
        "predicted_finish":  prediction["predicted_finish"],
        "top_insight":       prediction["insight"],
        "total_km":          total_km,
        "schedule":          schedule,
    }