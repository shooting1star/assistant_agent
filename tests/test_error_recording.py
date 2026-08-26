from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.server import app
from fastapi.testclient import TestClient


def test_error_event_creates_markdown_record(tmp_path):
    client = TestClient(app)
    payload = {
        "eventType": "error",
        "filePath": str(tmp_path / "main.py"),
        "message": "NameError: name 'x' is not defined",
        "stackTrace": "Traceback...",
        "apiKey": "secret123",
    }

    response = client.post("/events", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert "NameError" in str(data)
    assert "resolved" in str(data).lower() or "open" in str(data).lower()

    records_dir = Path(".codemate/errors")
    assert records_dir.exists()
    assert any(records_dir.glob("ERR-*.md"))
