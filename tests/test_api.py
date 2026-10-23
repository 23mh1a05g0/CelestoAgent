"""Integration tests for FastAPI endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "environment" in data
        assert "celesto_configured" in data
        assert "llm_configured" in data


@pytest.mark.asyncio
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Celesto AI Agent Sandbox Platform"
        assert data["status"] == "online"


@pytest.mark.asyncio
async def test_runs_validation_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid payload: task_description too short
        response = await client.post("/api/runs", json={"task_description": "ab"})
        assert response.status_code == 422
