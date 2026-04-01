from fastapi import APIRouter
from datetime import date
from api.services import generate_weekly_plan

router = APIRouter(prefix="/plan", tags=["plan"])


@router.get("/weekly")
def get_weekly_plan(race_date: str = "2026-11-01"):
    parsed_date = date.fromisoformat(race_date)
    plan = generate_weekly_plan(parsed_date)
    return plan