"""One assessment prompt shared by the application and local-model benchmark."""

import json
from pathlib import Path

from app.assessment_schema import AIAssessment
from app.mock_assessment import CATEGORY_RULES, TEAMS


def build_system_prompt() -> str:
    # The policy and schema are identical for every model and ticket.
    policy = Path(__file__).with_name("assessment_policy.txt").read_text(encoding="utf-8")
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
