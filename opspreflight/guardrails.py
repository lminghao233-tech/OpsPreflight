"""Guardrails for untrusted free text embedded inside IaC documents."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


PATTERNS = (
    re.compile(r"ignore (all |the )?(previous|prior|system) instructions", re.I),
    re.compile(r"reveal (the )?(system prompt|hidden instructions|secret|token)", re.I),
    re.compile(r"忽略.{0,8}(之前|系统).{0,8}(指令|提示)"),
)
REPLACEMENT = "[UNTRUSTED_INSTRUCTION_REDACTED]"


@dataclass(frozen=True)
class InjectionFinding:
    path: str
    pattern: str


def scan_prompt_injection(value: Any, path: str = "$") -> tuple[InjectionFinding, ...]:
    findings: list[InjectionFinding] = []
    if isinstance(value, dict):
        for key, item in value.items():
            findings.extend(scan_prompt_injection(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(scan_prompt_injection(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        for index, pattern in enumerate(PATTERNS):
            if pattern.search(value):
                findings.append(InjectionFinding(path, f"pattern-{index + 1}"))
    return tuple(findings)


def sanitize_untrusted_text(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: sanitize_untrusted_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_untrusted_text(item) for item in value]
    if isinstance(value, str) and any(pattern.search(value) for pattern in PATTERNS):
        return REPLACEMENT
    return value
