import sqlite3
import unittest

from infra.db.schema import SCHEMA_VERSION, initialize_schema


class SchemaMigrationTests(unittest.TestCase):
    def test_initialize_schema_adds_stage1_columns_to_legacy_schema(self) -> None:
        connection = sqlite3.connect(":memory:")
        try:
            connection.executescript(
                """
                CREATE TABLE sessions (
                    id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    total_attempts INTEGER DEFAULT 0,
                    accuracy REAL DEFAULT 0
                );

                CREATE TABLE attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    target_note TEXT NOT NULL,
                    guessed_note TEXT NOT NULL,
                    octave INTEGER NOT NULL,
                    correct INTEGER NOT NULL,
                    response_ms INTEGER NOT NULL,
                    timbre TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            initialize_schema(connection)
            session_columns = _columns(connection, "sessions")
            attempt_columns = _columns(connection, "attempts")
            self.assertIn("mode", session_columns)
            self.assertIn("total_lines", session_columns)
            self.assertIn("max_streak", session_columns)
            self.assertIn("survival_seconds", session_columns)
            self.assertIn("selected_note", attempt_columns)
            self.assertIn("selected_family", attempt_columns)
            self.assertIn("generated_piece", attempt_columns)
            self.assertIn("placement_outcome", attempt_columns)
            self.assertIn("board_height_after", attempt_columns)
            self.assertIn("lines_cleared_after", attempt_columns)
            version = connection.execute("PRAGMA user_version;").fetchone()[0]
            self.assertEqual(version, SCHEMA_VERSION)
        finally:
            connection.close()


def _columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name});").fetchall()
    return {str(row[1]) for row in rows}


if __name__ == "__main__":
    unittest.main()
