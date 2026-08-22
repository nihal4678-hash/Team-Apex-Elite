"""Shared validation result objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    stage: str
    passed: bool
    checks: list[dict[str, Any]] = field(default_factory=list)
    pending_issues: list[str] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            self.passed = False
            self.pending_issues.append(f"{name}: {detail}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "passed": self.passed,
            "checks": self.checks,
            "pending_issues": self.pending_issues,
        }
