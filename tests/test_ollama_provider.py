"""Exercise the real-provider boundary entirely with offline HTTP responses."""

import io
import json
import os
import unittest
from email.message import Message
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError
from urllib.request import BaseHandler, build_opener as real_build_opener
from urllib.response import addinfourl

from app import ai_service, config, mock_assessment, ollama_provider
from app.assessment_errors import AssessmentError
from app.assessment_policy import build_system_prompt
from app.assessment_schema import AIAssessment


def valid_assessment():
    return {
        "category": "Network",
        "priority": "High",
        "summary": "An intermittent network connection is interrupting important work.",
        "recommended_team": "Network Support",
        "requires_human_review": True,
    }


def response_bytes(assessment=None):
    content = valid_assessment() if assessment is None else assessment
    return json.dumps({"done": True, "message": {"content": json.dumps(content)}}).encode("utf-8")


class OllamaProviderTests(unittest.TestCase):
    def setUp(self):
        # Replacing the opener guarantees these tests never contact Ollama.
        self.opener_patch = patch("app.ollama_provider.build_opener")
        self.build_opener = self.opener_patch.start()
        self.addCleanup(self.opener_patch.stop)
        self.opener = self.build_opener.return_value
        self.response = MagicMock()
        self.response.read.return_value = response_bytes()
        self.opener.open.return_value.__enter__.return_value = self.response

    def assert_provider_error(self, status_code):
        with self.assertRaises(AssessmentError) as raised:
            ollama_provider.assess_ticket("Ticket title", "Ticket description")
        self.assertEqual(raised.exception.status_code, status_code)
        # Neither model output nor transport errors should expose ticket data.
        self.assertNotIn("PRIVATE-TICKET", str(raised.exception))
        return str(raised.exception)

    def test_request_uses_local_api_shared_policy_and_strict_output_contract(self):
        title = 'Network issue with "quoted text"'
        description = "Connection drops.\nImportant work is blocked."
        result = ollama_provider.assess_ticket(title, description)

        self.assertIsInstance(result, AIAssessment)
        self.assertEqual(result.model_dump(), valid_assessment())
        self.opener.open.assert_called_once()
        request = self.opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:11434/api/chat")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(self.opener.open.call_args.kwargs["timeout"], 120.0)
        self.assertEqual(self.build_opener.call_args.args[0].proxies, {})

        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "qwen3:1.7b")
        self.assertEqual(payload["format"], AIAssessment.model_json_schema())
        self.assertEqual(payload["options"], {
            "temperature": 0, "seed": 0, "num_ctx": 4096, "num_predict": 512,
        })
        self.assertIs(payload["stream"], False)
        self.assertIs(payload["think"], False)
        self.assertEqual(payload["messages"][0], {
            "role": "system", "content": build_system_prompt(),
        })
        self.assertEqual(len(payload["messages"]), 2)
        self.assertEqual(payload["messages"][1]["role"], "user")
        self.assertEqual(json.loads(payload["messages"][1]["content"]), {
            "title": title, "description": description,
        })

    def test_model_and_timeout_can_be_overridden(self):
        ollama_provider.assess_ticket("Title", "Description", model="gemma3:1b", timeout=30.0)
        request = self.opener.open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "gemma3:1b")
        self.assertNotIn("think", payload)
        self.assertEqual(self.opener.open.call_args.kwargs["timeout"], 30.0)

    def test_thinking_is_disabled_for_another_qwen3_size(self):
        ollama_provider.assess_ticket("Title", "Description", model="qwen3:8b")
        payload = json.loads(self.opener.open.call_args.args[0].data)
        self.assertIs(payload["think"], False)

    def test_invalid_assessment_fields_are_rejected_without_exposing_output(self):
        invalid_fields = (
            ("category", "PRIVATE-TICKET"),
            ("priority", "Urgent"),
            ("summary", " \t\n"),
            ("recommended_team", ""),
            ("requires_human_review", "true"),
            ("requires_human_review", 1),
            ("unexpected", "PRIVATE-TICKET"),
        )
        for field, value in invalid_fields:
            with self.subTest(field=field, value=value):
                self.response.read.return_value = response_bytes({**valid_assessment(), field: value})
                self.assert_provider_error(502)

    def test_each_assessment_field_is_required(self):
        for field in valid_assessment():
            with self.subTest(field=field):
                data = valid_assessment()
                del data[field]
                self.response.read.return_value = response_bytes(data)
                self.assert_provider_error(502)

    def test_review_flag_cannot_bypass_the_human_review_policy(self):
        self.response.read.return_value = response_bytes({
            **valid_assessment(), "requires_human_review": False,
        })
        self.assert_provider_error(502)

    def test_incomplete_or_malformed_envelopes_are_rejected(self):
        valid_content = json.dumps(valid_assessment())
        invalid_envelopes = (
            [],
            None,
            {"message": {"content": valid_content}},
            {"done": False, "message": {"content": valid_content}},
            {"done": 1, "message": {"content": valid_content}},
            {"done": True},
            {"done": True, "message": None},
            {"done": True, "message": {"content": valid_assessment()}},
            {"done": True, "message": {"content": "PRIVATE-TICKET"}},
            {"done": True, "message": {"content": "[]"}},
            {"done": True, "message": {"content": "```json\n" + valid_content + "\n```"}},
            {"error": "PRIVATE-TICKET"},
        )
        for envelope in invalid_envelopes:
            with self.subTest(envelope=envelope):
                self.response.read.return_value = json.dumps(envelope).encode("utf-8")
                self.assert_provider_error(502)

    def test_invalid_json_or_encoding_is_rejected(self):
        for raw_response in (b"", b"PRIVATE-TICKET", b"\xff"):
            with self.subTest(raw_response=raw_response):
                self.response.read.return_value = raw_response
                self.assert_provider_error(502)

    def test_unavailable_server_is_reported(self):
        self.opener.open.side_effect = URLError(ConnectionRefusedError("PRIVATE-TICKET"))
        message = self.assert_provider_error(503)
        self.assertIn("ollama", message.lower())

    def test_direct_and_wrapped_timeouts_are_reported(self):
        for error in (TimeoutError("PRIVATE-TICKET"), URLError(TimeoutError("PRIVATE-TICKET"))):
            with self.subTest(error=type(error).__name__):
                self.opener.open.side_effect = error
                message = self.assert_provider_error(504)
                self.assertIn("tim", message.lower())

    def test_read_timeout_is_reported(self):
        self.response.read.side_effect = TimeoutError("PRIVATE-TICKET")
        self.assert_provider_error(504)

    def test_http_errors_are_reported_without_raw_server_messages(self):
        for status in (400, 404, 500):
            with self.subTest(status=status):
                self.opener.open.side_effect = HTTPError(
                    "http://localhost:11434/api/chat", status, "PRIVATE-TICKET", {}, None,
                )
                message = self.assert_provider_error(502)
                if status == 404:
                    self.assertIn("model", message.lower())

    def test_redirects_never_send_requests_to_another_endpoint(self):
        for status in (301, 302, 303, 307, 308):
            with self.subTest(status=status):
                requested_urls = []

                class RedirectingHandler(BaseHandler):
                    # Simulate HTTP before any real network handler can run.
                    handler_order = 100

                    def http_open(self, request):
                        requested_urls.append(request.full_url)
                        if len(requested_urls) > 1:
                            raise AssertionError("A redirect was followed")
                        headers = Message()
                        headers["Location"] = "https://example.invalid/assessment"
                        response = addinfourl(io.BytesIO(b""), headers, request.full_url, status)
                        response.msg = "Redirect"
                        return response

                    https_open = http_open

                with patch("app.ollama_provider.build_opener", side_effect=lambda *handlers: real_build_opener(
                    *handlers, RedirectingHandler()
                )):
                    self.assert_provider_error(502)
                self.assertEqual(requested_urls, [ollama_provider.OLLAMA_URL])


class AssessmentConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.environment_patch = patch.dict(os.environ, {}, clear=True)
        self.environment_patch.start()
        self.addCleanup(self.environment_patch.stop)

    def test_defaults_use_the_mock_provider(self):
        settings = config.get_settings()
        self.assertEqual(settings.provider, "mock")
        self.assertEqual(settings.ollama_model, "qwen3:1.7b")
        self.assertEqual(settings.ollama_timeout, 120.0)

    def test_environment_can_select_ollama_and_override_settings(self):
        with patch.dict(os.environ, {
            "AI_PROVIDER": "ollama", "OLLAMA_MODEL": "qwen3:8b", "OLLAMA_TIMEOUT": "45.5",
        }):
            settings = config.get_settings()
        self.assertEqual(settings.provider, "ollama")
        self.assertEqual(settings.ollama_model, "qwen3:8b")
        self.assertEqual(settings.ollama_timeout, 45.5)

    def test_invalid_provider_is_reported(self):
        with patch.dict(os.environ, {"AI_PROVIDER": "cloud"}):
            with self.assertRaises(AssessmentError) as raised:
                config.get_settings()
        self.assertEqual(raised.exception.status_code, 503)

    def test_blank_model_is_rejected_for_ollama(self):
        for model in ("", " \t"):
            with self.subTest(model=model), patch.dict(os.environ, {
                "AI_PROVIDER": "ollama", "OLLAMA_MODEL": model,
            }):
                with self.assertRaises(AssessmentError) as raised:
                    config.get_settings()
                self.assertEqual(raised.exception.status_code, 503)

    def test_timeout_must_be_positive_and_finite(self):
        for timeout in ("", "abc", "0", "-1", "nan", "inf", "-inf"):
            with self.subTest(timeout=timeout), patch.dict(os.environ, {
                "AI_PROVIDER": "ollama", "OLLAMA_TIMEOUT": timeout,
            }):
                with self.assertRaises(AssessmentError) as raised:
                    config.get_settings()
                self.assertEqual(raised.exception.status_code, 503)

    def test_mock_ignores_irrelevant_ollama_settings(self):
        with patch.dict(os.environ, {
            "AI_PROVIDER": "mock", "OLLAMA_MODEL": "", "OLLAMA_TIMEOUT": "invalid",
        }):
            self.assertEqual(config.get_settings().provider, "mock")


