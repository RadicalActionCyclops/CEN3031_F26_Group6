from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.features.auth.models import AffiliationType


def normalize_text(value: str) -> str:
    return " ".join(value.split())


class ProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=2, max_length=100)
    status: AffiliationType
    graduation_year: int = Field(strict=True, ge=1900, le=datetime.now().year + 10)
    major: str = Field(default="", max_length=120)

    @field_validator("full_name", "major", mode="before")
    @classmethod
    def clean_text(cls, value):
        return normalize_text(value) if isinstance(value, str) else value


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    status: AffiliationType | None = None
    graduation_year: int | None = Field(
        default=None, strict=True, ge=1900, le=datetime.now().year + 10
    )
    major: str | None = Field(default=None, max_length=120)

    @field_validator("full_name", "major", mode="before")
    @classmethod
    def clean_text(cls, value):
        return normalize_text(value) if isinstance(value, str) else value

    @model_validator(mode="after")
    def reject_empty_or_null(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one profile field")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Profile fields cannot be null")
        return self


class ProfileResponse(BaseModel):
    user_id: str
    full_name: str
    status: AffiliationType
    graduation_year: int
    major: str
    title: str = ""
    updated_at: datetime


class MemberSearchResponse(BaseModel):
    items: list[ProfileResponse]
    total: int
    limit: int
    offset: int
