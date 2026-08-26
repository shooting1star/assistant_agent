import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI

from agent.change_manager import ChangeManager
from agent.error_analyzer import ErrorAnalyzer
from agent.ollama_client import OllamaClient
from agent.optimization_engine import OptimizationEngine
from agent.privacy_filter import PrivacyFilter
from agent.record_manager import RecordManager

app = FastAPI(title="assistant_agent")
record_manager = RecordManager()
change_manager = ChangeManager()
ollama_client = OllamaClient()
optimization_engine = OptimizationEngine(ollama_client=ollama_client, record_manager=record_manager)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "assistant_agent"}


@app.post("/events")
def receive_event(event: dict):
    masked_event = PrivacyFilter.mask_data(event)
    event_type = str(masked_event.get("eventType", "")).lower()

    if event_type in {"error", "diagnostic", "runtime_error"}:
        message = str(masked_event.get("message", "Unknown error"))
        stack = str(masked_event.get("stackTrace", ""))
        summary = ErrorAnalyzer.summarize(message, stack)
        record_path = record_manager.save_error_summary({**masked_event, "summary": summary})
        payload = {
            "status": "accepted",
            "eventType": "error",
            "summary": summary,
            "record": str(record_path),
        }
        return payload

    return {
        "status": "accepted",
        "received": masked_event,
    }


@app.post("/apply-change")
def apply_change(payload: dict):
    file_path = payload.get("file_path")
    new_content = payload.get("new_content", "")
    approved = bool(payload.get("approved", False))

    if not file_path:
        return {"status": "invalid", "message": "file_path is required"}

    result = change_manager.apply_change(file_path, new_content, approved=approved)

    if result["status"] == "pending_approval":
        return result

    if result["status"] in {"applied", "rolled_back"}:
        return result

    return {"status": "error", "message": "unknown change result"}


@app.post("/run-file")
def run_file(payload: dict):
    file_path = payload.get("file_path")
    timeout = min(float(payload.get("timeout", 10)), 30)

    if not file_path:
        return {"status": "invalid", "message": "file_path is required"}

    try:
        completed = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(Path(file_path).parent),
        )
    except subprocess.TimeoutExpired:
        return {"status": "error", "return_code": None, "stderr": "Execution timed out."}
    except OSError as error:
        return {"status": "error", "return_code": None, "stderr": str(error)}

    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "return_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


@app.post("/analyze")
def analyze(prompt: dict):
    text = str(prompt.get("text", ""))
    response = ollama_client.generate(text)
    return response


@app.post("/suggest-fix")
def suggest_fix(payload: dict):
    file_path = payload.get("file_path", "unknown.py")
    current_content = str(payload.get("current_content", ""))
    message = str(payload.get("message", "Unknown error"))

    suggested = current_content
    if "nameerror" in message.lower() or "not defined" in message.lower():
        suggested = current_content.strip() + "\n# Suggested fix: ensure the variable is defined before use\nvalue = 0\nprint(value)\n"
    elif "syntaxerror" in message.lower():
        suggested = current_content.strip() + "\n# Suggested fix: check syntax and bracket balance\n"
    else:
        suggested = current_content.strip() + "\n# Suggested fix: review the failing statement and validate again\n"

    return {
        "file_path": file_path,
        "message": message,
        "suggested_content": suggested,
        "status": "ready_for_approval",
    }


@app.post("/optimize")
def optimize_code(payload: dict):
    file_path = str(payload.get("file_path", "example.py"))
    code = str(payload.get("code", ""))
    result = optimization_engine.analyze_code(file_path, code)
    return {
        "status": result["status"],
        "model": result["model"],
        "suggestion": result["suggestion"],
        "record_path": str(result["record_path"]),
    }
