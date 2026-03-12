from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.user import User, HealthAssessment
from app.routers.auth import get_current_user

router = APIRouter()

class AssessmentRequest(BaseModel):
    age: int
    gender: str
    height: float
    weight: float
    fitness_level: str
    fitness_goal: str
    workout_preference: str
    workout_time_preference: str
    medical_history: Optional[str] = ""
    health_conditions: Optional[str] = ""
    injuries: Optional[str] = ""
    allergies: Optional[str] = ""
    medications: Optional[str] = ""
    diet_preference: Optional[str] = "vegetarian"
    calendar_sync: Optional[bool] = False

@router.post("/assessment/submit")
def submit_assessment(
    data: AssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bmi = round(data.weight / ((data.height / 100) ** 2), 1)

    assessment = HealthAssessment(
        user_id=current_user.id,
        age=data.age,
        gender=data.gender,
        height=data.height,
        weight=data.weight,
        bmi=bmi,
        medical_history=data.medical_history,
        injuries=data.injuries,
        allergies=data.allergies,
        medications=data.medications,
        health_conditions=data.health_conditions,
        fitness_level=data.fitness_level,
        fitness_goal=data.fitness_goal,
        workout_preference=data.workout_preference,
        workout_time_preference=data.workout_time_preference,
        calendar_sync=data.calendar_sync,
    )
    db.add(assessment)

    # update user profile too
    current_user.age = data.age
    current_user.gender = data.gender
    current_user.height = data.height
    current_user.weight = data.weight
    current_user.fitness_level = data.fitness_level
    current_user.fitness_goal = data.fitness_goal
    current_user.workout_preference = data.workout_preference
    current_user.diet_preference = data.diet_preference or "vegetarian"

    db.commit()
    db.refresh(assessment)
    return {"success": True, "bmi": bmi, "assessment_id": assessment.id}


@router.get("/assessment/latest")
def get_latest_assessment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    assessment = db.query(HealthAssessment).filter(
        HealthAssessment.user_id == current_user.id
    ).order_by(HealthAssessment.created_at.desc()).first()

    if not assessment:
        raise HTTPException(status_code=404, detail="No assessment found")

    return {
        "id": assessment.id,
        "bmi": assessment.bmi,
        "age": assessment.age,
        "gender": assessment.gender,
        "height": assessment.height,
        "weight": assessment.weight,
        "fitness_level": assessment.fitness_level,
        "fitness_goal": assessment.fitness_goal,
        "workout_preference": assessment.workout_preference,
        "health_conditions": assessment.health_conditions,
        "injuries": assessment.injuries,
        "allergies": assessment.allergies,
    }