import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from agent.server import app


def test_suggest_fix_returns_content_for_error():
    client = TestClient(app)
    response = client.post(
        "/suggest-fix",
        json={
            "file_path": "/tmp/example.py",
            "current_content": "print(unknown_variable)\n",
            "message": "NameError: name unknown_variable is not defined",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "suggested_content" in data
    assert "unknown_variable" in data["suggested_content"] or "fixed" in data["suggested_content"].lower()


def test_apply_change_endpoint_can_accept_approval():
    client = TestClient(app)
    file_path = Path("/tmp/assistant_agent_approval_test.py")
    file_path.write_text("print('before')\n", encoding="utf-8")

    response = client.post(
        "/apply-change",
        json={
            "file_path": str(file_path),
            "new_content": "print('approved')\n",
            "approved": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "applied"
    assert file_path.read_text(encoding="utf-8") == "print('approved')\n"
