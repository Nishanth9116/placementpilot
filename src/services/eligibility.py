"""Eligibility evaluation service for students and recruitment drives."""

from typing import Any, Dict, List, Optional, Tuple


class EligibilityService:
    """Evaluates student eligibility criteria (CGPA, Branch, Skills) for jobs."""

    @staticmethod
    def evaluate(student: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single student against a single job posting.

        Args:
            student: Student profile dictionary with 'cgpa', 'branch', and 'skills'.
            job: Job posting dictionary with 'min_cgpa', 'allowed_branches', and 'required_skills'.

        Returns:
            Dict containing:
                - is_eligible (bool): True if both CGPA and branch criteria are satisfied.
                - cgpa_satisfied (bool)
                - branch_satisfied (bool)
                - matched_skills (List[str])
                - missing_skills (List[str])
                - skill_match_percentage (float)
                - disqualification_reasons (List[str])
        """
        reasons: List[str] = []

        # 1. CGPA Check
        student_cgpa = float(student.get("cgpa", 0.0))
        min_cgpa = float(job.get("min_cgpa", 0.0))
        cgpa_ok = student_cgpa >= min_cgpa
        if not cgpa_ok:
            reasons.append(f"CGPA {student_cgpa:.2f} is below the minimum requirement of {min_cgpa:.2f}")

        # 2. Branch & Department Check
        student_branch = str(student.get("branch", "")).strip().upper()
        student_dept = str(student.get("department", "") or student.get("branch", "")).strip().upper()
        allowed_branches = [str(b).strip().upper() for b in job.get("allowed_branches", [])]

        # Wildcard or empty list signifies open to ALL departments
        allows_all = (
            not allowed_branches
            or any(w in allowed_branches for w in ["ALL", "ANY", "ALL DEPARTMENTS", "ALL BRANCHES", "*"])
        )

        if allows_all:
            branch_ok = True
        else:
            aliases = {
                "CSE": "COMPUTER SCIENCE",
                "CS": "COMPUTER SCIENCE",
                "IT": "INFORMATION TECHNOLOGY",
                "ISE": "INFORMATION TECHNOLOGY",
                "IS": "INFORMATION TECHNOLOGY",
                "MCA": "COMPUTER APPLICATIONS",
                "CA": "COMPUTER APPLICATIONS",
                "BCA": "COMPUTER APPLICATIONS",
                "COMMERCE": "COMMERCE",
                "B.COM": "COMMERCE",
                "BCOM": "COMMERCE",
                "BBA": "BUSINESS ADMINISTRATION",
                "MBA": "BUSINESS ADMINISTRATION",
                "MATH": "MATHEMATICS",
                "MATHS": "MATHEMATICS",
                "PHYSICS": "PHYSICS",
                "PHY": "PHYSICS",
                "CHEMISTRY": "CHEMISTRY",
                "CHEM": "CHEMISTRY",
                "MECH": "MECHANICAL ENGINEERING",
                "ECE": "ELECTRONICS & COMMUNICATION",
                "EEE": "ELECTRICAL & ELECTRONICS",
                "ISE": "INFORMATION SCIENCE",
            }

            def match_term(cand: str, allowed: str) -> bool:
                if not cand or not allowed:
                    return False
                if cand == allowed:
                    return True
                c_alias = aliases.get(cand, cand)
                a_alias = aliases.get(allowed, allowed)
                return c_alias == a_alias or allowed in c_alias or c_alias in allowed

            branch_ok = any(
                match_term(student_branch, b) or match_term(student_dept, b)
                for b in allowed_branches
            )

        if not branch_ok:
            disp_dept = student.get("branch") or student.get("department") or "Unknown"
            reasons.append(
                f"Branch '{disp_dept}' is not in allowed branches or eligible departments: {', '.join(job.get('allowed_branches', []))}"
            )

        # 3. Skills Analysis
        student_skills = {s.lower().strip() for s in student.get("skills", [])}
        required_skills = job.get("required_skills", [])

        matched_skills: List[str] = []
        missing_skills: List[str] = []

        if required_skills:
            for req in required_skills:
                if req.lower().strip() in student_skills:
                    matched_skills.append(req)
                else:
                    missing_skills.append(req)

            match_pct = round((len(matched_skills) / len(required_skills)) * 100.0, 1)
        else:
            match_pct = 100.0

        is_eligible = cgpa_ok and branch_ok

        return {
            "is_eligible": is_eligible,
            "cgpa_satisfied": cgpa_ok,
            "branch_satisfied": branch_ok,
            "student_cgpa": student_cgpa,
            "required_cgpa": min_cgpa,
            "student_branch": student_branch,
            "allowed_branches": allowed_branches,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "skill_match_percentage": match_pct,
            "disqualification_reasons": reasons,
        }

    @classmethod
    def rank_eligible_jobs(
        cls,
        student: Dict[str, Any],
        jobs: List[Dict[str, Any]],
        only_eligible: bool = True,
    ) -> List[Dict[str, Any]]:
        """Evaluate and rank jobs for a given student.

        Sorted by eligibility (eligible first), followed by skill match percentage and CTC.
        """
        evaluated_jobs = []
        for job in jobs:
            eval_result = cls.evaluate(student, job)
            if only_eligible and not eval_result["is_eligible"]:
                continue

            job_summary = dict(job)
            job_summary["eligibility"] = eval_result
            evaluated_jobs.append(job_summary)

        # Rank by: is_eligible (desc), skill_match_percentage (desc), ctc_lpa (desc)
        evaluated_jobs.sort(
            key=lambda x: (
                x["eligibility"]["is_eligible"],
                x["eligibility"]["skill_match_percentage"],
                x.get("ctc_lpa", 0.0),
            ),
            reverse=True,
        )
        return evaluated_jobs

    @classmethod
    def rank_candidates_for_job(
        cls,
        job: Dict[str, Any],
        students: List[Dict[str, Any]],
        only_eligible: bool = True,
    ) -> List[Dict[str, Any]]:
        """Evaluate and rank candidate students for a specific job drive.

        Sorted by eligibility (eligible first), followed by skill match percentage and CGPA.
        """
        evaluated_students = []
        for student in students:
            eval_result = cls.evaluate(student, job)
            if only_eligible and not eval_result["is_eligible"]:
                continue

            student_summary = dict(student)
            student_summary["eligibility"] = eval_result
            evaluated_students.append(student_summary)

        # Rank by: is_eligible (desc), skill_match_percentage (desc), cgpa (desc)
        evaluated_students.sort(
            key=lambda x: (
                x["eligibility"]["is_eligible"],
                x["eligibility"]["skill_match_percentage"],
                x.get("cgpa", 0.0),
            ),
            reverse=True,
        )
        return evaluated_students

