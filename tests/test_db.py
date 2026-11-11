"""Unit tests for PlacementPilot SQLite schema and repository CRUD operations."""

import sqlite3
import pytest
from pathlib import Path

from src.db.connection import get_connection
from src.db.init_db import SCHEMA_PATH
from src.db.repositories import (
    ApplicationRepository,
    CompanyRepository,
    QuestionRepository,
    StudentRepository,
)


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


class TestStudentCRUD:
    """Tests for StudentRepository CRUD operations."""

    def test_create_and_get_student(self, db_conn):
        repo = StudentRepository(db_conn)
        student = repo.create(
            usn="1TEST001",
            name="Test Candidate",
            email="candidate@test.edu",
            branch="CSE",
            cgpa=8.5,
            graduation_year=2025,
            skills=["Python", "SQL"],
        )

        assert student is not None
        assert student["id"] is not None
        assert student["usn"] == "1TEST001"
        assert student["skills"] == ["Python", "SQL"]

        fetched = repo.get_by_id(student["id"])
        assert fetched["email"] == "candidate@test.edu"

        fetched_usn = repo.get_by_usn("1TEST001")
        assert fetched_usn["id"] == student["id"]

    def test_list_and_filter_students(self, db_conn):
        repo = StudentRepository(db_conn)
        repo.create("1TEST002", "Alice", "alice@test.edu", "CSE", 9.0, 2025)
        repo.create("1TEST003", "Bob", "bob@test.edu", "ECE", 7.5, 2025)
        repo.create("1TEST004", "Charlie", "charlie@test.edu", "CSE", 7.0, 2025)

        cse_students = repo.list_all(branch="CSE")
        assert len(cse_students) == 2

        high_cgpa = repo.list_all(min_cgpa=8.0)
        assert len(high_cgpa) == 1
        assert high_cgpa[0]["name"] == "Alice"

    def test_update_and_delete_student(self, db_conn):
        repo = StudentRepository(db_conn)
        student = repo.create("1TEST005", "David", "david@test.edu", "MECH", 6.8, 2025)

        updated = repo.update(student["id"], cgpa=7.2, skills=["CAD", "Python"])
        assert updated["cgpa"] == 7.2
        assert updated["skills"] == ["CAD", "Python"]

        deleted = repo.delete(student["id"])
        assert deleted is True
        assert repo.get_by_id(student["id"]) is None


class TestCompanyAndJobCRUD:
    """Tests for CompanyRepository and recruitment drive operations."""

    def test_create_company_and_job(self, db_conn):
        repo = CompanyRepository(db_conn)
        company = repo.create_company(
            name="Acme Corp",
            website="https://acme.test",
            industry="Software",
            description="Innovative software solutions.",
        )
        assert company["id"] is not None
        assert company["name"] == "Acme Corp"

        job = repo.create_job(
            company_id=company["id"],
            role_title="Software Developer",
            ctc_lpa=18.5,
            min_cgpa=7.5,
            allowed_branches=["CSE", "ISE"],
            required_skills=["Python", "FastAPI"],
        )
        assert job["id"] is not None
        assert job["company_name"] == "Acme Corp"
        assert "CSE" in job["allowed_branches"]
        assert "FastAPI" in job["required_skills"]

    def test_list_and_filter_jobs(self, db_conn):
        repo = CompanyRepository(db_conn)
        comp = repo.create_company("Tech Giants")

        repo.create_job(comp["id"], "High CTC Role", 30.0, allowed_branches=["CSE"])
        repo.create_job(comp["id"], "Standard Role", 12.0, allowed_branches=["CSE", "ECE"])

        all_jobs = repo.list_jobs()
        assert len(all_jobs) == 2

        filtered_ctc = repo.list_jobs(min_ctc=20.0)
        assert len(filtered_ctc) == 1
        assert filtered_ctc[0]["role_title"] == "High CTC Role"

        filtered_branch = repo.list_jobs(branch="ECE")
        assert len(filtered_branch) == 1
        assert filtered_branch[0]["role_title"] == "Standard Role"

    def test_update_and_delete_job(self, db_conn):
        repo = CompanyRepository(db_conn)
        comp = repo.create_company("UpdateCorp")
        job = repo.create_job(comp["id"], "Junior Dev", 10.0)

        updated = repo.update_job(job["id"], ctc_lpa=12.5, status="closed")
        assert updated["ctc_lpa"] == 12.5
        assert updated["status"] == "closed"

        assert repo.delete_job(job["id"]) is True
        assert repo.get_job_by_id(job["id"]) is None


