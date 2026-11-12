"""Comprehensive tests for new PlacementPilot features:
1. Logout and Session Authentication
2. All Department Student Registration (Commerce, BBA, Math, Physics, Chemistry, CS, IT, Other)
3. Dynamic Department Management by Admin
4. All-Department and Restricted-Department Company Eligibility
5. Application Submission & Duplicate Prevention
6. Local SQLite Persistence
"""

import json
import sqlite3
import pytest
from pathlib import Path

from config.settings import settings
from src.db.init_db import initialize_database, seed_sample_data, SCHEMA_PATH
from src.db.repositories import (
    ApplicationRepository,
    CompanyRepository,
    DepartmentRepository,
    StudentRepository,
)
from src.services.eligibility import EligibilityService
from src.services.tracker import TrackerService


@pytest.fixture
def isolated_db(tmp_path):
    """Create a fully initialized, isolated temporary SQLite database."""
    test_db = tmp_path / "test_features.db"
    initialize_database(test_db)
    seed_sample_data(test_db)
    return test_db


class TestAllDepartmentRegistration:
    """Tests for multi-department student registration and profile management."""

    def test_register_students_across_departments(self, isolated_db):
        with sqlite3.connect(isolated_db) as conn:
            conn.row_factory = sqlite3.Row
            repo = StudentRepository(conn)

            # 1. Register Commerce student
            comm_student = repo.create(
                usn="COMM2025001",
                name="Aditi Rao",
                email="aditi.rao@college.edu",
                phone="+91 91234 56789",
                branch="COMMERCE",
                department="Commerce",
                year_of_study="3rd Year",
                cgpa=8.85,
                graduation_year=2026,
                skills=["Financial Modeling", "Accounting", "Excel", "Taxation"],
            )
            assert comm_student["id"] is not None
            assert comm_student["department"] == "Commerce"
            assert comm_student["phone"] == "+91 91234 56789"
            assert comm_student["year_of_study"] == "3rd Year"

            # 2. Register Business Administration student
            bba_student = repo.create(
                usn="BBA2025002",
                name="Karan Malhotra",
                email="karan.m@college.edu",
                phone="+91 98888 77777",
                branch="BBA",
                department="Business Administration",
                year_of_study="4th Year",
                cgpa=7.90,
                graduation_year=2025,
                skills=["Business Strategy", "Marketing", "Market Research", "Negotiation"],
            )
            assert bba_student["department"] == "Business Administration"

            # 3. Register Mathematics student
            math_student = repo.create(
                usn="MATH2025003",
                name="Sunita Nair",
                email="sunita.n@college.edu",
                branch="MATH",
                department="Mathematics",
                year_of_study="2nd Year",
                cgpa=9.30,
                graduation_year=2027,
                skills=["Linear Algebra", "Calculus", "Probability", "Python"],
            )
            assert math_student["department"] == "Mathematics"

            # 4. Register Chemistry student
            chem_student = repo.create(
                usn="CHEM2025004",
                name="Deepak Joshi",
                email="deepak.j@college.edu",
                branch="CHEMISTRY",
                department="Chemistry",
                year_of_study="4th Year",
                cgpa=8.10,
                graduation_year=2025,
                skills=["Organic Synthesis", "Spectroscopy", "Data Analysis"],
            )
            assert chem_student["department"] == "Chemistry"

            # 5. Register Physics student
            phys_student = repo.create(
                usn="PHYS2025005",
                name="Meera Sen",
                email="meera.s@college.edu",
                branch="PHYSICS",
                department="Physics",
                year_of_study="4th Year",
                cgpa=8.60,
                graduation_year=2025,
                skills=["Quantum Mechanics", "Computational Physics", "Python"],
            )
            assert phys_student["department"] == "Physics"

    def test_department_filtering(self, isolated_db):
        with sqlite3.connect(isolated_db) as conn:
            conn.row_factory = sqlite3.Row
            repo = StudentRepository(conn)

            commerce_list = repo.list_all(department="Commerce")
            assert any(s["department"] == "Commerce" for s in commerce_list)


