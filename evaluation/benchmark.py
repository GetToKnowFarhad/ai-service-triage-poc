"""Compare local Ollama models without importing routes or touching the database.

Run from the project folder: python -m evaluation.benchmark
"""

import argparse
import csv
import json
import math
import statistics
import sys
import time
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from app.assessment_schema import AIAssessment, Category, Priority
from app.mock_assessment import CATEGORY_RULES, TEAMS

EVALUATION_DIR = Path(__file__).resolve().parent
OLLAMA_URL = "http://localhost:11434/api/chat"
MODELS = ("qwen3:1.7b", "gemma3:1b")


class ExpectedLabels(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    category: Category
    priority: Priority
    recommended_team: str = Field(min_length=1)


class EvaluationTicket(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    expected: ExpectedLabels


@dataclass
class EvaluationResult:
    model: str
    ticket_id: str
    expected_category: str
    expected_priority: str
    expected_team: str
    latency_seconds: float
    predicted_category: str = ""
    predicted_priority: str = ""
    predicted_team: str = ""
    predicted_requires_human_review: bool | None = None
    schema_valid: bool = False
    category_correct: bool = False
    priority_correct: bool = False
    team_correct: bool = False
    response_received: bool = False
    status: str = "request_error"
    error: str = ""
    raw_response: str = ""


def load_dataset(path: Path) -> list[EvaluationTicket]:
    tickets = TypeAdapter(list[EvaluationTicket]).validate_json(path.read_text(encoding="utf-8"))
    if not tickets or len({ticket.id for ticket in tickets}) != len(tickets):
        raise ValueError("Dataset must be nonempty and ticket IDs must be unique.")
    for ticket in tickets:
        if ticket.expected.recommended_team != TEAMS[ticket.expected.category]:
            raise ValueError(f"Ticket {ticket.id}: expected team does not match the project mapping.")
    return tickets


def build_system_prompt() -> str:
    # The policy and schema are identical for every model and ticket.
    policy = (EVALUATION_DIR / "policy.txt").read_text(encoding="utf-8")
    guidance = "\n".join(
        f"- {category}: {', '.join(keywords)}" for category, keywords in CATEGORY_RULES
    )
    return (
        policy
        + "\nCategory guidance in precedence order:\n" + guidance
        + "\n- Other: none of the preceding categories fits.\n"
        + "\nExact category-to-team mapping:\n" + json.dumps(TEAMS)
        + "\nRequired JSON schema:\n" + json.dumps(AIAssessment.model_json_schema())
    )


def build_payload(model: str, ticket: EvaluationTicket, system_prompt: str) -> dict:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            # Expected labels and ticket IDs are never sent to the model.
            {"role": "user", "content": json.dumps({"title": ticket.title, "description": ticket.description})},
        ],
        "format": AIAssessment.model_json_schema(),
        "stream": False,
        "options": {"temperature": 0, "seed": 0, "num_ctx": 4096, "num_predict": 512},
    }
    # Qwen3 supports thinking; Gemma3 is not a thinking model.
    if model == "qwen3:1.7b":
        payload["think"] = False
    return payload


