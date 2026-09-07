"""Deterministic keyword rules for trying the workflow without a language model."""

import re

from app.assessment_schema import AIAssessment

# The first matching category wins, so security rules come first.
CATEGORY_RULES = (
    ("Security", ("phishing", "malware", "ransomware", "breach", "suspicious")),
    ("Account Access", ("password", "login", "log in", "account", "locked out", "mfa")),
    ("Network", ("network", "wifi", "wi-fi", "internet", "vpn", "connection")),
    ("Hardware", ("laptop", "printer", "monitor", "keyboard", "mouse", "hardware")),
    ("Software", ("software", "application", "app", "install", "crash", "license")),
)

TEAMS = {
    "Network": "Network Support",
    "Hardware": "Hardware Support",
    "Software": "Software Support",
    "Account Access": "Identity and Access",
    "Security": "IT Security",
    "Other": "Service Desk",
}


def _assess_priority(text: str, category: str) -> str:
    # Critical requires both broad scope and an interruption or severe incident.
    broad_impact = any(phrase in text for phrase in (
        "all users", "multiple users", "multiple services", "widespread",
        "company-wide", "company wide", "business-wide", "business wide",
        "entire company", "whole company", "entire office",
    ))
    disruption = any(phrase in text for phrase in (
        "outage", "interruption", "disruption", "unavailable", "offline",
        "is down", "are down", "system down", "systems down",
        "cannot connect", "can't connect", "cannot access", "unable to access",
        "cannot work", "can't work", "unable to work", "ransomware", "breach",
    ))
    if broad_impact and disruption:
        return "Critical"

    # A single user's blocked work can be High without being business-wide.
    blocked_work = any(phrase in text for phrase in (
        "cannot work", "can't work", "unable to work", "work is blocked",
        "work blocked", "blocking work", "cannot complete", "can't complete",
        "unable to complete", "production stopped", "payroll blocked",
    ))
    business_context = any(phrase in text for phrase in (
        "client", "customer", "meeting", "deadline", "presentation", "payroll", "production",
    ))
    imminent = bool(re.search(r"\bin \d+ (?:minutes?|hours?)\b", text))
    urgent = "urgent" in text and "not urgent" not in text
    time_sensitive = imminent or urgent or any(phrase in text for phrase in (
        "asap", "due today", "deadline today", "meeting today", "time-sensitive",
    ))
    if category == "Security" or blocked_work or (business_context and time_sensitive):
        return "High"

    # Deferral makes a planned request Low, not an otherwise disruptive incident.
    planned_request = any(phrase in text for phrase in (
        "planned", "request", "install", "upgrade", "license",
    ))
    deferred = any(phrase in text for phrase in (
        "for later", "next week", "next month", "when convenient",
        "no rush", "not urgent", "no urgency",
    ))
    minimal_impact = any(phrase in text for phrase in ("cosmetic", "how to", "minor"))
    if not disruption and not time_sensitive and (minimal_impact or (planned_request and deferred)):
        return "Low"

    # Ordinary single-user issues stay Medium unless an impact rule above matches.
    return "Medium"


def assess_ticket(title: str, description: str) -> AIAssessment:
    text = " ".join(f"{title} {description}".lower().replace("’", "'").split())
    category = "Other"
    for candidate, keywords in CATEGORY_RULES:
        if any(keyword in text for keyword in keywords):
            category = candidate
            break

    priority = _assess_priority(text, category)

    # This is a shortened copy of the input, not an AI-generated summary.
    summary = " ".join(f"{title}: {description}".split())
    if len(summary) > 240:
        summary = summary[:237] + "..."

    return AIAssessment(
        category=category,
        priority=priority,
        summary=summary,
        recommended_team=TEAMS[category],
        requires_human_review=True,
    )
