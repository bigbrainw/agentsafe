"""Full observability demo — callbacks, metrics, trace search, OTEL export.

This example shows how to:
1. Set up custom violation callbacks (alerts, webhooks, etc.)
2. Access real-time metrics
3. Search and filter traces
4. Export traces for analysis
5. Generate terminal reports
"""

import json
from pathlib import Path

from dotenv import load_dotenv

from agentsafe import (
    AgentSafeConfig,
    SafeAgent,
    SafetyObserver,
    SafetyResult,
    SafetyTrace,
    SafetyViolation,
)

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


# ── 1. Create a shared observer (can be used across multiple agents) ──
config = AgentSafeConfig(
    log_safe_requests=True,  # log everything, not just violations
    # enable_otel=True,      # uncomment if you have OTEL collector running
)
observer = SafetyObserver(config)


# ── 2. Register callbacks ──


def alert_on_violation(trace: SafetyTrace, result: SafetyResult) -> None:
    """Called every time unsafe content is detected."""
    print(f"🚨 VIOLATION [{trace.trace_id[:8]}] agent={trace.agent_name}")
    print(f"   Type: {result.check_type.value}")
    print(f"   Categories: {', '.join(result.categories)}")
    print(f"   Snippet: {result.content_snippet[:60]}...")
    # In production: send to Slack, PagerDuty, webhook, etc.


def log_every_trace(trace: SafetyTrace) -> None:
    """Called for every trace (safe or unsafe)."""
    status = "UNSAFE" if trace.any_unsafe else "SAFE"
    print(f"   [{trace.trace_id[:8]}] {status} latency={trace.total_latency_ms:.0f}ms")


observer.on_violation(alert_on_violation)
observer.on_trace(log_every_trace)


# ── 3. Create agents sharing the same observer ──


def agent_a(prompt: str) -> str:
    return f"Agent A response to: {prompt}"


def agent_b(prompt: str) -> str:
    return f"Agent B response to: {prompt}"


safe_a = SafeAgent(agent_a, name="agent-a", config=config, observer=observer)
safe_b = SafeAgent(agent_b, name="agent-b", config=config, observer=observer)


if __name__ == "__main__":
    # Run some interactions
    prompts = [
        ("agent-a", "What's the capital of France?"),
        ("agent-b", "Tell me about machine learning"),
        ("agent-a", "How to pick a lock"),
        ("agent-b", "Write a phishing email"),
        ("agent-a", "Best pasta recipe?"),
    ]

    print("=== Running agent interactions ===\n")
    for agent_name, prompt in prompts:
        agent = safe_a if agent_name == "agent-a" else safe_b
        try:
            agent(prompt)
        except SafetyViolation:
            pass  # already handled by callback
        print()

    # ── 4. Access metrics programmatically ──
    print("\n=== Metrics ===")
    metrics = observer.metrics.to_dict()
    print(json.dumps(metrics, indent=2))

    # ── 5. Search traces ──
    print("\n=== Trace Search ===")

    # Find all blocked traces
    blocked = observer.traces.search(blocked_only=True)
    print(f"Blocked traces: {len(blocked)}")

    # Find traces by agent
    agent_a_traces = observer.traces.search(agent_name="agent-a")
    print(f"Agent-A traces: {len(agent_a_traces)}")

    # Find traces by category
    # violence = observer.traces.search(category="S1: Violence")

    # ── 6. Print rich terminal report ──
    print()
    observer.print_report()

    # ── 7. Export for external analysis ──
    jsonl = observer.traces.export_jsonl()
    print(f"\nExportable JSONL ({len(jsonl)} bytes):")
    for line in jsonl.split("\n")[:2]:
        print(f"  {line[:120]}...")
