import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from agent.ollama_client import OllamaClient
from agent.server import app


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_ollama_client_calls_local_api(monkeypatch):
    called = {}

    def fake_urlopen(request, timeout=None):
        called["url"] = request.full_url
        called["timeout"] = timeout
        return FakeResponse({"response": "fixed"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    client = OllamaClient(model_name="demo-model", base_url="http://127.0.0.1:11434")
    result = client.generate("fix the bug")

    assert result["ok"] is True
    assert result["response"] == "fixed"
    assert called["url"].startswith("http://127.0.0.1:11434/api/generate")


def test_apply_change_endpoint_requires_approval(tmp_path):
    file_path = tmp_path / "demo.py"
    file_path.write_text("print('before')\n", encoding="utf-8")

    client = TestClient(app)
    response = client.post(
        "/apply-change",
        json={
            "file_path": str(file_path),
            "new_content": "print('after')\n",
            "approved": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pending_approval"
    assert file_path.read_text(encoding="utf-8") == "print('before')\n"
