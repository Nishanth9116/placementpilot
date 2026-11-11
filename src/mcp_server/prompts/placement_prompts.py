"""Reusable MCP prompt templates for interview preparation, job analysis, and follow-up emails."""

from typing import List
from mcp.types import PromptMessage, TextContent

from src.db.connection import get_db_connection
from src.db.repositories.applications import ApplicationRepository
from src.db.repositories.companies import CompanyRepository
from src.db.repositories.students import StudentRepository
from src.services.prep import PrepService


def get_interview_prep_prompt(student_id: int, job_id: int) -> List[PromptMessage]:
    """Generate a personalized mock interview coaching prompt for an AI assistant."""
    with get_db_connection() as conn:
        s_repo = StudentRepository(conn)
        c_repo = CompanyRepository(conn)
        prep = PrepService(conn)

        student = s_repo.get_by_id(student_id)
        if not student:
            raise ValueError(f"Student with ID {student_id} not found.")

        job = c_repo.get_job_by_id(job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found.")

        gap_analysis = prep.analyze_skill_gaps(student_id, job_id)

    questions_text = "\n".join(
        f"- [{q.get('category')}] {q.get('topic')}: {q.get('question_text')}"
        for q in gap_analysis.get("recommended_questions", [])[:4]
    )

    prompt_content = f"""
You are an expert technical and behavioral interviewer conducting a rigorous mock interview for PlacementPilot.

### Candidate Profile:
- Name: {student['name']} (USN: {student['usn']})
- Branch: {student['branch']} | CGPA: {student['cgpa']:.2f}
- Declared Skills: {', '.join(student['skills'])}

### Target Role & Company:
- Company: {job['company_name']}
- Role: {job['role_title']} (CTC: {job['ctc_lpa']} LPA)
- Required Skills: {', '.join(job['required_skills'])}
- Skill Match: {gap_analysis['skill_match_percentage']}%
- Identified Skill Gaps: {', '.join(gap_analysis['missing_skills']) if gap_analysis['missing_skills'] else 'None (Full match)'}

### Recommended Question Areas:
{questions_text or 'Standard DSA and System Design questions for this role.'}

### Your Instructions:
1. Act as the lead technical interviewer from {job['company_name']}.
2. Ask one question at a time. Start with a warm introduction, then transition into a technical problem targeting their skill gaps.
3. Challenge the candidate on edge cases, time/space complexity, and trade-offs.
4. Conclude with a behavioral question using the STAR framework.
5. Provide a constructive evaluation score (out of 100) and actionable feedback.
"""
    return [
        PromptMessage(
            role="user",
            content=TextContent(type="text", text=prompt_content.strip()),
        )
    ]


def get_job_analysis_prompt(job_id: int) -> List[PromptMessage]:
    """Generate a structured drive analysis prompt to evaluate role difficulty and student readiness."""
    with get_db_connection() as conn:
        c_repo = CompanyRepository(conn)
        job = c_repo.get_job_by_id(job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found.")

    prompt_content = f"""
You are a senior campus placement advisor analyzing a recruitment drive for college students.

### Drive Metadata:
- Company: {job['company_name']} ({job.get('company_website', 'N/A')})
- Role: {job['role_title']}
- Compensation: {job['ctc_lpa']} LPA
- Location: {job['location']}
- Minimum CGPA Cutoff: {job['min_cgpa']}
- Eligible Branches: {', '.join(job['allowed_branches']) if job['allowed_branches'] else 'Open to all branches'}
- Required Skills: {', '.join(job['required_skills'])}
- Application Deadline: {job.get('application_deadline', 'Open')}

### Role Description:
{job.get('job_description', 'No detailed description provided.')}

### Please provide a comprehensive analysis covering:
1. **Drive Competitiveness & Benchmarking:** How does the {job['ctc_lpa']} LPA package and CGPA cutoff compare to tier-1 tech benchmarks?
2. **Core Competencies Evaluated:** Break down the specific algorithms, system design patterns, or framework concepts likely to be tested.
3. **Round-by-Round Prep Roadmap:** Outline a step-by-step 2-week preparation strategy (Online Assessment, Technical Rounds, Managerial/HR).
4. **Key Pitfalls to Avoid:** Highlight common mistakes students make during interviews with {job['company_name']}.
"""
    return [
        PromptMessage(
            role="user",
            content=TextContent(type="text", text=prompt_content.strip()),
        )
    ]


def get_follow_up_email_prompt(application_id: int, round_id: int) -> List[PromptMessage]:
    """Generate a prompt to draft a post-interview follow-up or thank-you email."""
    with get_db_connection() as conn:
        a_repo = ApplicationRepository(conn)
        app = a_repo.get_by_id(application_id)
        if not app:
            raise ValueError(f"Application with ID {application_id} not found.")

        round_rec = a_repo.get_round_by_id(round_id)
        if not round_rec:
            raise ValueError(f"Interview round with ID {round_id} not found.")

    prompt_content = f"""
Draft a polite, professional, and memorable post-interview follow-up email from a student candidate to the campus recruitment coordinator or interviewer.

### Context:
- Student Name: {app['student_name']} (USN: {app['student_usn']})
- Company: {app['company_name']}
- Role: {app['role_title']}
- Interview Round: Round {round_rec['round_number']} ({round_rec['round_type']})
- Date of Interview: {round_rec.get('scheduled_at', 'Recent')}
- Interviewer Feedback / Topic: {round_rec.get('feedback') or 'Discussion on technical fundamentals and system scalability.'}

### Guidelines:
- Keep the tone courteous, confident, and professional.
- Express genuine appreciation for the interviewer's time and insights.
- Reiterate strong interest in joining {app['company_name']} for the {app['role_title']} position.
- Keep it concise (under 200 words).
- Provide placeholders for any personal moments or specific technical topics discussed.
"""
    return [
        PromptMessage(
            role="user",
            content=TextContent(type="text", text=prompt_content.strip()),
        )
    ]

