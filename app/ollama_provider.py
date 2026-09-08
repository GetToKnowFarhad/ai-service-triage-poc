"""Local Ollama provider. Only validated assessments leave this module."""

import json
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from app.assessment_errors import AssessmentError
from app.assessment_policy import build_system_prompt
from app.assessment_schema import AIAssessment

OLLAMA_URL = "http://localhost:11434/api/chat"


class LocalOnlyRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # A redirect is an HTTP failure, never a request to another endpoint.
        return None


def assess_ticket(
    title: str, description: str, *, model: str = "qwen3:1.7b", timeout: float = 120.0
) -> AIAssessment:
    try:
        policy = build_system_prompt()
    except OSError as error:
        raise AssessmentError("Cannot read the local assessment policy file.", status_code=503) from error

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": policy},
            {"role": "user", "content": json.dumps({"title": title, "description": description})},
        ],
        "format": AIAssessment.model_json_schema(),
        "stream": False,
        "options": {"temperature": 0, "seed": 0, "num_ctx": 4096, "num_predict": 512},
    }
    # Disable thinking for the supported boolean-thinking model families.
    family = model.rsplit("/", 1)[-1].split(":", 1)[0]
    if family in ("qwen3", "deepseek-r1", "deepseek-v3.1"):
        payload["think"] = False

    request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        # Disable proxies and redirects so ticket text stays at the local endpoint.
        with build_opener(ProxyHandler({}), LocalOnlyRedirectHandler()).open(request, timeout=timeout) as response:
            raw_response = response.read().decode("utf-8")
    except HTTPError as error:
        if error.code == 404:
            message = f"Ollama could not find model '{model}'. Install that model on this server and retry."
        else:
            message = f"Ollama returned HTTP {error.code}. Check the local Ollama service and retry."
        raise AssessmentError(message) from error
    except TimeoutError as error:
        raise AssessmentError("Ollama timed out. Try again or increase OLLAMA_TIMEOUT.", status_code=504) from error
    except URLError as error:
        if isinstance(error.reason, TimeoutError):
            raise AssessmentError("Ollama timed out. Try again or increase OLLAMA_TIMEOUT.", status_code=504) from error
        raise AssessmentError(
            "Ollama is unavailable at http://localhost:11434. Start the local Ollama service and retry.",
            status_code=503,
        ) from error
    except (OSError, HTTPException) as error:
        raise AssessmentError("The connection to local Ollama failed. Check the service and retry.", status_code=503) from error
    except UnicodeError as error:
        raise AssessmentError("Ollama returned an unreadable response. Try analyzing again.") from error

    try:
        envelope = json.loads(raw_response)
        if not isinstance(envelope, dict) or envelope.get("done") is not True or envelope.get("error"):
            raise ValueError("Incomplete or unsuccessful response")
        message = envelope.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ValueError("Missing response content")
        # No Markdown cleanup or coercion: validate the entire model output as-is.
        assessment = AIAssessment.model_validate_json(message["content"])
    except ValueError as error:
        raise AssessmentError("Ollama returned an invalid assessment. Try analyzing again.") from error

    # The schema permits both booleans, but this workflow requires human review.
    # Reject a policy violation instead of altering the original model output.
    if not assessment.requires_human_review:
        raise AssessmentError("Ollama did not require human review. Try analyzing again.")
    return assessment
