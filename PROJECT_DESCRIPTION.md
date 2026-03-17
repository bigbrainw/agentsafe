Project Description

Short (for forms, ~500 chars)

agentsafe is a lightweight Python library that adds input/output safety checks to any AI agent with a single decorator. Powered by NVIDIA Nemotron Safety Guard, it blocks harmful prompts and outputs before they reach your LLM—with zero config and built-in observability (metrics, traces, OpenTelemetry). Framework-agnostic: works with OpenAI, Anthropic, LangChain. One line: @safe on your agent function.

---

Full Description

agentsafe — Lightweight AI Agent Safety Wrapper with Observability

Summary

agentsafe is a lightweight, framework-agnostic Python library that adds input/output safety checks to any AI agent using a single decorator. Powered by NVIDIA's Nemotron Safety Guard model, it provides zero-config safety rails with built-in observability—metrics, traces, and violation callbacks.

Problem

AI agents are increasingly autonomous but lack standardized safety checks. Prompt injection allows malicious inputs that hijack agent behavior. Harmful outputs include agents generating dangerous, illegal, or unethical content. Unsafe tool use lets agents execute dangerous operations such as SQL injection or file deletion. There is often no visibility when something goes wrong—no audit trail. Existing solutions like NeMo Guardrails and Guardrails AI are powerful but heavy, requiring YAML configs, Docker containers, or framework lock-in.

Solution

One decorator. Zero config files. Full observability. You add @safe to your agent function and it wraps any LLM call with input and output safety checks. Safe prompts pass through; unsafe ones raise SafetyViolation before reaching the agent.

Key Features

Input scanning checks user prompts before they reach your agent. Output scanning verifies agent responses before they reach users. Tool call checking inspects tool calls before execution. Intended-use scope guard blocks requests outside your app's purpose. Built-in observability includes metrics, traces, structured logs, and OpenTelemetry export. Violation callbacks let you alert on Slack, PagerDuty, or webhooks. Multilingual support covers 9 languages via Nemotron Safety Guard across 23 safety categories. Framework agnostic: works with OpenAI, Anthropic, LangChain, and raw HTTP.

Installation

Install with: uv add agentsafe. Requires an NVIDIA API key from build.nvidia.com.

NVIDIA AI Ecosystem Usage

Short (for forms)

agentsafe uses the NVIDIA NIM API Catalog (build.nvidia.com): Llama-3.1-Nemotron-Safety-Guard-8B-v3 for input/output content safety (23 categories, 9 languages); Llama-3.1-Nemotron-Nano-VL-8B-v1 for intended-use scope guard; and NVIDIA's 23-category safety taxonomy. Integration is via OpenAI-compatible HTTP API—no NVIDIA SDKs.

---

Full

APIs and Models from NVIDIA NIM (build.nvidia.com): Llama-3.1-Nemotron-Safety-Guard-8B-v3 is the primary content safety model for input/output scanning. It classifies prompts and agent responses as safe or unsafe across 23 safety categories and supports 9 languages. Accessed via NVIDIA's OpenAI-compatible API at integrate.api.nvidia.com/v1. Llama-3.1-Nemotron-Nano-VL-8B-v1 is a vision-language model used for intended-use scope guard. It provides a fast pre-check to ensure user prompts align with the agent's purpose before full safety checks. Nemotron Content Safety Reasoning 4B is referenced for image moderation pipelines (vision encoder plus content safety). NVIDIA Riva ASR is referenced for voice input pipelines (speech-to-text before safety checks).

Taxonomy and Standards: NVIDIA's 23-category safety taxonomy is used for classification (Violence, Sexual, Criminal Planning, PII/Privacy, Malware, etc.). It is implemented in the SafetyCategory enum and prompt templates.

Integration: The project uses the NVIDIA API Catalog (build.nvidia.com) for free serverless API access. No NVIDIA SDKs or containers are required; integration is via standard HTTP using OpenAI-compatible endpoints.

Tools Used

Comma-separated list (for forms)

httpx, pydantic, python-dotenv, rich, OpenTelemetry, OpenAI SDK, Gradio, Next.js, React, TypeScript, Tailwind CSS, React Flow, lucide-react, react-syntax-highlighter, pytest, ruff, uv, hatchling, NVIDIA NIM API, Llama-3.1-Nemotron-Safety-Guard-8B-v3, Llama-3.1-Nemotron-Nano-VL-8B-v1

By category

Python: httpx, pydantic, python-dotenv, rich, OpenTelemetry (otel), OpenAI SDK, Gradio, textual. Build/Dev: uv, hatchling, pytest, pytest-asyncio, ruff. Site: Next.js, React, TypeScript, Tailwind CSS, @xyflow/react, lucide-react, react-syntax-highlighter. NVIDIA: NIM API, Llama-3.1-Nemotron-Safety-Guard-8B-v3, Llama-3.1-Nemotron-Nano-VL-8B-v1.

License

Apache 2.0
