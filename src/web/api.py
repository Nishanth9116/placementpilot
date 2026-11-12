"""REST API endpoints for PlacementPilot Web Dashboard.

Connects frontend interactions directly to existing repositories and domain services.
"""

import json
from typing import Any, Dict, Optional
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.db.connection import get_db_connection
from src.db.repositories import (
    ApplicationRepository,
    CompanyRepository,
    DepartmentRepository,
    QuestionRepository,
    StudentRepository,
)
from src.services.eligibility import EligibilityService
from src.services.prep import PrepService
from src.services.tracker import TrackerService
from src.mcp_server.prompts.placement_prompts import (
    get_follow_up_email_prompt,
    get_interview_prep_prompt,
    get_job_analysis_prompt,
)


def error_response(message: str, status_code: int = 400) -> JSONResponse:
    """Return a standard JSON error response."""
    return JSONResponse({"error": message, "success": False}, status_code=status_code)


def success_response(data: Any, status_code: int = 200) -> JSONResponse:
    """Return a standard JSON success response."""
    return JSONResponse({"data": data, "success": True}, status_code=status_code)


# ==============================================================================
# Authentication & Session Endpoints
# ==============================================================================

async def login_student(request: Request) -> JSONResponse:
    """Authenticate a student by USN / Register Number or Email."""
    try:
        body = await request.json()
    except Exception:
        return error_response("Invalid JSON body.")

    identifier = (body.get("identifier") or body.get("usn") or body.get("email") or "").strip()
    if not identifier:
        return error_response("Please enter your Register Number (USN) or College Email.")

    with get_db_connection() as conn:
        repo = StudentRepository(conn)
        student = repo.authenticate(identifier)
        if not student:
            return error_response(
                f"Candidate with identifier '{identifier}' not found. Please register first.",
                404,
            )

        token = f"token_{student['id']}_{student['usn']}"
        return success_response({
            "message": "Login successful.",
            "token": token,
            "student": student,
        })


async def register_student(request: Request) -> JSONResponse:
    """Register a new student from ANY college department."""
    try:
        body = await request.json()
    except Exception:
        return error_response("Invalid JSON body.")

    name = (body.get("name") or "").strip()
    usn = (body.get("usn") or "").strip()
    email = (body.get("email") or "").strip()
    phone = (body.get("phone") or "").strip()
    department = (body.get("department") or body.get("branch") or "").strip()
    year_of_study = (body.get("year_of_study") or "4th Year").strip()
    cgpa = body.get("cgpa")
    graduation_year = body.get("graduation_year", 2025)
    skills = body.get("skills", [])
    resume_path = body.get("resume_path")

    if not name or not usn or not email or not department or cgpa is None:
        return error_response("Missing required registration fields: name, usn, email, department, cgpa.")

    try:
        cgpa_val = float(cgpa)
        if not (0.0 <= cgpa_val <= 10.0):
            return error_response("CGPA must be between 0.0 and 10.0.")
    except ValueError:
        return error_response("Invalid CGPA value provided.")

    with get_db_connection() as conn:
        repo = StudentRepository(conn)

        # Check existing USN
        if repo.get_by_usn(usn):
            return error_response(f"A student with Register Number '{usn}' is already registered.", 409)

        # Check existing Email
        if repo.get_by_email(email):
            return error_response(f"A student with email '{email}' is already registered.", 409)

        student = repo.create(
            usn=usn,
            name=name,
            email=email,
            phone=phone,
            branch=department.upper(),
            department=department,
            year_of_study=year_of_study,
            cgpa=cgpa_val,
            graduation_year=int(graduation_year),
            skills=skills,
            resume_path=resume_path,
        )

        token = f"token_{student['id']}_{student['usn']}"
        return success_response({
            "message": "Student registration completed successfully.",
            "token": token,
            "student": student,
        }, status_code=201)


async def logout_student(request: Request) -> JSONResponse:
    """Clear session and log out."""
    return success_response({"message": "Logged out successfully."})


