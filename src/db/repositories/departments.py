"""Department repository for SQLite CRUD operations."""

import sqlite3
from typing import Any, Dict, List, Optional


class DepartmentRepository:
    """Data access repository for college academic departments."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, name: str, code: Optional[str] = None) -> Dict[str, Any]:
        """Create a new department."""
        clean_name = name.strip()
        clean_code = (code or clean_name[:6]).strip().upper()
        
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO departments (code, name, is_active)
            VALUES (?, ?, 1);
            """,
            (clean_code, clean_name),
        )
        dept_id = cursor.lastrowid
        return self.get_by_id(dept_id)  # type: ignore

    def get_by_id(self, department_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a department by primary key ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM departments WHERE id = ?;", (department_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_name_or_code(self, val: str) -> Optional[Dict[str, Any]]:
        """Fetch a department matching name or code (case-insensitive)."""
        clean_val = val.strip()
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM departments 
            WHERE LOWER(name) = LOWER(?) OR LOWER(code) = LOWER(?);
            """,
            (clean_val, clean_val),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_all(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """List all registered academic departments."""
        cursor = self.conn.cursor()
        if active_only:
            cursor.execute("SELECT * FROM departments WHERE is_active = 1 ORDER BY name ASC;")
        else:
            cursor.execute("SELECT * FROM departments ORDER BY name ASC;")
        return [dict(row) for row in cursor.fetchall()]

    def delete(self, department_id: int) -> bool:
        """Delete or deactivate a department."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM departments WHERE id = ?;", (department_id,))
        return cursor.rowcount > 0

