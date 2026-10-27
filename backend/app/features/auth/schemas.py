from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.features.auth.models import (
    AccountStatus,
    AffiliationStatus,
    AffiliationType,
    UserRole,
)


class UserRegistration(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def require_uf_email(cls, value: EmailStr) -> EmailStr:
        if value.lower().rsplit("@", 1)[-1] != "ufl.edu":
            raise ValueError("A @ufl.edu email address is required")
        return value

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("Display name must contain at least 2 characters")
        return normalized


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class PublicUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    affiliation: AffiliationType
    affiliation_status: AffiliationStatus
    created_at: datetime


class CurrentUserResponse(PublicUserResponse):
    email: EmailStr
    email_verified: bool
    account_status: AccountStatus
    role: UserRole
    updated_at: datetime


class RegistrationResponse(BaseModel):
    detail: str
    verification_delivery: str
    user: CurrentUserResponse


class LoginResponse(BaseModel):
    detail: str
    user: CurrentUserResponse


class EmailVerificationRequest(BaseModel):
    token: str = Field(min_length=32, max_length=512)


class EmailVerificationResponse(BaseModel):
    detail: str
    user: CurrentUserResponse


class AuthenticationStatus(BaseModel):
    authenticated: bool
    local_auth_enabled: bool
    user: CurrentUserResponse | None = None


class DetailResponse(BaseModel):
    detail: str


class AuthenticationError(BaseModel):
    detail: str
    code: str | None = None