async def get_current_student(request: Request) -> JSONResponse:
    """Get currently authenticated student profile."""
    student_id = request.query_params.get("student_id")
    auth_header = request.headers.get("Authorization", "")
    
    sid: Optional[int] = None
    if student_id:
        try:
            sid = int(student_id)
        except ValueError:
            pass
    elif auth_header.startswith("Bearer token_"):
        parts = auth_header.replace("Bearer token_", "").split("_")
        if parts and parts[0].isdigit():
            sid = int(parts[0])

    if not sid:
        return error_response("Unauthorized: Missing or invalid authentication token.", 401)

    with get_db_connection() as conn:
        repo = StudentRepository(conn)
        student = repo.get_by_id(sid)
        if not student:
            return error_response("Student not found.", 404)
        return success_response(student)


# ==============================================================================
# Academic Department Endpoints
# ==============================================================================

async def list_departments(request: Request) -> JSONResponse:
    """List all registered academic departments."""
    with get_db_connection() as conn:
        repo = DepartmentRepository(conn)
        departments = repo.list_all()
        return success_response(departments)


async def create_department(request: Request) -> JSONResponse:
    """Allow admin to add a new academic department dynamically."""
    try:
        body = await request.json()
    except Exception:
        return error_response("Invalid JSON body.")

    name = (body.get("name") or "").strip()
    code = (body.get("code") or "").strip().upper()

    if not name:
        return error_response("Department name is required.")

    with get_db_connection() as conn:
        repo = DepartmentRepository(conn)
        existing = repo.get_by_name_or_code(name)
        if existing:
            return success_response(existing)

        dept = repo.create(name=name, code=code)
        return success_response(dept, status_code=201)


async def delete_department(request: Request) -> JSONResponse:
    """Delete an academic department."""
    dept_id = int(request.path_params["id"])
    with get_db_connection() as conn:
        repo = DepartmentRepository(conn)
        deleted = repo.delete(dept_id)
        if not deleted:
            return error_response(f"Department {dept_id} not found.", 404)
        return success_response({"message": f"Department {dept_id} deleted."})


# ==============================================================================
# Students Endpoints
# ==============================================================================

async def list_students(request: Request) -> JSONResponse:
    """List all students with optional filters."""
    branch = request.query_params.get("branch")
    department = request.query_params.get("department")
    min_cgpa = request.query_params.get("min_cgpa")
    min_cgpa_val = float(min_cgpa) if min_cgpa else None

    with get_db_connection() as conn:
        repo = StudentRepository(conn)
        students = repo.list_all(
            branch=branch,
            department=department,
            min_cgpa=min_cgpa_val,
            limit=100,
        )
        return success_response(students)


async def get_student(request: Request) -> JSONResponse:
    """Get single student details."""
    student_id = int(request.path_params["id"])
    with get_db_connection() as conn:
        repo = StudentRepository(conn)
        student = repo.get_by_id(student_id)
        if not student:
            return error_response(f"Student with ID {student_id} not found.", 404)
        return success_response(student)


