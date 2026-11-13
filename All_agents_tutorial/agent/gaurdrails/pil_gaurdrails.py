import re
from typing import Any


SENSITIVE_COLUMN_HINTS = {
    "email",
    "phone",
    "mobile",
    "address",
    "password",
    "secret",
    "token",
    "api_key",
    "ssn",
    "aadhaar",
    "pan",
    "card",
    "cvv",
    "date_of_birth",
    "dob",
    "first_name",
    "last_name",
    "full_name",
}


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)"
)


def is_sensitive_column(column_name: str) -> bool:
    normalized_name = column_name.lower().replace("-", "_")

    return any(
        hint in normalized_name
        for hint in SENSITIVE_COLUMN_HINTS
    )


def mask_email(value: str) -> str:
    local_part, _, domain = value.partition("@")

    if not domain:
        return "[REDACTED_EMAIL]"

    return f"{local_part[:1]}***@{domain}"


def mask_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)

    if len(digits) < 4:
        return "[REDACTED_PHONE]"

    return f"******{digits[-4:]}"


def redact_value(
    column_name: str,
    value: Any,
) -> Any:
    if value is None:
        return None

    if not is_sensitive_column(column_name):
        return value

    text_value = str(value)
    normalized_name = column_name.lower()

    if "email" in normalized_name:
        return mask_email(text_value)

    if "phone" in normalized_name or "mobile" in normalized_name:
        return mask_phone(text_value)

    return "[REDACTED]"


def redact_rows(rows: list[dict]) -> list[dict]:
    return [
        {
            column_name: redact_value(column_name, value)
            for column_name, value in row.items()
        }
        for row in rows
    ]


def redact_text(text: str) -> str:
    text = EMAIL_PATTERN.sub(
        lambda match: mask_email(match.group(0)),
        text,
    )

    text = PHONE_PATTERN.sub(
        lambda match: mask_phone(match.group(0)),
        text,
    )

    return text