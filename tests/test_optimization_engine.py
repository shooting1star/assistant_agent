import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.optimization_engine import OptimizationEngine
from agent.record_manager import RecordManager


def test_optimization_engine_uses_ollama_and_saves_record(tmp_path, monkeypatch):
    def fake_generate(self, prompt):
        assert "optimize" in prompt.lower()
        return {
            "ok": True,
            "model": "demo-model",
            "response": "- Use a list comprehension instead of an append loop.\n- Avoid repeated function calls inside the loop.",
        }

    monkeypatch.setattr("agent.ollama_client.OllamaClient.generate", fake_generate)

    record_root = tmp_path / ".codemate"
    engine = OptimizationEngine(record_manager=RecordManager(root_dir=str(record_root)))
    result = engine.analyze_code(
        "demo.py",
        "result = []\nfor i in range(10):\n    result.append(i * 2)\n",
    )

    assert result["status"] == "suggested"
    assert "list comprehension" in result["suggestion"].lower()
    assert result["record_path"].exists()
    assert "OPT-" in result["record_path"].name
