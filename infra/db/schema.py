import sqlite3

SCHEMA_VERSION = 2


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            total_attempts INTEGER DEFAULT 0,
            accuracy REAL DEFAULT 0,
            mode TEXT NOT NULL DEFAULT 'training',
            total_lines INTEGER NOT NULL DEFAULT 0,
            max_streak INTEGER NOT NULL DEFAULT 0,
            survival_seconds INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            target_note TEXT NOT NULL,
            guessed_note TEXT NOT NULL,
            octave INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            response_ms INTEGER NOT NULL,
            timbre TEXT NOT NULL,
            created_at TEXT NOT NULL,
            selected_note TEXT,
            selected_family TEXT,
            generated_piece TEXT,
            placement_outcome TEXT,
            board_height_after INTEGER,
            lines_cleared_after INTEGER,
            FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_attempts_created_at ON attempts(created_at);
        CREATE INDEX IF NOT EXISTS idx_attempts_target_note ON attempts(target_note);
        CREATE INDEX IF NOT EXISTS idx_attempts_correct ON attempts(correct);
        """
    )
    _migrate_sessions_table(connection)
    _migrate_attempts_table(connection)
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION};")
    connection.commit()


def _migrate_sessions_table(connection: sqlite3.Connection) -> None:
    existing = _table_columns(connection, "sessions")
    if "mode" not in existing:
        connection.execute(
            "ALTER TABLE sessions ADD COLUMN mode TEXT NOT NULL DEFAULT 'training';"
        )
    if "total_lines" not in existing:
        connection.execute(
            "ALTER TABLE sessions ADD COLUMN total_lines INTEGER NOT NULL DEFAULT 0;"
        )
    if "max_streak" not in existing:
        connection.execute(
            "ALTER TABLE sessions ADD COLUMN max_streak INTEGER NOT NULL DEFAULT 0;"
        )
    if "survival_seconds" not in existing:
        connection.execute(
            "ALTER TABLE sessions ADD COLUMN survival_seconds INTEGER NOT NULL DEFAULT 0;"
        )


def _migrate_attempts_table(connection: sqlite3.Connection) -> None:
    existing = _table_columns(connection, "attempts")
    if "selected_note" not in existing:
        connection.execute("ALTER TABLE attempts ADD COLUMN selected_note TEXT;")
    if "selected_family" not in existing:
        connection.execute("ALTER TABLE attempts ADD COLUMN selected_family TEXT;")
    if "generated_piece" not in existing:
        connection.execute("ALTER TABLE attempts ADD COLUMN generated_piece TEXT;")
    if "placement_outcome" not in existing:
        connection.execute("ALTER TABLE attempts ADD COLUMN placement_outcome TEXT;")
    if "board_height_after" not in existing:
        connection.execute("ALTER TABLE attempts ADD COLUMN board_height_after INTEGER;")
    if "lines_cleared_after" not in existing:
        connection.execute("ALTER TABLE attempts ADD COLUMN lines_cleared_after INTEGER;")


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}
