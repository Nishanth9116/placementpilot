"""Question bank and Mock Interview repository for SQLite CRUD operations."""

import json
import sqlite3
from typing import Any, Dict, List, Optional


class QuestionRepository:
    """Data access repository for placement questions and student practice sessions."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # --- Question Bank Operations ---

    def create_question(
        self,
        category: str,
        topic: str,
        question_text: str,
        difficulty: str = "Medium",
        solution_guide: Optional[str] = None,
        company_tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Add a new placement prep question."""
        valid_categories = {"DSA", "Core_CS", "System_Design", "Database", "Behavioral_HR", "Aptitude"}
        if category not in valid_categories:
            raise ValueError(f"Invalid category '{category}'. Must be one of: {valid_categories}")

        valid_difficulties = {"Easy", "Medium", "Hard"}
        if difficulty not in valid_difficulties:
            raise ValueError(f"Invalid difficulty '{difficulty}'. Must be one of: {valid_difficulties}")

        tags_json = json.dumps(company_tags or [])
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO question_bank (category, topic, question_text, difficulty, solution_guide, company_tags)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (category, topic, question_text, difficulty, solution_guide, tags_json),
        )
        q_id = cursor.lastrowid
        return self.get_question_by_id(q_id)  # type: ignore

    def get_question_by_id(self, question_id: int) -> Optional[Dict[str, Any]]:
        """Fetch question by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM question_bank WHERE id = ?;", (question_id,))
        row = cursor.fetchone()
        return self._format_question_row(row) if row else None

    def list_questions(
        self,
        category: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        company: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List questions with optional filtering."""
        query = "SELECT * FROM question_bank WHERE 1=1"
        params: List[Any] = []

        if category:
            query += " AND category = ?"
            params.append(category)
        if topic:
            query += " AND LOWER(topic) LIKE LOWER(?)"
            params.append(f"%{topic}%")
        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty)

        query += " ORDER BY id ASC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        cursor = self.conn.cursor()
        cursor.execute(query, tuple(params))
        questions = [self._format_question_row(row) for row in cursor.fetchall()]

        if company:
            company_lower = company.lower()
            questions = [
                q for q in questions
                if any(company_lower == tag.lower() for tag in q.get("company_tags", []))
            ]

        return questions

    def get_random_questions(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Fetch random prep questions for practice or mock interviews."""
        query = "SELECT * FROM question_bank WHERE 1=1"
        params: List[Any] = []

        if category:
            query += " AND category = ?"
            params.append(category)
        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty)

        query += " ORDER BY RANDOM() LIMIT ?;"
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, tuple(params))
        return [self._format_question_row(row) for row in cursor.fetchall()]

    def delete_question(self, question_id: int) -> bool:
        """Delete a question."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM question_bank WHERE id = ?;", (question_id,))
        return cursor.rowcount > 0

    # --- Mock Interview Logs Operations ---

    def log_mock_interview(
        self,
        student_id: int,
        topic: str,
        score: Optional[float] = None,
        feedback: Optional[str] = None,
        transcript: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record the outcome of a student mock interview session."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO mock_interviews (student_id, topic, score, feedback, transcript)
            VALUES (?, ?, ?, ?, ?);
            """,
            (student_id, topic, score, feedback, transcript),
        )
        interview_id = cursor.lastrowid
        cursor.execute("SELECT * FROM mock_interviews WHERE id = ?;", (interview_id,))
        return dict(cursor.fetchone())

    def list_mock_interviews_for_student(self, student_id: int) -> List[Dict[str, Any]]:
        """List past mock interview sessions for a student."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM mock_interviews
            WHERE student_id = ?
            ORDER BY conducted_at DESC;
            """,
            (student_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def _format_question_row(row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        if "company_tags" in data and isinstance(data["company_tags"], str):
            try:
                data["company_tags"] = json.loads(data["company_tags"])
            except json.JSONDecodeError:
                data["company_tags"] = []
        return data

