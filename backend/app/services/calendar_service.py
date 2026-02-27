"""
Google Calendar API integration — sync workout and nutrition plans to calendar.
Uses OAuth2 flow. Falls back gracefully when credentials are not configured.
"""
import os
from datetime import datetime, timedelta
from typing import Optional

# Google Calendar requires OAuth2 credentials
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/calendar/callback")


def is_configured() -> bool:
    """Check if Google Calendar credentials are configured."""
    return bool(CLIENT_ID and CLIENT_SECRET
                and not CLIENT_ID.startswith("your_")
                and not CLIENT_SECRET.startswith("your_"))


def get_auth_url(state: str = "") -> str:
    """Generate Google OAuth2 authorization URL."""
    if not is_configured():
        return ""

    from urllib.parse import urlencode, quote_plus
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.events",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params, quote_via=quote_plus)}"


async def exchange_code(code: str) -> Optional[dict]:
    """Exchange authorization code for access and refresh tokens."""
    if not is_configured():
        return None

    import httpx
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post("https://oauth2.googleapis.com/token", data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
            })
            if resp.status_code == 200:
                return resp.json()  # { access_token, refresh_token, expires_in, ... }
            else:
                print(f"⚠️ Calendar token exchange failed: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        print(f"⚠️ Calendar token exchange error: {e}")
    return None


async def refresh_access_token(refresh_token: str) -> Optional[str]:
    """Refresh an expired access token."""
    if not is_configured():
        return None

    import httpx
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post("https://oauth2.googleapis.com/token", data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            })
            if resp.status_code == 200:
                return resp.json().get("access_token")
    except Exception as e:
        print(f"⚠️ Calendar token refresh error: {e}")
    return None


async def create_workout_event(
    access_token: str,
    workout_name: str,
    date: datetime,
    duration_minutes: int = 45,
    description: str = "",
) -> Optional[dict]:
    """Create a workout event in Google Calendar."""
    import httpx
    try:
        start_time = date.replace(hour=7, minute=0, second=0)  # Default: 7 AM
        end_time = start_time + timedelta(minutes=duration_minutes)

        event = {
            "summary": f"🏋️ {workout_name} — ArogyaMitra",
            "description": description or f"Workout: {workout_name}\nPowered by ArogyaMitra",
            "start": {"dateTime": start_time.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "Asia/Kolkata"},
            "colorId": "6",  # Orange
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 30},
                    {"method": "popup", "minutes": 10},
                ],
            },
        }

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                json=event,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code in (200, 201):
                return resp.json()
            else:
                print(f"⚠️ Calendar event creation failed: {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Calendar event creation error: {e}")
    return None


async def create_meal_event(
    access_token: str,
    meal_name: str,
    meal_type: str,
    date: datetime,
    calories: int = 0,
) -> Optional[dict]:
    """Create a meal reminder in Google Calendar."""
    import httpx

    meal_times = {"breakfast": 8, "lunch": 13, "dinner": 20, "snack": 16}
    hour = meal_times.get(meal_type.lower(), 12)

    try:
        start_time = date.replace(hour=hour, minute=0, second=0)
        end_time = start_time + timedelta(minutes=30)

        event = {
            "summary": f"🍽️ {meal_type.title()}: {meal_name} — ArogyaMitra",
            "description": f"Meal: {meal_name}\nCalories: {calories} cal\nPowered by ArogyaMitra",
            "start": {"dateTime": start_time.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "Asia/Kolkata"},
            "colorId": "2",  # Green
            "reminders": {
                "useDefault": False,
                "overrides": [{"method": "popup", "minutes": 15}],
            },
        }

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                json=event,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code in (200, 201):
                return resp.json()
    except Exception as e:
        print(f"⚠️ Calendar meal event error: {e}")
    return None


async def sync_weekly_plan(
    access_token: str,
    workout_days: list,
    nutrition_days: list = None,
) -> dict:
    """Sync an entire weekly plan to Google Calendar."""
    results = {"workouts_synced": 0, "meals_synced": 0, "errors": 0}
    today = datetime.now()

    for i, day in enumerate(workout_days):
        date = today + timedelta(days=i)
        if day.get("rest_day"):
            continue
        try:
            result = await create_workout_event(
                access_token=access_token,
                workout_name=day.get("focus_area", f"Day {i+1} Workout"),
                date=date,
                duration_minutes=day.get("duration_minutes", 45),
                description=f"Exercises: {', '.join(e.get('name','') for e in day.get('exercises', [])[:5])}",
            )
            if result:
                results["workouts_synced"] += 1
            else:
                results["errors"] += 1
        except Exception:
            results["errors"] += 1

    if nutrition_days:
        for i, day in enumerate(nutrition_days):
            date = today + timedelta(days=i)
            for meal_type in ["breakfast", "lunch", "dinner"]:
                meal = day.get(meal_type)
                if meal:
                    try:
                        result = await create_meal_event(
                            access_token=access_token,
                            meal_name=meal.get("name", meal_type),
                            meal_type=meal_type,
                            date=date,
                            calories=meal.get("calories", 0),
                        )
                        if result:
                            results["meals_synced"] += 1
                    except Exception:
                        results["errors"] += 1

    return results
