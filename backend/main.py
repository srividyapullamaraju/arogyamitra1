from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback

app = FastAPI(title="ArogyaMitra API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = traceback.format_exc()
    print(f"❌ ERROR: {error_detail}")
    return JSONResponse(status_code=500, content={"detail": str(exc)})

# ── Routers ────────────────────────────────────────
from app.routers import auth, workouts, nutrition, progress, health_assessment, ai_coach, calendar

app.include_router(auth.router,              prefix="/api/auth",              tags=["Auth"])
app.include_router(workouts.router,          prefix="/api/workouts",          tags=["Workouts"])
app.include_router(nutrition.router,         prefix="/api/nutrition",         tags=["Nutrition"])
app.include_router(progress.router,          prefix="/api/progress",          tags=["Progress"])
app.include_router(health_assessment.router, prefix="/api/health-assessment", tags=["Health"])
app.include_router(ai_coach.router,          prefix="/api",                  tags=["AI Coach"])
app.include_router(calendar.router,          prefix="/api/calendar",         tags=["Calendar"])

@app.on_event("startup")
async def startup():
    from app.database import create_tables
    create_tables()
    print("✅ All routers loaded!")
    print("🚀 ArogyaMitra API running at http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")

@app.get("/")
def root():
    return {"message": "ArogyaMitra API Running ✅"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)