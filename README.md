# 🛡️ agentsafe

**Lightweight AI agent safety wrapper with observability, powered by NVIDIA Nemotron.**

As AI agents proliferate — tool-calling, code execution, browser automation — there's no simple, framework-agnostic way to add safety rails. `agentsafe` fixes that with a one-line decorator that wraps any agent with input/output safety checks using NVIDIA's Nemotron Safety Guard model, plus built-in observability so you can *see* what your agents are doing.

## The Problem

AI agents are increasingly autonomous but lack standardized safety checks:

- **Prompt injection** — malicious inputs that hijack agent behavior
- **Harmful outputs** — agents generating dangerous, illegal, or unethical content
- **Unsafe tool use** — agents executing dangerous operations (SQL injection, file deletion, etc.)
- **No visibility** — when something goes wrong, there's no audit trail

Existing solutions (NeMo Guardrails, Guardrails AI) are powerful but heavy — requiring YAML configs, Docker containers, or framework lock-in.

## The Solution

```bash
uv add agentsafe
```

One decorator. Zero config files. Full observability.

```python
from agentsafe import safe

@safe
def my_agent(prompt: str) -> str:
    return call_any_llm(prompt)

my_agent("What's the weather?")     # ✅ passes through
my_agent("How to make a bomb?")     # 🚫 raises SafetyViolation
```

## Features

| Feature | Description |
|---------|-------------|
| 🔍 **Input scanning** | Check user prompts before they reach your agent |
| 🎯 **Intended-use scope guard** | Block requests that are outside your app's purpose |
| 🛡️ **Output scanning** | Verify agent responses before they reach users |
| 🔧 **Tool call checking** | Inspect tool calls before execution |
| 📊 **Built-in observability** | Metrics, traces, structured logs — zero config |
| 📈 **OpenTelemetry export** | Send traces to Jaeger, Datadog, Grafana, etc. |
| 🔔 **Violation callbacks** | Get alerted on Slack, PagerDuty, webhooks |
| 🌍 **Multilingual** | 9 languages via Nemotron Safety Guard |
| ⚡ **Async support** | First-class async/await support |
| 🔌 **Framework agnostic** | Works with OpenAI, Anthropic, LangChain, raw HTTP |

## Install

```bash
# Core (minimal dependencies: httpx, pydantic, rich)
uv add agentsafe

# With OpenTelemetry export
uv add agentsafe[otel]

# With OpenAI client support
uv add agentsafe[openai]

# With notebook/browser chat UI demos (Gradio)
uv add agentsafe[ui]

# Everything
uv add agentsafe[all]
```

## Setup

