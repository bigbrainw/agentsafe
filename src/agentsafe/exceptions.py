"""Exceptions raised by agentsafe."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentsafe.models import SafetyResult, SafetyTrace


class AgentSafeError(Exception):
    """Base exception for agentsafe."""


class SafetyViolation(AgentSafeError):
    """Raised when content is flagged as unsafe and blocking is enabled."""

    def __init__(
        self,
        message: str,
        result: SafetyResult | None = None,
        trace: SafetyTrace | None = None,
    ):
        self.result = result
        self.trace = trace
        super().__init__(message)

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.result and self.result.categories:
            parts.append(f"Categories: {', '.join(self.result.categories)}")
        return " | ".join(parts)


class SafetyCheckError(AgentSafeError):
    """Raised when the safety check itself fails (API error, timeout, etc.)."""


class ConfigError(AgentSafeError):
    """Raised for configuration problems."""
