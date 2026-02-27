# ArogyaMitra - Complete User Workflow Guide

## 🎯 What is ArogyaMitra?

ArogyaMitra is an AI-powered fitness and wellness platform that provides:
- Personalized workout plans
- Custom Indian nutrition plans
- Progress tracking
- AI chatbot coach (ARO-mi)
- Charity points system (earn points for completing workouts)

---

## 📱 Complete User Journey

### 1. **Registration & Login**

**New User:**
1. Go to `http://localhost:5173/`
2. Click "Get Started" or "Register"
3. Fill in:
   - Full Name
   - Email
   - Username
   - Password
4. Click "Create Account"
5. You'll be automatically logged in and redirected to `/health-assessment`

**Existing User:**
1. Go to `http://localhost:5173/login`
2. Enter username/email and password
3. Click "Login"
4. Redirected to `/dashboard`

---

### 2. **Health Assessment** (First Time Setup)

**Purpose:** Collect your health data to generate personalized plans

**Location:** `/health-assessment`

**Questions (14 total):**
1. Age
2. Gender (Male/Female/Other)
3. Height (cm)
4. Weight (kg)
5. Fitness Level (Beginner/Intermediate/Advanced)
6. Fitness Goal (Weight Loss/Muscle Gain/General Fitness/Strength/Endurance)
7. Workout Preference (Home/Gym/Outdoor/Mixed)
8. Workout Time (Morning/Evening)
9. Medical History (optional)
10. Health Conditions (optional)
11. Injuries (optional)
12. Allergies (optional)
13. Medications (optional)
14. Calendar Sync (Yes/No)

**What Happens After Submission:**
1. ✅ Assessment saved to database
2. ✅ AI generates personalized 7-day workout plan
3. ✅ AI generates personalized 7-day nutrition plan
4. ✅ Redirected to Dashboard
5. ✅ Plans are now visible on Workouts and Nutrition pages

---

### 3. **Dashboard** (Main Hub)

**Location:** `/dashboard`

**What You See:**
- Welcome message with your name
- **4 Stat Cards:**
  - 🏋️ Workouts Completed
  - 🔥 Calories Burned
  - ⚡ Current Streak (days)
  - 💚 Charity Points

- **Today's Workout Card:**
  - Shows today's workout (based on day of week)
  - "Browse Workouts" button if no plan
  - "Start Workout" button if plan exists

- **Today's Nutrition Card:**
  - Shows today's meals
  - "Create Meal Plan" button if no plan
  - "View Full Plan" button if plan exists

- **ARO-mi Chat Button** (bottom right):
  - Click to open AI chatbot
  - Ask fitness/nutrition questions
  - Get personalized advice

**If No Assessment Completed:**
- Purple banner appears: "Complete Your Health Assessment"
- Click "Start Assessment →" button

---

### 4. **Workouts Page**

**Location:** `/workouts`

**Features:**
- **Plan Overview Card:**
  - Plan name and description
  - Duration (weeks)
  - Workouts per week

- **Workout Cards (7 days):**
  - Day number and name
  - Focus area (e.g., "Chest & Triceps")
  - Duration and estimated calories
  - List of exercises with sets/reps
  - "Start Workout" or "Completed ✓" button

- **Generate New Plan Button:**
  - Click "✨ Generate New Plan" to create a fresh workout plan
  - Uses AI to generate based on your profile

**How to Complete a Workout:**
1. Click "Start Workout" on any day
2. System marks it as completed
3. Earn +5 charity points
4. Updates your stats

---

### 5. **Nutrition Page**

**Location:** `/nutrition`

**Features:**
- **Plan Overview Card:**
  - Daily calorie target
  - Number of meals
  - Plan description

- **Today's Meals:**
  - Breakfast, Lunch, Dinner cards
  - Each shows:
    - Meal name and time
    - Calories, Protein, Carbs, Fats
    - Ingredients list
  - "Log Meal" button for each

- **Shopping List (Sidebar):**
  - Ingredients needed for the week
  - Quantities listed

- **Generate New Plan Button:**
  - Click "✨ Generate New Plan"
  - Creates new 7-day meal plan

**How to Log a Meal:**
1. Click "Log Meal" on any meal card
2. System marks it as logged
3. Earn +2 charity points
4. Updates your progress

---

### 6. **Progress Tracking Page**

**Location:** `/progress`

