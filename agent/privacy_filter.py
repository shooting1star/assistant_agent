import re


class PrivacyFilter:
    """Mask sensitive values before sending to the local LLM."""

    SENSITIVE_KEYS = {
        "api_key",
        "apikey",
        "apiKey",
        "token",
        "secret",
        "password",
        "passwd",
        "pwd",
        "aws_access_key_id",
        "aws_secret_access_key",
    }

    PATTERNS = [
        (
            re.compile(
                r"(?i)((?:api[_-]?key|apiKey|token|secret|password|passwd|pwd|aws_access_key_id|aws_secret_access_key)\s*[:=]\s*['\"]?)([^'\"\s,}]+)"
            ),
            r"\1[MASKED]",
        ),
        (
            re.compile(r"(?i)(?:\b(?:Bearer\s+)?(?:sk|ghp|github_pat|hf_)[A-Za-z0-9_\-]+)"),
            "[MASKED]",
        ),
    ]

    @staticmethod
    def mask_data(data):
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                key_name = str(key)
                if key_name.lower() in PrivacyFilter.SENSITIVE_KEYS or any(
                    part.lower() in PrivacyFilter.SENSITIVE_KEYS for part in key_name.lower().split("_")
                ):
                    sanitized[key] = "[MASKED]"
                else:
                    sanitized[key] = PrivacyFilter.mask_data(value)
            return sanitized
        if isinstance(data, list):
            return [PrivacyFilter.mask_data(item) for item in data]
        if isinstance(data, tuple):
            return tuple(PrivacyFilter.mask_data(item) for item in data)
        return data

    @staticmethod
    def mask_text(text: str):
        if not text:
            return text
        if isinstance(text, (dict, list, tuple)):
            return PrivacyFilter.mask_data(text)
        masked = str(text)
        for pattern, replacement in PrivacyFilter.PATTERNS:
            masked = pattern.sub(replacement, masked)
        return masked