Get a free NVIDIA API key from [build.nvidia.com](https://build.nvidia.com):

```bash
export NVIDIA_API_KEY="nvapi-..."
```

## Usage

### Decorator (simplest)

```python
from agentsafe import safe

@safe
def my_agent(prompt: str) -> str:
    return my_llm.generate(prompt)

result = my_agent("hello")  # ✅ checked and safe
```

### Wrapper (more control)

```python
from agentsafe import SafeAgent, AgentSafeConfig

config = AgentSafeConfig(
    check_input=True,
    check_output=True,
    block_on_unsafe=True,
)

agent = SafeAgent(my_agent_fn, config=config, name="my-agent")
result = agent("hello")
```

### Strict streaming (`@safe_stream`)

`safe_stream` supports streaming-style agent functions while keeping strict
output safety semantics: it buffers the full response, runs output checks, and
only then yields chunks to the caller.

```python
from agentsafe import AgentSafeConfig, safe_stream

@safe_stream(config=AgentSafeConfig(check_input=True, check_output=True))
def my_streaming_agent(prompt: str):
    # any iterable[str] is supported
    yield "hello "
    yield "world"

for chunk in my_streaming_agent("hi"):
    print(chunk, end="")
```

You can also call the wrapper directly:

```python
from agentsafe import AgentSafeConfig, SafeAgent

agent = SafeAgent(my_streaming_agent, config=AgentSafeConfig(check_output=True))
for chunk in agent.run_stream("hi", chunk_size=64):
    print(chunk, end="")
```

### With OpenAI-compatible clients

```python
from openai import OpenAI
from agentsafe import SafeAgent

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key="...")
agent = SafeAgent.from_openai(client, model="nvidia/llama-3.1-8b-instruct")

result = agent.chat("explain quantum computing")
```

### Tool call checking

```python
agent = SafeAgent(my_fn)

# Before executing a tool, check it
agent.check_tool_call("execute_sql", {"query": "DROP TABLE users"})
# 🚫 raises SafetyViolation
```

### Intended-use scope guard

Use a fast model-based pre-check to ensure user prompts are aligned with your
agent's intended purpose (while keeping standard Nemotron checks enabled).

```python
from agentsafe import AgentSafeConfig, SafeAgent

config = AgentSafeConfig(
    check_scope=True,
    intended_use_prompt=(
        "This assistant only helps users find SJSU-area chicken restaurants, "
        "menu items, pricing, and hours."
    ),
    # Existing Nemotron safeguards still run.
    check_input=True,
    check_output=True,
    scope_base_url="https://integrate.api.nvidia.com/v1",
    scope_model="nvidia/llama-3.1-nemotron-nano-vl-8b-v1",
)

agent = SafeAgent(my_fn, config=config, name="sjsu-chicken-bot")
```

Out-of-scope prompts like "solve my calculus homework" are blocked before the
agent runs.

## Observability

Observability is built-in, not bolted on. Every safety check produces a trace with timing, verdict, and categories.

### Real-time metrics

```python
agent = SafeAgent(my_fn, name="prod-agent")

# After some interactions...
metrics = agent.observer.metrics.to_dict()
# {
#   "total_checks": 1547,
#   "safe": 1520,
#   "unsafe": 24,
#   "errors": 3,
#   "blocked": 24,
#   "unsafe_rate": 0.0155,
#   "avg_latency_ms": 142.3,
#   "p99_latency_ms": 380.1,
#   "top_categories": {"S3: Criminal Planning": 8, "S17: Malware": 6, ...},
#   "checks_by_type": {"input": 1000, "output": 547}
# }
```

### Violation alerts

```python
# Get alerted when unsafe content is detected
agent.observer.on_violation(
    lambda trace, result: slack.post(
        f"🚨 Safety violation in {trace.agent_name}: {result.categories}"
    )
)
```

### Trace search

```python
# Find all blocked interactions
blocked = agent.observer.traces.search(blocked_only=True)

# Find violations by category
pii_leaks = agent.observer.traces.search(category="S9: PII/Privacy")

# Find by agent
agent_a_issues = agent.observer.traces.search(agent_name="agent-a", blocked_only=True)
```

### Terminal report

```python
agent.observer.print_report()
```

```
═══ agentsafe Safety Report ═══

         Summary
┌──────────────┬────────┐
│ Total Checks │  1,547 │
│ Safe         │  1,520 │
│ Unsafe       │     24 │
│ Errors       │      3 │
│ Blocked      │     24 │
│ Unsafe Rate  │  1.6%  │
│ Avg Latency  │  142ms │
│ P99 Latency  │  380ms │
└──────────────┴────────┘
```

### OpenTelemetry export

```python
config = AgentSafeConfig(
    enable_otel=True,
    otel_service_name="agentsafe-app",
    otel_exporter_protocol="http/protobuf",  # or "grpc"
    otel_exporter_endpoint="http://localhost:4318",  # local collector
)
agent = SafeAgent(my_fn, config=config)

# Traces and metrics are exported to any OTEL-compatible backend:
# Jaeger, Datadog, Grafana Tempo, Honeycomb, etc.
```

### Local-only OTEL (no SaaS)

Run everything on localhost with Jaeger + OTLP ingestion:

```bash
# from project root
docker compose -f docker-compose.otel.yml up -d
```

Jaeger UI will be at `http://localhost:16686` and OTLP ingestion at:
- HTTP: `http://localhost:4318`
- gRPC: `localhost:4317`

Use this local config:

```python
config = AgentSafeConfig(
    enable_otel=True,
    otel_service_name="agentsafe-local",
    otel_exporter_protocol="http/protobuf",
    otel_exporter_endpoint="http://localhost:4318",
    otel_include_content=False,  # secure default
    otel_content_max_chars=200,
)
```

### Jaeger payload visibility

By default, `agentsafe` does not attach prompt/response text to OTEL spans.
Jaeger will still show timing, verdict, block status, and categories.

Enable snippet visibility only for local debugging:

```python
config = AgentSafeConfig(
    enable_otel=True,
    otel_include_content=True,
    otel_content_max_chars=200,
)
```

For the `.py` local demo, you can toggle this with:

```bash
AGENTSAFE_OTEL_INCLUDE_CONTENT=true uv run python examples/local_otel_openai_demo.py
```

Treat this as sensitive data: keep it local and avoid enabling in production.

Stop local stack:

```bash
docker compose -f docker-compose.otel.yml down
```

Examples:
- `.py` flow (opens browser dashboard): `examples/local_otel_openai_demo.py`
- notebook flow (embedded Jaeger UI inside notebook output): `examples/ollama_openai_agentsafe_demo.ipynb`
- Responses API + tools + scope blocking notebook:
  `examples/sjsu_chicken_chatbot_otel_demo.ipynb`
- Safe Gradio notebook UI (scope + Nemotron checks enabled):
  `examples/sjsu_chicken_chatbot_ui_safe.ipynb`
- Unsafe Gradio notebook UI baseline (same model/tools, no AgentSafe wrapper):
  `examples/sjsu_chicken_chatbot_ui_unsafe.ipynb`

### UI comparison notebooks (safe vs unsafe)

Run dependencies:

```bash
uv sync --extra openai --extra ui
```

Then run the two notebooks side-by-side:

- `examples/sjsu_chicken_chatbot_ui_safe.ipynb`
- `examples/sjsu_chicken_chatbot_ui_unsafe.ipynb`

Both notebooks use the same NVIDIA generation model (`meta/llama-3.1-8b-instruct`) and
the same SJSU chicken tools/prompt battery, including:
- allowed in-scope food query
- out-of-scope homework request
- in-scope but unsafe criminal request
- long prompt with sneaky second malicious request
- jailbreak-style prompts (role-play and override)

Expected difference:
- Safe notebook blocks unsafe/out-of-scope prompts via AgentSafe checks.
- Unsafe notebook shows baseline behavior without those checks.

### JSONL export

```python
# Export all traces for analysis in pandas, DuckDB, etc.
jsonl = agent.observer.traces.export_jsonl()
with open("safety_traces.jsonl", "w") as f:
    f.write(jsonl)
```

### Shared observer across agents

```python
from agentsafe import SafetyObserver

# One observer, multiple agents
observer = SafetyObserver()

agent_a = SafeAgent(fn_a, name="agent-a", observer=observer)
agent_b = SafeAgent(fn_b, name="agent-b", observer=observer)

# Unified metrics and traces across all agents
observer.print_report()
```

## CLI

```bash
# Quick safety check
agentsafe check "Is this message safe?"

# Interactive mode with live metrics
agentsafe interactive
```

## Safety Categories

agentsafe uses NVIDIA's 23-category safety taxonomy:

| Code | Category | Code | Category |
|------|----------|------|----------|
| S1 | Violence | S13 | Needs Caution |
| S2 | Sexual | S14 | Other |
| S3 | Criminal Planning | S15 | Manipulation |
| S4 | Guns/Weapons | S16 | Fraud/Deception |
| S5 | Controlled Substances | S17 | Malware |
| S6 | Suicide/Self Harm | S18 | High Risk Gov |
| S7 | Sexual (minor) | S19 | Misinfo/Conspiracy |
| S8 | Hate/Identity Hate | S20 | Copyright |
| S9 | PII/Privacy | S21 | Unauthorized Advice |
| S10 | Harassment | S22 | Illegal Activity |
| S11 | Threat | S23 | Immoral/Unethical |
| S12 | Profanity | | |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Your Agent                        │
│  (OpenAI, Anthropic, LangChain, custom, etc.)       │
└──────────────────┬──────────────────────────────────┘
                   │
          ┌────────▼────────┐
          │   agentsafe     │
          │                 │
          │  ┌───────────┐  │     ┌─────────────────────┐
          │  │  Input     │──────▶│  Nemotron Safety     │
          │  │  Check     │◀──────│  Guard API           │
          │  └───────────┘  │     │  (build.nvidia.com)  │
          │        │        │     └─────────────────────┘
          │  ┌─────▼─────┐  │
          │  │  Agent     │  │
          │  │  Execution │  │
          │  └─────┬─────┘  │
          │        │        │     ┌─────────────────────┐
          │  ┌─────▼─────┐  │     │  Observer            │
          │  │  Output    │──────▶│  ├─ Metrics          │
          │  │  Check     │  │     │  ├─ Traces           │
          │  └───────────┘  │     │  ├─ Structured Logs  │
          │                 │     │  ├─ OTEL Export       │
          └─────────────────┘     │  └─ Callbacks        │
                                  └─────────────────────┘
```

## Powered by NVIDIA Nemotron

This project uses [Llama-3.1-Nemotron-Safety-Guard-8B-v3](https://build.nvidia.com/nvidia/llama-3_1-nemotron-safety-guard-8b-v3) — NVIDIA's multilingual content safety model supporting 9 languages and 23 safety categories. Free API access available at [build.nvidia.com](https://build.nvidia.com).

## License

Apache 2.0
