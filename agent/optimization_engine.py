from __future__ import annotations

import ast
from pathlib import Path

from agent.ollama_client import OllamaClient
from agent.record_manager import RecordManager


class OptimizationEngine:
    def __init__(self, ollama_client: OllamaClient | None = None, record_manager: RecordManager | None = None):
        self.ollama_client = ollama_client or OllamaClient()
        self.record_manager = record_manager or RecordManager()

    def analyze_code(self, file_path: str, code: str) -> dict:
        static_findings = self._static_findings(code)
        prompt = (
            "Optimize this Python code. You are a Python optimization reviewer; return concise, actionable suggestions. "
            "Cover performance, time and space complexity, readability, and risks. "
            "Do not rewrite or apply files. Use this format: Summary, Findings, Complexity, Proposed change.\n\n"
            f"File: {file_path}\n\nCode:\n{code}"
        )

        result = self.ollama_client.generate(prompt)
        response_text = str(result.get("response", ""))

        suggestion = response_text.strip()
        if not result.get("ok") or not suggestion or suggestion.startswith("Ollama unavailable"):
            suggestion = "\n".join(static_findings) or "정적 분석에서 즉시 개선할 항목을 찾지 못했습니다."
        elif static_findings:
            suggestion = f"{suggestion}\n\n정적 분석 참고:\n" + "\n".join(static_findings)
        title = f"Optimization for {Path(file_path).name}"
        record_path = self.record_manager.save_optimization(title, suggestion)

        return {
            "status": "suggested",
            "model": result.get("model", self.ollama_client.model_name),
            "suggestion": suggestion,
            "record_path": record_path,
        }

    def _static_findings(self, code: str) -> list[str]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return ["코드가 현재 문법 오류 상태이므로 최적화 전에 문법을 먼저 수정하세요."]

        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.For) and any(isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == "append" for child in ast.walk(node)):
                findings.append("반복문 내부 append 패턴은 리스트 컴프리헨션으로 단순화할 수 있는지 검토하세요.")
                break
        if sum(isinstance(node, ast.For) for node in ast.walk(tree)) > 1:
            findings.append("중첩 반복문이 있어 입력 크기에 따라 시간 복잡도가 커질 수 있습니다.")
        return findings
