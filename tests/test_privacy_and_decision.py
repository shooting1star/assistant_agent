import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.privacy_filter import PrivacyFilter
from agent.decision_engine import DecisionEngine


def test_mask_sensitive_values():
    text = "Bearer sk-123456 and password=secret123 and API_KEY=abcd"
    masked = PrivacyFilter.mask_text(text)

    assert "sk-123456" not in masked
    assert "secret123" not in masked
    assert "abcd" not in masked
    assert "[MASKED]" in masked


def test_decision_engine_requires_repeat_signals():
    engine = DecisionEngine()

    assert engine.should_intervene("python") is False
    assert engine.should_intervene("python") is False
    assert engine.should_intervene("python") is False

    engine.record_event("python", "error")
    engine.record_event("python", "error")
    engine.record_event("python", "error")

    assert engine.should_intervene("python") is True


def test_quiet_mode_blocks_intervention():
    engine = DecisionEngine(quiet_mode=True)
    engine.record_event("python", "error")
    engine.record_event("python", "error")
    engine.record_event("python", "error")

    assert engine.should_intervene("python") is False
