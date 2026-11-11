"""Unit and integration tests for PlacementPilot MCP Server tools, resources, and prompts."""

import json
import pytest

from config.settings import settings
from src.db.init_db import initialize_database, seed_sample_data
from src.mcp_server.server import server
from src.mcp_server import tools, resources, prompts


@pytest.fixture(autouse=True)
def init_test_db(tmp_path, monkeypatch):
    """Point database settings to a temporary test database and seed sample data."""
    test_db = tmp_path / "test_mcp.db"
    monkeypatch.setattr(settings, "DATABASE_PATH", test_db)
    initialize_database(test_db)
    seed_sample_data(test_db)


class TestMCPServerRegistration:
    """Verifies that all required MCP tools, resources, and prompts are properly registered."""

    def test_registered_tools(self):
        registered = {t.name for t in server._tool_manager.list_tools()}
        expected_tools = {
            "register_student",
            "add_job_opening",
            "check_job_eligibility",
            "apply_for_job",
            "schedule_interview",
            "update_interview_outcome",
            "get_student_placement_summary",
            "get_interview_prep_plan",
        }
        assert expected_tools.issubset(registered), f"Missing tools: {expected_tools - registered}"

    def test_registered_resources(self):
        static_resources = {r.uri for r in server._resource_manager.list_resources()}
        assert "placement://jobs/active" in static_resources

        templates = {t.uri_template for t in server._resource_manager.list_templates()}
        expected_templates = {
            "placement://students/{student_id}/profile",
            "placement://students/{student_id}/applications",
            "placement://students/{student_id}/skills",
        }
        assert expected_templates.issubset(templates), f"Missing templates: {expected_templates - templates}"

    def test_registered_prompts(self):
        prompt_names = {p.name for p in server._prompt_manager.list_prompts()}
        expected_prompts = {"interview_preparation", "job_analysis", "follow_up_email"}
        assert expected_prompts.issubset(prompt_names), f"Missing prompts: {expected_prompts - prompt_names}"


class TestMCPToolsExecution:
    """Comprehensive tests for all 8 MCP tools including input validation and error handling."""

    def test_tool_register_student(self):
        # 1. New registration
        res = tools.register_student(
            usn="1TEST_MCP_01",
            name="Rohit Sharma",
            email="rohit@college.edu",
            branch="CSE",
            cgpa=8.75,
            graduation_year=2025,
            skills=["Python", "FastAPI", "SQL"],
        )
        assert res["status"] == "created"
        assert res["student"]["usn"] == "1TEST_MCP_01"
        student_id = res["student"]["id"]

        # 2. Update existing registration
        update_res = tools.register_student(
            usn="1TEST_MCP_01",
            name="Rohit Sharma",
            email="rohit@college.edu",
            branch="CSE",
            cgpa=9.1,
            graduation_year=2025,
            skills=["Python", "FastAPI", "SQL", "Docker"],
        )
        assert update_res["status"] == "updated"
        assert update_res["student"]["cgpa"] == 9.1
        assert "Docker" in update_res["student"]["skills"]

        # 3. Input validation errors
        with pytest.raises(ValueError, match="CGPA must be between 0.0 and 10.0"):
            tools.register_student("1TEST_ERR", "Name", "email@test.com", "CSE", 11.5, 2025)

        with pytest.raises(ValueError, match="Invalid email address"):
            tools.register_student("1TEST_ERR", "Name", "bad-email", "CSE", 8.0, 2025)

        with pytest.raises(ValueError, match="USN cannot be empty"):
            tools.register_student("", "Name", "email@test.com", "CSE", 8.0, 2025)

    def test_tool_add_job_opening(self):
        # 1. Create opening
        res = tools.add_job_opening(
            company_name="Netflix",
            role_title="Backend Software Engineer",
            ctc_lpa=35.0,
            min_cgpa=8.0,
            allowed_branches=["CSE", "ISE"],
            required_skills=["Java", "Distributed Systems", "SQL"],
            location="Remote",
            application_deadline="2026-12-31",
        )
        assert res["status"] == "created"
        job = res["job"]
        assert job["company_name"] == "Netflix"
        assert job["ctc_lpa"] == 35.0
        assert "CSE" in job["allowed_branches"]

        # 2. Validation errors
        with pytest.raises(ValueError, match="CTC cannot be negative"):
            tools.add_job_opening("BadCorp", "Dev", -5.0)

        with pytest.raises(ValueError, match="Minimum CGPA must be between 0.0 and 10.0"):
            tools.add_job_opening("BadCorp", "Dev", 10.0, min_cgpa=12.0)

        with pytest.raises(ValueError, match="Company name cannot be empty"):
            tools.add_job_opening("", "Dev", 10.0)

    def test_tool_check_job_eligibility(self):
        # Seeded student 1 (Aarav, CSE, CGPA 8.9) and Job 1 (Google, min CGPA 8.0, CSE/ISE)
        res = tools.check_job_eligibility(student_id=1, job_id=1)
        assert res["student_id"] == 1
        assert res["job_id"] == 1
        assert res["evaluation"]["is_eligible"] is True
        assert res["evaluation"]["cgpa_satisfied"] is True
        assert res["evaluation"]["branch_satisfied"] is True

        # Ineligible check: Seeded student 2 (Priya, ECE, CGPA 7.8) against Google (min 8.0, CSE/ISE)
        ineligible_res = tools.check_job_eligibility(student_id=2, job_id=1)
        assert ineligible_res["evaluation"]["is_eligible"] is False
        assert len(ineligible_res["evaluation"]["disqualification_reasons"]) >= 1

        # Invalid IDs
        with pytest.raises(ValueError, match="Student ID must be a positive integer"):
            tools.check_job_eligibility(student_id=0, job_id=1)

    def test_tool_apply_for_job(self):
        # Seeded student 6 (Sneha, ISE, CGPA 8.65) applies to Microsoft (Job 2, min CGPA 7.5, CSE/ISE/ECE)
        res = tools.apply_for_job(
            student_id=6,
            job_id=2,
            notes="Strong interest in distributed services.",
            enforce_eligibility=True,
        )
        assert res["status"] == "applied"
        assert res["application"]["student_id"] == 6
        assert res["application"]["job_id"] == 2

        # Ineligible application rejection: student 2 (ECE, 7.8) to Google (min 8.0)
        with pytest.raises(ValueError, match="Student is not eligible"):
            tools.apply_for_job(student_id=2, job_id=1, enforce_eligibility=True)

    def test_tool_schedule_and_update_interview(self):
        # Seeded application 1 has rounds 1, 2, 3 already. Schedule round 4:
        sched_res = tools.schedule_interview(
            application_id=1,
            round_type="Managerial & Fitment Round",
            scheduled_at="2026-11-28 16:00:00",
            interviewer_notes="Discussion with Engineering Director.",
        )
        assert sched_res["status"] == "scheduled"
        round_id = sched_res["round_id"]
        assert sched_res["round_number"] == 4

        # Record outcome as cleared
        outcome_res = tools.update_interview_outcome(
            round_id=round_id,
            status="cleared",
            feedback="Strong leadership principles and clear communication.",
        )
        assert outcome_res["status"] == "updated"
        assert outcome_res["round_status"] == "cleared"

        # Invalid status
        with pytest.raises(ValueError, match="Invalid status"):
            tools.update_interview_outcome(round_id=round_id, status="unknown_status")

    def test_tool_get_student_placement_summary(self):
        summary = tools.get_student_placement_summary(student_id=1)
        assert summary["student_id"] == 1
        assert summary["student_name"] == "Aarav Sharma"
        assert summary["total_applications"] >= 1
        assert "status_breakdown" in summary

    def test_tool_get_interview_prep_plan(self):
        plan = tools.get_interview_prep_plan(student_id=1, job_id=2)
        assert plan["student_id"] == 1
        assert "target_role" in plan
        assert "recommended_questions" in plan
        assert isinstance(plan["recommended_questions"], list)

    def test_tool_log_mock_interview(self):
        res = tools.log_mock_interview_evaluation(
            student_id=1,
            topic="Core CS - Concurrency",
            score=92.0,
            feedback="Great explanation of semaphores and mutexes.",
        )
        assert res["total_mock_sessions"] >= 1
        assert res["average_score"] >= 80.0
        assert res["readiness_verdict"] == "High Readiness"


