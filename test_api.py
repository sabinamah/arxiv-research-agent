import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api


class FakeAgent:
    def __init__(self, answer="A cited answer.", error=None, delay=0.0):
        self.answer, self.error, self.delay = answer, error, delay

    async def ainvoke(self, payload):
        await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return {"messages": [SimpleNamespace(text=self.answer)]}


@pytest.fixture
def client():
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def use_agent(agent):
    api.app.dependency_overrides[api.get_agent] = lambda: agent


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_returns_answer_and_latency(client):
    use_agent(FakeAgent())
    response = client.post("/ask", json={"question": "What are LLM agents?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "A cited answer."
    assert body["latency_seconds"] >= 0


def test_ask_rejects_too_short_question(client):
    use_agent(FakeAgent())
    assert client.post("/ask", json={"question": "hi"}).status_code == 422


def test_ask_returns_502_when_agent_fails(client):
    use_agent(FakeAgent(error=RuntimeError("provider down")))
    response = client.post("/ask", json={"question": "What are LLM agents?"})
    assert response.status_code == 502


def test_ask_returns_504_on_timeout(client, monkeypatch):
    monkeypatch.setattr(api, "REQUEST_TIMEOUT_SECONDS", 0.01)
    use_agent(FakeAgent(delay=1))
    response = client.post("/ask", json={"question": "What are LLM agents?"})
    assert response.status_code == 504


def test_ask_returns_503_when_agent_cannot_be_created(client, monkeypatch):
    def broken_build():
        raise RuntimeError("missing key")

    api._cached_agent.cache_clear()
    monkeypatch.setattr(api, "build_agent", broken_build)
    response = client.post("/ask", json={"question": "What are LLM agents?"})
    assert response.status_code == 503
