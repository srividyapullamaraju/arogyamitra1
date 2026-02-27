from sqlalchemy import Column, Integer, String, Boolean, Float, Text, Date, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

# ── Enums ──────────────────────────────────────────
class FitnessLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class FitnessGoal(str, enum.Enum):
    weight_loss = "weight_loss"
    weight_gain = "weight_gain"
    muscle_gain = "muscle_gain"
    maintenance = "maintenance"
    endurance = "endurance"

class WorkoutPreference(str, enum.Enum):
    home = "home"
    gym = "gym"
    outdoor = "outdoor"
    hybrid = "hybrid"

class DietPreference(str, enum.Enum):
    vegetarian = "vegetarian"
    non_vegetarian = "non_vegetarian"
    vegan = "vegan"
    keto = "keto"
    paleo = "paleo"

class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"

# ── Models ─────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id                  = Column(Integer, primary_key=True, index=True)
    email               = Column(String, unique=True, index=True, nullable=False)
    username            = Column(String, unique=True, index=True, nullable=False)
    hashed_password     = Column(String, nullable=False)
    full_name           = Column(String)
    age                 = Column(Integer)
    gender              = Column(String)
    height              = Column(Float)
    weight              = Column(Float)
    fitness_level       = Column(String, default="beginner")
    fitness_goal        = Column(String, default="maintenance")
    workout_preference  = Column(String, default="home")
    diet_preference     = Column(String, default="vegetarian")
    role                = Column(String, default="user")
    is_active           = Column(Boolean, default=True)
    streak_points       = Column(Integer, default=0)
    total_workouts      = Column(Integer, default=0)
    charity_donations   = Column(Float, default=0.0)
    phone               = Column(String)
    bio                 = Column(Text)
    profile_photo_url   = Column(String)
    calendar_token      = Column(String, default="")
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    updated_at          = Column(DateTime(timezone=True), onupdate=func.now())

    workout_plans       = relationship("WorkoutPlan", back_populates="user")
    nutrition_plans     = relationship("NutritionPlan", back_populates="user")
    health_assessments  = relationship("HealthAssessment", back_populates="user")
    progress_records    = relationship("ProgressRecord", back_populates="user")
    chat_sessions       = relationship("ChatSession", back_populates="user")


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_data   = Column(Text)  # JSON string
    week_start  = Column(Date)
    week_end    = Column(Date)
    fitness_goal= Column(String)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    user        = relationship("User", back_populates="workout_plans")


class NutritionPlan(Base):
    __tablename__ = "nutrition_plans"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_data       = Column(Text)  # JSON string
    week_start      = Column(Date)
    week_end        = Column(Date)
    calorie_target  = Column(Integer)
    diet_type       = Column(String)
    allergies       = Column(String)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    user            = relationship("User", back_populates="nutrition_plans")


class HealthAssessment(Base):
    __tablename__ = "health_assessments"

    id                      = Column(Integer, primary_key=True, index=True)
    user_id                 = Column(Integer, ForeignKey("users.id"), nullable=False)
    age                     = Column(Integer)
    gender                  = Column(String)
    height                  = Column(Float)
    weight                  = Column(Float)
    bmi                     = Column(Float)
    medical_history         = Column(Text)
    injuries                = Column(Text)
    allergies               = Column(Text)
    medications             = Column(Text)
    health_conditions       = Column(Text)
    fitness_level           = Column(String)
    fitness_goal            = Column(String)
    workout_preference      = Column(String)
    workout_time_preference = Column(String)
    calendar_sync           = Column(Boolean, default=False)
    created_at              = Column(DateTime(timezone=True), server_default=func.now())

    user                    = relationship("User", back_populates="health_assessments")


class ProgressRecord(Base):
    __tablename__ = "progress_records"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), nullable=False)
    date                = Column(Date)
    calories_burned     = Column(Float, default=0)
    workout_completed   = Column(Boolean, default=False)
    meal_tracked        = Column(Boolean, default=False)
    workout_duration    = Column(Integer, default=0)
    weight              = Column(Float)
    notes               = Column(Text)
    created_at          = Column(DateTime(timezone=True), server_default=func.now())

    user                = relationship("User", back_populates="progress_records")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    message      = Column(Text)
    response     = Column(Text)
    session_type = Column(String, default="aromi")
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    user         = relationship("User", back_populates="chat_sessions")