from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date, timedelta
import json

from app.database import get_db
from app.models.user import User, WorkoutPlan, ProgressRecord
from app.routers.auth import get_current_user

router = APIRouter()

class CompleteExerciseRequest(BaseModel):
    exercise_id: Optional[str] = None
    calories_burned: Optional[float] = 0
    duration_minutes: Optional[int] = 0

@router.post("/generate")
def generate_workout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app.services.ai_agent import ai_agent
        user_data = {
            "age": current_user.age,
            "gender": current_user.gender,
            "fitness_level": str(current_user.fitness_level or "beginner"),
            "fitness_goal": str(current_user.fitness_goal or "maintenance"),
            "workout_preference": str(current_user.workout_preference or "home"),
            "weight": current_user.weight,
            "height": current_user.height,
        }
        plan = ai_agent.generate_workout_plan(user_data)
    except Exception as e:
        print(f"AI error: {e}")
        plan = get_fallback_plan()

    # deactivate old plans
    db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == current_user.id,
        WorkoutPlan.is_active == True
    ).update({"is_active": False})

    today = date.today()
    workout_plan = WorkoutPlan(
        user_id=current_user.id,
        plan_data=json.dumps(plan),
        week_start=today,
        week_end=today + timedelta(days=6),
        fitness_goal=str(current_user.fitness_goal or "maintenance"),
        is_active=True
    )
    db.add(workout_plan)
    db.commit()
    db.refresh(workout_plan)
    return {"plan": plan, "plan_id": workout_plan.id}


@router.get("/current")
def get_current_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == current_user.id,
        WorkoutPlan.is_active == True
    ).order_by(WorkoutPlan.created_at.desc()).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No active workout plan found")

    return {"plan": json.loads(plan.plan_data), "plan_id": plan.id}


@router.get("/today")
def get_today_workout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == current_user.id,
        WorkoutPlan.is_active == True
    ).order_by(WorkoutPlan.created_at.desc()).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No active workout plan")

    plan_data = json.loads(plan.plan_data)
    days = plan_data.get("days", plan_data.get("weekly_plan", []))
    
    day_names = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    today_name = day_names[date.today().weekday()]

    today_workout = None
    for day in days:
        if day.get("day", "").lower() == today_name.lower():
            today_workout = day
            break

    if not today_workout and days:
        today_workout = days[0]

    return {"today": today_workout, "day_name": today_name}


@router.post("/complete")
def complete_exercise(
    data: CompleteExerciseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()
    record = db.query(ProgressRecord).filter(
        ProgressRecord.user_id == current_user.id,
        ProgressRecord.date == today
    ).first()

    if record:
        record.calories_burned = (record.calories_burned or 0) + (data.calories_burned or 0)
        record.workout_completed = True
        record.workout_duration = (record.workout_duration or 0) + (data.duration_minutes or 0)
    else:
        record = ProgressRecord(
            user_id=current_user.id,
            date=today,
            calories_burned=data.calories_burned or 0,
            workout_completed=True,
            workout_duration=data.duration_minutes or 0,
        )
        db.add(record)

    current_user.total_workouts = (current_user.total_workouts or 0) + 1
    current_user.charity_donations = (current_user.charity_donations or 0) + 5
    db.commit()
    return {"message": "Exercise completed! +5 charity points 💚", "total_workouts": current_user.total_workouts}


@router.get("/history")
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plans = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == current_user.id
    ).order_by(WorkoutPlan.created_at.desc()).all()
    return {"history": [{"id": p.id, "week_start": str(p.week_start), "is_active": p.is_active} for p in plans]}


def get_fallback_plan():
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    focuses = ["Chest & Triceps","Back & Biceps","Legs","Shoulders","Core","Full Body","Rest"]
    plan = {"days": []}
    for i, day in enumerate(days):
        if i == 6:
            plan["days"].append({"day": day, "focus_area": "Rest", "rest_day": True, "duration_minutes": 0, "exercises": []})
        else:
            plan["days"].append({
                "day": day,
                "focus_area": focuses[i],
                "rest_day": False,
                "duration_minutes": 45,
                "warmup": "5 min light cardio",
                "cool_down": "5 min stretching",
                "daily_tip": "Stay hydrated!",
                "exercises": [
                    {"name": "Push Ups", "sets": 3, "reps": "12", "rest_seconds": 60, "description": "Classic push up", "youtube_search_query": "push ups proper form"},
                    {"name": "Squats", "sets": 3, "reps": "15", "rest_seconds": 60, "description": "Bodyweight squat", "youtube_search_query": "squat proper form"},
                    {"name": "Plank", "sets": 3, "reps": "30 seconds", "rest_seconds": 45, "description": "Core plank hold", "youtube_search_query": "plank exercise form"},
                ]
            })
    return plan


@router.get("/youtube-search")
async def youtube_search(q: str):
    """Search YouTube for exercise tutorial videos."""
    from app.services.youtube_service import search_exercise_video
    result = await search_exercise_video(q)
    return result