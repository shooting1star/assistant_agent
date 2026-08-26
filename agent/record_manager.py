from datetime import datetime
from pathlib import Path


class RecordManager:
    def __init__(self, root_dir: str = ".codemate"):
        self.root = Path(root_dir)
        self.root.mkdir(exist_ok=True)
        (self.root / "errors").mkdir(exist_ok=True)
        (self.root / "issues").mkdir(exist_ok=True)
        (self.root / "optimizations").mkdir(exist_ok=True)

    def save_error(self, title: str, content: str) -> Path:
        return self._save_record("errors", "ERR", title, content)

    def save_issue(self, title: str, content: str) -> Path:
        return self._save_record("issues", "ISSUE", title, content)

    def save_optimization(self, title: str, content: str) -> Path:
        return self._save_record("optimizations", "OPT", title, content)

    def _save_record(self, folder: str, prefix: str, title: str, content: str) -> Path:
        folder_path = self.root / folder
        count = len(list(folder_path.glob(f"{prefix}-*.md"))) + 1
        file_name = f"{prefix}-{count:04d}.md"
        file_path = folder_path / file_name
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        file_path.write_text(f"# {title}\n\n**생성일:** {timestamp}\n\n{content}\n", encoding="utf-8")
        return file_path

    def save_error_summary(self, event: dict) -> Path:
        summary = event.get("summary") or {}
        title = summary.get("problem") or event.get("message") or "오류 기록"
        body = (
            f"## 문제\n{summary.get('problem', '알 수 없는 오류')}\n\n"
            f"## 원인\n{summary.get('cause', '원인을 확인해야 합니다')}\n\n"
            f"## 기대 결과\n{summary.get('expected_result', '오류 없이 실행')}\n\n"
            f"## 해결 방법\n{summary.get('solution', '근본 원인을 확인하고 수정하세요')}\n\n"
            f"## 상태\n{summary.get('status', '열림')}\n"
        )
        return self.save_error(title[:80], body)
