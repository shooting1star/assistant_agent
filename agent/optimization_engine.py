from __future__ import annotations

import ast
import re
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
            "Write every heading, subheading, explanation, finding, risk, and complexity description in Korean. "
            "Use Korean labels such as 요약, 개선 사항, 복잡도, 위험 요소, 제안 코드, 설명. "
            "Return a short explanation followed by the complete optimized Python code inside a ```python code fence. "
            "Do not apply files.\n\n"
            f"File: {file_path}\n\nCode:\n{code}"
        )

        result = self.ollama_client.generate(prompt)
        response_text = str(result.get("response", ""))

        suggestion = response_text.strip()
        if not result.get("ok") or not suggestion or suggestion.startswith("Ollama unavailable"):
            suggestion = "\n".join(static_findings) or "정적 분석에서 즉시 개선할 항목을 찾지 못했습니다."
        elif static_findings:
            suggestion = f"{suggestion}\n\n정적 분석 참고:\n" + "\n".join(static_findings)
        optimized_code = self._extract_code(response_text) or self._fallback_code(code)
        title = f"최적화 제안: {Path(file_path).name}"
        record_content = (
            f"## 분석 결과\n{suggestion}\n\n"
            f"## 제안 코드\n```python\n{optimized_code}\n```\n"
        )
        record_path = self.record_manager.save_optimization(title, record_content)

        return {
            "status": "suggested" if result.get("ok") else "fallback",
            "ollama_connected": bool(result.get("ok")),
            "model": result.get("model", self.ollama_client.model_name),
            "suggestion": suggestion,
            "optimized_code": optimized_code,
            "record_path": record_path,
        }

    def _extract_code(self, response: str) -> str:
        matches = re.findall(r"```(?:python|py)?\s*\n(.*?)```", response, re.DOTALL | re.IGNORECASE)
        for candidate in reversed(matches):
            candidate = candidate.strip()
            try:
                compile(candidate, "<ollama-optimization>", "exec")
                return candidate
            except SyntaxError:
                continue
        return ""

    def _fallback_code(self, code: str) -> str:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code
        for node in ast.walk(tree):
            if isinstance(node, ast.While) and isinstance(node.test, ast.Constant) and node.test.value is True:
                return code
        return code

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
