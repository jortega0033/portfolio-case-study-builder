"""SQLite persistence. One connection per operation; transactional saves."""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects(
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  revision INTEGER NOT NULL CHECK(revision>=1),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sections(
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  position INTEGER NOT NULL,
  section_id TEXT NOT NULL,
  heading TEXT NOT NULL,
  body TEXT NOT NULL,
  PRIMARY KEY(project_id, position),
  UNIQUE(project_id, section_id)
);
"""


class NotFound(Exception):
    pass


class RevisionConflict(Exception):
    def __init__(self, current_revision: int):
        super().__init__(f"revision conflict (current {current_revision})")
        self.current_revision = current_revision


class SchemaTooNew(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Storage:
    def __init__(self, path):
        self.path = str(path)
        conn = self._connect()
        try:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version > SCHEMA_VERSION:
                raise SchemaTooNew(
                    f"Database schema version {version} is newer than supported "
                    f"version {SCHEMA_VERSION}; upgrade the application."
                )
            if version < SCHEMA_VERSION:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("BEGIN IMMEDIATE")
                try:
                    for stmt in _SCHEMA.split(";"):
                        if stmt.strip():
                            conn.execute(stmt)
                    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
                    conn.execute("COMMIT")
                except BaseException:
                    conn.execute("ROLLBACK")
                    raise
            else:
                conn.execute("PRAGMA journal_mode=WAL")
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=5.0, isolation_level=None)
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    @contextmanager
    def _conn(self):
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()

    @staticmethod
    def _load(conn, project_id: str) -> dict:
        row = conn.execute(
            "SELECT id, title, revision, created_at, updated_at FROM projects WHERE id=?",
            (project_id,),
        ).fetchone()
        if row is None:
            raise NotFound(project_id)
        secs = conn.execute(
            "SELECT section_id, heading, body FROM sections WHERE project_id=? ORDER BY position",
            (project_id,),
        ).fetchall()
        return {
            "id": row[0],
            "title": row[1],
            "revision": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "sections": [{"id": s[0], "heading": s[1], "body": s[2]} for s in secs],
        }

    def list_projects(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT p.id, p.title, p.revision, p.updated_at, "
                "(SELECT COUNT(*) FROM sections s WHERE s.project_id = p.id) "
                "FROM projects p ORDER BY p.updated_at DESC, p.id ASC"
            ).fetchall()
        return [
            {"id": r[0], "title": r[1], "revision": r[2], "updated_at": r[3], "section_count": r[4]}
            for r in rows
        ]

    def get_project(self, project_id: str) -> dict:
        with self._conn() as conn:
            return self._load(conn, project_id)

    @staticmethod
    def _write_sections(conn, project_id: str, sections: list[dict]) -> None:
        conn.execute("DELETE FROM sections WHERE project_id=?", (project_id,))
        conn.executemany(
            "INSERT INTO sections(project_id, position, section_id, heading, body) "
            "VALUES (?,?,?,?,?)",
            [(project_id, i, s["id"], s["heading"], s["body"]) for i, s in enumerate(sections)],
        )

    def create_project(self, title: str, sections: list[dict]) -> dict:
        pid = uuid.uuid4().hex
        now = _now()
        with self._conn() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    "INSERT INTO projects(id, title, revision, created_at, updated_at) "
                    "VALUES (?,?,1,?,?)",
                    (pid, title, now, now),
                )
                self._write_sections(conn, pid, sections)
                result = self._load(conn, pid)
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            return result

    def update_project(self, project_id: str, title: str, sections: list[dict],
                       base_revision: int) -> dict:
        with self._conn() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = conn.execute(
                    "SELECT revision FROM projects WHERE id=?", (project_id,)
                ).fetchone()
                if row is None:
                    raise NotFound(project_id)
                if row[0] != base_revision:
                    raise RevisionConflict(row[0])
                conn.execute(
                    "UPDATE projects SET title=?, revision=revision+1, updated_at=? WHERE id=?",
                    (title, _now(), project_id),
                )
                self._write_sections(conn, project_id, sections)
                result = self._load(conn, project_id)
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            return result
