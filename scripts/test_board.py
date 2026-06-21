# Integration tests for the public board page at /.
import os
from unittest import mock

from fastapi.testclient import TestClient

from app import create_app


def test_root_returns_200_without_auth():
    client = TestClient(create_app())
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_root_renders_created_project_name():
    env = {k: v for k, v in os.environ.items() if k != "APP_API_KEY"}
    with mock.patch.dict(os.environ, env, clear=True):
        client = TestClient(create_app())
        client.post("/projects", json={"name": "Board Project"})
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Board Project" in resp.text