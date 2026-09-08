"""Read assessment settings from the environment without extra dependencies."""

import math
import os
from dataclasses import dataclass

from app.assessment_errors import AssessmentError


@dataclass(frozen=True)
class Settings:
    provider: str = "mock"
    ollama_model: str = "qwen3:1.7b"
    ollama_timeout: float = 120.0


def get_settings() -> Settings:
    provider = os.getenv("AI_PROVIDER", "mock").strip().lower() or "mock"
    if provider == "mock":
        # Offline development does not depend on any Ollama settings.
        return Settings()
    if provider != "ollama":
        raise AssessmentError("AI_PROVIDER must be 'mock' or 'ollama'.", status_code=503)

    model = os.getenv("OLLAMA_MODEL", "qwen3:1.7b").strip()
    if not model:
        raise AssessmentError("OLLAMA_MODEL must name a local Ollama model.", status_code=503)
    try:
        timeout = float(os.getenv("OLLAMA_TIMEOUT", "120"))
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError
    except ValueError as error:
        raise AssessmentError(
            "OLLAMA_TIMEOUT must be a positive, finite number of seconds.", status_code=503
        ) from error
    return Settings(provider=provider, ollama_model=model, ollama_timeout=timeout)
