import unittest
from unittest.mock import patch

from pydantic import ValidationError

from app import ai_service, mock_assessment
from app.assessment_schema import AIAssessment, CATEGORIES, PRIORITIES


class AssessmentSchemaTests(unittest.TestCase):
    def setUp(self):
        self.valid_data = {
            "category": "Network",
            "priority": "High",
            "summary": "Wi-Fi drops before a client meeting.",
            "recommended_team": "Network Support",
            "requires_human_review": True,
        }

    def test_allowed_categories_and_priorities(self):
        self.assertEqual(CATEGORIES, ("Network", "Hardware", "Software", "Account Access", "Security", "Other"))
        self.assertEqual(PRIORITIES, ("Low", "Medium", "High", "Critical"))
        for category in CATEGORIES:
            for priority in PRIORITIES:
                with self.subTest(category=category, priority=priority):
                    result = AIAssessment(**{**self.valid_data, "category": category, "priority": priority})
                    self.assertEqual(result.category, category)
                    self.assertEqual(result.priority, priority)

    def test_invalid_categories_are_rejected(self):
        for value in ("Networking", "network", " Network ", "", None, 123):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                AIAssessment(**{**self.valid_data, "category": value})

    def test_invalid_priorities_are_rejected(self):
        for value in ("Urgent", "high", " High ", "", None, 1):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                AIAssessment(**{**self.valid_data, "priority": value})

    def test_all_fields_are_required_and_extra_fields_are_rejected(self):
        for field in self.valid_data:
            data = self.valid_data.copy()
            del data[field]
            with self.subTest(field=field), self.assertRaises(ValidationError):
                AIAssessment(**data)
        with self.assertRaises(ValidationError):
            AIAssessment(**self.valid_data, confidence=0.9)

    def test_summary_and_team_require_nonblank_strings(self):
        for field in ("summary", "recommended_team"):
            for value in ("", " \t\n", None, 123, True, ["text"]):
                with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                    AIAssessment(**{**self.valid_data, field: value})

    def test_review_flag_is_a_strict_boolean(self):
        for value in ("true", "false", "yes", 0, 1, None):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                AIAssessment(**{**self.valid_data, "requires_human_review": value})
        for value in (True, False):
            self.assertIs(AIAssessment(**{**self.valid_data, "requires_human_review": value}).requires_human_review, value)

    def test_assessment_cannot_be_modified_after_validation(self):
        assessment = AIAssessment(**self.valid_data)
        with self.assertRaises(ValidationError):
            assessment.priority = "Urgent"
        self.assertEqual(assessment.priority, "High")


class AssessmentServiceTests(unittest.TestCase):
    def test_mock_and_service_return_the_same_valid_schema(self):
        title = "My laptop keeps losing Wi-Fi"
        description = "I have a client meeting in 20 minutes"
        provider_result = mock_assessment.assess_ticket(title, description)
        result = ai_service.assess_ticket(title, description)
        self.assertIsInstance(provider_result, AIAssessment)
        self.assertIsInstance(result, AIAssessment)
        self.assertEqual(result, provider_result)
        self.assertEqual((result.category, result.priority), ("Network", "High"))
        self.assertTrue(result.requires_human_review)
        self.assertEqual(AIAssessment.model_validate(result.model_dump()), result)

    def test_service_passes_inputs_to_provider(self):
        expected = mock_assessment.assess_ticket("Printer issue", "Please help")
        with patch("app.ai_service.mock_assessment.assess_ticket", return_value=expected) as provider:
            self.assertEqual(ai_service.assess_ticket("Title", "Description"), expected)
            provider.assert_called_once_with("Title", "Description")

    def test_service_rejects_invalid_provider_output(self):
        valid_data = mock_assessment.assess_ticket("VPN issue", "Please help").model_dump()
        for field, value in (("category", "Invalid"), ("priority", "Urgent")):
            with self.subTest(field=field):
                with patch("app.ai_service.mock_assessment.assess_ticket", return_value={**valid_data, field: value}):
                    with self.assertRaises(ValidationError):
                        ai_service.assess_ticket("Title", "Description")


if __name__ == "__main__":
    unittest.main()
