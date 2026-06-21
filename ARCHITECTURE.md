# TaskDeck Architecture Contract

## Project Overview

TaskDeck is a Standard SOV Program — a multi-project task board (projects → tasks → comments, with status flow `open` / `doing` / `done`). It is a FastAPI ASGI web service (Python 3.12) run via `uvicorn main:app`, packaged as a Docker image. Persistence uses SQLAlchemy (SQLite by default, Postgres via `DATABASE_URL` with Alembic-owned schema). The stack includes Jinja server-rendered pages, optional capsule/self-knowledge endpoints, and CRUD HTTP surfaces for domain entities.

## File Structure

```
main.py                 # ASGI entrypoint exposing `app` (uvicorn main:app)
app/
  __init__.py           # create_app() factory; auto-includes routers; DB init
  config.py             # pydantic-settings (app_name, version, database_url)
  db.py                 # SQLAlchemy engine, SessionLocal, Base, get_session
  models.py             # ORM entities (SQLAlchemy 2.0 Mapped models)
  health.py             # Immutable /health contract
  capsule.py            # Capsule descriptor (charter, skills, tool_surface)
  routers/
    web.py              # Jinja UI at /
    items.py            # Example CRUD surface (+db)
    capsule.py          # /capsule and /memory/* endpoints (+capsule)
alembic/                # Schema migrations (Postgres; Alembic-owned)
  versions/             # Revision scripts
templates/              # Jinja2 HTML templates
scripts/
  smoke_boot.py         # Boot smoke: import main:app, assert /health
  test_unit.py          # Fast pytest suite (app factory + contracts)
  setup.py              # Project setup helper
Dockerfile              # python:3.12-slim image, HEALTHCHECK on /health
docker-compose.yml      # Local compose stack
requirements.in         # Direct dependencies (compile to requirements.lock)
pyproject.toml          # pytest paths, ruff line-length 100
```

## Naming Conventions

**Packages and modules.** New application code lives under `app/`. One feature router per `app/routers/<name>.py`, each exposing a module-level `router = APIRouter(...)` that `create_app()` auto-includes via `pkgutil.iter_modules` — no manual registration list.

**ORM models.** SQLAlchemy 2.0 style: subclass `app.db.Base`, use `Mapped[]` and `mapped_column`, snake_case `__tablename__` (e.g. `items`). Preserve existing field names when extending (e.g. `Item.name`).

**Pydantic schemas.** Request/response models named `<Entity>In` and `<Entity>Out` with `model_config = {"from_attributes": True}` for ORM serialization.

**Routes and tags.** Router `prefix` and `tags` match the feature name (e.g. `prefix="/items"`, `tags=["items"]`). Health stays at `/health` with no prefix.

**Templates.** Jinja files in `templates/` with lowercase snake_case names (e.g. `index.html`).

**Tests.** Unit tests in `scripts/test_*.py`; boot verification in `scripts/smoke_boot.py`. Do not create `scripts/tests/test_misc.py` (banned by semgrep gate).

**Style.** Ruff line-length 100. Snake_case for functions and variables; PascalCase for classes.

## Module Responsibilities

| Module | Owns | Must NOT |
|--------|------|----------|
| `main.py` | `app = create_app()` re-export for uvicorn | Contain business logic; be renamed or moved |
| `app/__init__.py` | App assembly, router auto-include, conditional DB init | HTTP handlers, domain rules |
| `app/config.py` | `Settings` and `settings` singleton | Database or route wiring |
| `app/db.py` | Engine, `SessionLocal`, `Base`, `get_session`, SQLite `create_all` | Business logic; Postgres `create_all` |
| `app/models.py` | ORM table definitions | HTTP or validation schemas |
| `app/health.py` | `GET /health` returning exactly `{"status": "ok"}` | Auth, DB access, extra fields |
| `app/capsule.py` | Capsule descriptor data and `tool_surface()` | HTTP routing |
| `app/routers/*` | HTTP surface for one feature (paths, deps, schemas) | Cross-cutting infra; direct engine creation |
| `alembic/` | Postgres schema revisions | Runtime table creation for Postgres |
| `scripts/smoke_boot.py` | Import `main:app`, verify `/health` | Modify `sys.path` |
| `templates/` | Jinja HTML only | Python logic |

**Invariants.** A task belongs to exactly one project. Task status ∈ `{open, doing, done}`. Postgres schema is applied only through Alembic (never `Base.metadata.create_all` on Postgres). The `/health` response body is immutable.

## How to Test

From the repository root (no `PYTHONPATH`, no `src/` layout):

```bash
# Fast unit smoke (<15s)
python -m pytest scripts/test_unit.py -x -q

# Boot verification (imports main:app like Docker CMD)
python -m scripts.smoke_boot
```

When adding topic-specific tests under `scripts/tests/`, run the matching file:

```bash
python -m pytest scripts/tests/test_<topic>.py -x -q --tb=short
```

Do not run the full `scripts/tests/` suite in CI workers (10+ minutes). Migration shape can be checked with `alembic check` (no DB required); runtime migration apply belongs in forge_uat.