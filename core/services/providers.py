import os
import re

import requests
from django.conf import settings

from core.sanitizers import sanitize_plain_text


LEGACY_GEMINI_MODELS = {
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-2.5-flash-preview-05-06",
}


def normalize_gemini_model(value=None):
    raw_value = (value if value is not None else os.getenv("GEMINI_MODEL", "gemini-3.5-flash")).strip()
    if not raw_value:
        return "gemini-3.5-flash"
    if raw_value in LEGACY_GEMINI_MODELS:
        return "gemini-3.5-flash"
    return raw_value


def redact_secrets(value, secrets=()):
    if not isinstance(value, str):
        return value
    redacted = value
    sensitive_values = [
        *secrets,
        os.getenv("GEMINI_API_KEY", ""),
        os.getenv("GROQ_API_KEY", ""),
        os.getenv("OPENROUTER_API_KEY", ""),
        os.getenv("DJANGO_SECRET_KEY", ""),
        getattr(settings, "SECRET_KEY", ""),
    ]
    for secret in sensitive_values:
        if isinstance(secret, str) and secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    redacted = re.sub(r"AIza[0-9A-Za-z\-_]+", "[REDACTED_API_KEY]", redacted)
    redacted = re.sub(
        r"(?i)([?&](?:key|api[_-]?key|access[_-]?token|refresh[_-]?token|token|password)=)[^&\s]+",
        r"\1[REDACTED]",
        redacted,
    )
    redacted = re.sub(r"(?i)(authorization\s*:\s*bearer\s+)[^\s,]+", r"\1[REDACTED]", redacted)
    return re.sub(
        r"(?i)([\"']?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|token|password|authorization)[\"']?\s*[:=]\s*[\"']?)[^\"'\s,}]+",
        r"\1[REDACTED]",
        redacted,
    )


def safe_response_body(value, secrets=()):
    if not value:
        return ""
    return redact_secrets(str(value), secrets)[:400]


class BaseProvider:
    name = "provider"
    endpoint = ""
    api_key_env = ""
    model_env = ""
    default_model = ""

    def __init__(self, api_key=None, model=None):
        self.api_key = (api_key if api_key is not None else os.getenv(self.api_key_env, "")).strip()
        configured_model = model if model is not None else os.getenv(self.model_env, self.default_model)
        if self.name == "gemini":
            configured_model = normalize_gemini_model(configured_model)
        self.model = (configured_model or "").strip()

    def _failure(self, error, *, status=None, exception=None, response=""):
        return {
            "success": False,
            "provider": self.name,
            "error": redact_secrets(error, (self.api_key,))[:400],
            "status": status,
            "exception": exception,
            "response": safe_response_body(response, (self.api_key,)),
        }

    def _build_payload(self, messages, system_prompt):
        raise NotImplementedError

    def _extract_text(self, payload):
        raise NotImplementedError

    def _headers(self):
        raise NotImplementedError

    def _endpoint(self):
        return self.endpoint

    def _request_json(self, payload, timeout_seconds):
        if not self.api_key:
            return self._failure(f"{self.name.title()} is not configured.", exception="ConfigurationError")
        if not self.model:
            return self._failure(f"{self.name.title()} model is not configured.", exception="ConfigurationError")

        params = {"key": self.api_key} if self.name == "gemini" else None
        try:
            response = requests.post(
                self._endpoint(),
                params=params,
                json=payload,
                headers=self._headers(),
                timeout=timeout_seconds,
            )
        except requests.exceptions.Timeout as exc:
            return self._failure(
                f"{self.name.title()} request timed out.",
                exception=exc.__class__.__name__,
            )
        except requests.exceptions.ConnectionError as exc:
            return self._failure(
                f"Could not connect to {self.name.title()}.",
                exception=exc.__class__.__name__,
            )
        except requests.RequestException as exc:
            return self._failure(
                f"{self.name.title()} request failed.",
                exception=exc.__class__.__name__,
            )

        status = getattr(response, "status_code", 0)
        if not 200 <= status < 300:
            body = safe_response_body(getattr(response, "text", ""), (self.api_key,))
            message = f"{self.name.title()} request failed with HTTP {status}."
            try:
                error_payload = response.json()
                error = error_payload.get("error") if isinstance(error_payload, dict) else None
                if isinstance(error, dict) and isinstance(error.get("message"), str):
                    message = f"{self.name.title()} request failed with HTTP {status}: {error['message']}"
                elif isinstance(error, str):
                    message = f"{self.name.title()} request failed with HTTP {status}: {error}"
            except (TypeError, ValueError):
                pass
            return self._failure(message, status=status, exception="HTTPError", response=body)

        try:
            data = response.json()
        except ValueError as exc:
            return self._failure(
                f"{self.name.title()} returned invalid JSON.",
                status=status,
                exception=exc.__class__.__name__,
                response=getattr(response, "text", ""),
            )
        if not isinstance(data, dict):
            return self._failure(
                f"{self.name.title()} returned an invalid response.",
                status=status,
                exception="InvalidResponse",
                response=getattr(response, "text", ""),
            )
        return {"success": True, "payload": data, "status": status}

    def generate_response(self, messages, system_prompt, timeout_seconds=20):
        result = self._request_json(self._build_payload(messages, system_prompt), timeout_seconds)
        if not result["success"]:
            return result
        text = self._extract_text(result["payload"])
        if not text:
            return self._failure(
                f"{self.name.title()} returned no usable text.",
                status=result["status"],
                exception="EmptyResponse",
                response=result["payload"],
            )
        return {"success": True, "provider": self.name, "text": sanitize_plain_text(text)}


class GeminiProvider(BaseProvider):
    name = "gemini"
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    api_key_env = "GEMINI_API_KEY"
    model_env = "GEMINI_MODEL"
    default_model = "gemini-2.5-flash"

    def _build_payload(self, messages, system_prompt):
        contents = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            text = message.get("content")
            if not isinstance(text, str) or not text.strip():
                continue
            role = "model" if message.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": text}]})
        return {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
        }

    def _headers(self):
        return {"Content-Type": "application/json"}

    def _endpoint(self):
        return self.endpoint.format(model=self.model)

    def _extract_text(self, payload):
        candidates = payload.get("candidates") or []
        if not isinstance(candidates, list):
            return ""
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            content = candidate.get("content")
            if not isinstance(content, dict):
                continue
            parts = content.get("parts")
            if not isinstance(parts, list):
                continue
            for part in parts:
                if isinstance(part, dict) and isinstance(part.get("text"), str) and part["text"].strip():
                    return part["text"]
        return ""


class OpenAICompatibleProvider(BaseProvider):
    def _build_payload(self, messages, system_prompt):
        normalized_messages = [{"role": "system", "content": system_prompt}]
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = message.get("role")
            content = message.get("content")
            if role not in {"user", "assistant"} or not isinstance(content, str):
                continue
            normalized_messages.append({"role": role, "content": content})
        return {"model": self.model, "messages": normalized_messages}

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _extract_text(self, payload):
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            return ""
        message = choices[0].get("message")
        if not isinstance(message, dict):
            return ""
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            return "\n".join(
                part["text"]
                for part in content
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ).strip()
        return ""


class GroqProvider(OpenAICompatibleProvider):
    name = "groq"
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    api_key_env = "GROQ_API_KEY"
    model_env = "GROQ_MODEL"
    default_model = "openai/gpt-oss-20b"


class OpenRouterProvider(OpenAICompatibleProvider):
    name = "openrouter"
    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    api_key_env = "OPENROUTER_API_KEY"
    model_env = "OPENROUTER_MODEL"
    default_model = "openai/gpt-oss-20b"