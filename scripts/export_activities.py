import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(os.getenv("LOCAL_DATABASE_URL"))

df = pd.read_sql("""
    SELECT
        strava_id,
        athlete_id,
        name,
        date,
        distance_m,
        duration_s,
        elevation_m,
        avg_heartrate,
        avg_pace_s_per_km
    FROM activities
    ORDER BY date ASC
""", engine)

os.makedirs("data/processed", exist_ok=True)
df.to_csv("data/processed/activities.csv", index=False)
print(f"Exported {len(df)} runs to data/processed/activities.csv")
print(df.tail(5))