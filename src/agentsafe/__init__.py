"""agentsafe — Lightweight AI agent safety wrapper with observability, powered by NVIDIA Nemotron.

Quick start:
    from agentsafe import safe

    @safe
    def my_agent(prompt: str) -> str:
        return call_llm(prompt)

    result = my_agent("hello")  # input & output are safety-checked

With observability:
    from agentsafe import SafeAgent, AgentSafeConfig

    config = AgentSafeConfig(enable_otel=True)
    agent = SafeAgent(my_fn, config=config, name="my-agent")

    result = agent("hello")
    agent.observer.print_report()
"""

__version__ = "0.1.0"

from agentsafe.checker import AsyncNemotronChecker, NemotronChecker
from agentsafe.exceptions import AgentSafeError, SafetyCheckError, SafetyViolation
from agentsafe.models import (
    AgentSafeConfig,
    CheckType,
    SafetyCategory,
    SafetyResult,
    SafetyTrace,
    SafetyVerdict,
)
from agentsafe.observability import SafetyMetrics, SafetyObserver, TraceStore
from agentsafe.wrapper import SafeAgent, safe, safe_stream

__all__ = [
    # Core
    "SafeAgent",
    "safe",
    "safe_stream",
    "NemotronChecker",
    "AsyncNemotronChecker",
    # Config & Models
    "AgentSafeConfig",
    "SafetyResult",
    "SafetyTrace",
    "SafetyVerdict",
    "SafetyCategory",
    "CheckType",
    # Observability
    "SafetyObserver",
    "SafetyMetrics",
    "TraceStore",
    # Exceptions
    "SafetyViolation",
    "SafetyCheckError",
    "AgentSafeError",
]
