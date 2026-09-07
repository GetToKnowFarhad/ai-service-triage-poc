"""Application entry point for assessments; the mock is the active provider."""

from app import mock_assessment
from app.assessment_schema import AIAssessment


def assess_ticket(title: str, description: str) -> AIAssessment:
    """Return a validated assessment, or raise a validation error."""
    result = mock_assessment.assess_ticket(title, description)
    return AIAssessment.model_validate(result)
