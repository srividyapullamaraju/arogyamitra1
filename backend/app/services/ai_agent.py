import os
import json
import time
from groq import Groq

class ArogyaMitraAgent:
    def __init__(self):
        self.groq_client = None
        self.initialize_ai_clients()

    def initialize_ai_clients(self):
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            self.groq_client = Groq(api_key=api_key)
            print("✅ Groq AI client initialized")
        else:
            print("⚠️ No Groq API key found — using fallback plans")

    def _call_groq(self, system_prompt: str, user_prompt: str, max_tokens: int = 3000) -> str:
        if not self.groq_client:
            return None
        for attempt in range(3):
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"Groq attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)
        return None

    def _extract_json(self, text: str) -> dict:
        if not text:
            return None
        try:
            return json.loads(text)
        except:
            pass
        try:
            start = text.find("{")
            end   = text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except:
            pass
        try:
            start = text.find("[")
            end   = text.rfind("]") + 1
            if start != -1 and end > start:
                return {"days": json.loads(text[start:end])}
        except:
            pass
        return None

    def generate_workout_plan(self, user_data: dict) -> dict:
        system = (
            "You are an expert fitness coach for Indian users. "
            "ALWAYS respond with valid JSON only. No explanation, no markdown, no extra text."
        )
        user_prompt = f"""
Generate a 7-day personalized workout plan for:
- Age: {user_data.get('age', 25)}
- Gender: {user_data.get('gender', 'male')}
- Fitness Level: {user_data.get('fitness_level', 'beginner')}
- Goal: {user_data.get('fitness_goal', 'weight_loss')}
- Preference: {user_data.get('workout_preference', 'home')}
- Weight: {user_data.get('weight', 70)}kg

Return ONLY this JSON structure:
{{
  "days": [
    {{
      "day": "Monday",
      "focus_area": "Chest & Triceps",
      "duration_minutes": 45,
      "rest_day": false,
      "warmup": "5 min light cardio",
      "cool_down": "5 min stretching",
      "daily_tip": "Stay hydrated!",
      "exercises": [
        {{
          "name": "Push Ups",
          "sets": 3,
          "reps": "12",
          "rest_seconds": 60,
          "description": "Classic push up for chest",
          "youtube_search_query": "push ups proper form tutorial"
        }}
      ]
    }}
  ]
}}
Make Sunday a rest day. Include 3-5 exercises per day.
"""
        raw = self._call_groq(system, user_prompt, max_tokens=4000)
        plan = self._extract_json(raw)
        if not plan:
            print("⚠️ Using fallback workout plan")
            return self._fallback_workout_plan(user_data)
        return plan

    def generate_nutrition_plan(self, user_data: dict, health_data: dict) -> dict:
        system = (
            "You are an expert Indian nutritionist. "
            "ALWAYS respond with valid JSON only. No markdown, no extra text."
        )
        user_prompt = f"""
Generate a 7-day Indian meal plan for:
- Age: {user_data.get('age', 25)}
- Gender: {user_data.get('gender', 'male')}
- Goal: {user_data.get('fitness_goal', 'weight_loss')}
- Diet: {user_data.get('diet_preference', 'vegetarian')}
- Target Calories: {user_data.get('calorie_target', 1800)}
- Allergies: {user_data.get('allergies', 'none')}

Return ONLY this JSON:
{{
  "days": [
    {{
      "day": "Monday",
      "breakfast": {{
        "name": "Idli Sambar",
        "calories": 350,
        "protein_g": 12,
        "carbs_g": 60,
        "fat_g": 5,
        "ingredients": ["idli", "sambar", "coconut chutney"],
        "time": "7:00 AM"
      }},
      "lunch": {{
        "name": "Dal Rice",
        "calories": 450,
        "protein_g": 18,
        "carbs_g": 75,
        "fat_g": 8,
        "ingredients": ["dal", "rice", "ghee"],
        "time": "1:00 PM"
      }},
      "dinner": {{
        "name": "Roti Sabzi",
        "calories": 400,
        "protein_g": 14,
        "carbs_g": 65,
        "fat_g": 9,
        "ingredients": ["roti", "mixed sabzi", "curd"],
        "time": "7:30 PM"
      }},
      "snacks": [
        {{"name": "Banana", "calories": 90}},
        {{"name": "Green Tea", "calories": 5}}
      ],
      "total_calories": 1295
    }}
  ]
}}
Use authentic Indian foods. All 7 days must be different.
"""
        raw = self._call_groq(system, user_prompt, max_tokens=4000)
        plan = self._extract_json(raw)
        if not plan:
            print("⚠️ Using fallback nutrition plan")
            return self._fallback_nutrition_plan()
        return plan

    def aromi_coach_chat(self, message: str, user_data: dict, conversation_history: list) -> str:
        system = """You are AROMI, a warm empathetic AI wellness coach for ArogyaMitra.
Speak in a friendly tone, occasionally mixing Hindi words (Namaste, ji, bilkul, etc.).
You help users with their fitness and nutrition plans.
When users mention travel, injury, or mood changes — offer to adjust their plan.
Always be motivating, specific, and caring. Keep responses concise (2-4 sentences)."""

        messages = [{"role": "system", "content": system}]
        for msg in conversation_history[-10:]:
            messages.append(msg)
        messages.append({"role": "user", "content": message})

        if not self.groq_client:
            return "Namaste ji! 🙏 I'm AROMI. Please add your Groq API key to activate me! 💚"

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.8,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AROMI chat error: {e}")
            return "Namaste ji! 🙏 Having a small technical issue. Please try again! 💚"

    def adjust_plan_dynamically(self, reason: str, duration_days: int, current_plan: dict, user_data: dict) -> dict:
        system = "You are a fitness coach. Respond with valid JSON only."
        user_prompt = f"""
The user needs plan adjustment for: "{reason}" for {duration_days} days.
Create a modified workout plan with lighter/travel-friendly exercises.
Keep the same JSON structure. Return ONLY valid JSON.
"""
        raw = self._call_groq(system, user_prompt, max_tokens=2000)
        plan = self._extract_json(raw)
        return plan if plan else current_plan

    def analyze_health(self, health_data: dict) -> dict:
        bmi = health_data.get("bmi", 22)
        if bmi < 18.5:     category = "Underweight"
        elif bmi < 25:     category = "Normal weight"
        elif bmi < 30:     category = "Overweight"
        else:              category = "Obese"
        return {
            "bmi_category": category,
            "health_insights": [
                f"Your BMI of {bmi} indicates {category.lower()}",
                "Regular exercise will significantly improve your health",
                "Stay hydrated — drink 8 glasses of water daily",
            ],
            "recommended_calorie_target": 1800,
            "recommended_workout_intensity": "moderate",
            "safety_notes": ["Consult a doctor before starting intense exercise"],
        }

    def _fallback_workout_plan(self, user_data: dict) -> dict:
        days_data = [
            ("Monday",    "Chest & Triceps",  False),
            ("Tuesday",   "Back & Biceps",    False),
            ("Wednesday", "Legs",             False),
            ("Thursday",  "Shoulders & Core", False),
            ("Friday",    "Full Body",        False),
            ("Saturday",  "Cardio",           False),
            ("Sunday",    "Rest",             True),
        ]
        days = []
        for day, focus, rest in days_data:
            if rest:
                days.append({
                    "day": day, "focus_area": "Rest", "rest_day": True,
                    "duration_minutes": 0, "exercises": [],
                    "warmup": "", "cool_down": "", "daily_tip": "Rest and recover!"
                })
            else:
                days.append({
                    "day": day, "focus_area": focus, "rest_day": False,
                    "duration_minutes": 45,
                    "warmup": "5 min light cardio",
                    "cool_down": "5 min stretching",
                    "daily_tip": "Push yourself today!",
                    "exercises": [
                        {"name": "Push Ups", "sets": 3, "reps": "12", "rest_seconds": 60,
                         "description": "Classic push up", "youtube_search_query": "push ups form"},
                        {"name": "Squats", "sets": 3, "reps": "15", "rest_seconds": 60,
                         "description": "Bodyweight squat", "youtube_search_query": "squat form tutorial"},
                        {"name": "Plank", "sets": 3, "reps": "30s", "rest_seconds": 45,
                         "description": "Core hold", "youtube_search_query": "plank exercise tutorial"},
                    ]
                })
        return {"days": days}

    def _fallback_nutrition_plan(self) -> dict:
        meals = [
            {"breakfast": {"name":"Idli Sambar","calories":350,"protein_g":12,"carbs_g":60,"fat_g":5,
                          "ingredients":["idli","sambar","coconut chutney"],"time":"7:00 AM"},
             "lunch":     {"name":"Dal Rice","calories":450,"protein_g":18,"carbs_g":75,"fat_g":8,
                          "ingredients":["dal","rice","ghee","pickle"],"time":"1:00 PM"},
             "dinner":    {"name":"Roti Sabzi","calories":400,"protein_g":14,"carbs_g":65,"fat_g":9,
                          "ingredients":["roti","mixed sabzi","curd"],"time":"7:30 PM"},
             "snacks":    [{"name":"Banana","calories":90},{"name":"Green Tea","calories":5}],
             "total_calories": 1295},
        ]
        days_list = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        plan = {"days": []}
        for i, day in enumerate(days_list):
            meal = meals[i % len(meals)].copy()
            meal["day"] = day
            plan["days"].append(meal)
        return plan


# singleton
ai_agent = ArogyaMitraAgent()