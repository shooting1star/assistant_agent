from __future__ import annotations

from pathlib import Path

from agent.ollama_client import OllamaClient
from agent.record_manager import RecordManager


class OptimizationEngine:
    def __init__(self, ollama_client: OllamaClient | None = None, record_manager: RecordManager | None = None):
        self.ollama_client = ollama_client or OllamaClient()
        self.record_manager = record_manager or RecordManager()

    def analyze_code(self, file_path: str, code: str) -> dict:
        prompt = (
            "Optimize this Python code for performance and readability. "
            "Provide practical suggestions in Korean or English. "
            "Focus on logic, unnecessary loops, repeated work, and clearer structure.\n\n"
            f"File: {file_path}\n\nCode:\n{code}"
        )

        result = self.ollama_client.generate(prompt)
        response_text = str(result.get("response", ""))

        suggestion = response_text.strip() or "No optimization suggestion generated."
        title = f"Optimization for {Path(file_path).name}"
        record_path = self.record_manager.save_optimization(title, suggestion)

        return {
            "status": "suggested",
            "model": result.get("model", self.ollama_client.model_name),
            "suggestion": suggestion,
            "record_path": record_path,
        }
