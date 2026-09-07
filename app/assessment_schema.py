"""The assessment contract shared by providers and the application."""

from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal["Network", "Hardware", "Software", "Account Access", "Security", "Other"]
Priority = Literal["Low", "Medium", "High", "Critical"]

# Use the same allowed values for the model and human-review form choices.
CATEGORIES = get_args(Category)
PRIORITIES = get_args(Priority)


class AIAssessment(BaseModel):
    """A complete, validated recommendation, independent of storage and provider."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    category: Category
    priority: Priority
    summary: str = Field(min_length=1)
    recommended_team: str = Field(min_length=1)
    requires_human_review: bool

    @field_validator("summary", "recommended_team")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Text must not be blank")
        return value