class ConfiguredAssessmentServiceTests(unittest.TestCase):
    def setUp(self):
        self.environment_patch = patch.dict(os.environ, {}, clear=True)
        self.environment_patch.start()
        self.addCleanup(self.environment_patch.stop)

    def test_default_mock_works_without_calling_ollama(self):
        with patch("app.ai_service.ollama_provider.assess_ticket") as real_provider:
            actual = ai_service.assess_ticket("Printer issue", "One user's printer is unavailable")
        self.assertEqual(actual, mock_assessment.assess_ticket(
            "Printer issue", "One user's printer is unavailable",
        ))
        real_provider.assert_not_called()

    def test_ollama_receives_inputs_and_configured_settings(self):
        expected = AIAssessment(**valid_assessment())
        with patch.dict(os.environ, {
            "AI_PROVIDER": "ollama", "OLLAMA_MODEL": "qwen3:8b", "OLLAMA_TIMEOUT": "45",
        }), patch("app.ai_service.ollama_provider.assess_ticket", return_value=expected) as provider, \
                patch("app.ai_service.mock_assessment.assess_ticket") as mock_provider:
            self.assertEqual(ai_service.assess_ticket("Title", "Description"), expected)
        provider.assert_called_once_with("Title", "Description", model="qwen3:8b", timeout=45.0)
        mock_provider.assert_not_called()

    def test_ollama_failure_never_falls_back_to_mock(self):
        failure = AssessmentError("Ollama is unavailable.", status_code=503)
        with patch.dict(os.environ, {"AI_PROVIDER": "ollama"}), \
                patch("app.ai_service.ollama_provider.assess_ticket", side_effect=failure), \
                patch("app.ai_service.mock_assessment.assess_ticket") as mock_provider:
            with self.assertRaises(AssessmentError) as raised:
                ai_service.assess_ticket("Title", "Description")
        self.assertIs(raised.exception, failure)
        mock_provider.assert_not_called()

    def test_invalid_output_is_rejected_at_the_service_boundary(self):
        for selected_provider in ("mock", "ollama"):
            with self.subTest(provider=selected_provider), \
                    patch.dict(os.environ, {"AI_PROVIDER": selected_provider}), \
                    patch("app.ai_service.mock_assessment.assess_ticket", return_value={"category": "Invalid"}), \
                    patch("app.ai_service.ollama_provider.assess_ticket", return_value={"category": "Invalid"}):
                with self.assertRaises(AssessmentError) as raised:
                    ai_service.assess_ticket("Title", "Description")
                self.assertEqual(raised.exception.status_code, 502)


if __name__ == "__main__":
    unittest.main()
