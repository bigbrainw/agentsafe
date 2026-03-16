from __future__ import annotations

import argparse
import os
import socket
import threading
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from openai import OpenAI
import uvicorn

from agentsafe import AgentSafeConfig, SafetyViolation, safe


def load_env_file(env_filename: str = ".env") -> Path | None:
    start = Path.cwd().resolve()
    candidates = [start / env_filename, *[(p / env_filename) for p in start.parents]]
    for c in candidates:
        if c.exists():
            load_dotenv(c)
            return c
    return None


def prompt_from_messages(messages: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for m in messages:
        if m.get("role") == "user":
            content = m.get("content", "")
            if isinstance(content, str):
                parts.append(content)
    return "\n\n".join(parts).strip()


def wait_for_port(host: str, port: int, timeout_s: float = 15.0) -> None:
    start = time.time()
    while time.time() - start < timeout_s:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex((host, port)) == 0:
                return
        time.sleep(0.1)
    raise TimeoutError(f"port {port} did not open in time")


def start_server(app: FastAPI, port: int) -> tuple[uvicorn.Server, threading.Thread]:
    cfg = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(cfg)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    wait_for_port("127.0.0.1", port)
    return server, thread


def build_apps(
    model: str, model_base_url: str, model_api_key: str, nvidia_api_key: str
) -> tuple[FastAPI, FastAPI]:
    backend = OpenAI(base_url=model_base_url, api_key=model_api_key)

    def call_backend(prompt: str) -> str:
        r = backend.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return (r.choices[0].message.content or "").strip()

    config = AgentSafeConfig(
        check_scope=False,
        check_input=True,
        check_output=True,
        block_on_unsafe=True,
        nemotron_base_url="https://integrate.api.nvidia.com/v1",
        nemotron_model="nvidia/llama-3.1-nemotron-safety-guard-8b-v3",
        nemotron_api_key=nvidia_api_key,
    )

    @safe(config=config, name="garak-guarded-agent")
    def guarded_call(prompt: str) -> str:
        return call_backend(prompt)

    unsafe_app = FastAPI(title="unsafe-agent")
    guarded_app = FastAPI(title="guarded-agent")

    @unsafe_app.post("/v1/chat/completions")
    def unsafe_chat(payload: dict[str, Any]) -> dict[str, Any]:
        prompt = prompt_from_messages(payload.get("messages", []))
        out = call_backend(prompt)
        payload_model = payload.get("model", model)
        return {
            "id": "chatcmpl-unsafe",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": payload_model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": out},
                    "finish_reason": "stop",
                }
            ],
        }

    @guarded_app.post("/v1/chat/completions")
    def guarded_chat(payload: dict[str, Any]) -> dict[str, Any]:
        prompt = prompt_from_messages(payload.get("messages", []))
        try:
            out = guarded_call(prompt)
        except SafetyViolation as e:
            # Return normal completion shape so garak keeps scanning.
            out = f"[AGENTSAFE_BLOCKED] {e}"
        payload_model = payload.get("model", model)
        return {
            "id": "chatcmpl-guarded",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": payload_model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": out},
                    "finish_reason": "stop",
                }
            ],
        }

    return unsafe_app, guarded_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Start unsafe + guarded local endpoints for garak")
    parser.add_argument("--unsafe-port", type=int, default=int(os.getenv("GARAK_UNSAFE_PORT", "8011")))
    parser.add_argument(
        "--guarded-port", type=int, default=int(os.getenv("GARAK_GUARDED_PORT", "8012"))
    )
    args = parser.parse_args()

    load_env_file()
    model = os.getenv("MODEL_NAME", "dolphin-mistral:7b")
    model_base_url = os.getenv("MODEL_BASE_URL", "http://localhost:11434/v1")
    model_api_key = os.getenv("MODEL_API_KEY", os.getenv("OPENAI_API_KEY", "ollama"))
    nvidia_api_key = os.getenv("NVIDIA_API_KEY")
    if not nvidia_api_key:
        raise RuntimeError("NVIDIA_API_KEY required for guarded server")

    unsafe_app, guarded_app = build_apps(model, model_base_url, model_api_key, nvidia_api_key)
    unsafe_server, _ = start_server(unsafe_app, args.unsafe_port)
    guarded_server, _ = start_server(guarded_app, args.guarded_port)

    print(f"Backend model: {model} @ {model_base_url}")
    print(f"Unsafe endpoint:  http://127.0.0.1:{args.unsafe_port}/v1")
    print(f"Guarded endpoint: http://127.0.0.1:{args.guarded_port}/v1")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        unsafe_server.should_exit = True
        guarded_server.should_exit = True


if __name__ == "__main__":
    main()
