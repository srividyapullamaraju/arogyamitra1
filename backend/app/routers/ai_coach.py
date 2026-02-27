from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json

from app.database import get_db
from app.models.user import User, WorkoutPlan, NutritionPlan, ChatSession
from app.routers.auth import get_current_user
from app.services.ai_agent import ai_agent

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = []

class AdjustPlanRequest(BaseModel):
    reason: str
    duration_days: Optional[int] = 3

@router.post("/aromi-chat")
def aromi_chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_data = {
        "name": current_user.full_name,
        "age": current_user.age,
        "fitness_goal": str(current_user.fitness_goal or "maintenance"),
        "fitness_level": str(current_user.fitness_level or "beginner"),
    }

    response = ai_agent.aromi_coach_chat(
        message=data.message,
        user_data=user_data,
        conversation_history=data.conversation_history
    )

    chat = ChatSession(
        user_id=current_user.id,
        message=data.message,
        response=response,
        session_type="aromi"
    )
    db.add(chat)
    db.commit()

    return {"response": response, "timestamp": datetime.utcnow().isoformat()}


@router.post("/adjust-plan")
def adjust_plan(
    data: AdjustPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_plan_record = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == current_user.id,
        WorkoutPlan.is_active == True
    ).order_by(WorkoutPlan.created_at.desc()).first()

    if not current_plan_record:
        raise HTTPException(status_code=404, detail="No active workout plan")

    current_plan = json.loads(current_plan_record.plan_data)
    user_data = {
        "fitness_level": str(current_user.fitness_level or "beginner")
    }

    adjusted = ai_agent.adjust_plan_dynamically(
        data.reason, data.duration_days, current_plan, user_data
    )

    from datetime import date, timedelta
    new_plan = WorkoutPlan(
        user_id=current_user.id,
        plan_data=json.dumps(adjusted),
        week_start=date.today(),
        week_end=date.today() + timedelta(days=6),
        fitness_goal=str(current_user.fitness_goal or "maintenance"),
        is_active=True
    )
    current_plan_record.is_active = False
    db.add(new_plan)
    db.commit()

    return {"message": f"Plan adjusted for {data.reason}", "plan": adjusted}


@router.get("/chat-history")
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chats = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).limit(20).all()

    return {"history": [
        {
            "message": c.message,
            "response": c.response,
            "timestamp": str(c.created_at)
        }
        for c in chats
    ]}