"""Application entry point for the configured assessment provider."""

from pydantic import ValidationError

from app import mock_assessment, ollama_provider
from app.assessment_errors import AssessmentError
from app.assessment_schema import AIAssessment
from app.config import get_settings


def assess_ticket(title: str, description: str) -> AIAssessment:
    """Return a validated assessment, or report failure without a fallback."""
    settings = get_settings()
    try:
        if settings.provider == "mock":
            result = mock_assessment.assess_ticket(title, description)
        else:
            result = ollama_provider.assess_ticket(
                title, description, model=settings.ollama_model, timeout=settings.ollama_timeout
            )
        return AIAssessment.model_validate(result)
    except ValidationError as error:
        raise AssessmentError("The assessment provider returned an invalid assessment.") from error
