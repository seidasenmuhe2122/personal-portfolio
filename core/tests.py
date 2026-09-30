import json
import os
from unittest.mock import Mock, patch

import requests
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import resolve, reverse

from core.models import AIConversation
from core.services.ai_service import AIService, get_ai_configuration, get_provider_order
from core.services.providers import GeminiProvider, GroqProvider, OpenRouterProvider


class StubProvider:
    def __init__(self, name, result):
        self.name = name
        self.result = result
        self.calls = []

    def generate_response(self, messages, system_prompt, timeout_seconds=20):
        self.calls.append((messages, system_prompt, timeout_seconds))
        if isinstance(self.result, Exception):
            raise self.result
        return dict(self.result)


class AIServiceTests(TestCase):
    def setUp(self):
        self.fallback = "AI assistant is temporarily unavailable. Please try again."

    def test_gemini_success_stops_provider_chain(self):
        gemini = StubProvider("gemini", {"success": True, "provider": "gemini", "text": "Gemini reply"})
        groq = StubProvider("groq", {"success": True, "provider": "groq", "text": "Groq reply"})
        service = AIService(
            providers={"gemini": gemini, "groq": groq},
            provider_order=("gemini", "groq"),
            timeout_seconds=20,
            fallback_message=self.fallback,
        )

        result = service.generate_response([{"role": "user", "content": "hello"}], "portfolio prompt")

        self.assertEqual(result, {"success": True, "provider": "gemini", "text": "Gemini reply"})
        self.assertEqual(len(gemini.calls), 1)
        self.assertEqual(groq.calls, [])

    def test_gemini_failure_then_groq_success(self):
        gemini = StubProvider("gemini", {"success": False, "status": 503, "error": "busy"})
        groq = StubProvider("groq", {"success": True, "provider": "groq", "text": "Groq reply"})
        service = AIService(
            providers={"gemini": gemini, "groq": groq},
            provider_order=("gemini", "groq"),
            fallback_message=self.fallback,
        )

        result = service.generate_response([{"role": "user", "content": "hello"}], "same prompt")

        self.assertEqual(result["provider"], "groq")
        self.assertEqual(result["text"], "Groq reply")
        self.assertEqual(groq.calls[0][1], "same prompt")
        self.assertEqual(len(gemini.calls), 1)
        self.assertEqual(len(groq.calls), 1)

    def test_gemini_and_groq_failure_then_openrouter_success(self):
        providers = {
            "gemini": StubProvider("gemini", {"success": False, "status": 503, "error": "busy"}),
            "groq": StubProvider("groq", {"success": False, "status": 429, "error": "limited"}),
            "openrouter": StubProvider("openrouter", {"success": True, "text": "OpenRouter reply"}),
        }
        service = AIService(providers=providers, fallback_message=self.fallback)

        result = service.generate_response([{"role": "user", "content": "hello"}], "portfolio prompt")

        self.assertEqual(result["provider"], "openrouter")
        self.assertEqual(result["text"], "OpenRouter reply")
        self.assertTrue(all(len(provider.calls) == 1 for provider in providers.values()))

    def test_all_providers_fail_returns_existing_fallback_once_each(self):
        providers = {
            name: StubProvider(name, {"success": False, "status": 503, "error": "busy"})
            for name in ("gemini", "groq", "openrouter")
        }
        service = AIService(providers=providers, fallback_message=self.fallback)

        result = service.generate_response([{"role": "user", "content": "hello"}], "portfolio prompt")

        self.assertFalse(result["success"])
        self.assertEqual(result["provider"], "fallback")
        self.assertEqual(result["text"], self.fallback)
        self.assertEqual(len(result["attempts"]), 3)
        self.assertTrue(all(len(provider.calls) == 1 for provider in providers.values()))

    def test_unexpected_provider_exception_does_not_stop_failover(self):
        providers = {
            "gemini": StubProvider("gemini", requests.exceptions.Timeout("secret should not be logged")),
            "groq": StubProvider("groq", {"success": True, "text": "Groq reply"}),
        }
        service = AIService(providers=providers, provider_order=("gemini", "groq"), fallback_message=self.fallback)

        result = service.generate_response([{"role": "user", "content": "hello"}], "portfolio prompt")

        self.assertEqual(result["provider"], "groq")
        self.assertEqual(len(providers["gemini"].calls), 1)
        self.assertEqual(len(providers["groq"].calls), 1)

    def test_provider_order_and_timeout_configuration(self):
        with patch.dict(os.environ, {"AI_PROVIDER_ORDER": "groq,gemini,groq,invalid", "AI_TIMEOUT_SECONDS": "20"}, clear=False):
            self.assertEqual(get_provider_order(), ("groq", "gemini"))
            service = AIService(
                providers={
                    "groq": StubProvider("groq", {"success": False, "error": "no"}),
                    "gemini": StubProvider("gemini", {"success": True, "text": "ok"}),
                },
                fallback_message=self.fallback,
            )
        result = service.generate_response([{"role": "user", "content": "hello"}], "prompt")
        self.assertEqual(result["provider"], "gemini")