async def create_or_update_student(request: Request) -> JSONResponse:
    """Create or update a student."""
    try:
        body = await request.json()
    except Exception:
        return error_response("Invalid JSON body.")

    usn = body.get("usn")
    name = body.get("name")
    email = body.get("email")
    phone = body.get("phone")
    branch = body.get("branch")
    department = body.get("department") or branch
    year_of_study = body.get("year_of_study")
    cgpa = body.get("cgpa")
    graduation_year = body.get("graduation_year", 2025)
    skills = body.get("skills", [])
    resume_path = body.get("resume_path")

    if not usn or not name or not email or not (branch or department) or cgpa is None:
        return error_response("Missing required fields: usn, name, email, department, cgpa.")

    try:
        cgpa_val = float(cgpa)
        if not (0.0 <= cgpa_val <= 10.0):
            return error_response("CGPA must be between 0.0 and 10.0.")
    except ValueError:
        return error_response("Invalid CGPA value.")

    with get_db_connection() as conn:
        repo = StudentRepository(conn)
        existing = repo.get_by_usn(usn.strip())
        if existing:
            student = repo.update(
                student_id=existing["id"],
                name=name.strip(),
                email=email.strip(),
                phone=phone.strip() if phone else None,
                branch=branch.strip().upper() if branch else department.strip().upper(),
                department=department.strip() if department else None,
                year_of_study=str(year_of_study) if year_of_study else None,
                cgpa=cgpa_val,
                graduation_year=int(graduation_year),
                skills=skills,
                resume_path=resume_path,
            )
            return success_response({"action": "updated", "student": student})
        else:
            student = repo.create(
                usn=usn.strip(),
                name=name.strip(),
                email=email.strip(),
                phone=phone.strip() if phone else None,
                branch=branch.strip().upper() if branch else department.strip().upper(),
                department=department.strip() if department else None,
                year_of_study=str(year_of_study) if year_of_study else "4th Year",
                cgpa=cgpa_val,
                graduation_year=int(graduation_year),
                skills=skills,
                resume_path=resume_path,
            )
            return success_response({"action": "created", "student": student}, status_code=201)


async def delete_student(request: Request) -> JSONResponse:
    """Delete student by ID."""
    student_id = int(request.path_params["id"])
    with get_db_connection() as conn:
        repo = StudentRepository(conn)
        deleted = repo.delete(student_id)
        if not deleted:
            return error_response(f"Student with ID {student_id} not found.", 404)
        return success_response({"message": f"Student {student_id} deleted successfully."})


async def get_student_summary(request: Request) -> JSONResponse:
    """Get placement metrics and summary for a student."""
    student_id = int(request.path_params["id"])
    with get_db_connection() as conn:
        tracker = TrackerService(conn)
        try:
            summary = tracker.get_student_placement_summary(student_id)
            return success_response(summary)
        except ValueError as e:
            return error_response(str(e), 404)


# ==============================================================================
# Companies & Jobs Endpoints
# ==============================================================================

async def list_companies(request: Request) -> JSONResponse:
    """List all registered companies."""
    industry = request.query_params.get("industry")
    with get_db_connection() as conn:
        repo = CompanyRepository(conn)
        companies = repo.list_companies(industry=industry)
        return success_response(companies)


async def create_company(request: Request) -> JSONResponse:
    """Create a new company."""
    try:
        body = await request.json()
    except Exception:
        return error_response("Invalid JSON body.")

    name = body.get("name")
    if not name or not name.strip():
        return error_response("Company name is required.")

    with get_db_connection() as conn:
        repo = CompanyRepository(conn)
        existing = repo.get_company_by_name(name.strip())
        if existing:
            return success_response(existing)
        company = repo.create_company(
            name=name.strip(),
            website=body.get("website"),
            industry=body.get("industry", "Technology"),
            description=body.get("description"),
        )
        return success_response(company, status_code=201)


async def list_jobs(request: Request) -> JSONResponse:
    """List job openings with optional filters."""
    company_id = request.query_params.get("company_id")
    status = request.query_params.get("status")
    min_ctc = request.query_params.get("min_ctc")
    branch = request.query_params.get("branch")

    cid = int(company_id) if company_id else None
    ctc_val = float(min_ctc) if min_ctc else None

    with get_db_connection() as conn:
        repo = CompanyRepository(conn)
        jobs = repo.list_jobs(
            company_id=cid,
            status=status,
            min_ctc=ctc_val,
            branch=branch,
            limit=100,
        )
        return success_response(jobs)


async def get_job(request: Request) -> JSONResponse:
    """Get single job opening details."""
    job_id = int(request.path_params["id"])
    with get_db_connection() as conn:
        repo = CompanyRepository(conn)
        job = repo.get_job_by_id(job_id)
        if not job:
            return error_response(f"Job with ID {job_id} not found.", 404)
        return success_response(job)