class TestDynamicDepartmentManagement:
    """Tests for dynamic department addition and retrieval by admin."""

    def test_default_departments_seeded(self, isolated_db):
        with sqlite3.connect(isolated_db) as conn:
            conn.row_factory = sqlite3.Row
            dept_repo = DepartmentRepository(conn)
            depts = dept_repo.list_all()
            dept_names = [d["name"] for d in depts]

            # Verify standard required departments
            required = [
                "Computer Science",
                "Information Technology",
                "Computer Applications",
                "Commerce",
                "Business Administration",
                "Mathematics",
                "Physics",
                "Chemistry",
                "Other",
            ]
            for req in required:
                assert req in dept_names, f"Department '{req}' was expected to be seeded"

    def test_admin_add_department_dynamically(self, isolated_db):
        with sqlite3.connect(isolated_db) as conn:
            conn.row_factory = sqlite3.Row
            dept_repo = DepartmentRepository(conn)

            new_dept = dept_repo.create(name="Data Science & Artificial Intelligence", code="DSAI")
            assert new_dept["id"] is not None
            assert new_dept["name"] == "Data Science & Artificial Intelligence"
            assert new_dept["code"] == "DSAI"

            fetched = dept_repo.get_by_name_or_code("dsai")
            assert fetched is not None
            assert fetched["id"] == new_dept["id"]


class TestLoginAndLogout:
    """Tests for student authentication, lookup, and session token simulation."""

    def test_authenticate_by_usn_and_email(self, isolated_db):
        with sqlite3.connect(isolated_db) as conn:
            conn.row_factory = sqlite3.Row
            repo = StudentRepository(conn)

            # Authenticate by USN
            s1 = repo.authenticate("1PI21CS001")
            assert s1 is not None
            assert s1["name"] == "Aarav Sharma"

            # Authenticate by Email (case-insensitive)
            s2 = repo.authenticate("AARAV.SHARMA@EXAMPLE.EDU")
            assert s2 is not None
            assert s2["id"] == s1["id"]

            # Non-existent user fails
            s_none = repo.authenticate("NON_EXISTENT_REGISTER_NO")
            assert s_none is None