class ProviderTests(TestCase):
    def _response(self, status, payload=None, text=""):
        response = Mock()
        response.status_code = status
        response.text = text
        response.json.return_value = payload
        return response

    def test_gemini_success_parses_candidates_and_request_format(self):
        response = self._response(200, {"candidates": [{"content": {"parts": [{"text": "Gemini answer"}]}}]})
        provider = GeminiProvider(api_key="test-gemini-secret", model="gemini-3.8-flash")

        with patch("core.services.providers.requests.post", return_value=response) as post:
            result = provider.generate_response([{"role": "user", "content": "hello"}], "system prompt", 5)

        self.assertEqual(result, {"success": True, "provider": "gemini", "text": "Gemini answer"})
        self.assertEqual(post.call_args.args[0], "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent")
        self.assertEqual(post.call_args.kwargs["params"], {"key": "test-gemini-secret"})
        self.assertEqual(post.call_args.kwargs["timeout"], 5)
        self.assertEqual(post.call_args.kwargs["json"]["systemInstruction"]["parts"][0]["text"], "system prompt")

    def test_gemini_handles_provider_http_statuses_safely(self):
        for status in (400, 401, 403, 404, 429, 500, 503):
            with self.subTest(status=status):
                response = self._response(
                    status,
                    {"error": {"message": f"Rejected key=test-gemini-secret with HTTP {status}"}},
                    text='{"key":"test-gemini-secret"}',
                )
                provider = GeminiProvider(api_key="test-gemini-secret", model="gemini-3.8-flash")
                with patch("core.services.providers.requests.post", return_value=response):
                    result = provider.generate_response([{"role": "user", "content": "hello"}], "prompt", 2)
                self.assertFalse(result["success"])
                self.assertEqual(result["status"], status)
                self.assertNotIn("test-gemini-secret", json.dumps(result))

    def test_timeout_and_connection_errors_are_safe(self):
        provider = GeminiProvider(api_key="test-gemini-secret", model="gemini-3.8-flash")
        for error in (requests.exceptions.ReadTimeout("private URL"), requests.exceptions.ConnectionError("private URL")):
            with self.subTest(error=type(error).__name__):
                with patch("core.services.providers.requests.post", side_effect=error):
                    result = provider.generate_response([{"role": "user", "content": "hello"}], "prompt", 2)
                self.assertFalse(result["success"])
                self.assertEqual(result["exception"], type(error).__name__)
                self.assertNotIn("private URL", json.dumps(result))

    def test_gemini_invalid_json_and_empty_payloads_fail_safely(self):
        invalid_json = self._response(200, text='Authorization: Bearer test-gemini-secret')
        invalid_json.json.side_effect = ValueError("bad JSON")
        payloads = [
            {"candidates": []},
            {"candidates": [{"content": {"parts": []}}]},
            {"candidates": [{"content": {"parts": [{"text": "  "}]}}]},
            {"candidates": [{"content": None}]},
        ]
        provider = GeminiProvider(api_key="test-gemini-secret", model="gemini-3.8-flash")
        with patch("core.services.providers.requests.post", return_value=invalid_json):
            result = provider.generate_response([{"role": "user", "content": "hello"}], "prompt", 2)
        self.assertFalse(result["success"])
        self.assertNotIn("test-gemini-secret", json.dumps(result))

        for payload in payloads:
            with self.subTest(payload=payload):
                response = self._response(200, payload)
                with patch("core.services.providers.requests.post", return_value=response):
                    result = provider.generate_response([{"role": "user", "content": "hello"}], "prompt", 2)
                self.assertFalse(result["success"])
                self.assertEqual(result["exception"], "EmptyResponse")

    def test_groq_request_uses_openai_chat_contract(self):
        response = self._response(200, {"choices": [{"message": {"content": "Groq answer"}}]})
        provider = GroqProvider(api_key="test-groq-secret", model="openai/gpt-oss-20b")
        with patch("core.services.providers.requests.post", return_value=response) as post:
            result = provider.generate_response([{"role": "user", "content": "hello"}], "system prompt", 4)

        self.assertEqual(result["text"], "Groq answer")
        self.assertEqual(post.call_args.args[0], "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer test-groq-secret")
        self.assertEqual(post.call_args.kwargs["json"]["messages"][0], {"role": "system", "content": "system prompt"})
        self.assertEqual(post.call_args.kwargs["json"]["model"], "openai/gpt-oss-20b")

    def test_openrouter_success_parses_assistant_message(self):
        response = self._response(200, {"choices": [{"message": {"content": "OpenRouter answer"}}]})
        provider = OpenRouterProvider(api_key="test-openrouter-secret", model="vendor/model")
        with patch("core.services.providers.requests.post", return_value=response) as post:
            result = provider.generate_response([{"role": "user", "content": "hello"}], "system prompt", 4)

        self.assertEqual(result["text"], "OpenRouter answer")
        self.assertEqual(post.call_args.args[0], "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer test-openrouter-secret")