async def create_job(request: Request) -> JSONResponse:
    """Create a new job drive."""
    try:
        body = await request.json()
    except Exception:
        return error_response("Invalid JSON body.")

    company_name = body.get("company_name")
    company_id = body.get("company_id")
    role_title = body.get("role_title")
    ctc_lpa = body.get("ctc_lpa")

    if not role_title or ctc_lpa is None:
        return error_response("role_title and ctc_lpa are required.")

    with get_db_connection() as conn:
        repo = CompanyRepository(conn)
        if not company_id and company_name:
            comp = repo.get_company_by_name(company_name.strip())
            if not comp:
                comp = repo.create_company(name=company_name.strip())
            company_id = comp["id"]

        if not company_id:
            return error_response("Either company_id or company_name must be provided.")

        job = repo.create_job(
            company_id=int(company_id),
            role_title=role_title.strip(),
            job_description=body.get("job_description"),
            ctc_lpa=float(ctc_lpa),
            location=body.get("location", "On-site"),
            min_cgpa=float(body.get("min_cgpa", 0.0)),
            allowed_branches=body.get("allowed_branches", []),
            required_skills=body.get("required_skills", []),
            application_deadline=body.get("application_deadline"),
            status=body.get("status", "open"),
        )
        return success_response(job, status_code=201)


async def delete_job(request: Request) -> JSONResponse:
    """Delete a job drive."""
    job_id = int(request.path_params["id"])
    with get_db_connection() as conn:
        repo = CompanyRepository(conn)
        deleted = repo.delete_job(job_id)
        if not deleted:
            return error_response(f"Job with ID {job_id} not found.", 404)
        return success_response({"message": f"Job {job_id} deleted."})


# ==============================================================================
# Applications & Interviews Endpoints
# ==============================================================================

async def list_applications(request: Request) -> JSONResponse:
    """List student applications."""
    student_id = request.query_params.get("student_id")
    job_id = request.query_params.get("job_id")
    status = request.query_params.get("status")

    sid = int(student_id) if student_id else None
    jid = int(job_id) if job_id else None

    with get_db_connection() as conn:
        repo = ApplicationRepository(conn)
        apps = repo.list_applications(student_id=sid, job_id=jid, status=status, limit=100)
        return success_response(apps)


async def apply_job(request: Request) -> JSONResponse:
    """Submit an application."""
    try:
        body = await request.json()
    except Exception:
        return error_response("Invalid JSON body.")

    student_id = body.get("student_id")
    job_id = body.get("job_id")
    notes = body.get("notes")
    enforce = body.get("enforce_eligibility", True)

    if not student_id or not job_id:
        return error_response("student_id and job_id are required.")

    with get_db_connection() as conn:
        tracker = TrackerService(conn)
        try:
            app = tracker.apply_to_job(
                student_id=int(student_id),
                job_id=int(job_id),
                notes=notes,
                enforce_eligibility=bool(enforce),
            )
            return success_response(app, status_code=201)
        except ValueError as e:
            return error_response(str(e), 400)


async def update_application_status(request: Request) -> JSONResponse:
    """Update application pipeline status."""
    app_id = int(request.path_params["id"])
    try:
        body = await request.json()
    except Exception:
        return error_response("Invalid JSON body.")

    status = body.get("status")
    current_stage = body.get("current_stage")
    notes = body.get("notes")

    if not status:
        return error_response("status is required.")

    with get_db_connection() as conn:
        tracker = TrackerService(conn)
        try:
            updated = tracker.advance_stage(
                application_id=app_id,
                next_status=status,
                current_stage=current_stage,
                notes=notes,
            )
            return success_response(updated)
        except ValueError as e:
            return error_response(str(e), 400)


async def list_application_rounds(request: Request) -> JSONResponse:
    """List interview rounds for an application."""
    app_id = int(request.path_params["id"])
    with get_db_connection() as conn:
        repo = ApplicationRepository(conn)
        rounds = repo.list_rounds_for_application(app_id)
        return success_response(rounds)


