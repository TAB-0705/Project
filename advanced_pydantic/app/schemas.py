import re
from datetime import date
from pydantic import BaseModel, Field, field_validator, model_validator

# --- Business-rule patterns kept in one place -----------------------------
MEMBER_ID_PATTERN = re.compile(r"^WNS-\d{4}$")          # e.g. WNS-0427
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?\d{10,15}$")           # 10-15 digits, optional +
MIN_AGE = 18


def compute_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class MemberCreate(BaseModel):
    """Registration payload. Every field carries its own business rule.

    A plain version of this model would just be `member_id: str` etc. The
    refactor is moving each rule OUT of route handlers and INTO the model,
    so validation happens once, automatically, before any logic runs.
    """

    member_id: str
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str
    phone: str
    date_of_birth: date
    password: str
    confirm_password: str

    # --- single-field validators -----------------------------------------
    @field_validator("member_id")
    @classmethod
    def validate_member_id(cls, v: str) -> str:
        # A custom validator (vs Field(pattern=...)) lets us give a clear,
        # domain-specific error message instead of a generic regex failure.
        if not MEMBER_ID_PATTERN.match(v):
            raise ValueError("member_id must look like 'WNS-1234' (WNS- then 4 digits)")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_PATTERN.match(v):
            raise ValueError("email is not a valid address")
        return v.lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not PHONE_PATTERN.match(v):
            raise ValueError("phone must be 10-15 digits, optionally starting with '+'")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("date_of_birth must be in the past")
        if compute_age(v) < MIN_AGE:
            raise ValueError(f"member must be at least {MIN_AGE} years old")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        if not any(c.isdigit() for c in v):
            raise ValueError("password must contain at least one digit")
        if not any(c.isupper() for c in v):
            raise ValueError("password must contain at least one uppercase letter")
        return v

    # --- cross-field validator -------------------------------------------
    @model_validator(mode="after")
    def passwords_match(self) -> "MemberCreate":
        # A model validator sees the whole object, so it can compare fields.
        if self.password != self.confirm_password:
            raise ValueError("password and confirm_password do not match")
        return self


class MemberResponse(BaseModel):
    """Safe view returned to clients — note: no password fields."""
    member_id: str
    full_name: str
    email: str
    phone: str
    date_of_birth: date
    age: int
