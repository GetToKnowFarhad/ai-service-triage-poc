"""Check benchmark reports with scored synthetic replies and no HTTP requests."""

import io
import json
import unittest
from contextlib import redirect_stdout

from app.assessment_schema import CATEGORIES, PRIORITIES
from app.mock_assessment import TEAMS
from evaluation import benchmark


def scored_ticket(ticket_id, category, priority, latency=1, *, changes=None, invalid=False, failed=False):
    ticket = benchmark.EvaluationTicket(
        id=ticket_id,
        title="Synthetic reporting test",
        description="An offline fixture used only to check evaluation calculations.",
        expected=benchmark.ExpectedLabels(
            category=category,
            priority=priority,
            recommended_team=TEAMS[category],
        ),
    )
    if failed:
        return benchmark.score_response("test-model", ticket, "", latency, "Connection refused")

    assessment = {
        "category": category,
        "priority": priority,
        "summary": "Synthetic assessment for a reporting test.",
        "recommended_team": TEAMS[category],
        "requires_human_review": True,
        **(changes or {}),
    }
    if invalid:
        del assessment["summary"]
    response = json.dumps({"done": True, "message": {"content": json.dumps(assessment)}})
    return benchmark.score_response("test-model", ticket, response, latency)


def mixed_results():
    return [
        scored_ticket("NET-CORRECT", "Network", "High", 1),
        scored_ticket("NET-AS-HARDWARE", "Network", "Medium", 3, changes={
            "category": "Hardware", "priority": "Low", "recommended_team": "Hardware Support",
        }),
        scored_ticket("HW-WRONG-PRIORITY", "Hardware", "Medium", 5, changes={"priority": "High"}),
        scored_ticket("SOFT-WRONG-TEAM", "Software", "Low", 7, changes={"recommended_team": "Service Desk"}),
        scored_ticket("NET-INVALID", "Network", "High", 9, invalid=True),
        scored_ticket("SEC-NO-RESPONSE", "Security", "Critical", 0.02, failed=True),
    ]