async def schedule_round(request: Request) -> JSONResponse:
    """Schedule an interview round."""
    app_id = int(request.path_params["id"])
    try:
        body = await request.json()
    except Exception:
        return error_response("Invalid JSON body.")

    round_type = body.get("round_type")
    scheduled_at = body.get("scheduled_at")
    interviewer_notes = body.get("interviewer_notes")

    if not round_type:
        return error_response("round_type is required.")

    with get_db_connection() as conn:
        tracker = TrackerService(conn)
        try:
            round_rec = tracker.schedule_interview_round(
                application_id=app_id,
                round_type=round_type.strip(),
                scheduled_at=scheduled_at,
                interviewer_notes=interviewer_notes,
            )
            return success_response(round_rec, status_code=201)
        except ValueError as e:
            return error_response(str(e), 400)


async def update_round_outcome(request: Request) -> JSONResponse:
    """Update round outcome (cleared/failed)."""
    round_id = int(request.path_params["id"])
    try:
        body = await request.json()
    except Exception:
        return error_response("Invalid JSON body.")

    status = body.get("status")
    feedback = body.get("feedback")
    interviewer_notes = body.get("interviewer_notes")
    auto_advance = body.get("auto_advance", True)

    if not status:
        return error_response("status is required.")

    with get_db_connection() as conn:
        tracker = TrackerService(conn)
        try:
            round_rec = tracker.record_interview_outcome(
                round_id=round_id,
                status=status,
                feedback=feedback,
                interviewer_notes=interviewer_notes,
                auto_update_application=bool(auto_advance),
            )
            return success_response(round_rec)
        except ValueError as e:
            return error_response(str(e), 400)


async def list_upcoming_interviews(request: Request) -> JSONResponse:
    """List all upcoming interview schedules for calendar/agenda."""
    student_id = request.query_params.get("student_id")
    sid = int(student_id) if student_id else None

    with get_db_connection() as conn:
        repo = ApplicationRepository(conn)
        upcoming = repo.list_upcoming_interviews(student_id=sid)
        return success_response(upcoming)


# ==============================================================================
# AI Placement Prep, Skill Gap Analysis & Prompts
# ==============================================================================

async def evaluate_eligibility(request: Request) -> JSONResponse:
    """Check eligibility between student and job."""
    student_id = request.query_params.get("student_id")
    job_id = request.query_params.get("job_id")

    if not student_id or not job_id:
        return error_response("student_id and job_id query parameters are required.")

    with get_db_connection() as conn:
        s_repo = StudentRepository(conn)
        c_repo = CompanyRepository(conn)

        student = s_repo.get_by_id(int(student_id))
        job = c_repo.get_job_by_id(int(job_id))

        if not student:
            return error_response(f"Student {student_id} not found.", 404)
        if not job:
            return error_response(f"Job {job_id} not found.", 404)

        result = EligibilityService.evaluate(student, job)
        return success_response(result)


async def get_skill_gap_analysis(request: Request) -> JSONResponse:
    """Diagnose skill gaps and return recommended prep questions."""
    student_id = request.query_params.get("student_id")
    job_id = request.query_params.get("job_id")

    if not student_id or not job_id:
        return error_response("student_id and job_id query parameters are required.")

    with get_db_connection() as conn:
        prep = PrepService(conn)
        try:
            analysis = prep.analyze_skill_gaps(int(student_id), int(job_id))
            return success_response(analysis)
        except ValueError as e:
            return error_response(str(e), 400)


async def list_questions(request: Request) -> JSONResponse:
    """List placement prep questions."""
    category = request.query_params.get("category")
    topic = request.query_params.get("topic")
    difficulty = request.query_params.get("difficulty")
    company = request.query_params.get("company")

    with get_db_connection() as conn:
        repo = QuestionRepository(conn)
        questions = repo.list_questions(
            category=category,
            topic=topic,
            difficulty=difficulty,
            company=company,
            limit=50,
        )
        return success_response(questions)


