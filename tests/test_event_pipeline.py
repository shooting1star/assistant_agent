import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from agent.server import app


def test_event_endpoint_masks_sensitive_values():
    client = TestClient(app)
    payload = {
        "eventType": "save",
        "filePath": "/tmp/example.py",
        "apiKey": "secret123",
        "token": "abc123xyz",
        "password": "super-secret"
    }

    response = client.post("/events", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert "secret123" not in str(body)
    assert "abc123xyz" not in str(body)
    assert "super-secret" not in str(body)
    assert "[MASKED]" in str(body)
