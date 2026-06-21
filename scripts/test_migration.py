# Migration tests for TaskDeck. Applies 0002_projects up/down against a
# throwaway SQLite DB and renders it in offline mode (--sql), mirroring the
# plain-pytest style of scripts/test_unit.py. No live MCP DB is touched.
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

REVISION = "0002_projects"
DOWN_REVISION = "0001_initial"


def _alembic_config() -> Config:
    # env.py reads the URL from DATABASE_URL, so the config just needs to locate
    # the alembic tree regardless of the cwd pytest runs from.
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    return cfg


def _table_names(db_path: str) -> set:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


def _columns(db_path: str, table: str):
    conn = sqlite3.connect(db_path)
    try:
        # pragma_table_info -> (cid, name, type, notnull, dflt_value, pk)
        return conn.execute(
            "SELECT * FROM pragma_table_info(:table)", {"table": table}
        ).fetchall()
    finally:
        conn.close()


def test_upgrade_creates_projects_then_downgrade_removes_it():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "throwaway.db")
        prev = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        try:
            cfg = _alembic_config()

            # Acceptance: upgrade head creates the projects table.
            command.upgrade(cfg, "head")
            assert "projects" in _table_names(db_path)

            cols = {c[1]: c for c in _columns(db_path, "projects")}
            assert set(cols) == {"id", "name"}, f"unexpected columns: {set(cols)}"
            # id is the primary key (pk flag == 1)...
            assert cols["id"][5] == 1, "id must be the primary key"
            # ...and name is NOT NULL (notnull flag == 1).
            assert cols["name"][3] == 1, "name must be NOT NULL"

            # Acceptance: downgrade removes the table cleanly.
            command.downgrade(cfg, DOWN_REVISION)
            assert "projects" not in _table_names(db_path)
        finally:
            if prev is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = prev


def _offline_sql(database_url: str, rev_range: str, direction: str = "upgrade") -> str:
    # Render via the real CLI exactly as deploy does: `alembic upgrade <range> --sql`.
    env = dict(os.environ)
    env["DATABASE_URL"] = database_url
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_INI),
         direction, rev_range, "--sql"],
        cwd=str(REPO_ROOT), env=env,
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"offline render failed:\n{proc.stderr}"
    return proc.stdout


def test_offline_render_emits_create_and_drop_without_connection_literals():
    # Offline-safe check: rendering only this revision's SQL must succeed and
    # contain a CREATE TABLE for projects with no embedded connection string.
    sql = _offline_sql("sqlite:///./offline.db", f"{DOWN_REVISION}:{REVISION}")
    assert "CREATE TABLE" in sql.upper()
    assert "projects" in sql
    # No connection literals / credentials leak into the rendered DDL.
    for literal in ("DATABASE_URL", "://", "password", "@"):
        assert literal not in sql, f"connection literal '{literal}' leaked into SQL"

    # The downgrade direction renders a DROP TABLE for the same revision.
    down_sql = _offline_sql(
        "sqlite:///./offline.db", f"{REVISION}:{DOWN_REVISION}", direction="downgrade")
    assert "DROP TABLE" in down_sql.upper()
    assert "projects" in down_sql


def test_offline_render_emits_serial_primary_key_for_postgres():
    # Against a (credential-free) Postgres URL the migration must emit a serial
    # primary key — proven offline, without connecting to any database.
    sql = _offline_sql("postgresql://localhost/taskdeck", f"{DOWN_REVISION}:{REVISION}")
    upper = sql.upper()
    assert "CREATE TABLE" in upper
    assert "SERIAL" in upper, "Postgres render must use a serial primary key"
    assert "NOT NULL" in upper, "name column must be NOT NULL"
