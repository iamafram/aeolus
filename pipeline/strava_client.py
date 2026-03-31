import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REDIRECT_URI  = os.getenv("STRAVA_REDIRECT_URI")

AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL     = "https://www.strava.com/oauth/token"


def get_authorization_url() -> str:
    params = {
        "client_id":       CLIENT_ID,
        "redirect_uri":    REDIRECT_URI,
        "response_type":   "code",
        "approval_prompt": "auto",
        "scope":           "read,activity:read_all",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{AUTHORIZE_URL}?{query}"


def exchange_code_for_token(code: str) -> dict:
    response = requests.post(TOKEN_URL, data={
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code":          code,
        "grant_type":    "authorization_code",
    })
    response.raise_for_status()
    return response.json()


def refresh_access_token(refresh_token: str) -> dict:
    response = requests.post(TOKEN_URL, data={
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type":    "refresh_token",
    })
    response.raise_for_status()
    return response.json()


def get_valid_token(stored_token: dict) -> str:
    if time.time() > stored_token["expires_at"] - 300:
        new_token = refresh_access_token(stored_token["refresh_token"])
        return new_token["access_token"]
    return stored_token["access_token"]