class TestApplicationAndInterviewScheduleCRUD:
    """Tests for job applications and interview round scheduling."""

    def test_apply_and_schedule_rounds(self, db_conn):
        s_repo = StudentRepository(db_conn)
        c_repo = CompanyRepository(db_conn)
        a_repo = ApplicationRepository(db_conn)

        student = s_repo.create("1APP001", "Emma Watson", "emma@test.edu", "CSE", 8.8, 2025)
        company = c_repo.create_company("InnovateX")
        job = c_repo.create_job(company["id"], "Cloud Engineer", 16.0)

        # 1. Apply
        app = a_repo.apply(student["id"], job["id"], notes="Referral from hackathon.")
        assert app is not None
        assert app["status"] == "applied"
        assert app["student_name"] == "Emma Watson"
        assert app["role_title"] == "Cloud Engineer"

        # 2. Schedule Round 1 (Online Assessment)
        round1 = a_repo.schedule_round(
            application_id=app["id"],
            round_number=1,
            round_type="Online Assessment",
            scheduled_at="2026-11-20 10:00:00",
            interviewer_notes="Automated HackerRank link dispatched.",
        )
        assert round1["round_number"] == 1
        assert round1["status"] == "pending"

        # Verify application status auto-updated to interview_scheduled
        refreshed_app = a_repo.get_by_id(app["id"])
        assert refreshed_app["status"] == "interview_scheduled"

        # 3. Update Round 1 to Cleared
        updated_round = a_repo.update_round_result(
            round_id=round1["id"],
            status="cleared",
            feedback="Full test cases passed in 30 mins.",
        )
        assert updated_round["status"] == "cleared"

        # 4. Schedule Round 2 (Technical Interview)
        round2 = a_repo.schedule_round(
            application_id=app["id"],
            round_number=2,
            round_type="Technical Interview 1",
            scheduled_at="2026-11-25 15:00:00",
        )
        assert round2["round_number"] == 2

        rounds = a_repo.list_rounds_for_application(app["id"])
        assert len(rounds) == 2

        # 5. Check upcoming interviews
        upcoming = a_repo.list_upcoming_interviews(student_id=student["id"])
        assert len(upcoming) == 1
        assert upcoming[0]["round_type"] == "Technical Interview 1"

        # 6. Offer state transition
        offered_app = a_repo.update_status(
            app["id"],
            status="offered",
            current_stage="Job Offer Extended",
            notes="CTC accepted.",
        )
        assert offered_app["status"] == "offered"

    def test_duplicate_application_prevention(self, db_conn):
        s_repo = StudentRepository(db_conn)
        c_repo = CompanyRepository(db_conn)
        a_repo = ApplicationRepository(db_conn)

        student = s_repo.create("1DUP001", "Duplicate Test", "dup@test.edu", "CSE", 8.0, 2025)
        company = c_repo.create_company("OneApplyCorp")
        job = c_repo.create_job(company["id"], "Single Opening", 10.0)

        a_repo.apply(student["id"], job["id"])

        with pytest.raises(sqlite3.IntegrityError):
            a_repo.apply(student["id"], job["id"])


class TestQuestionAndMockInterviewCRUD:
    """Tests for QuestionRepository and interview prep operations."""

    def test_question_bank_operations(self, db_conn):
        q_repo = QuestionRepository(db_conn)

        q1 = q_repo.create_question(
            category="DSA",
            topic="Binary Trees",
            question_text="Lowest Common Ancestor in a Binary Tree",
            difficulty="Medium",
            solution_guide="Recursive post-order traversal.",
            company_tags=["Google", "Amazon"],
        )
        assert q1["id"] is not None
        assert "Google" in q1["company_tags"]

        questions = q_repo.list_questions(category="DSA", company="Amazon")
        assert len(questions) == 1
        assert questions[0]["topic"] == "Binary Trees"

        random_qs = q_repo.get_random_questions(category="DSA", limit=1)
        assert len(random_qs) == 1

    def test_mock_interview_logging(self, db_conn):
        s_repo = StudentRepository(db_conn)
        q_repo = QuestionRepository(db_conn)

        student = s_repo.create("1MOCK01", "Mock Student", "mock@test.edu", "ISE", 8.1, 2025)

        mock = q_repo.log_mock_interview(
            student_id=student["id"],
            topic="System Design - Rate Limiter",
            score=88.5,
            feedback="Great understanding of token bucket algorithm.",
            transcript="Interviewer: Design a distributed rate limiter...",
        )
        assert mock["id"] is not None
        assert mock["score"] == 88.5

        history = q_repo.list_mock_interviews_for_student(student["id"])
        assert len(history) == 1
        assert history[0]["topic"] == "System Design - Rate Limiter"

