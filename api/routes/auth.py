from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from pipeline.strava_client import get_authorization_url, exchange_code_for_token
from pipeline.models import SessionLocal, Athlete

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/strava")
def strava_login():
    return RedirectResponse(get_authorization_url())


@router.get("/callback")
def strava_callback(code: str, scope: str = ""):
    token_data = exchange_code_for_token(code)

    athlete_data = token_data["athlete"]
    db = SessionLocal()

    athlete = db.query(Athlete).filter_by(
        strava_id=athlete_data["id"]
    ).first()

    if athlete:
        athlete.access_token  = token_data["access_token"]
        athlete.refresh_token = token_data["refresh_token"]
        athlete.expires_at    = token_data["expires_at"]
    else:
        athlete = Athlete(
            strava_id     = athlete_data["id"],
            firstname     = athlete_data["firstname"],
            lastname      = athlete_data["lastname"],
            city          = athlete_data.get("city"),
            country       = athlete_data.get("country"),
            access_token  = token_data["access_token"],
            refresh_token = token_data["refresh_token"],
            expires_at    = token_data["expires_at"],
        )
        db.add(athlete)

    db.commit()
    db.close()

    return {
        "message":    "Athlete saved to database",
        "athlete_id": athlete_data["id"],
        "name":       f"{athlete_data['firstname']} {athlete_data['lastname']}",
    }