class AiChatTests(TestCase):
    def test_empty_message_rejected(self):
        response = self.client.post(reverse("ai_chat"), {"message": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn("message", response.json()["error"].lower())

    def test_missing_message_rejected(self):
        response = self.client.post(reverse("ai_chat"), data=json.dumps({}), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_very_long_message_rejected(self):
        response = self.client.post(reverse("ai_chat"), {"message": "x" * 1201})
        self.assertEqual(response.status_code, 400)

    def test_invalid_json_rejected(self):
        response = self.client.post(reverse("ai_chat"), data="{", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_media_route_is_registered_for_uploaded_images(self):
        match = resolve("/media/profile/test.jpg")
        self.assertEqual(match.route, r"^media/(?P<path>.*)$")

    @patch("core.views.AIService")
    def test_endpoint_returns_reply_and_records_answering_provider(self, service_class):
        service_class.return_value.generate_response.return_value = {
            "success": True,
            "provider": "groq",
            "text": "Groq answered hello.",
        }
        response = self.client.post(
            reverse("ai_chat"),
            data=json.dumps({"message": "hello"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(response.json()["reply"], "Groq answered hello.")
        self.assertEqual(response.json()["answer"], "Groq answered hello.")
        self.assertEqual(AIConversation.objects.get().provider, "groq")

    @patch("core.views.AIService")
    def test_endpoint_returns_safe_fallback_after_all_providers_fail(self, service_class):
        fallback = "AI assistant is temporarily unavailable. Please try again."
        service_class.return_value.generate_response.return_value = {
            "success": False,
            "provider": "fallback",
            "text": fallback,
            "attempts": [{"provider": "gemini", "status": 503, "error": "busy"}],
        }
        response = self.client.post(reverse("ai_chat"), {"message": "hello"})

        self.assertFalse(response.json()["success"])
        self.assertEqual(response.json()["reply"], fallback)
        self.assertEqual(AIConversation.objects.get().provider, "fallback")

    def test_provider_configuration_diagnostic_never_returns_keys(self):
        secrets = {
            "GEMINI_API_KEY": "test-gemini-secret",
            "GROQ_API_KEY": "test-groq-secret",
            "OPENROUTER_API_KEY": "test-openrouter-secret",
            "GEMINI_MODEL": "gemini-test-model",
            "GROQ_MODEL": "test/groq-model",
            "OPENROUTER_MODEL": "test/router-model",
            "AI_PROVIDER_ORDER": "gemini,groq,openrouter",
        }
        with patch.dict(os.environ, secrets, clear=False):
            config = get_ai_configuration()
        self.assertTrue(config["gemini_configured"])
        self.assertTrue(config["groq_configured"])
        self.assertTrue(config["openrouter_configured"])
        self.assertNotIn("test-gemini-secret", json.dumps(config))
        self.assertNotIn("test-groq-secret", json.dumps(config))
        self.assertNotIn("test-openrouter-secret", json.dumps(config))

    def test_openrouter_model_has_catalog_verified_default(self):
        with patch.dict(os.environ, {"OPENROUTER_MODEL": ""}, clear=False):
            config = get_ai_configuration()
        self.assertEqual(config["openrouter_model"], "openai/gpt-oss-20b")

    def test_default_gemini_model_is_supported_runtime_default(self):
        with patch.dict(os.environ, {"GEMINI_MODEL": ""}, clear=False):
            config = get_ai_configuration()
        self.assertEqual(config["gemini_model"], "gemini-3.5-flash")

    def test_legacy_gemini_model_names_are_normalized(self):
        with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash"}, clear=False):
            config = get_ai_configuration()
        self.assertEqual(config["gemini_model"], "gemini-3.5-flash")

    @patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY": "test-gemini-secret",
            "GEMINI_MODEL": "gemini-3.8-flash",
            "GROQ_API_KEY": "test-groq-secret",
            "GROQ_MODEL": "openai/gpt-oss-20b",
            "OPENROUTER_API_KEY": "test-openrouter-secret",
            "OPENROUTER_MODEL": "test/router-model",
            "AI_PROVIDER_ORDER": "gemini,groq,openrouter",
            "AI_TIMEOUT_SECONDS": "20",
        },
        clear=False,
    )
    @patch("core.services.providers.requests.post")
    def test_post_hello_gemini_503_falls_through_to_groq(self, post):
        gemini_response = Mock(status_code=503, text='{"error":{"message":"High demand"}}')
        gemini_response.json.return_value = {"error": {"message": "High demand"}}
        groq_response = Mock(status_code=200, text="")
        groq_response.json.return_value = {"choices": [{"message": {"content": "Groq says hello."}}]}
        post.side_effect = [gemini_response, groq_response]

        response = self.client.post(
            reverse("ai_chat"),
            data=json.dumps({"message": "hello"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["reply"], "Groq says hello.")
        self.assertEqual(response.json()["provider"], "groq")
        self.assertEqual(post.call_count, 2)
        self.assertEqual(post.call_args_list[1].kwargs["headers"]["Authorization"], "Bearer test-groq-secret")
        self.assertNotIn("test-gemini-secret", response.content.decode())
        self.assertNotIn("test-groq-secret", response.content.decode())
        self.assertNotIn("test-openrouter-secret", response.content.decode())
        self.assertEqual(AIConversation.objects.get().provider, "groq")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-gemini-secret", "GEMINI_MODEL": "gemini-3.8-flash"}, clear=False)
    @patch("core.services.providers.requests.post")
    def test_portfolio_question_reaches_gemini_with_shared_system_prompt(self, post):
        response_payload = {
            "candidates": [{"content": {"parts": [{"text": "No projects are listed yet."}]}}]
        }
        provider_response = Mock(status_code=200, text="")
        provider_response.json.return_value = response_payload
        post.return_value = provider_response
        question = "What projects are in this portfolio?"

        response = self.client.post(
            reverse("ai_chat"),
            data=json.dumps({"message": question}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reply"], "No projects are listed yet.")
        sent_payload = post.call_args.kwargs["json"]
        self.assertEqual(sent_payload["contents"][0]["parts"][0]["text"], question)
        self.assertIn("Projects:", sent_payload["systemInstruction"]["parts"][0]["text"])


class SecurityControlTests(TestCase):
    def test_json_post_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)

        response = client.post(
            reverse("ai_chat"),
            data=json.dumps({"message": "hello"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_sensitive_endpoint_rate_limit_returns_429(self):
        cache.clear()
        with override_settings(RATE_LIMIT_RULES=[
            {"path": "/contact/", "method": "POST", "limit": 1, "window": 60},
        ]):
            client = Client()
            first_response = client.post(reverse("contact"), data={})
            second_response = client.post(reverse("contact"), data={})

        self.assertNotEqual(first_response.status_code, 429)
        self.assertEqual(second_response.status_code, 429)
