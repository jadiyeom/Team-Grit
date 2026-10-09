from pathlib import Path
import sys

# Ensure the repository root is importable in GitHub Actions and local pytest runs.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_provider_modes_are_available():
    response = client.get("/api/v1/providers")
    assert response.status_code == 200
    modes = {item["id"] for item in response.json()["modes"]}
    assert {"auto", "quality", "fast", "local", "custom"} <= modes


def test_generation_validates_prompt():
    response = client.post("/api/v1/projects", json={"prompt": "tiny"})
    assert response.status_code == 422


def test_unknown_project_returns_404():
    response = client.get("/api/v1/projects/aaaaaaaaaaaa")
    assert response.status_code == 404