def call_ollama(payload: dict, timeout: float) -> str:
    request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # Local evaluation must not send requests through an environment HTTP proxy.
    with build_opener(ProxyHandler({})).open(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def score_response(
    model: str,
    ticket: EvaluationTicket,
    raw_response: str,
    latency_seconds: float,
    request_error: str = "",
) -> EvaluationResult:
    """Score one attempt; invalid output earns no accuracy credit."""
    result = EvaluationResult(
        model=model,
        ticket_id=ticket.id,
        expected_category=ticket.expected.category,
        expected_priority=ticket.expected.priority,
        expected_team=ticket.expected.recommended_team,
        latency_seconds=latency_seconds,
        error=request_error,
        raw_response=raw_response,
    )
    if request_error:
        return result

    result.response_received = True
    result.status = "invalid_response"
    try:
        envelope = json.loads(raw_response)
        if not isinstance(envelope, dict) or envelope.get("done") is not True:
            raise ValueError("Expected a completed Ollama chat response.")
        message = envelope.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ValueError("Ollama response is missing message.content text.")
        content = message["content"]
        parsed = json.loads(content)
        # Keep readable predictions for diagnosis even when another field is invalid.
        if isinstance(parsed, dict):
            for field, output in (("category", "predicted_category"), ("priority", "predicted_priority"),
                                  ("recommended_team", "predicted_team")):
                if isinstance(parsed.get(field), str):
                    setattr(result, output, parsed[field])
            if isinstance(parsed.get("requires_human_review"), bool):
                result.predicted_requires_human_review = parsed["requires_human_review"]
        assessment = AIAssessment.model_validate(parsed)
    except (ValueError, ValidationError) as error:
        result.error = str(error)
        return result

    result.schema_valid = True
    result.status = "ok"
    result.category_correct = assessment.category == ticket.expected.category
    result.priority_correct = assessment.priority == ticket.expected.priority
    result.team_correct = assessment.recommended_team == ticket.expected.recommended_team
    return result


def evaluate_ticket(model: str, ticket: EvaluationTicket, system_prompt: str, timeout: float) -> EvaluationResult:
    payload = build_payload(model, ticket, system_prompt)
    raw_response, error = "", ""
    started = time.perf_counter()
    try:
        raw_response = call_ollama(payload, timeout)
    except (URLError, OSError, HTTPException, UnicodeError) as exception:
        error = f"{type(exception).__name__}: {exception}"
    elapsed = time.perf_counter() - started
    return score_response(model, ticket, raw_response, elapsed, error)


def summarize(results: list[EvaluationResult]) -> dict:
    count = len(results)
    # A failed connection is not a fast model response. Invalid completed responses
    # still have a response latency and remain in this timing sample.
    latencies = [row.latency_seconds for row in results if row.response_received]
    return {
        "attempts": count,
        "responses": len(latencies),
        "category_accuracy": sum(row.category_correct for row in results) / count if count else 0.0,
        "priority_accuracy": sum(row.priority_correct for row in results) / count if count else 0.0,
        "routing_accuracy": sum(row.team_correct for row in results) / count if count else 0.0,
        "valid_output_rate": sum(row.schema_valid for row in results) / count if count else 0.0,
        "average_latency": statistics.mean(latencies) if latencies else None,
        "median_latency": statistics.median(latencies) if latencies else None,
    }


def print_summary(model: str, results: list[EvaluationResult]):
    summary = summarize(results)
    print(f"\n{model}: {summary['attempts']} attempts, {summary['responses']} completed HTTP responses")
    for label, key in (("Category accuracy", "category_accuracy"), ("Priority accuracy", "priority_accuracy"),
                       ("Routing accuracy", "routing_accuracy"), ("Valid structured-output rate", "valid_output_rate")):
        print(f"  {label}: {summary[key]:.1%}")
    for label, key in (("Average response latency", "average_latency"), ("Median response latency", "median_latency")):
        value = summary[key]
        print(f"  {label}: {value:.3f} s" if value is not None else f"  {label}: N/A (no completed responses)")


def run_evaluation(models: list[str], tickets: list[EvaluationTicket], output: Path, timeout: float):
    system_prompt = build_system_prompt()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Refuse to overwrite earlier benchmark evidence. Flush every completed attempt.
    with output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[field.name for field in fields(EvaluationResult)])
        writer.writeheader()
        for model in models:
            results = []
            for index, ticket in enumerate(tickets, start=1):
                print(f"{model} [{index}/{len(tickets)}] {ticket.id} ...", flush=True)
                result = evaluate_ticket(model, ticket, system_prompt, timeout)
                results.append(result)
                writer.writerow(asdict(result))
                handle.flush()
                print(f"  {result.status}, {result.latency_seconds:.3f} s", flush=True)
                if result.error:
                    print(f"  {result.error.splitlines()[0]}", flush=True)
            print_summary(model, results)
    print(f"\nDetailed results: {output.resolve()}")


def positive_timeout(value: str) -> float:
    timeout = float(value)
    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError("Timeout must be a positive finite number of seconds.")
    return timeout


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--dataset", type=Path, default=EVALUATION_DIR / "tickets.json")
    parser.add_argument("--output", type=Path, default=EVALUATION_DIR / "results" / (
        "ollama_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".csv"
    ))
    parser.add_argument("--timeout", type=positive_timeout, default=120.0, help="HTTP timeout in seconds (default: 120)")
    args = parser.parse_args(argv)
    try:
        tickets = load_dataset(args.dataset)
        run_evaluation(list(dict.fromkeys(args.models)), tickets, args.output, args.timeout)
    except (OSError, ValueError) as error:
        print(f"Evaluation could not run: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nEvaluation interrupted; completed rows remain in the CSV.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
