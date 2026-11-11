"""Unit tests for PlacementPilot core business logic and domain services."""

import sqlite3
import pytest

from src.db.init_db import SCHEMA_PATH
from src.db.repositories import (
    ApplicationRepository,
    CompanyRepository,
    QuestionRepository,
    StudentRepository,
)
from src.services.eligibility import EligibilityService
from src.services.prep import PrepService
from src.services.tracker import TrackerService


@pytest.fixture
def db_conn():
    """Create an isolated, in-memory SQLite database with schema for each test."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    yield conn
    conn.close()


class TestEligibilityService:
    """Tests for student eligibility evaluation and ranking algorithms."""

    def test_eligible_student(self):
        student = {
            "name": "Aarav",
            "branch": "CSE",
            "cgpa": 8.5,
            "skills": ["Python", "SQL", "Docker", "DSA"],
        }
        job = {
            "role_title": "Backend Dev",
            "min_cgpa": 7.5,
            "allowed_branches": ["CSE", "ISE"],
            "required_skills": ["Python", "SQL", "Docker"],
        }

        res = EligibilityService.evaluate(student, job)
        assert res["is_eligible"] is True
        assert res["cgpa_satisfied"] is True
        assert res["branch_satisfied"] is True
        assert res["skill_match_percentage"] == 100.0
        assert len(res["missing_skills"]) == 0
        assert len(res["disqualification_reasons"]) == 0

    def test_ineligible_due_to_cgpa(self):
        student = {"branch": "CSE", "cgpa": 6.8, "skills": ["Python"]}
        job = {"min_cgpa": 7.5, "allowed_branches": ["CSE"], "required_skills": ["Python"]}

        res = EligibilityService.evaluate(student, job)
        assert res["is_eligible"] is False
        assert res["cgpa_satisfied"] is False
        assert any("CGPA" in r for r in res["disqualification_reasons"])

    def test_ineligible_due_to_branch(self):
        student = {"branch": "MECH", "cgpa": 8.9, "skills": ["Python"]}
        job = {"min_cgpa": 7.0, "allowed_branches": ["CSE", "ECE"], "required_skills": []}

        res = EligibilityService.evaluate(student, job)
        assert res["is_eligible"] is False
        assert res["branch_satisfied"] is False
        assert any("Branch 'MECH'" in r for r in res["disqualification_reasons"])

    def test_rank_eligible_jobs(self):
        student = {"branch": "CSE", "cgpa": 8.0, "skills": ["Python", "SQL"]}
        jobs = [
            {"id": 1, "role_title": "Job A", "min_cgpa": 7.0, "allowed_branches": ["CSE"], "ctc_lpa": 12.0, "required_skills": ["Python", "SQL"]},
            {"id": 2, "role_title": "Job B", "min_cgpa": 8.5, "allowed_branches": ["CSE"], "ctc_lpa": 25.0, "required_skills": ["Python"]},
            {"id": 3, "role_title": "Job C", "min_cgpa": 6.5, "allowed_branches": ["CSE"], "ctc_lpa": 10.0, "required_skills": ["Java"]},
        ]

        ranked = EligibilityService.rank_eligible_jobs(student, jobs, only_eligible=True)
        assert len(ranked) == 2
        # Job A has 100% skill match, Job C has 0% skill match
        assert ranked[0]["id"] == 1
        assert ranked[1]["id"] == 3


class TestTrackerService:
    """Tests for application pipeline state transitions and interview scheduling."""

    def test_apply_with_eligibility(self, db_conn):
        s_repo = StudentRepository(db_conn)
        c_repo = CompanyRepository(db_conn)
        tracker = TrackerService(db_conn)

        student = s_repo.create("1SRV01", "Eligible Student", "el@test.edu", "CSE", 8.5, 2025)
        company = c_repo.create_company("TopTier")
        job = c_repo.create_job(company["id"], "SWE", 20.0, min_cgpa=7.5, allowed_branches=["CSE"])

        # Eligible application
        app = tracker.apply_to_job(student["id"], job["id"], notes="Campus referral")
        assert app["status"] == "applied"

        # Duplicate application rejected
        with pytest.raises(ValueError, match="already has an active application"):
            tracker.apply_to_job(student["id"], job["id"])

    def test_apply_ineligible_rejected(self, db_conn):
        s_repo = StudentRepository(db_conn)
        c_repo = CompanyRepository(db_conn)
        tracker = TrackerService(db_conn)

        student = s_repo.create("1SRV02", "Ineligible Student", "inel@test.edu", "CIVIL", 6.0, 2025)
        company = c_repo.create_company("StrictCorp")
        job = c_repo.create_job(company["id"], "Architect", 15.0, min_cgpa=8.0, allowed_branches=["CSE"])

        with pytest.raises(ValueError, match="Student is not eligible"):
            tracker.apply_to_job(student["id"], job["id"], enforce_eligibility=True)

    def test_pipeline_transitions_and_funnel(self, db_conn):
        s_repo = StudentRepository(db_conn)
        c_repo = CompanyRepository(db_conn)
        tracker = TrackerService(db_conn)

        student = s_repo.create("1SRV03", "Pipeline Student", "pipe@test.edu", "CSE", 8.2, 2025)
        company = c_repo.create_company("CloudWorks")
        job = c_repo.create_job(company["id"], "Cloud Engineer", 18.0, min_cgpa=7.0, allowed_branches=["CSE"])

        app = tracker.apply_to_job(student["id"], job["id"])

        # 1. Advance to shortlisted
        adv = tracker.advance_stage(app["id"], "shortlisted", current_stage="Shortlisted for OA")
        assert adv["status"] == "shortlisted"

        # 2. Schedule Round 1
        r1 = tracker.schedule_interview_round(app["id"], "Online Coding Test", "2026-11-20 10:00")
        assert r1["round_number"] == 1

        # 3. Clear Round 1
        tracker.record_interview_outcome(r1["id"], "cleared", feedback="All test cases passed")

        # 4. Schedule Round 2
        r2 = tracker.schedule_interview_round(app["id"], "System Design", "2026-11-25 14:00")
        assert r2["round_number"] == 2

        # 5. Fail Round 2 -> auto reject
        tracker.record_interview_outcome(r2["id"], "failed", feedback="Struggled with sharding", auto_update_application=True)
        summary = tracker.get_student_placement_summary(student["id"])
        assert summary["status_breakdown"]["rejected"] == 1

        # Check job funnel
        funnel = tracker.get_drive_funnel(job["id"])
        assert funnel["total_applicants"] == 1
        assert funnel["shortlisted_or_beyond"] == 1
        assert funnel["rejected"] == 1


class TestPrepService:
    """Tests for skill gap diagnosis and mock interview plans."""

    def test_skill_gap_analysis(self, db_conn):
        s_repo = StudentRepository(db_conn)
        c_repo = CompanyRepository(db_conn)
        q_repo = QuestionRepository(db_conn)
        prep = PrepService(db_conn)

        student = s_repo.create(
            "1PREP01", "Prep Candidate", "prep@test.edu", "CSE", 8.0, 2025,
            skills=["Python", "DSA"]
        )
        company = c_repo.create_company("Amazon")
        job = c_repo.create_job(
            company["id"], "SDE", 22.0, min_cgpa=7.0, allowed_branches=["CSE"],
            required_skills=["Python", "DSA", "System Design", "Docker"]
        )

        q_repo.create_question(
            "System_Design", "Rate Limiter", "Design a rate limiter", "Medium",
            company_tags=["Amazon"]
        )

        analysis = prep.analyze_skill_gaps(student["id"], job["id"])
        assert "System Design" in analysis["missing_skills"]
        assert "Docker" in analysis["missing_skills"]
        assert len(analysis["recommended_questions"]) > 0

    def test_mock_interview_workflow(self, db_conn):
        s_repo = StudentRepository(db_conn)
        q_repo = QuestionRepository(db_conn)
        prep = PrepService(db_conn)

        student = s_repo.create("1PREP02", "Mock Candidate", "mock@test.edu", "CSE", 8.4, 2025)
        q_repo.create_question("DSA", "Arrays", "Two Sum Problem", "Easy", company_tags=["Google"])

        plan = prep.generate_mock_interview_plan(student["id"], target_company="Google", num_questions=3)
        assert len(plan["plan_questions"]) > 0

        eval_res = prep.log_and_evaluate_mock(
            student_id=student["id"],
            topic="DSA Mock",
            score=90.0,
            feedback="Great algorithmic efficiency.",
        )
        assert eval_res["total_mock_sessions"] == 1
        assert eval_res["average_score"] == 90.0
        assert eval_res["readiness_verdict"] == "High Readiness"

