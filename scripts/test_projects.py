# Unit tests for Project model and /projects endpoints.
import os
from unittest import mock

from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app import create_app
from app.db import Base, engine, init_sqlite_schema
from app.models import Project

API_KEY = "test-secret-key"


def test_project_model_attributes():
    project = Project(name="x")
    assert project.name == "x"
    assert hasattr(project, "id")


def test_projects_table_registered():
    import app.models  # noqa: F401

    assert "projects" in Base.metadata.tables


def test_init_sqlite_schema_creates_projects():
    init_sqlite_schema()
    inspector = inspect(engine)
    assert "projects" in inspector.get_table_names()


def test_post_without_api_key_returns_401():
    with mock.patch.dict(os.environ, {"TASKDECK_API_KEY": API_KEY}, clear=False):
        client = TestClient(create_app())
        resp = client.post("/projects", json={"name": "Alpha"})
        assert resp.status_code == 401


def test_post_with_api_key_returns_201():
    with mock.patch.dict(os.environ, {"TASKDECK_API_KEY": API_KEY}, clear=False):
        client = TestClient(create_app())
        resp = client.post(
            "/projects",
            json={"name": "Alpha"},
            headers={"X-API-Key": API_KEY},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Alpha"
        assert isinstance(data["id"], int)


def test_get_projects_returns_created():
    with mock.patch.dict(os.environ, {"TASKDECK_API_KEY": API_KEY}, clear=False):
        client = TestClient(create_app())
        client.post(
            "/projects",
            json={"name": "Beta"},
            headers={"X-API-Key": API_KEY},
        )
        resp = client.get("/projects", headers={"X-API-Key": API_KEY})
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()]
        assert "Beta" in names


def test_auth_bypassed_when_no_key_configured():
    env = {k: v for k, v in os.environ.items() if k != "TASKDECK_API_KEY"}
    with mock.patch.dict(os.environ, env, clear=True):
        client = TestClient(create_app())
        resp = client.post("/projects", json={"name": "Open"})
        assert resp.status_code == 201
        assert resp.json()["name"] == "Open"