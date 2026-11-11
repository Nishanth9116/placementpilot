"""Student repository for SQLite CRUD operations."""

import json
import sqlite3
from typing import Any, Dict, List, Optional


class StudentRepository:
    """Data access repository for students."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(
        self,
        usn: str,
        name: str,
        email: str,
        branch: str,
        cgpa: float,
        graduation_year: int,
        skills: Optional[List[str]] = None,
        resume_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Insert a new student profile."""
        skills_json = json.dumps(skills or [])
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO students (usn, name, email, branch, cgpa, graduation_year, skills, resume_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (usn, name, email, branch.upper(), cgpa, graduation_year, skills_json, resume_path),
        )
        student_id = cursor.lastrowid
        return self.get_by_id(student_id)  # type: ignore

    def get_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a student by primary key ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?;", (student_id,))
        row = cursor.fetchone()
        return self._format_row(row) if row else None

    def get_by_usn(self, usn: str) -> Optional[Dict[str, Any]]:
        """Fetch a student by university roll number (USN)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM students WHERE usn = ?;", (usn,))
        row = cursor.fetchone()
        return self._format_row(row) if row else None

    def list_all(
        self,
        branch: Optional[str] = None,
        min_cgpa: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List students with optional branch and CGPA filters."""
        query = "SELECT * FROM students WHERE 1=1"
        params: List[Any] = []

        if branch:
            query += " AND branch = ?"
            params.append(branch.upper())
        if min_cgpa is not None:
            query += " AND cgpa >= ?"
            params.append(min_cgpa)

        query += " ORDER BY cgpa DESC, name ASC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        cursor = self.conn.cursor()
        cursor.execute(query, tuple(params))
        return [self._format_row(row) for row in cursor.fetchall()]

    def update(
        self,
        student_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        branch: Optional[str] = None,
        cgpa: Optional[float] = None,
        graduation_year: Optional[int] = None,
        skills: Optional[List[str]] = None,
        resume_path: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update fields of an existing student."""
        updates: List[str] = []
        params: List[Any] = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if branch is not None:
            updates.append("branch = ?")
            params.append(branch.upper())
        if cgpa is not None:
            updates.append("cgpa = ?")
            params.append(cgpa)
        if graduation_year is not None:
            updates.append("graduation_year = ?")
            params.append(graduation_year)
        if skills is not None:
            updates.append("skills = ?")
            params.append(json.dumps(skills))
        if resume_path is not None:
            updates.append("resume_path = ?")
            params.append(resume_path)

        if not updates:
            return self.get_by_id(student_id)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(student_id)

        sql = f"UPDATE students SET {', '.join(updates)} WHERE id = ?;"
        cursor = self.conn.cursor()
        cursor.execute(sql, tuple(params))
        return self.get_by_id(student_id)

    def delete(self, student_id: int) -> bool:
        """Delete student and all associated cascade records."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = ?;", (student_id,))
        return cursor.rowcount > 0

    @staticmethod
    def _format_row(row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        if "skills" in data and isinstance(data["skills"], str):
            try:
                data["skills"] = json.loads(data["skills"])
            except json.JSONDecodeError:
                data["skills"] = []
        return data

