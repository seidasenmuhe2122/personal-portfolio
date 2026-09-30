import logging
import os
import time

from core.sanitizers import sanitize_plain_text

from .providers import GeminiProvider, GroqProvider, OpenRouterProvider, normalize_gemini_model, redact_secrets

logger = logging.getLogger(__name__)

PROVIDER_NAMES = ("gemini", "groq", "openrouter")
DEFAULT_PROVIDER_ORDER = PROVIDER_NAMES
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-oss-20b"


def get_provider_order(value=None):
    raw_order = value if value is not None else os.getenv("AI_PROVIDER_ORDER", "")
    order = []
    for item in raw_order.split(","):
        provider = item.strip().lower()
        if provider in PROVIDER_NAMES and provider not in order:
            order.append(provider)
    return tuple(order) or DEFAULT_PROVIDER_ORDER


def get_ai_timeout_seconds(value=None):
    raw_value = value if value is not None else os.getenv("AI_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    try:
        timeout = float(raw_value)
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT_SECONDS
    return min(max(timeout, 1.0), 120.0)


def get_ai_configuration():
    gemini_model = normalize_gemini_model(os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL))
    groq_model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL
    openrouter_model = os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL).strip() or DEFAULT_OPENROUTER_MODEL
    return {
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY", "").strip()),
        "groq_configured": bool(os.getenv("GROQ_API_KEY", "").strip()),
        "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY", "").strip()),
        "gemini_model": redact_secrets(gemini_model),
        "groq_model": redact_secrets(groq_model),
        "openrouter_model": redact_secrets(openrouter_model),
        "provider_order": get_provider_order(),
        "timeout_seconds": get_ai_timeout_seconds(),
    }


class AIService:
    def __init__(
        self,
        providers=None,
        provider_order=None,
        timeout_seconds=None,
        fallback_message="AI assistant is temporarily unavailable. Please try again.",
    ):
        self.provider_order = get_provider_order(",".join(provider_order)) if provider_order is not None else get_provider_order()
        self.providers = providers or {
            "gemini": GeminiProvider(),
            "groq": GroqProvider(),
            "openrouter": OpenRouterProvider(),
        }
        self.timeout_seconds = get_ai_timeout_seconds(timeout_seconds) if timeout_seconds is not None else get_ai_timeout_seconds()
        self.fallback_message = fallback_message

    def generate_response(self, messages, system_prompt):
        deadline = time.monotonic() + self.timeout_seconds
        attempts = []
        per_provider_budget = self.timeout_seconds / max(len(self.provider_order), 1)

        for index, provider_name in enumerate(self.provider_order):
            provider = self.providers.get(provider_name)
            if provider is None:
                result = {
                    "success": False,
                    "provider": provider_name,
                    "error": "Provider is not available.",
                    "exception": "ConfigurationError",
                }
            else:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                timeout_seconds = min(remaining, per_provider_budget)
                try:
                    result = provider.generate_response(
                        messages,
                        system_prompt,
                        timeout_seconds=timeout_seconds,
                    )
                except Exception as exc:
                    result = {
                        "success": False,
                        "provider": provider_name,
                        "error": f"{provider_name.title()} request failed.",
                        "exception": exc.__class__.__name__,
                    }

            text = result.get("text") if isinstance(result, dict) else None
            if isinstance(result, dict) and result.get("success") and isinstance(text, str) and text.strip():
                logger.info("AI provider success: %s", provider_name)
                return {
                    "success": True,
                    "provider": provider_name,
                    "text": sanitize_plain_text(text),
                }

            result = result if isinstance(result, dict) else {}
            failure = {
                "provider": provider_name,
                "status": result.get("status"),
                "exception": result.get("exception"),
                "error": redact_secrets(str(result.get("error") or "Provider returned no usable response."))[:400],
                "response": redact_secrets(str(result.get("response") or ""))[:400],
            }
            attempts.append(failure)
            if failure["status"] is not None:
                logger.warning(
                    "AI provider failed: %s | HTTP %s | %s | response=%s",
                    provider_name,
                    failure["status"],
                    failure["error"],
                    failure["response"],
                )
            else:
                logger.warning(
                    "AI provider failed: %s | %s | %s | response=%s",
                    provider_name,
                    failure["exception"] or "request error",
                    failure["error"],
                    failure["response"],
                )

            if index + 1 < len(self.provider_order):
                next_provider = self.provider_order[index + 1]
                if time.monotonic() < deadline:
                    logger.info("Trying next provider: %s", next_provider)

        logger.warning("AI providers exhausted; returning safe fallback.")
        return {
            "success": False,
            "provider": "fallback",
            "text": self.fallback_message,
            "error": "All configured AI providers failed or are unavailable.",
            "attempts": attempts,
        }