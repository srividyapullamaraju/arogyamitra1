from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date, timedelta
import json

from app.database import get_db
from app.models.user import User, ProgressRecord, HealthAssessment
from app.routers.auth import get_current_user

router = APIRouter()

class LogProgressRequest(BaseModel):
    calories_burned: Optional[float] = 0
    workout_completed: Optional[bool] = False
    meal_tracked: Optional[bool] = False
    weight: Optional[float] = None
    notes: Optional[str] = None

@router.get("/summary")
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = db.query(ProgressRecord).filter(
        ProgressRecord.user_id == current_user.id
    ).order_by(ProgressRecord.date.desc()).all()

    total_calories = sum(r.calories_burned or 0 for r in records)
    meals_tracked = sum(1 for r in records if r.meal_tracked)

    # calculate streak
    streak = 0
    check_date = date.today()
    for _ in range(365):
        found = any(r.date == check_date and r.workout_completed for r in records)
        if found:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # get bmi
    latest_assessment = db.query(HealthAssessment).filter(
        HealthAssessment.user_id == current_user.id
    ).order_by(HealthAssessment.created_at.desc()).first()
    bmi = latest_assessment.bmi if latest_assessment else None

    return {
        "total_workouts": current_user.total_workouts or 0,
        "total_calories_burned": round(total_calories, 1),
        "current_streak": streak,
        "meals_tracked": meals_tracked,
        "charity_donations": current_user.charity_donations or 0,
        "bmi": bmi,
        "weight_lost": 0,
    }


@router.get("/history")
def get_history(
    period: Optional[str] = "week",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    days_map = {"week": 7, "month": 30, "3months": 90, "year": 365}
    days = days_map.get(period, 7)
    start_date = date.today() - timedelta(days=days)

    records = db.query(ProgressRecord).filter(
        ProgressRecord.user_id == current_user.id,
        ProgressRecord.date >= start_date
    ).order_by(ProgressRecord.date.desc()).all()

    return {"history": [
        {"date": str(r.date), "calories_burned": r.calories_burned,
         "workout_completed": r.workout_completed, "meal_tracked": r.meal_tracked,
         "weight": r.weight, "notes": r.notes}
        for r in records
    ]}


@router.post("/log")
def log_progress(
    data: LogProgressRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()
    record = db.query(ProgressRecord).filter(
        ProgressRecord.user_id == current_user.id,
        ProgressRecord.date == today
    ).first()

    if record:
        if data.calories_burned: record.calories_burned = (record.calories_burned or 0) + data.calories_burned
        if data.workout_completed: record.workout_completed = True
        if data.meal_tracked: record.meal_tracked = True
        if data.weight: record.weight = data.weight
        if data.notes: record.notes = data.notes
    else:
        record = ProgressRecord(
            user_id=current_user.id,
            date=today,
            calories_burned=data.calories_burned or 0,
            workout_completed=data.workout_completed or False,
            meal_tracked=data.meal_tracked or False,
            weight=data.weight,
            notes=data.notes,
        )
        db.add(record)

    if data.calories_burned:
        current_user.charity_donations = (current_user.charity_donations or 0) + (data.calories_burned // 10)

    db.commit()
    return {"message": "Progress logged ✅"}


@router.get("/achievements")
def get_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = db.query(ProgressRecord).filter(ProgressRecord.user_id == current_user.id).all()
    total_calories = sum(r.calories_burned or 0 for r in records)
    meals_tracked = sum(1 for r in records if r.meal_tracked)
    total_workouts = current_user.total_workouts or 0

    streak = 0
    check_date = date.today()
    for _ in range(365):
        found = any(r.date == check_date and r.workout_completed for r in records)
        if found:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    achievements = [
        {"name":"First Step","description":"Complete your first workout","icon":"⚡","target":1,"current":total_workouts,"category":"workouts"},
        {"name":"Workout Warrior","description":"Complete 5 workouts","icon":"💪","target":5,"current":total_workouts,"category":"workouts"},
        {"name":"Beast Mode","description":"Complete 10 workouts","icon":"🦾","target":10,"current":total_workouts,"category":"workouts"},
        {"name":"Nutrition Ninja","description":"Track 5 meals","icon":"🥗","target":5,"current":meals_tracked,"category":"nutrition"},
        {"name":"Fire Starter","description":"Burn 500 calories","icon":"🔥","target":500,"current":total_calories,"category":"calories"},
        {"name":"Fire Master","description":"Burn 1000 calories","icon":"🔥🔥","target":1000,"current":total_calories,"category":"calories"},
        {"name":"Consistency Counts","description":"3-day workout streak","icon":"📅","target":3,"current":streak,"category":"streak"},
        {"name":"Streak King","description":"7-day workout streak","icon":"👑","target":7,"current":streak,"category":"streak"},
    ]

    for a in achievements:
        a["percentage"] = min(100, round((a["current"] / a["target"]) * 100))
        a["unlocked"] = a["current"] >= a["target"]

    return {"achievements": achievements}


@router.get("/charts")
def get_charts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    last_7 = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
    records = db.query(ProgressRecord).filter(
        ProgressRecord.user_id == current_user.id,
        ProgressRecord.date >= last_7[0]
    ).all()

    records_by_date = {r.date: r for r in records}
    calories_chart = [
        {"date": str(d), "calories": records_by_date.get(d, ProgressRecord(calories_burned=0)).calories_burned or 0}
        for d in last_7
    ]
    streak_chart = [
        {"day": d.strftime("%a"), "completed": 1 if (records_by_date.get(d) and records_by_date[d].workout_completed) else 0}
        for d in last_7
    ]

    return {"calories_chart": calories_chart, "streak_chart": streak_chart}