class EvaluationReportingTests(unittest.TestCase):
    def test_totals_rates_and_latencies_include_every_attempt(self):
        summary = benchmark.summarize(mixed_results())
        self.assertEqual(summary["attempts"], 6)
        self.assertEqual(summary["responses"], 5)
        for label, correct in (("category", 3), ("priority", 2), ("routing", 2)):
            with self.subTest(label=label):
                self.assertEqual(summary[f"{label}_correct"], correct)
                self.assertEqual(summary[f"{label}_incorrect"], 6 - correct)
                self.assertAlmostEqual(summary[f"{label}_accuracy"], correct / 6)
        self.assertAlmostEqual(summary["valid_output_rate"], 4 / 6)
        # Invalid replies take time; connection failures are excluded from response latency.
        self.assertEqual(summary["average_latency"], 5)
        self.assertEqual(summary["median_latency"], 5)

    def test_per_category_groups_by_expected_category_and_scores_category_only(self):
        groups = benchmark.summarize(mixed_results())["per_category"]
        self.assertEqual(set(groups), set(CATEGORIES))
        self.assertEqual(groups["Network"], {"total": 3, "correct": 1, "incorrect": 2, "accuracy": 1 / 3})
        # A Network ticket predicted as Hardware must not enter the Hardware denominator.
        # A Hardware ticket with the wrong priority still earns category credit.
        self.assertEqual(groups["Hardware"], {"total": 1, "correct": 1, "incorrect": 0, "accuracy": 1.0})
        self.assertEqual(groups["Software"], {"total": 1, "correct": 1, "incorrect": 0, "accuracy": 1.0})
        self.assertEqual(groups["Security"], {"total": 1, "correct": 0, "incorrect": 1, "accuracy": 0.0})
        for category in ("Account Access", "Other"):
            self.assertEqual(groups[category], {"total": 0, "correct": 0, "incorrect": 0, "accuracy": None})

    def test_per_priority_groups_by_expected_priority_and_scores_priority_only(self):
        groups = benchmark.summarize(mixed_results())["per_priority"]
        self.assertEqual(set(groups), set(PRIORITIES))
        self.assertEqual(groups["High"], {"total": 2, "correct": 1, "incorrect": 1, "accuracy": 0.5})
        self.assertEqual(groups["Medium"], {"total": 2, "correct": 0, "incorrect": 2, "accuracy": 0.0})
        # The wrong team does not remove credit for a correctly predicted priority.
        self.assertEqual(groups["Low"], {"total": 1, "correct": 1, "incorrect": 0, "accuracy": 1.0})
        self.assertEqual(groups["Critical"], {"total": 1, "correct": 0, "incorrect": 1, "accuracy": 0.0})

    def test_misclassified_list_includes_team_only_errors_and_failed_attempts_in_order(self):
        rows = mixed_results()
        mismatches = benchmark.summarize(rows)["misclassified_tickets"]
        self.assertEqual([row.ticket_id for row in mismatches], [row.ticket_id for row in rows[1:]])
        for actual, original in zip(mismatches, rows[1:]):
            self.assertIs(actual, original)
        invalid = mismatches[-2]
        self.assertEqual(invalid.predicted_category, invalid.expected_category)
        self.assertEqual(invalid.predicted_priority, invalid.expected_priority)
        self.assertEqual(invalid.predicted_team, invalid.expected_team)
        self.assertFalse(invalid.schema_valid)
        self.assertEqual(mismatches[-1].status, "request_error")

    def test_empty_report_has_zero_totals_no_accuracy_for_absent_groups_and_no_mismatches(self):
        summary = benchmark.summarize([])
        for label in ("category", "priority", "routing"):
            self.assertEqual(summary[f"{label}_correct"], 0)
            self.assertEqual(summary[f"{label}_incorrect"], 0)
            self.assertEqual(summary[f"{label}_accuracy"], 0)
        for name, labels in (("per_category", CATEGORIES), ("per_priority", PRIORITIES)):
            self.assertEqual(set(summary[name]), set(labels))
            for group in summary[name].values():
                self.assertEqual(group, {"total": 0, "correct": 0, "incorrect": 0, "accuracy": None})
        self.assertEqual(summary["misclassified_tickets"], [])
        self.assertEqual(summary["valid_output_rate"], 0)
        self.assertIsNone(summary["average_latency"])
        self.assertIsNone(summary["median_latency"])

    def test_console_shows_rates_totals_groups_and_expected_vs_predicted_errors(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            benchmark.print_summary("test-model", mixed_results())
        output = stdout.getvalue()
        self.assertIn("test-model: 6 attempts, 5 completed HTTP responses", output)
        for label in ("Category accuracy", "Priority accuracy", "Routing accuracy",
                      "Valid structured-output rate", "Average response latency", "Median response latency"):
            self.assertIn(label, output)
        for value in ("50.0%", "33.3%", "66.7%", "5.000 s"):
            self.assertIn(value, output)
        for label, correct, incorrect in (("Category", 3, 3), ("Priority", 2, 4), ("Routing", 2, 4)):
            self.assertRegex(output, rf"{label} decisions:\s+{correct} correct,\s+{incorrect} incorrect")
        self.assertIn("per-category", output.lower())
        self.assertIn("per-priority", output.lower())
        for label in (*CATEGORIES, *PRIORITIES):
            self.assertIn(label, output)
        for row in mixed_results()[1:]:
            self.assertIn(row.ticket_id, output)
        self.assertNotIn("NET-CORRECT", output)
        self.assertIn("expected", output.lower())
        self.assertIn("predicted", output.lower())
        for team in ("Network Support", "Hardware Support", "Software Support", "Service Desk", "IT Security"):
            self.assertIn(team, output)
        self.assertIn("(no prediction)", output)

    def test_console_keeps_expected_and_predicted_values_associated_with_ticket(self):
        row = scored_ticket("UNIQUE-MISMATCH-ID", "Network", "Medium", changes={
            "category": "Hardware", "priority": "Low", "recommended_team": "Hardware Support",
        })
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            benchmark.print_summary("test-model", [row])
        output = stdout.getvalue()
        # The diagnostic follows the ID, separate from the aggregate accuracy tables.
        diagnostic = output.split("UNIQUE-MISMATCH-ID", 1)[1]
        self.assertIn("expected", diagnostic.lower())
        self.assertIn("predicted", diagnostic.lower())
        for value in ("Network", "Medium", "Network Support", "Hardware", "Low", "Hardware Support"):
            self.assertIn(value, diagnostic)

    def test_perfect_and_empty_console_reports_explicitly_have_no_misclassifications(self):
        for rows in ([], [scored_ticket("ONLY-CORRECT-ID", "Account Access", "Low")]):
            with self.subTest(attempts=len(rows)):
                self.assertEqual(benchmark.summarize(rows)["misclassified_tickets"], [])
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    benchmark.print_summary("test-model", rows)
                self.assertIn("None", stdout.getvalue())
                self.assertIn("N/A", stdout.getvalue())
                self.assertNotIn("ONLY-CORRECT-ID", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