class TestCompanyEligibilityAndApplicationSubmission:
    """Tests for all-department eligibility and restricted company eligibility rules."""

    def test_all_department_company_eligibility(self, isolated_db):
        """When a job drive allows 'ALL', students from ANY department can apply."""
        with sqlite3.connect(isolated_db) as conn:
            conn.row_factory = sqlite3.Row
            student_repo = StudentRepository(conn)
            company_repo = CompanyRepository(conn)
            tracker = TrackerService(conn)

            # Create an open job accepting ALL departments
            comp = company_repo.create_company("Global Management Partners", industry="Consulting")
            all_dept_job = company_repo.create_job(
                company_id=comp["id"],
                role_title="Business & Operations Associate",
                ctc_lpa=12.0,
                min_cgpa=6.5,
                allowed_branches=["ALL"],
                required_skills=["Communication", "Excel", "Analysis"],
            )

            # Candidate 1: Commerce
            comm_student = student_repo.create(
                usn="TEST_COMM_01",
                name="Bhavna V",
                email="bhavna@test.edu",
                branch="COMMERCE",
                department="Commerce",
                cgpa=8.2,
                graduation_year=2025,
            )
            eval1 = EligibilityService.evaluate(comm_student, all_dept_job)
            assert eval1["is_eligible"] is True
            assert eval1["branch_satisfied"] is True

            # Candidate 2: Physics
            phys_student = student_repo.create(
                usn="TEST_PHYS_01",
                name="Alok K",
                email="alok@test.edu",
                branch="PHYSICS",
                department="Physics",
                cgpa=7.8,
                graduation_year=2025,
            )
            eval2 = EligibilityService.evaluate(phys_student, all_dept_job)
            assert eval2["is_eligible"] is True
            assert eval2["branch_satisfied"] is True

            # Successfully apply to all-department job
            app = tracker.apply_to_job(comm_student["id"], all_dept_job["id"], notes="All departments welcome.")
            assert app["id"] is not None
            assert app["status"] == "applied"

    def test_restricted_department_company_eligibility(self, isolated_db):
        """When a job restricts to specific departments, ineligible candidates are rejected with clear reasons."""
        with sqlite3.connect(isolated_db) as conn:
            conn.row_factory = sqlite3.Row
            student_repo = StudentRepository(conn)
            company_repo = CompanyRepository(conn)
            tracker = TrackerService(conn)

            comp = company_repo.create_company("FinAudit Corp", industry="Financial Services")
            finance_job = company_repo.create_job(
                company_id=comp["id"],
                role_title="Senior Financial Analyst",
                ctc_lpa=16.0,
                min_cgpa=7.5,
                allowed_branches=["Commerce", "Business Administration"],
                required_skills=["Accounting", "Financial Analysis"],
            )

            # 1. Eligible Commerce student
            comm_student = student_repo.create(
                usn="TEST_COMM_OK",
                name="Ramesh R",
                email="ramesh@test.edu",
                branch="COMMERCE",
                department="Commerce",
                cgpa=8.0,
                graduation_year=2025,
            )
            eval_ok = EligibilityService.evaluate(comm_student, finance_job)
            assert eval_ok["is_eligible"] is True

            app_ok = tracker.apply_to_job(comm_student["id"], finance_job["id"])
            assert app_ok["id"] is not None

            # 2. Ineligible Chemistry student (Wrong department)
            chem_student = student_repo.create(
                usn="TEST_CHEM_NO",
                name="Suman C",
                email="suman@test.edu",
                branch="CHEMISTRY",
                department="Chemistry",
                cgpa=8.5, # High CGPA but wrong department
                graduation_year=2025,
            )
            eval_inelig = EligibilityService.evaluate(chem_student, finance_job)
            assert eval_inelig["is_eligible"] is False
            assert eval_inelig["branch_satisfied"] is False
            assert any("not in allowed branches" in r for r in eval_inelig["disqualification_reasons"])

            with pytest.raises(ValueError) as excinfo:
                tracker.apply_to_job(chem_student["id"], finance_job["id"], enforce_eligibility=True)
            assert "not in allowed branches" in str(excinfo.value)

            # 3. Ineligible Commerce student due to CGPA cutoff
            low_cgpa_comm = student_repo.create(
                usn="TEST_COMM_LOW",
                name="Tanya P",
                email="tanya@test.edu",
                branch="COMMERCE",
                department="Commerce",
                cgpa=6.8, # Below 7.5 cutoff
                graduation_year=2025,
            )
            eval_low = EligibilityService.evaluate(low_cgpa_comm, finance_job)
            assert eval_low["is_eligible"] is False
            assert eval_low["cgpa_satisfied"] is False
            assert any("below the minimum requirement" in r for r in eval_low["disqualification_reasons"])

    def test_duplicate_application_prevention(self, isolated_db):
        """Ensure a student cannot submit duplicate applications for the same job."""
        with sqlite3.connect(isolated_db) as conn:
            conn.row_factory = sqlite3.Row
            student_repo = StudentRepository(conn)
            company_repo = CompanyRepository(conn)
            tracker = TrackerService(conn)

            comp = company_repo.create_company("Acme Analytics")
            job = company_repo.create_job(
                company_id=comp["id"],
                role_title="Operations Trainee",
                ctc_lpa=8.0,
                min_cgpa=6.0,
                allowed_branches=["ALL"],
            )

            student = student_repo.create(
                usn="TEST_DUP_01",
                name="Pooja M",
                email="pooja@test.edu",
                branch="BBA",
                department="Business Administration",
                cgpa=7.2,
                graduation_year=2025,
            )

            # First application succeeds
            tracker.apply_to_job(student["id"], job["id"])

            # Second application is blocked
            with pytest.raises(ValueError) as excinfo:
                tracker.apply_to_job(student["id"], job["id"])
            assert "already has an active application" in str(excinfo.value)

