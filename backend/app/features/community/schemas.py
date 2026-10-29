from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PostCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=5000)

    @field_validator('content')
    @classmethod
    def validate_content(cls, value: str) -> str:
        # Strip surrounding whitespace while allowing for leading paragraph indentations
        value = value.lstrip(" \b\f\n\r").rstrip(" \b\f\n\r\t")
        if not value.strip():
            raise ValueError("Post content cannot be empty.")
        return value


class PostUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=5000)

    @field_validator('content')
    @classmethod
    def validate_content(cls, value: str) -> str:
        # Strip surrounding whitespace while allowing for leading paragraph indentations
        value = value.lstrip(" \b\f\n\r").rstrip(" \b\f\n\r\t")
        if not value.strip():
            raise ValueError("Post content cannot be empty.")
        return value


class PostResponse(BaseModel):
    id: int
    user_id: str
    author_name: str
    content: str
    created_at: datetime
    updated_at: datetime
