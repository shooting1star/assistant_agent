from pathlib import Path


class ChangeManager:
    def __init__(self):
        self._backup = {}

    def apply_change(self, file_path: str, new_content: str, approved: bool = False):
        path = Path(file_path)
        original = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""

        if not approved:
            return {
                "status": "pending_approval",
                "file_path": file_path,
                "preview": new_content,
                "validation": "pending",
            }

        self._backup[file_path] = original

        try:
            path.write_text(new_content, encoding="utf-8")
            validation = self._validate(path)

            if validation == "passed":
                return {
                    "status": "applied",
                    "file_path": file_path,
                    "validation": "passed",
                }

            path.write_text(original, encoding="utf-8")
            return {
                "status": "rolled_back",
                "file_path": file_path,
                "validation": "failed",
            }
        except Exception:
            if file_path in self._backup:
                path.write_text(self._backup[file_path], encoding="utf-8")
            return {
                "status": "rolled_back",
                "file_path": file_path,
                "validation": "failed",
            }

    def _validate(self, path: Path) -> str:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            compile(text, str(path), "exec")
            return "passed"
        except Exception:
            return "failed"
