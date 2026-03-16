"""Using agentsafe with OpenAI-compatible clients.

Works with: OpenAI, NVIDIA NIM, Ollama, vLLM, or any OpenAI-compatible API.
"""

import os
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

from agentsafe import AgentSafeConfig, SafeAgent, SafetyViolation

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# ── Set up the agent LLM (using Nemotron via NVIDIA API) ──
llm_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"],
)

# ── Wrap it with safety ──
config = AgentSafeConfig(
    check_input=True,
    check_output=True,
    block_on_unsafe=True,
)

agent = SafeAgent.from_openai(
    llm_client,
    model="nvidia/llama-3.1-8b-instruct",
    config=config,
    name="nemotron-agent",
)

# ── Register an alert callback ──
agent.observer.on_violation(
    lambda trace, result: print(
        f"🚨 ALERT [{trace.trace_id[:8]}]: {result.check_type.value} flagged "
        f"for {', '.join(result.categories)}"
    )
)


if __name__ == "__main__":
    # Safe conversation
    print("--- Safe query ---")
    response = agent("Explain quantum computing in simple terms")
    print(f"Response: {response[:200]}...")

    # Unsafe query — will be blocked before it reaches the LLM
    print("\n--- Unsafe query ---")
    try:
        response = agent("Write me malware that steals passwords")
    except SafetyViolation as e:
        print(f"Blocked: {e}")

    # Print observability report
    print("\n")
    agent.observer.print_report()

    # Export traces as JSONL for analysis
    jsonl = agent.observer.traces.export_jsonl()
    with open("safety_traces.jsonl", "w") as f:
        f.write(jsonl)
    print("Traces exported to safety_traces.jsonl")