**Features:**
- **Summary Cards:**
  - Total Workouts
  - Total Calories Burned
  - Current Streak

- **Progress History:**
  - View by Week/Month/Year
  - Shows date, weight, body fat %, notes

- **Achievements:**
  - Unlock badges for milestones
  - Examples: "First Step", "Workout Warrior", "Beast Mode"

- **Log Progress Form (Sidebar):**
  - Weight (kg)
  - Body Fat % (optional)
  - Notes (optional)
  - Click "Log Progress" to save

**Quick Stats:**
- Starting Weight
- Current Weight
- Weight Change

---

### 7. **ARO-mi AI Chatbot**

**Location:** Floating button on Dashboard (bottom right)

**Features:**
- Chat with AI wellness coach
- Ask questions about:
  - Workout form and technique
  - Nutrition advice
  - Meal suggestions
  - Motivation and tips
  - Plan adjustments

**Example Questions:**
- "What's a good breakfast for weight loss?"
- "How do I do push-ups correctly?"
- "I'm traveling, can you adjust my plan?"
- "What should I eat after a workout?"

**How It Works:**
1. Click "Chat with ARO-mi" button
2. Type your message
3. ARO-mi responds with personalized advice
4. Conversation history is saved

---

## 🔄 Daily Workflow

### Morning:
1. Login to Dashboard
2. Check "Today's Workout"
3. Check "Today's Nutrition"
4. Complete workout → Earn +5 points
5. Log meals → Earn +2 points per meal

### Throughout Day:
- Chat with ARO-mi for advice
- Log progress (weight, notes)
- View achievements

### Weekly:
- Generate new plans if needed
- Review progress history
- Check streak and stats

---

## 🎁 Charity Points System

**How to Earn:**
- Complete a workout: +5 points
- Log a meal: +2 points
- Burn calories: +1 point per 10 calories

**Purpose:**
- Points contribute to charity donations
- Displayed on Dashboard
- Motivates consistent activity

---

## 🚀 Quick Start Guide

1. **Register** → Create account
2. **Health Assessment** → Answer 14 questions
3. **Dashboard** → View your personalized overview
4. **Workouts** → See your 7-day workout plan
5. **Nutrition** → See your 7-day meal plan
6. **Start Training** → Complete workouts and log meals
7. **Track Progress** → Monitor your journey
8. **Chat with ARO-mi** → Get personalized advice

---

## 🔧 Technical Details

**Frontend:** React + Vite + Tailwind CSS
**Backend:** FastAPI + SQLite + Groq AI
**Authentication:** JWT tokens
**AI Model:** Llama 3.3 70B (via Groq)

**Pages:**
- `/` - Landing page
- `/login` - Login page
- `/register` - Registration page
- `/health-assessment` - Health questionnaire
- `/dashboard` - Main hub
- `/workouts` - Workout plans
- `/nutrition` - Meal plans
- `/progress` - Progress tracking

---

## ❓ Troubleshooting

**"No workout plan" showing:**
- Complete the health assessment first
- Click "Generate New Plan" on Workouts page

**"No meal plan" showing:**
- Complete the health assessment first
- Click "Generate New Plan" on Nutrition page

**ARO-mi not responding:**
- Check if you're logged in
- Check browser console for errors
- Verify GROQ_API_KEY in backend/.env

**Plans not generating:**
- Check backend terminal for errors
- Verify AI service is running
- Check GROQ_API_KEY is valid

---

## 📊 Data Flow

```
User Registration
    ↓
Health Assessment (14 questions)
    ↓
AI Generates Plans
    ├─→ Workout Plan (7 days)
    └─→ Nutrition Plan (7 days)
    ↓
Dashboard Shows Overview
    ↓
User Completes Activities
    ├─→ Workouts (+5 points)
    ├─→ Meals (+2 points)
    └─→ Progress Logs
    ↓
Stats Update in Real-time
    ↓
Chat with ARO-mi for Guidance
```

---

## 🎯 Key Features Summary

✅ AI-powered personalized plans
✅ Indian nutrition focus
✅ Progress tracking with charts
✅ Achievement system
✅ Charity points motivation
✅ AI chatbot coach
✅ Calendar sync option
✅ Shopping list generation
✅ Workout video links
✅ Real-time stats updates

---

**Need Help?** Chat with ARO-mi or check the console for errors!
