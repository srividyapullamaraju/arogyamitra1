"""
Simple calendar router — generates Google Calendar URLs.
No OAuth tokens needed! The frontend opens these URLs directly.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/url")
def get_calendar_url(title: str, details: str = "", start: str = "", end: str = "", location: str = ""):
    """Generate a Google Calendar event creation URL."""
    import urllib.parse

    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{start}/{end}" if start and end else "",
        "details": details,
        "location": location,
    }
    # Remove empty params
    params = {k: v for k, v in params.items() if v}

    url = f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"
    return {"url": url}
