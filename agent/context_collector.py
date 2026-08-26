from pathlib import Path


class ContextCollector:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)

    def collect_context(self, file_path: str | None = None, max_lines: int = 80):
        if not file_path:
            return {
                "active_file": None,
                "snippet": "",
                "workspace_files": [],
            }

        path = Path(file_path)
        if not path.exists():
            return {
                "active_file": file_path,
                "snippet": "",
                "workspace_files": [],
            }

        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        snippet = "\n".join(lines[-max_lines:])

        return {
            "active_file": file_path,
            "snippet": snippet,
            "workspace_files": [str(p) for p in self.workspace_root.rglob("*") if p.is_file()],
        }
