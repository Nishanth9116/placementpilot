"""Starlette application serving the PlacementPilot web dashboard and REST API."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from src.web import api

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


async def serve_index(request):
    """Serve the single-page application entry point."""
    index_file = STATIC_DIR / "index.html"
    return FileResponse(index_file)


# REST API Routes
routes = [
    # Authentication & Session
    Route("/api/auth/login", api.login_student, methods=["POST"]),
    Route("/api/auth/register", api.register_student, methods=["POST"]),
    Route("/api/auth/logout", api.logout_student, methods=["POST"]),
    Route("/api/auth/me", api.get_current_student, methods=["GET"]),

    # Departments (All College Departments)
    Route("/api/departments", api.list_departments, methods=["GET"]),
    Route("/api/departments", api.create_department, methods=["POST"]),
    Route("/api/departments/{id:int}", api.delete_department, methods=["DELETE"]),

    # Dashboard & Overview
    Route("/api/overview", api.get_overview_stats, methods=["GET"]),

    # Students
    Route("/api/students", api.list_students, methods=["GET"]),
    Route("/api/students", api.create_or_update_student, methods=["POST"]),
    Route("/api/students/{id:int}", api.get_student, methods=["GET"]),
    Route("/api/students/{id:int}", api.delete_student, methods=["DELETE"]),
    Route("/api/students/{id:int}/summary", api.get_student_summary, methods=["GET"]),

    # Companies & Jobs
    Route("/api/companies", api.list_companies, methods=["GET"]),
    Route("/api/companies", api.create_company, methods=["POST"]),
    Route("/api/jobs", api.list_jobs, methods=["GET"]),
    Route("/api/jobs", api.create_job, methods=["POST"]),
    Route("/api/jobs/{id:int}", api.get_job, methods=["GET"]),
    Route("/api/jobs/{id:int}", api.delete_job, methods=["DELETE"]),
    Route("/api/jobs/{id:int}/analysis", api.generate_job_analysis, methods=["POST"]),

    # Applications & Interview Pipeline
    Route("/api/applications", api.list_applications, methods=["GET"]),
    Route("/api/applications", api.apply_job, methods=["POST"]),
    Route("/api/applications/{id:int}/status", api.update_application_status, methods=["PATCH"]),
    Route("/api/applications/{id:int}/rounds", api.list_application_rounds, methods=["GET"]),
    Route("/api/applications/{id:int}/rounds", api.schedule_round, methods=["POST"]),
    Route("/api/rounds/{id:int}", api.update_round_outcome, methods=["PATCH"]),
    Route("/api/interviews/upcoming", api.list_upcoming_interviews, methods=["GET"]),

    # AI Placement Prep & Tools
    Route("/api/prep/eligibility", api.evaluate_eligibility, methods=["GET"]),
    Route("/api/prep/skill-gap", api.get_skill_gap_analysis, methods=["GET"]),
    Route("/api/prep/questions", api.list_questions, methods=["GET"]),
    Route("/api/prep/mock-interview", api.log_mock_interview, methods=["POST"]),
    Route("/api/generator/follow-up-email", api.generate_email, methods=["POST"]),

    # Static Assets & Frontend SPA
    Mount("/static", app=StaticFiles(directory=str(STATIC_DIR)), name="static"),
    Route("/", serve_index, methods=["GET"]),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

@asynccontextmanager
async def lifespan(app):
    """Ensure database schema and sample data exist upon startup."""
    try:
        from src.db.init_db import initialize_database, seed_sample_data
        initialize_database()
        seed_sample_data()
    except Exception as e:
        import logging
        logging.getLogger("uvicorn.error").warning("Database startup initialization check: %s", e)
    yield


app = Starlette(routes=routes, middleware=middleware, lifespan=lifespan)


def run_server(host: str = None, port: int = None) -> None:
    """Run the web server using uvicorn."""
    import uvicorn
    if host is None:
        host = os.getenv("HOST", "0.0.0.0")
    if port is None:
        port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.web.app:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()

