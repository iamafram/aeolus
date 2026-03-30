from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from pipeline.strava_client import get_authorization_url, exchange_code_for_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/strava")
def strava_login():
    url = get_authorization_url()
    return RedirectResponse(url)


@router.get("/callback")
def strava_callback(code: str, scope: str = ""):
    token_data = exchange_code_for_token(code)
    print("Athlete ID:",    token_data["athlete"]["id"])
    print("Access token:",  token_data["access_token"])
    print("Refresh token:", token_data["refresh_token"])
    print("Expires at:",    token_data["expires_at"])
    return {
        "message": "Authorization successful",
        "athlete": token_data["athlete"]
    }