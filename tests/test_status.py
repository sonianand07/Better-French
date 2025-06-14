import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from mcp_server.main import app, ROLLING_JSON_PATH

client = TestClient(app)


@pytest.fixture
def fake_rolling_file(tmp_path, monkeypatch):
    data = [{"id": i} for i in range(42)]
    path = tmp_path / "rolling_articles.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    # point ROLLING_JSON_PATH to tmp file
    monkeypatch.setattr("mcp_server.main.ROLLING_JSON_PATH", path)
    # patch git pull subprocess
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: None)
    yield


def test_status_endpoint(fake_rolling_file):
    res = client.get("/status")
    assert res.status_code == 200
    assert res.json() == {"live_articles": 42}


def test_chat_article_count(fake_rolling_file, monkeypatch):
    # patch the model call to avoid LLM
    async def fake_post(*args, **kwargs):
        raise AssertionError("LLM should not be called for count question")

    monkeypatch.setattr("httpx.AsyncClient.post", fake_post)

    payload = {"user_id": "u", "message": "How many articles are live?"}
    res = client.post("/chat", json=payload)
    assert res.status_code == 200
    assert "42" in res.json()["reply"]
    assert res.json()["total_tokens"] == 0 