"""Data models for safety checks and observability."""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class SafetyVerdict(str, Enum):
    """Result of a safety check."""

    SAFE = "safe"
    UNSAFE = "unsafe"
    ERROR = "error"


class SafetyCategory(str, Enum):
    """Nemotron safety taxonomy — 23 categories."""

    VIOLENCE = "S1: Violence"
    SEXUAL = "S2: Sexual"
    CRIMINAL_PLANNING = "S3: Criminal Planning/Confessions"
    GUNS_WEAPONS = "S4: Guns and Illegal Weapons"
    CONTROLLED_SUBSTANCES = "S5: Controlled/Regulated Substances"
    SUICIDE_SELF_HARM = "S6: Suicide and Self Harm"
    SEXUAL_MINOR = "S7: Sexual (minor)"
    HATE = "S8: Hate/Identity Hate"
    PII_PRIVACY = "S9: PII/Privacy"
    HARASSMENT = "S10: Harassment"
    THREAT = "S11: Threat"
    PROFANITY = "S12: Profanity"
    NEEDS_CAUTION = "S13: Needs Caution"
    OTHER = "S14: Other"
    MANIPULATION = "S15: Manipulation"
    FRAUD_DECEPTION = "S16: Fraud/Deception"
    MALWARE = "S17: Malware"
    HIGH_RISK_GOV = "S18: High Risk Gov Decision Making"
    POLITICAL_MISINFO = "S19: Political/Misinformation/Conspiracy"
    COPYRIGHT = "S20: Copyright/Trademark/Plagiarism"
    UNAUTHORIZED_ADVICE = "S21: Unauthorized Advice"
    ILLEGAL_ACTIVITY = "S22: Illegal Activity"
    IMMORAL_UNETHICAL = "S23: Immoral/Unethical"


class CheckType(str, Enum):
    """What kind of content was checked."""

    INPUT = "input"
    SCOPE = "scope"
    OUTPUT = "output"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class SafetyResult(BaseModel):
    """Result of a single safety check."""

    verdict: SafetyVerdict
    categories: list[str] = Field(default_factory=list)
    check_type: CheckType
    content_snippet: str = ""  # first 200 chars for audit
    raw_response: dict[str, Any] | None = None
    latency_ms: float = 0.0
    error: str | None = None

    @property
    def is_safe(self) -> bool:
        return self.verdict == SafetyVerdict.SAFE


class SafetyTrace(BaseModel):
    """A complete observability trace for one agent interaction."""

    trace_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: float = Field(default_factory=time.time)
    agent_name: str = "default"

    # The checks that were performed
    scope_check: SafetyResult | None = None
    input_check: SafetyResult | None = None
    output_check: SafetyResult | None = None
    tool_checks: list[SafetyResult] = Field(default_factory=list)

    # Overall
    blocked: bool = False
    block_reason: str | None = None

    # Timing
    total_latency_ms: float = 0.0

    @property
    def all_checks(self) -> list[SafetyResult]:
        checks = []
        if self.scope_check:
            checks.append(self.scope_check)
        if self.input_check:
            checks.append(self.input_check)
        if self.output_check:
            checks.append(self.output_check)
        checks.extend(self.tool_checks)
        return checks

    @property
    def any_unsafe(self) -> bool:
        return any(not c.is_safe for c in self.all_checks)

    @property
    def violated_categories(self) -> list[str]:
        cats: list[str] = []
        for c in self.all_checks:
            cats.extend(c.categories)
        return list(set(cats))


class AgentSafeConfig(BaseModel):
    """Configuration for agentsafe."""

    # Nemotron API settings
    nemotron_base_url: str = "https://integrate.api.nvidia.com/v1"
    nemotron_model: str = "nvidia/llama-3.1-nemotron-safety-guard-8b-v3"
    nemotron_api_key: str | None = None  # falls back to NVIDIA_API_KEY env var

    # Behavior
    check_scope: bool = False
    check_input: bool = True
    check_output: bool = True
    check_tool_calls: bool = True
    block_on_unsafe: bool = True  # raise exception vs. just log
    block_on_error: bool = False  # block if safety check itself fails

    # Intended-use scope checks (OpenAI-compatible endpoint)
    intended_use_prompt: str | None = None
    scope_base_url: str = "https://integrate.api.nvidia.com/v1"
    scope_model: str = "nvidia/llama-3.1-nemotron-nano-vl-8b-v1"
    scope_api_key: str | None = None

    # Content
    max_content_length: int = 4096  # truncate content before sending to checker
    snippet_length: int = 200  # how much content to store in traces

    # Custom safety categories to watch for (empty = all)
    watched_categories: list[str] = Field(default_factory=list)

    # Observability
    enable_otel: bool = False
    otel_service_name: str = "agentsafe"
    otel_exporter_protocol: Literal["http/protobuf", "grpc"] = "http/protobuf"
    otel_exporter_endpoint: str | None = None  # defaults to localhost endpoint by protocol
    otel_exporter_insecure: bool = True
    otel_include_content: bool = False  # include prompt/response snippets in span attributes
    otel_content_max_chars: int = 200
    otel_include_categories: bool = True
    enable_logging: bool = True
    log_safe_requests: bool = False  # only log unsafe by default
    trace_store_max: int = 10000  # max traces to keep in memory
