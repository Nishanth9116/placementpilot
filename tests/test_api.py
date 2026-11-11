"""Integration tests for PlacementPilot Web REST API endpoints."""

import pytest
from starlette.testclient import TestClient

from config.settings import settings
from src.db.init_db import initialize_database, seed_sample_data
from src.web.app import app


@pytest.fixture(autouse=True)
def init_test_db(tmp_path, monkeypatch):
    """Isolate database to a fresh temporary SQLite file for each test."""
    test_db = tmp_path / "test_api.db"
    monkeypatch.setattr(settings, "DATABASE_PATH", test_db)
    initialize_database(test_db)
    seed_sample_data(test_db)


@pytest.fixture
def client():
    """Starlette test client."""
    return TestClient(app)


class TestWebAPIEndpoints:
    """Verifies all REST API endpoints for the dashboard frontend."""

    def test_serve_index_html(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert "PlacementPilot" in res.text
        assert "app-container" in res.text

    def test_get_overview_stats(self, client):
        res = client.get("/api/overview")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total_students"] >= 3
        assert data["active_jobs"] >= 3
        assert "top_companies" in data

    def test_student_endpoints(self, client):
        # 1. List students
        res = client.get("/api/students")
        assert res.status_code == 200
        students = res.json()["data"]
        assert len(students) >= 3

        # 2. Create student
        payload = {
            "usn": "1WEB001",
            "name": "Web Candidate",
            "email": "web.cand@test.edu",
            "branch": "CSE",
            "cgpa": 9.4,
            "graduation_year": 2025,
            "skills": ["Python", "FastAPI", "React"],
        }
        res_post = client.post("/api/students", json=payload)
        assert res_post.status_code == 201
        created = res_post.json()["data"]["student"]
        assert created["usn"] == "1WEB001"
        student_id = created["id"]

        # 3. Get single student
        res_get = client.get(f"/api/students/{student_id}")
        assert res_get.status_code == 200
        assert res_get.json()["data"]["name"] == "Web Candidate"

        # 4. Get student summary
        res_summary = client.get(f"/api/students/{student_id}/summary")
        assert res_summary.status_code == 200
        assert res_summary.json()["data"]["total_applications"] == 0

    def test_company_and_job_endpoints(self, client):
        # 1. Create company
        comp_payload = {
            "name": "Cloudflare",
            "website": "https://cloudflare.com",
            "industry": "Cloud & Security",
        }
        res_comp = client.post("/api/companies", json=comp_payload)
        assert res_comp.status_code == 201
        comp = res_comp.json()["data"]
        comp_id = comp["id"]

        # 2. Create job
        job_payload = {
            "company_id": comp_id,
            "role_title": "Lakehouse Engineer",
            "ctc_lpa": 38.0,
            "min_cgpa": 8.0,
            "allowed_branches": ["CSE", "ISE"],
            "required_skills": ["Spark", "Python", "SQL"],
        }
        res_job = client.post("/api/jobs", json=job_payload)
        assert res_job.status_code == 201
        job_id = res_job.json()["data"]["id"]

        # 3. List jobs
        res_list = client.get("/api/jobs")
        assert res_list.status_code == 200
        assert any(j["id"] == job_id for j in res_list.json()["data"])

    def test_application_and_round_workflow(self, client):
        # Student 1 applies to Job 3 (Amazon)
        apply_payload = {
            "student_id": 1,
            "job_id": 3,
            "notes": "E-commerce interest.",
            "enforce_eligibility": True,
        }
        res_apply = client.post("/api/applications", json=apply_payload)
        assert res_apply.status_code == 201
        app_id = res_apply.json()["data"]["id"]

        # Schedule round
        sched_payload = {
            "round_type": "Technical Interview 1",
            "scheduled_at": "2026-11-29 11:00:00",
            "interviewer_notes": "Live coding round.",
        }
        res_sched = client.post(f"/api/applications/{app_id}/rounds", json=sched_payload)
        assert res_sched.status_code == 201
        round_id = res_sched.json()["data"]["id"]

        # List upcoming interviews
        res_up = client.get("/api/interviews/upcoming")
        assert res_up.status_code == 200
        assert any(r["id"] == round_id for r in res_up.json()["data"])

        # Update round outcome to cleared
        outcome_payload = {
            "status": "cleared",
            "feedback": "Passed all test cases.",
        }
        res_out = client.patch(f"/api/rounds/{round_id}", json=outcome_payload)
        assert res_out.status_code == 200
        assert res_out.json()["data"]["status"] == "cleared"

    def test_ai_prep_and_email_endpoints(self, client):
        # 1. Skill gap analysis
        res_gap = client.get("/api/prep/skill-gap?student_id=1&job_id=2")
        assert res_gap.status_code == 200
        gap_data = res_gap.json()["data"]
        assert "skill_match_percentage" in gap_data
        assert "recommended_questions" in gap_data

        # 2. List question bank
        res_q = client.get("/api/prep/questions?category=DSA")
        assert res_q.status_code == 200
        assert len(res_q.json()["data"]) >= 1

        # 3. Log mock interview
        mock_payload = {
            "student_id": 1,
            "topic": "Graph Algorithms",
            "score": 95.0,
            "feedback": "Flawless Dijkstra implementation.",
        }
        res_mock = client.post("/api/prep/mock-interview", json=mock_payload)
        assert res_mock.status_code == 201
        assert res_mock.json()["data"]["average_score"] >= 80.0

        # 4. Generate follow-up email
        email_payload = {
            "application_id": 1,
            "round_id": 1,
        }
        res_email = client.post("/api/generator/follow-up-email", json=email_payload)
        assert res_email.status_code == 200
        email_data = res_email.json()["data"]
        assert "draft_subject" in email_data
        assert "draft_body" in email_data
        assert "Aarav Sharma" in email_data["draft_body"]

