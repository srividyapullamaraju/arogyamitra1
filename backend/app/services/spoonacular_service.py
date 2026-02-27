"""
Spoonacular API integration — fetch nutrition data, recipes, and meal info.
Falls back to local data when no API key is configured.
"""
import os
import httpx

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY", "")
BASE_URL = "https://api.spoonacular.com"


async def search_recipes(query: str, diet: str = "", number: int = 5) -> list:
    """
    Search Spoonacular for recipes matching a query.
    Returns list of { id, title, image, calories, readyInMinutes, servings }.
    """
    if SPOONACULAR_API_KEY and not SPOONACULAR_API_KEY.startswith("your_"):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{BASE_URL}/recipes/complexSearch", params={
                    "apiKey": SPOONACULAR_API_KEY,
                    "query": query,
                    "diet": diet,
                    "number": number,
                    "addRecipeNutrition": True,
                    "cuisine": "Indian",
                })
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for r in data.get("results", []):
                        nutrients = {n["name"]: n["amount"] for n in r.get("nutrition", {}).get("nutrients", [])}
                        results.append({
                            "id": r["id"],
                            "title": r["title"],
                            "image": r.get("image", ""),
                            "calories": round(nutrients.get("Calories", 0)),
                            "protein_g": round(nutrients.get("Protein", 0)),
                            "carbs_g": round(nutrients.get("Carbohydrates", 0)),
                            "fat_g": round(nutrients.get("Fat", 0)),
                            "ready_in_minutes": r.get("readyInMinutes", 30),
                            "servings": r.get("servings", 2),
                            "source": "spoonacular",
                        })
                    return results
                else:
                    print(f"⚠️ Spoonacular API error {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"⚠️ Spoonacular API failed: {e}")

    return _fallback_recipes(query)


async def get_recipe_info(recipe_id: int) -> dict:
    """Get detailed recipe information by ID."""
    if SPOONACULAR_API_KEY and not SPOONACULAR_API_KEY.startswith("your_"):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{BASE_URL}/recipes/{recipe_id}/information",
                    params={"apiKey": SPOONACULAR_API_KEY, "includeNutrition": True}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    nutrients = {n["name"]: n["amount"] for n in data.get("nutrition", {}).get("nutrients", [])}
                    return {
                        "id": data["id"],
                        "title": data["title"],
                        "image": data.get("image", ""),
                        "instructions": data.get("instructions", ""),
                        "ingredients": [i["original"] for i in data.get("extendedIngredients", [])],
                        "calories": round(nutrients.get("Calories", 0)),
                        "protein_g": round(nutrients.get("Protein", 0)),
                        "carbs_g": round(nutrients.get("Carbohydrates", 0)),
                        "fat_g": round(nutrients.get("Fat", 0)),
                        "ready_in_minutes": data.get("readyInMinutes", 30),
                        "source": "spoonacular",
                    }
        except Exception as e:
            print(f"⚠️ Spoonacular recipe info failed: {e}")

    return {"id": recipe_id, "title": "Recipe not found", "source": "fallback"}


async def get_nutrition_info(food_name: str) -> dict:
    """Get nutrition info for a food item."""
    if SPOONACULAR_API_KEY and not SPOONACULAR_API_KEY.startswith("your_"):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{BASE_URL}/food/ingredients/search", params={
                    "apiKey": SPOONACULAR_API_KEY,
                    "query": food_name,
                    "number": 1,
                })
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    if results:
                        return {
                            "id": results[0]["id"],
                            "name": results[0]["name"],
                            "image": results[0].get("image", ""),
                            "source": "spoonacular",
                        }
        except Exception as e:
            print(f"⚠️ Spoonacular nutrition search failed: {e}")

    return {"name": food_name, "source": "fallback"}


def _fallback_recipes(query: str) -> list:
    """Return mock Indian recipes when no API key is available."""
    fallback_db = {
        "breakfast": [
            {"id": 1, "title": "Masala Oats Upma", "calories": 280, "protein_g": 10, "carbs_g": 45, "fat_g": 8, "ready_in_minutes": 15},
            {"id": 2, "title": "Moong Dal Chilla", "calories": 220, "protein_g": 14, "carbs_g": 30, "fat_g": 5, "ready_in_minutes": 20},
        ],
        "lunch": [
            {"id": 3, "title": "Dal Tadka with Brown Rice", "calories": 450, "protein_g": 18, "carbs_g": 65, "fat_g": 12, "ready_in_minutes": 35},
            {"id": 4, "title": "Rajma Chawal", "calories": 480, "protein_g": 20, "carbs_g": 70, "fat_g": 10, "ready_in_minutes": 40},
        ],
        "dinner": [
            {"id": 5, "title": "Palak Paneer with Roti", "calories": 380, "protein_g": 16, "carbs_g": 40, "fat_g": 18, "ready_in_minutes": 30},
            {"id": 6, "title": "Chicken Tikka with Naan", "calories": 520, "protein_g": 35, "carbs_g": 45, "fat_g": 20, "ready_in_minutes": 45},
        ],
    }

    q_lower = query.lower()
    for key, recipes in fallback_db.items():
        if key in q_lower:
            return [{**r, "image": "", "servings": 2, "source": "fallback"} for r in recipes]

    # default
    return [
        {"id": 99, "title": f"Indian {query.title()}", "calories": 350, "protein_g": 15,
         "carbs_g": 50, "fat_g": 10, "image": "", "ready_in_minutes": 30, "servings": 2, "source": "fallback"}
    ]
