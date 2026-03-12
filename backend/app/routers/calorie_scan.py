from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
import os, json

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()


@router.post("/scan")
async def scan_food_calories(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze a food photo using Gemini Vision and return estimated calories + macros."""
    contents = await image.read()

    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"food_name": "Error", "total_calories": 0, "items": [],
                "health_tip": "Gemini API key not configured.", "error": "No API key"}

    genai.configure(api_key=api_key)

    prompt = (
        "You are a nutrition expert. Analyze this food image and identify each food item visible. "
        "For each item, estimate calories, protein (g), carbs (g), and fat (g). "
        "Reply ONLY with valid JSON (no markdown, no explanation):\n"
        '{"food_name":"overall dish name","items":[{"name":"...","calories":...,"protein_g":...,"carbs_g":...,"fat_g":...}],'
        '"total_calories":...,"total_protein_g":...,"total_carbs_g":...,"total_fat_g":...,'
        '"health_tip":"one short practical tip about this meal"}'
    )

    image_part = {
        "mime_type": image.content_type or "image/jpeg",
        "data": contents
    }

    # Try multiple models in case one hits quota
    models_to_try = [
        "gemini-3-flash-preview",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash-8b",
        "gemini-1.5-flash",
        "gemini-2.0-flash-lite"
    ]
    raw = None
    last_error = None

    for model_name in models_to_try:
        try:
            print(f"Trying model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([prompt, image_part])
            raw = response.text.strip()
            print(f"Success with {model_name}")
            break
        except Exception as e:
            last_error = e
            print(f"Model {model_name} failed: {e}")
            continue

    if raw is None:
        print(f"All models failed. Last error: {last_error}")
        return {
            "food_name": "Unknown", "items": [], "total_calories": 0,
            "total_protein_g": 0, "total_carbs_g": 0, "total_fat_g": 0,
            "health_tip": "All AI models hit quota. Please try again later.",
            "error": str(last_error)
        }

    try:
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
        except Exception:
            pass
        return {"food_name": "Unknown", "total_calories": 0, "items": [],
                "health_tip": "Could not parse AI response. Try again.", "error": "Parse error"}