class TestMCPResources:
    """Verifies URI resource read capabilities for student profiles, applications, and skills."""

    def test_student_profile_resource(self):
        raw = resources.get_student_profile_resource(student_id=1)
        data = json.loads(raw)
        assert data["id"] == 1
        assert data["name"] == "Aarav Sharma"
        assert data["cgpa"] == 8.9

    def test_student_applications_resource(self):
        raw = resources.get_student_applications_resource(student_id=1)
        data = json.loads(raw)
        assert data["student_id"] == 1
        assert data["total_applications"] >= 1
        assert isinstance(data["applications"], list)

    def test_student_skills_resource(self):
        raw = resources.get_student_skills_resource(student_id=1)
        data = json.loads(raw)
        assert data["student_id"] == 1
        assert "declared_skills" in data

    def test_active_jobs_resource(self):
        raw = resources.get_active_jobs_resource()
        data = json.loads(raw)
        assert data["total_open_drives"] >= 3
        assert isinstance(data["drives"], list)


class TestMCPPrompts:
    """Verifies that MCP prompt templates render valid, context-filled PromptMessage objects."""

    def test_interview_prep_prompt(self):
        messages = prompts.get_interview_prep_prompt(student_id=1, job_id=1)
        assert len(messages) == 1
        assert messages[0].role == "user"
        text = messages[0].content.text
        assert "Aarav Sharma" in text
        assert "Google" in text
        assert "Associate Software Engineer" in text

    def test_job_analysis_prompt(self):
        messages = prompts.get_job_analysis_prompt(job_id=1)
        assert len(messages) == 1
        assert messages[0].role == "user"
        text = messages[0].content.text
        assert "Associate Software Engineer" in text
        assert "28.5 LPA" in text

    def test_follow_up_email_prompt(self):
        messages = prompts.get_follow_up_email_prompt(application_id=1, round_id=1)
        assert len(messages) == 1
        assert messages[0].role == "user"
        text = messages[0].content.text
        assert "Aarav Sharma" in text
        assert "Google" in text
        assert "Online Assessment" in text
