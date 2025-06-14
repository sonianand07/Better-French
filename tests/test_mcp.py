import json
from fastapi.testclient import TestClient
import pytest

from mcp_server.main import app

client = TestClient(app)


def fake_openrouter_call(*args, **kwargs):
    """Return a minimal fake OpenRouter response."""
    return {
        "choices": [
            {"message": {"content": "Hello world"}}
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


@pytest.fixture(autouse=True)
def patch_openrouter(monkeypatch):
    # Patch httpx.AsyncClient.post to avoid real API calls
    async def _fake_post(self, url, json, headers):
        class _Resp:
            status_code = 200

            def json(self_inner):
                return fake_openrouter_call()

            def raise_for_status(self_inner):
                return None

        return _Resp()

    monkeypatch.setattr("httpx.AsyncClient.post", _fake_post)


def test_chat_endpoint():
    payload = {"user_id": "test", "message": "Ping"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Hello world"
    assert data["total_tokens"] == 15
    assert data["cost_usd"] == pytest.approx(0.00035 * 10 / 1000 + 0.00070 * 5 / 1000) 