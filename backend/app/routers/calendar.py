"""
Google Calendar router — OAuth2 flow + sync endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.services import calendar_service

router = APIRouter()


@router.get("/status")
async def calendar_status(current_user: User = Depends(get_current_user)):
    """Check if Google Calendar is configured and user has connected."""
    configured = calendar_service.is_configured()
    connected = bool(getattr(current_user, 'calendar_token', None))
    return {
        "configured": configured,
        "connected": connected,
        "message": (
            "Connected to Google Calendar ✅" if connected
            else "Google Calendar not connected" if configured
            else "Google Calendar credentials not configured in .env"
        ),
    }


@router.get("/connect")
async def calendar_connect(current_user: User = Depends(get_current_user)):
    """Start Google Calendar OAuth2 flow."""
    if not calendar_service.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Google Calendar not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env"
        )
    auth_url = calendar_service.get_auth_url(state=str(current_user.id))
    return {"auth_url": auth_url}


@router.get("/callback")
async def calendar_callback(code: str, state: str = "", db: Session = Depends(get_db)):
    """Handle Google OAuth2 callback — exchange code for tokens."""
    tokens = await calendar_service.exchange_code(code)
    if not tokens:
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code")

    # Save refresh token to user record
    if state:
        try:
            user_id = int(state)
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.calendar_token = tokens.get("refresh_token", "")
                db.commit()
        except (ValueError, Exception) as e:
            print(f"⚠️ Failed to save calendar token: {e}")

    # Redirect back to frontend
    return RedirectResponse(url="http://localhost:5173/dashboard?calendar=connected")


@router.post("/sync")
async def sync_to_calendar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync current workout and nutrition plans to Google Calendar."""
    refresh_token = getattr(current_user, 'calendar_token', None)
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Google Calendar not connected. Connect first.")

    # Get fresh access token
    access_token = await calendar_service.refresh_access_token(refresh_token)
    if not access_token:
        raise HTTPException(status_code=401, detail="Calendar token expired. Please reconnect.")

    # Get user's current plans
    from app.models.user import WorkoutPlan, NutritionPlan
    import json

    workout_plan = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == current_user.id
    ).order_by(WorkoutPlan.created_at.desc()).first()

    nutrition_plan = db.query(NutritionPlan).filter(
        NutritionPlan.user_id == current_user.id
    ).order_by(NutritionPlan.created_at.desc()).first()

    workout_days = []
    nutrition_days = []

    if workout_plan and workout_plan.plan_data:
        try:
            plan = json.loads(workout_plan.plan_data) if isinstance(workout_plan.plan_data, str) else workout_plan.plan_data
            workout_days = plan.get("days", [])
        except (json.JSONDecodeError, Exception):
            pass

    if nutrition_plan and nutrition_plan.plan_data:
        try:
            plan = json.loads(nutrition_plan.plan_data) if isinstance(nutrition_plan.plan_data, str) else nutrition_plan.plan_data
            nutrition_days = plan.get("days", [])
        except (json.JSONDecodeError, Exception):
            pass

    if not workout_days and not nutrition_days:
        raise HTTPException(status_code=400, detail="No plans to sync. Generate plans first.")

    results = await calendar_service.sync_weekly_plan(
        access_token=access_token,
        workout_days=workout_days,
        nutrition_days=nutrition_days,
    )

    return {
        "message": "Calendar sync complete! 📅",
        "workouts_synced": results["workouts_synced"],
        "meals_synced": results["meals_synced"],
        "errors": results["errors"],
    }


@router.post("/disconnect")
async def disconnect_calendar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect Google Calendar."""
    current_user.calendar_token = ""
    db.commit()
    return {"message": "Google Calendar disconnected"}
