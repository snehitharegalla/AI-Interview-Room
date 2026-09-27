import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import init_db
from backend.routes import (
    auth,
    candidate,
    recruiter,
    question_bank,
    analytics,
    notifications,
    interview,
    report
)

# Initialize database schema
init_db()

app = FastAPI(
    title="AI Interview Room Enterprise API",
    description="Adaptive Technical Interview & Recruitment Platform powered by GenAI & Deterministic Cognitive Profiling.",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix="/api/auth")
app.include_router(candidate.router, prefix="/api/candidate")
app.include_router(recruiter.router, prefix="/api/recruiter")
app.include_router(question_bank.router, prefix="/api/question-bank")
app.include_router(analytics.router, prefix="/api/recruiter/analytics")
app.include_router(notifications.router, prefix="/api/notifications")

# Legacy routes preserved for existing tests & backward compatibility
app.include_router(interview.router, prefix="/api/interview")
app.include_router(report.router, prefix="/api/interview")
app.include_router(report.router, prefix="/api/reports")
app.include_router(interview.router, prefix="/interview")
app.include_router(report.router, prefix="/interview")

# Static frontend assets
FRONTEND_DIR = PROJECT_ROOT / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_landing():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/index.html")
    async def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/login")
    @app.get("/login.html")
    async def serve_login():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/candidate")
    @app.get("/candidate-dashboard.html")
    async def serve_candidate_dashboard():
        return FileResponse(str(FRONTEND_DIR / "candidate-dashboard.html"))

    @app.get("/interview.html")
    async def serve_interview_room():
        return FileResponse(str(FRONTEND_DIR / "interview.html"))

    @app.get("/recruiter")
    @app.get("/recruiter.html")
    async def serve_recruiter_portal():
        return FileResponse(str(FRONTEND_DIR / "recruiter.html"))

    @app.get("/report.html")
    async def serve_report_page():
        return FileResponse(str(FRONTEND_DIR / "report.html"))


@app.get("/api/health")
async def health_check():
    from backend.services.ai_service import ai_service
    return {
        "status": "healthy",
        "service": "AI Interview Room Enterprise",
        "version": "2.0.0",
        "provider": ai_service.provider
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
