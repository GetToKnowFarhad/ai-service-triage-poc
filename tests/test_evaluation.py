import csv
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from uuid import uuid4

from app.assessment_schema import AIAssessment, CATEGORIES, PRIORITIES
from app.mock_assessment import assess_ticket
from evaluation import benchmark


def example_ticket():
    return benchmark.EvaluationTicket(
        id="TEST-ONLY-ID",
        title="Network interruption",
        description="I cannot work because my connection is unavailable.",
        expected=benchmark.ExpectedLabels(
            category="Network", priority="High", recommended_team="Network Support"
        ),
    )


def assessment_data(**changes):
    return {
        "category": "Network", "priority": "High",
        "summary": "A network interruption blocks one user's work.",
        "recommended_team": "Network Support", "requires_human_review": True,
        **changes,
    }


def chat_response(data):
    return json.dumps({"done": True, "message": {"content": json.dumps(data)}})


class EvaluationCalculationTests(unittest.TestCase):
    def test_exact_match_scoring(self):
        raw = chat_response(assessment_data())
        result = benchmark.score_response("test-model", example_ticket(), raw, 1.25)
        self.assertTrue(result.schema_valid)
        self.assertTrue(result.category_correct)
        self.assertTrue(result.priority_correct)
        self.assertTrue(result.team_correct)
        self.assertEqual(result.predicted_category, "Network")
        self.assertEqual(result.predicted_priority, "High")
        self.assertEqual(result.predicted_team, "Network Support")
        self.assertEqual(result.raw_response, raw)
        self.assertEqual(result.latency_seconds, 1.25)

    def test_team_matching_is_exact_and_independent(self):
        raw = chat_response(assessment_data(recommended_team="network support"))
        result = benchmark.score_response("test-model", example_ticket(), raw, 1)
        self.assertTrue(result.schema_valid)
        self.assertTrue(result.category_correct)
        self.assertTrue(result.priority_correct)
        self.assertFalse(result.team_correct)

    def test_invalid_output_gets_no_accuracy_credit(self):
        invalid = assessment_data()
        del invalid["summary"]
        result = benchmark.score_response("test-model", example_ticket(), chat_response(invalid), 2)
        self.assertFalse(result.schema_valid)
        self.assertFalse(result.category_correct)
        self.assertFalse(result.priority_correct)
        self.assertFalse(result.team_correct)
        self.assertEqual(result.predicted_category, "Network")
        self.assertEqual(result.status, "invalid_response")
        self.assertTrue(result.error)

    def test_accuracy_denominators_and_latency_calculations(self):
        ticket = example_ticket()
        invalid = assessment_data(requires_human_review="true")
        rows = [
            benchmark.score_response("model", ticket, chat_response(assessment_data()), 1),
            benchmark.score_response("model", ticket, chat_response(assessment_data(
                category="Hardware", recommended_team="Hardware Support"
            )), 3),
            benchmark.score_response("model", ticket, chat_response(invalid), 9),
            benchmark.score_response("model", ticket, "", 0.02, "Connection refused"),
        ]
        summary = benchmark.summarize(rows)
        self.assertEqual(summary["attempts"], 4)
        self.assertEqual(summary["responses"], 3)
        self.assertEqual(summary["category_accuracy"], 0.25)
        self.assertEqual(summary["priority_accuracy"], 0.5)
        self.assertEqual(summary["routing_accuracy"], 0.25)
        self.assertEqual(summary["valid_output_rate"], 0.5)
        self.assertAlmostEqual(summary["average_latency"], 13 / 3)
        self.assertEqual(summary["median_latency"], 3)

    def test_even_number_of_response_latencies(self):
        rows = [benchmark.score_response("model", example_ticket(), chat_response(assessment_data()), value)
                for value in (1, 3, 9, 10)]
        summary = benchmark.summarize(rows)
        self.assertEqual(summary["average_latency"], 5.75)
        self.assertEqual(summary["median_latency"], 6)

    def test_empty_and_all_failed_results_have_no_response_latency(self):
        failed = benchmark.score_response("model", example_ticket(), "", 5, "Timed out")
        for rows in ([], [failed]):
            with self.subTest(rows=len(rows)):
                summary = benchmark.summarize(rows)
                self.assertEqual(summary["category_accuracy"], 0)
                self.assertEqual(summary["priority_accuracy"], 0)
                self.assertEqual(summary["routing_accuracy"], 0)
                self.assertEqual(summary["valid_output_rate"], 0)
                self.assertIsNone(summary["average_latency"])
                self.assertIsNone(summary["median_latency"])


