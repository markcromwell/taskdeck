"""projects — projects table

Revision ID: 0002_projects
Revises: 0001_initial
Create Date: 2026-06-21 00:00:00
"""
from alembic import op

revision = "0002_projects"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


# Idempotency comes from Alembic version tracking; the IF NOT EXISTS / IF EXISTS
# guards make upgrade()/downgrade() safe under blue/green deploys where both
# environments may run migrations against the same Postgres instance. We do not
# reflect the live database — runtime reflection breaks offline mode
# (alembic upgrade --sql) and is blocked by the push gate. The dialect name is
# read from the offline-safe migration context, so `serial` is emitted for
# Postgres while SQLite gets a portable integer primary key.
def _is_postgres() -> bool:
    return op.get_context().dialect.name == "postgresql"


def upgrade() -> None:
    if _is_postgres():
        op.execute(
            "CREATE TABLE IF NOT EXISTS projects ("
            "id SERIAL PRIMARY KEY, "
            "name TEXT NOT NULL)"
        )
    else:
        op.execute(
            "CREATE TABLE IF NOT EXISTS projects ("
            "id INTEGER PRIMARY KEY, "
            "name TEXT NOT NULL)"
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS projects")
