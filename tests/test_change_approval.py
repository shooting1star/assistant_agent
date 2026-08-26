from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.change_manager import ChangeManager


def test_unapproved_change_stays_pending(tmp_path):
    file_path = tmp_path / "sample.py"
    file_path.write_text("print('before')\n", encoding="utf-8")

    manager = ChangeManager()
    result = manager.apply_change(str(file_path), "print('after')\n", approved=False)

    assert result["status"] == "pending_approval"
    assert file_path.read_text(encoding="utf-8") == "print('before')\n"


def test_approved_change_is_written_and_validated(tmp_path):
    file_path = tmp_path / "sample.py"
    file_path.write_text("print('before')\n", encoding="utf-8")

    manager = ChangeManager()
    result = manager.apply_change(str(file_path), "print('after')\n", approved=True)

    assert result["status"] == "applied"
    assert result["validation"] == "passed"
    assert file_path.read_text(encoding="utf-8") == "print('after')\n"


def test_invalid_change_rolls_back(tmp_path):
    file_path = tmp_path / "sample.py"
    file_path.write_text("print('before')\n", encoding="utf-8")

    manager = ChangeManager()
    result = manager.apply_change(str(file_path), "def broken(:\n", approved=True)

    assert result["status"] == "rolled_back"
    assert result["validation"] == "failed"
    assert file_path.read_text(encoding="utf-8") == "print('before')\n"