class EvaluationRequestTests(unittest.TestCase):
    def test_same_policy_schema_and_options_without_expected_labels(self):
        ticket = example_ticket()
        prompt = benchmark.build_system_prompt()
        payloads = [benchmark.build_payload(model, ticket, prompt) for model in benchmark.MODELS]
        self.assertEqual(payloads[0]["messages"], payloads[1]["messages"])
        for payload in payloads:
            self.assertEqual(payload["format"], AIAssessment.model_json_schema())
            self.assertEqual(payload["options"]["temperature"], 0)
            self.assertFalse(payload["stream"])
            self.assertEqual(json.loads(payload["messages"][1]["content"]), {
                "title": ticket.title, "description": ticket.description,
            })
            self.assertNotIn(ticket.id, json.dumps(payload))
        self.assertIs(payloads[0]["think"], False)
        self.assertNotIn("think", payloads[1])
        self.assertNotIn("20 minutes", prompt)
        self.assertNotIn("Wi-Fi", prompt)

    def test_http_request_is_local_and_nonstreaming(self):
        payload = benchmark.build_payload(benchmark.MODELS[0], example_ticket(), "Shared policy")
        with patch("evaluation.benchmark.build_opener") as opener:
            opener.return_value.open.return_value.__enter__.return_value.read.return_value = b'{"done":true}'
            self.assertEqual(benchmark.call_ollama(payload, 7), '{"done":true}')
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:11434/api/chat")
        self.assertEqual(request.method, "POST")
        self.assertEqual(json.loads(request.data), payload)
        self.assertEqual(opener.return_value.open.call_args.kwargs["timeout"], 7)

    def test_connection_http_and_timeout_failures_are_recorded(self):
        errors = (URLError("Connection refused"), TimeoutError("Timed out"),
                  HTTPError(benchmark.OLLAMA_URL, 404, "Model not found", {}, None))
        for error in errors:
            with self.subTest(error=type(error).__name__):
                with patch("evaluation.benchmark.call_ollama", side_effect=error):
                    with patch("evaluation.benchmark.time.perf_counter", side_effect=[10, 12.5]):
                        result = benchmark.evaluate_ticket("model", example_ticket(), "Policy", 3)
                self.assertEqual(result.status, "request_error")
                self.assertFalse(result.response_received)
                self.assertFalse(result.schema_valid)
                self.assertEqual(result.latency_seconds, 2.5)
                self.assertIn(type(error).__name__, result.error)

    def test_malformed_envelopes_and_assessments_do_not_crash(self):
        responses = (
            "not JSON", "[]", '{"error":"model unavailable"}',
            '{"done":false}', '{"done":true}',
            '{"done":true,"message":{"content":42}}',
            '{"done":true,"message":{"content":"not JSON"}}',
            chat_response([]), chat_response(assessment_data(category="Invalid")),
            chat_response(assessment_data(priority="Urgent")),
            chat_response(assessment_data(summary=" ")),
            chat_response(assessment_data(extra="unexpected")),
        )
        for raw in responses:
            with self.subTest(raw=raw):
                result = benchmark.score_response("model", example_ticket(), raw, 1)
                self.assertFalse(result.schema_valid)
                self.assertEqual(result.status, "invalid_response")
                self.assertTrue(result.response_received)
                self.assertTrue(result.error)


class EvaluationDatasetAndExportTests(unittest.TestCase):
    def test_synthetic_dataset_coverage(self):
        tickets = benchmark.load_dataset(benchmark.EVALUATION_DIR / "tickets.json")
        self.assertEqual(len(tickets), 10)
        self.assertEqual({ticket.expected.category for ticket in tickets}, set(CATEGORIES))
        self.assertEqual({ticket.expected.priority for ticket in tickets}, set(PRIORITIES))
        self.assertEqual(len({ticket.id for ticket in tickets}), 10)
        for ticket in tickets:
            with self.subTest(ticket=ticket.id):
                assessment = assess_ticket(ticket.title, ticket.description)
                self.assertEqual(
                    (assessment.category, assessment.priority, assessment.recommended_team),
                    (ticket.expected.category, ticket.expected.priority, ticket.expected.recommended_team),
                )

    def test_complete_two_model_export_continues_after_failures(self):
        output = Path.cwd() / f"test-evaluation-{uuid4().hex}.csv"
        stdout = io.StringIO()
        # One failed call, one malformed reply, then valid responses for the rest.
        responses = [URLError("Connection refused"), "bad JSON"] + [chat_response(assessment_data())] * 18
        try:
            with patch("evaluation.benchmark.call_ollama", side_effect=responses) as client:
                with redirect_stdout(stdout):
                    code = benchmark.main(["--output", str(output)])
            self.assertEqual(code, 0)
            self.assertEqual(client.call_count, 20)
            with output.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 20)
            self.assertEqual({row["model"] for row in rows}, set(benchmark.MODELS))
            self.assertEqual(rows[0]["status"], "request_error")
            self.assertEqual(rows[1]["status"], "invalid_response")
            self.assertEqual(rows[-1]["status"], "ok")
            self.assertEqual(rows[-1]["raw_response"], responses[-1])
            for name in ("expected_category", "predicted_category", "expected_priority", "predicted_priority",
                         "expected_team", "predicted_team", "schema_valid", "latency_seconds",
                         "category_correct", "priority_correct", "team_correct"):
                self.assertIn(name, rows[0])
            for model in benchmark.MODELS:
                self.assertIn(model + ": 10 attempts", stdout.getvalue())
            for label in ("Category accuracy", "Priority accuracy", "Routing accuracy",
                          "Valid structured-output rate", "Average response latency", "Median response latency"):
                self.assertEqual(stdout.getvalue().count(label), 2)
            with self.assertRaises(FileExistsError):
                benchmark.run_evaluation(list(benchmark.MODELS), [example_ticket()], output, 1)
        finally:
            output.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
