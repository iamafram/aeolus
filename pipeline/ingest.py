import requests
from pipeline.strava_client import get_valid_token

ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"


def fetch_activities(stored_token: dict, pages: int = 5) -> list[dict]:
    access_token = get_valid_token(stored_token)
    headers = {"Authorization": f"Bearer {access_token}"}
    all_activities = []

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
        all_activities.extend(runs)
        print(f"Page {page}: fetched {len(runs)} runs")

    return all_activities


def extract_key_fields(activity: dict) -> dict:
    return {
        "strava_id":         activity["id"],
        "name":              activity["name"],
        "date":              activity["start_date"],
        "distance_m":        activity["distance"],
        "duration_s":        activity["moving_time"],
        "elevation_m":       activity["total_elevation_gain"],
        "avg_heartrate":     activity.get("average_heartrate"),
        "avg_pace_s_per_km": activity["moving_time"] / (activity["distance"] / 1000)
                             if activity["distance"] > 0 else None,
    }