"""End-to-end demonstration and smoke test of PlacementPilot MCP tools, resources, and prompts."""

import sys
from pathlib import Path

# Add project root to Python search path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import logging
from config.settings import settings
from src.db.init_db import initialize_database, seed_sample_data
from src.mcp_server import prompts, resources, tools

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("demo_client")


def run_demo():
    print("=" * 80)
    print("🎓✈️  PlacementPilot MCP Server - End-to-End Client Demo")
    print("=" * 80)

    # 1. Initialize local SQLite database
    print("\n[1] Ensuring local SQLite database is initialized...")
    initialize_database()
    seed_sample_data()
    print("    Database ready at:", settings.DATABASE_PATH)

    # 2. Register a new candidate via MCP tool
    print("\n[2] Executing MCP Tool: `register_student`...")
    student_res = tools.register_student(
        usn="1PI21CS105",
        name="Kavya Rao",
        email="kavya.rao@example.edu",
        branch="CSE",
        cgpa=9.15,
        graduation_year=2025,
        skills=["Python", "SQL", "React", "Docker", "Algorithms"],
        resume_path="/resumes/1PI21CS105_Kavya.pdf",
    )
    student = student_res["student"]
    print(f"    Student Registered: {student['name']} ({student['usn']}) - CGPA: {student['cgpa']}")

    # 3. Add a new recruitment drive via MCP tool
    print("\n[3] Executing MCP Tool: `add_job_opening`...")
    job_res = tools.add_job_opening(
        company_name="Stripe",
        role_title="Software Engineer - Payments Infrastructure",
        ctc_lpa=32.0,
        min_cgpa=8.5,
        allowed_branches=["CSE", "ISE"],
        required_skills=["Python", "Distributed Systems", "SQL", "APIs"],
        location="Bangalore",
        application_deadline="2026-12-20",
    )
    job = job_res["job"]
    print(f"    Job Created: {job['role_title']} at {job['company_name']} ({job['ctc_lpa']} LPA)")

    # 4. Check eligibility via MCP tool
    print("\n[4] Executing MCP Tool: `check_job_eligibility`...")
    eligibility_res = tools.check_job_eligibility(student_id=student["id"], job_id=job["id"])
    eval_data = eligibility_res["evaluation"]
    print(f"    Eligibility Verdict: {'ELIGIBLE' if eval_data['is_eligible'] else 'NOT ELIGIBLE'}")
    print(f"    Skill Match: {eval_data['skill_match_percentage']}%")
    print(f"    Matched Skills: {eval_data['matched_skills']}")
    print(f"    Missing Skills: {eval_data['missing_skills']}")

    # 5. Apply for job via MCP tool
    print("\n[5] Executing MCP Tool: `apply_for_job`...")
    app_res = tools.apply_for_job(
        student_id=student["id"],
        job_id=job["id"],
        notes="Strong background in payment microservices and API design.",
        enforce_eligibility=True,
    )
    app = app_res["application"]
    print(f"    Application Submitted (ID: {app['id']}) - Status: {app['status']}")

    # 6. Schedule Interview Round via MCP tool
    print("\n[6] Executing MCP Tool: `schedule_interview`...")
    sched_res = tools.schedule_interview(
        application_id=app["id"],
        round_type="System Design & Architecture",
        scheduled_at="2026-11-28 14:00:00",
        interviewer_notes="Focus on idempotent payment processing.",
    )
    round_rec = sched_res["round"]
    print(f"    Interview Scheduled: Round {round_rec['round_number']} ({round_rec['round_type']})")

    # 7. Update Interview Outcome via MCP tool
    print("\n[7] Executing MCP Tool: `update_interview_outcome`...")
    outcome_res = tools.update_interview_outcome(
        round_id=round_rec["id"],
        status="cleared",
        feedback="Exceptional understanding of idempotency keys, distributed locks, and retry strategies.",
    )
    print(f"    Interview Outcome Updated: {outcome_res['round_status'].upper()}")

    # 8. Retrieve Placement Summary Dashboard via MCP tool
    print("\n[8] Executing MCP Tool: `get_student_placement_summary`...")
    summary = tools.get_student_placement_summary(student_id=student["id"])
    print(f"    Total Applications: {summary['total_applications']}")
    print(f"    Pipeline Breakdown: {summary['status_breakdown']}")

    # 9. Retrieve Interview Prep Plan via MCP tool
    print("\n[9] Executing MCP Tool: `get_interview_prep_plan`...")
    prep_plan = tools.get_interview_prep_plan(student_id=student["id"], job_id=job["id"])
    print(f"    Target Role: {prep_plan['target_role']} at {prep_plan['company_name']}")
    print(f"    Recommended Prep Questions ({len(prep_plan['recommended_questions'])} items):")
    for q in prep_plan["recommended_questions"][:2]:
        print(f"      * [{q['category']}] {q['topic']}: {q['question_text'][:70]}...")

    # 10. Read MCP Resources
    print("\n[10] Reading MCP Resources...")
    profile_json = resources.get_student_profile_resource(student_id=student["id"])
    print("    URI `placement://students/{id}/profile`:")
    profile_data = json.loads(profile_json)
    print(f"      Name: {profile_data['name']} | Branch: {profile_data['branch']} | CGPA: {profile_data['cgpa']}")

    active_jobs_json = resources.get_active_jobs_resource()
    active_jobs = json.loads(active_jobs_json)
    print(f"    URI `placement://jobs/active`: {active_jobs['total_open_drives']} open drives found.")

    # 11. Render MCP Prompts
    print("\n[11] Rendering MCP Prompts...")
    prep_prompt = prompts.get_interview_prep_prompt(student_id=student["id"], job_id=job["id"])
    print("    Rendered `interview_preparation` Prompt Length:", len(prep_prompt[0].content.text), "characters")

    job_prompt = prompts.get_job_analysis_prompt(job_id=job["id"])
    print("    Rendered `job_analysis` Prompt Length:", len(job_prompt[0].content.text), "characters")

    email_prompt = prompts.get_follow_up_email_prompt(application_id=app["id"], round_id=round_rec["id"])
    print("    Rendered `follow_up_email` Prompt Length:", len(email_prompt[0].content.text), "characters")

    print("\n" + "=" * 80)
    print("✅ All MCP Tools, Resources, and Prompts verified successfully!")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()

