import json
import urllib.request


class OllamaClient:
    def __init__(self, model_name: str = "llama3.2", base_url: str = "http://127.0.0.1:11434"):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str) -> dict:
        payload = json.dumps({
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }).encode("utf-8")

        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
                parsed = json.loads(body)
                return {
                    "ok": True,
                    "model": self.model_name,
                    "response": parsed.get("response", ""),
                }
        except Exception:
            return {
                "ok": False,
                "model": self.model_name,
                "response": "Ollama unavailable. Fallback to local logic only.",
            }
