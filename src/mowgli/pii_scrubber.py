"""
PII scrubber — regex pipeline that redacts sensitive data before any provider dispatch.

Patterns covered:
  - API keys (OpenAI, Anthropic, Google, AWS, GitHub, generic Bearer)
  - AWS credentials (access key ID + secret)
  - Email addresses
  - JWT tokens
  - Private key blocks (PEM)
  - Generic high-entropy secrets (32+ hex chars)
"""
from __future__ import annotations
import re

# (label, pattern, replacement)
_RULES: list[tuple[str, re.Pattern, str]] = [
    # OpenAI
    ("openai_key",    re.compile(r"sk-[A-Za-z0-9]{20,}"), "[OPENAI_KEY]"),
    # Anthropic
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9\-]{20,}"), "[ANTHROPIC_KEY]"),
    # Google / GCP
    ("google_key",    re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "[GOOGLE_KEY]"),
    # AWS Access Key ID
    ("aws_key_id",    re.compile(r"(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])"), "[AWS_KEY_ID]"),
    # AWS Secret Key (40-char base64-ish)
    ("aws_secret",    re.compile(r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])"), "[AWS_SECRET]"),
    # GitHub tokens
    ("github_token",  re.compile(r"ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82}"), "[GITHUB_TOKEN]"),
    # Bearer tokens
    ("bearer",        re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "Bearer [TOKEN]"),
    # JWT (three base64url segments separated by dots)
    ("jwt",           re.compile(r"ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), "[JWT]"),
    # PEM private key blocks
    ("pem",           re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[PRIVATE_KEY]"),
    # Email addresses
    ("email",         re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"), "[EMAIL]"),
    # Generic high-entropy hex secrets (32+ chars)
    ("hex_secret",    re.compile(r"(?<![a-fA-F0-9])[a-fA-F0-9]{32,}(?![a-fA-F0-9])"), "[SECRET]"),
]


def scrub(text: str) -> tuple[str, list[str]]:
    """
    Scrub PII from *text*.

    Returns:
        (scrubbed_text, list_of_redaction_labels)
    """
    redacted: list[str] = []
    for label, pattern, replacement in _RULES:
        new_text, n = pattern.subn(replacement, text)
        if n > 0:
            redacted.append(label)
            text = new_text
    return text, redacted
