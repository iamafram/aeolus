import requests
from datetime import datetime
from pipeline.strava_client import get_valid_token
from pipeline.models import SessionLocal, Activity

ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"


def fetch_and_store_activities(stored_token: dict, athlete_id: int, pages: int = 5):
    access_token = get_valid_token(stored_token)
    headers = {"Authorization": f"Bearer {access_token}"}
    db = SessionLocal()
    total_saved = 0

    for page in range(1, pages + 1):
        response = requests.get(ACTIVITIES_URL, headers=headers, params={
            "per_page": 200,
            "page":     page,
        })
        response.raise_for_status()
        batch = response.json()

        if not batch:
            break

        runs = [a for a in batch if a["type"] == "Run"]

        for a in runs:
            exists = db.query(Activity).filter_by(
                strava_id=a["id"]
            ).first()

            if exists:
                continue

            pace = (
                a["moving_time"] / (a["distance"] / 1000)
                if a["distance"] > 0 else None
            )

            activity = Activity(
                strava_id         = a["id"],
                athlete_id        = athlete_id,
                name              = a["name"],
                date              = datetime.strptime(
                                      a["start_date"], "%Y-%m-%dT%H:%M:%SZ"
                                    ),
                distance_m        = a["distance"],
                duration_s        = a["moving_time"],
                elevation_m       = a["total_elevation_gain"],
                avg_heartrate     = a.get("average_heartrate"),
                avg_pace_s_per_km = pace,
            )
            db.add(activity)
            total_saved += 1

        db.commit()
        print(f"Page {page}: saved {len(runs)} runs")

    db.close()
    print(f"Total new runs saved: {total_saved}")
    return total_saved
