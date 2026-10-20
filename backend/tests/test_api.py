import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.database import init_db

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_status"] == "connected"
    assert "gemini" in data["llm_model"].lower()

def test_get_settings():
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["chunk_size"] == 1000
    assert data["chunk_overlap"] == 150
    assert data["temperature"] == 0.2

def test_list_documents_empty():
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_seed_documents():
    response = client.get("/api/documents/seed/list")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
