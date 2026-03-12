from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date, timedelta
import json

from app.database import get_db
from app.models.user import User, NutritionPlan, ProgressRecord
from app.routers.auth import get_current_user

router = APIRouter()

class GenerateNutritionRequest(BaseModel):
    calorie_target: Optional[int] = 1800
    diet_type: Optional[str] = "vegetarian"
    allergies: Optional[str] = ""

class CompleteMealRequest(BaseModel):
    meal_id: Optional[str] = None
    meal_type: Optional[str] = "lunch"

@router.post("/generate")
def generate_nutrition(
    data: GenerateNutritionRequest = GenerateNutritionRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app.services.ai_agent import ai_agent
        user_data = {
            "age": current_user.age,
            "gender": current_user.gender,
            "weight": current_user.weight,
            "height": current_user.height,
            "fitness_goal": str(current_user.fitness_goal or "maintenance"),
            "diet_preference": str(current_user.diet_preference or "vegetarian"),
            "calorie_target": data.calorie_target,
            "allergies": data.allergies,
        }
        plan = ai_agent.generate_nutrition_plan(user_data, {})
    except Exception as e:
        print(f"Nutrition AI error: {e}")
        plan = get_fallback_nutrition_plan()

    db.query(NutritionPlan).filter(
        NutritionPlan.user_id == current_user.id,
        NutritionPlan.is_active == True
    ).update({"is_active": False})

    today = date.today()
    nutrition_plan = NutritionPlan(
        user_id=current_user.id,
        plan_data=json.dumps(plan),
        week_start=today,
        week_end=today + timedelta(days=6),
        calorie_target=data.calorie_target,
        diet_type=data.diet_type,
        allergies=data.allergies,
        is_active=True
    )
    db.add(nutrition_plan)
    db.commit()
    return {"plan": plan, "plan_id": nutrition_plan.id}


@router.get("/current")
def get_current_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(NutritionPlan).filter(
        NutritionPlan.user_id == current_user.id,
        NutritionPlan.is_active == True
    ).order_by(NutritionPlan.created_at.desc()).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No active nutrition plan")

    return {"plan": json.loads(plan.plan_data), "plan_id": plan.id}


@router.get("/today")
def get_today_nutrition(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(NutritionPlan).filter(
        NutritionPlan.user_id == current_user.id,
        NutritionPlan.is_active == True
    ).order_by(NutritionPlan.created_at.desc()).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No active nutrition plan")

    plan_data = json.loads(plan.plan_data)
    days = plan_data.get("days", [])
    day_names = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    today_name = day_names[date.today().weekday()]

    today_meals = None
    for day in days:
        if day.get("day", "").lower() == today_name.lower():
            today_meals = day
            break

    if not today_meals and days:
        today_meals = days[0]

    return {"today": today_meals, "day_name": today_name}


@router.post("/meal/complete")
def complete_meal(
    data: CompleteMealRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()
    record = db.query(ProgressRecord).filter(
        ProgressRecord.user_id == current_user.id,
        ProgressRecord.date == today
    ).first()

    if record:
        record.meal_tracked = True
    else:
        record = ProgressRecord(
            user_id=current_user.id,
            date=today,
            meal_tracked=True,
        )
        db.add(record)

    current_user.charity_donations = (current_user.charity_donations or 0) + 2
    db.commit()
    return {"message": "Meal tracked! +2 charity points 💚"}


@router.get("/shopping-list")
def get_shopping_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(NutritionPlan).filter(
        NutritionPlan.user_id == current_user.id,
        NutritionPlan.is_active == True
    ).order_by(NutritionPlan.created_at.desc()).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No active nutrition plan")

    plan_data = json.loads(plan.plan_data)
    ingredient_count = {}

    for day in plan_data.get("days", []):
        for meal_type in ["breakfast", "lunch", "dinner"]:
            meal = day.get(meal_type, {})
            for ing in meal.get("ingredients", []):
                ing = ing.strip().lower()
                if ing:
                    ingredient_count[ing] = ingredient_count.get(ing, 0) + 1

    shopping_list = [{"ingredient": k, "count": v} for k, v in sorted(ingredient_count.items())]
    return {"shopping_list": shopping_list}


class SwapMealRequest(BaseModel):
    day: str  # e.g. "Monday"
    meal_type: str  # e.g. "breakfast", "lunch", "dinner"
    current_meal: Optional[str] = ""


@router.post("/meal/swap")
def swap_meal(
    data: SwapMealRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Use AI to generate an alternative meal, then update the stored plan."""
    plan_record = db.query(NutritionPlan).filter(
        NutritionPlan.user_id == current_user.id,
        NutritionPlan.is_active == True
    ).order_by(NutritionPlan.created_at.desc()).first()

    if not plan_record:
        raise HTTPException(status_code=404, detail="No active nutrition plan")

    plan_data = json.loads(plan_record.plan_data)
    diet_pref = current_user.diet_preference or "vegetarian"

    # Ask AI for an alternative
    prompt = (
        f"Suggest ONE alternative Indian {diet_pref} {data.meal_type} meal "
        f"to replace '{data.current_meal}'. Keep similar calories. "
        f"Reply ONLY with valid JSON (no markdown):\n"
        f'{{"name":"...","calories":...,"protein_g":...,"carbs_g":...,"fat_g":...,'
        f'"ingredients":["...","..."],"time":"..."}}'
    )

    try:
        from app.services.ai_agent import ai_agent
        system_prompt = "You are a nutrition expert. Return ONLY valid JSON, no markdown."
        user_prompt = (
            f"Suggest ONE alternative Indian {diet_pref} {data.meal_type} meal "
            f"to replace '{data.current_meal}'. Keep similar calories. "
            f"Reply ONLY with valid JSON:\n"
            f'{{"name":"...","calories":...,"protein_g":...,"carbs_g":...,"fat_g":...,'
            f'"ingredients":["...","..."],"time":"..."}}'
        )
        raw = ai_agent._call_groq(system_prompt, user_prompt, max_tokens=500)
        new_meal = ai_agent._extract_json(raw)
        if not new_meal or "name" not in new_meal:
            raise ValueError("Invalid AI response")
    except Exception as e:
        print(f"Swap AI error: {e}")
        raise HTTPException(status_code=500, detail="AI could not generate alternative")

    # Update the plan in-place
    for day_obj in plan_data.get("days", []):
        if day_obj.get("day", "").lower() == data.day.lower():
            day_obj[data.meal_type.lower()] = new_meal
            break

    plan_record.plan_data = json.dumps(plan_data)
    db.commit()

    return {"new_meal": new_meal}


@router.get("/grocery-redirect/{ingredient}")
def grocery_redirect(ingredient: str):
    return {"url": f"https://www.bigbasket.com/ps/?q={ingredient}"}


def get_fallback_nutrition_plan():
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    plan = {"days": []}
    meals = [
        {"breakfast": {"name":"Idli Sambar","calories":350,"protein_g":12,"carbs_g":60,"fat_g":5,"ingredients":["idli","sambar","coconut chutney"],"time":"7:00 AM"},
         "lunch": {"name":"Dal Rice","calories":450,"protein_g":18,"carbs_g":75,"fat_g":8,"ingredients":["dal","rice","ghee","pickle"],"time":"1:00 PM"},
         "dinner": {"name":"Roti Sabzi","calories":400,"protein_g":14,"carbs_g":65,"fat_g":9,"ingredients":["roti","mixed vegetable sabzi","curd"],"time":"7:30 PM"},
         "snacks": [{"name":"Banana","calories":90},{"name":"Green Tea","calories":5}],
         "total_calories": 1295},
    ]
    for i, day in enumerate(days):
        meal = meals[i % len(meals)].copy()
        meal["day"] = day
        plan["days"].append(meal)
    return plan