async def log_mock_interview(request: Request) -> JSONResponse:
    """Record a mock interview practice session."""
    try:
        body = await request.json()
    except Exception:
        return error_response("Invalid JSON body.")

    student_id = body.get("student_id")
    topic = body.get("topic")
    score = body.get("score")
    feedback = body.get("feedback")
    transcript = body.get("transcript")

    if not student_id or not topic or score is None:
        return error_response("student_id, topic, and score are required.")

    with get_db_connection() as conn:
        prep = PrepService(conn)
        try:
            result = prep.log_and_evaluate_mock(
                student_id=int(student_id),
                topic=topic.strip(),
                score=float(score),
                feedback=feedback or "Completed practice session.",
                transcript=transcript,
            )
            return success_response(result, status_code=201)
        except ValueError as e:
            return error_response(str(e), 400)


async def generate_email(request: Request) -> JSONResponse:
    """Generate a follow-up email prompt and ready-to-use template."""
    try:
        body = await request.json()
    except Exception:
        return error_response("Invalid JSON body.")

    app_id = body.get("application_id")
    round_id = body.get("round_id")

    if not app_id or not round_id:
        return error_response("application_id and round_id are required.")

    try:
        messages = get_follow_up_email_prompt(int(app_id), int(round_id))
        prompt_text = messages[0].content.text

        # Generate standard template draft directly from database context
        with get_db_connection() as conn:
            a_repo = ApplicationRepository(conn)
            app = a_repo.get_by_id(int(app_id))
            round_rec = a_repo.get_round_by_id(int(round_id))

        draft_subject = f"Thank you - {app['role_title']} Interview ({app['student_name']})"
        draft_body = (
            f"Dear {app['company_name']} Recruitment Team,\n\n"
            f"Thank you for the opportunity to interview for the {app['role_title']} position today. "
            f"I truly enjoyed our discussion during {round_rec['round_type']}.\n\n"
            f"Our conversation further reinforced my enthusiasm for joining {app['company_name']} and "
            f"contributing my skills towards your engineering initiatives. "
            f"Please let me know if you need any additional details or work samples from my side.\n\n"
            f"Looking forward to hearing from you regarding the next steps.\n\n"
            f"Warm regards,\n"
            f"{app['student_name']}\n"
            f"{app['student_email']} | USN: {app['student_usn']}"
        )

        return success_response({
            "prompt": prompt_text,
            "draft_subject": draft_subject,
            "draft_body": draft_body,
        })
    except ValueError as e:
        return error_response(str(e), 400)


async def generate_job_analysis(request: Request) -> JSONResponse:
    """Generate an AI job drive breakdown."""
    job_id = int(request.path_params["id"])
    try:
        messages = get_job_analysis_prompt(job_id)
        prompt_text = messages[0].content.text
        return success_response({"prompt": prompt_text})
    except ValueError as e:
        return error_response(str(e), 404)


async def get_overview_stats(request: Request) -> JSONResponse:
    """Retrieve global dashboard metrics."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM students;")
        total_students = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM companies;")
        total_companies = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM jobs WHERE status = 'open';")
        active_jobs = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM applications;")
        total_applications = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM applications WHERE status = 'offered';")
        offers_extended = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM interview_rounds WHERE status = 'pending';")
        upcoming_interviews = c.fetchone()[0]

        # Top hiring companies
        c.execute("""
            SELECT c.name, COUNT(j.id) as drive_count, MAX(j.ctc_lpa) as max_ctc
            FROM companies c
            LEFT JOIN jobs j ON c.id = j.company_id
            GROUP BY c.id
            ORDER BY max_ctc DESC
            LIMIT 5;
        """)
        top_companies = [dict(row) for row in c.fetchall()]

        return success_response({
            "total_students": total_students,
            "total_companies": total_companies,
            "active_jobs": active_jobs,
            "total_applications": total_applications,
            "offers_extended": offers_extended,
            "upcoming_interviews": upcoming_interviews,
            "top_companies": top_companies,
        })

