"""SafeAgent wrapper and decorators for adding safety to any agent."""

from __future__ import annotations

import functools
import time
from collections.abc import Iterable, Iterator
from typing import Any, Callable, TypeVar

from agentsafe.checker import NemotronChecker, ScopeChecker
from agentsafe.exceptions import SafetyViolation
from agentsafe.models import (
    AgentSafeConfig,
    CheckType,
    SafetyResult,
    SafetyTrace,
    SafetyVerdict,
)
from agentsafe.observability import SafetyObserver

F = TypeVar("F", bound=Callable[..., Any])


class SafeAgent:
    """Wraps any agent function or OpenAI-compatible client with safety checks.

    Usage with a function:
        agent = SafeAgent(my_agent_fn)
        result = agent("tell me something")  # checked before and after

    Usage with OpenAI client:
        from openai import OpenAI
        client = OpenAI(base_url="...", api_key="...")
        agent = SafeAgent.from_openai(client, model="nvidia/nemotron-3-nano")
        result = agent.chat("hello")

    Observability:
        agent = SafeAgent(fn)
        agent.observer.on_violation(lambda t, r: print(f"ALERT: {r.categories}"))
        agent.observer.print_report()
    """

    def __init__(
        self,
        fn: Callable[..., Any] | None = None,
        *,
        config: AgentSafeConfig | None = None,
        name: str = "default",
        observer: SafetyObserver | None = None,
    ):
        self.config = config or AgentSafeConfig()
        self.name = name
        self._fn = fn
        self._checker = NemotronChecker(self.config)
        self._scope_checker = ScopeChecker(self.config)
        self.observer = observer or SafetyObserver(self.config)

    def __call__(self, prompt: str, **kwargs: Any) -> str:
        """Run the wrapped function with safety checks."""
        if self._fn is None:
            raise ValueError("No agent function provided. Use SafeAgent(fn) or SafeAgent.from_openai(client).")
        return self.run(prompt, **kwargs)

    def run(self, prompt: str, **kwargs: Any) -> str:
        """Execute the agent with input/output safety checks."""
        trace = SafetyTrace(agent_name=self.name)
        start = time.perf_counter()

        # ── Intended-use scope check ──
        if self.config.check_scope and self.config.intended_use_prompt:
            with self.observer.span("safety_check_scope") as scope_span:
                scope_result = self._scope_checker.check(prompt, self.config.intended_use_prompt)
                trace.scope_check = scope_result
                self._annotate_safety_span(
                    scope_span,
                    check_type=CheckType.SCOPE,
                    result=scope_result,
                    blocked=False,
                    block_reason=None,
                    prompt=prompt,
                )

                if not scope_result.is_safe and scope_result.verdict != SafetyVerdict.ERROR:
                    trace.blocked = True
                    categories = ", ".join(scope_result.categories) if scope_result.categories else "OUT_OF_SCOPE"
                    trace.block_reason = f"Out of scope: {categories}"
                    self._annotate_safety_span(
                        scope_span,
                        check_type=CheckType.SCOPE,
                        result=scope_result,
                        blocked=True,
                        block_reason=trace.block_reason,
                        prompt=prompt,
                    )
                    trace.total_latency_ms = (time.perf_counter() - start) * 1000
                    self.observer.record(trace)
                    if self.config.block_on_unsafe:
                        raise SafetyViolation(
                            "Input blocked by intended-use scope check",
                            result=scope_result,
                            trace=trace,
                        )

                if scope_result.verdict == SafetyVerdict.ERROR and self.config.block_on_error:
                    trace.blocked = True
                    trace.block_reason = f"Scope check error: {scope_result.error}"
                    self._annotate_safety_span(
                        scope_span,
                        check_type=CheckType.SCOPE,
                        result=scope_result,
                        blocked=True,
                        block_reason=trace.block_reason,
                        prompt=prompt,
                    )
                    trace.total_latency_ms = (time.perf_counter() - start) * 1000
                    self.observer.record(trace)
                    raise SafetyViolation(
                        f"Scope check failed: {scope_result.error}",
                        result=scope_result,
                        trace=trace,
                    )

        # ── Input check ──
        if self.config.check_input:
            with self.observer.span("safety_check_input") as input_span:
                input_result = self._checker.check(prompt, CheckType.INPUT)
                trace.input_check = input_result
                self._annotate_safety_span(
                    input_span,
                    check_type=CheckType.INPUT,
                    result=input_result,
                    blocked=False,
                    block_reason=None,
                    prompt=prompt,
                )

                if not input_result.is_safe and input_result.verdict != SafetyVerdict.ERROR:
                    trace.blocked = True
                    trace.block_reason = f"Unsafe input: {', '.join(input_result.categories)}"
                    self._annotate_safety_span(
                        input_span,
                        check_type=CheckType.INPUT,
                        result=input_result,
                        blocked=True,
                        block_reason=trace.block_reason,
                        prompt=prompt,
                    )
                    trace.total_latency_ms = (time.perf_counter() - start) * 1000
                    self.observer.record(trace)

                    if self.config.block_on_unsafe:
                        raise SafetyViolation(
                            f"Input blocked by safety check",
                            result=input_result,
                            trace=trace,
                        )

                if input_result.verdict == SafetyVerdict.ERROR and self.config.block_on_error:
                    trace.blocked = True
                    trace.block_reason = f"Safety check error: {input_result.error}"
                    self._annotate_safety_span(
                        input_span,
                        check_type=CheckType.INPUT,
                        result=input_result,
                        blocked=True,
                        block_reason=trace.block_reason,
                        prompt=prompt,
                    )
                    trace.total_latency_ms = (time.perf_counter() - start) * 1000
                    self.observer.record(trace)
                    raise SafetyViolation(
                        f"Safety check failed: {input_result.error}",
                        result=input_result,
                        trace=trace,
                    )

        # ── Run the agent ──
        if self._fn is None:
            raise ValueError("No agent function set")
        response = self._fn(prompt, **kwargs)

        # ── Output check ──
        if self.config.check_output and isinstance(response, str):
            with self.observer.span("safety_check_output") as output_span:
                output_result = self._checker.check(response, CheckType.OUTPUT)
                trace.output_check = output_result
                self._annotate_safety_span(
                    output_span,
                    check_type=CheckType.OUTPUT,
                    result=output_result,
                    blocked=False,
                    block_reason=None,
                    prompt=prompt,
                    response=response,
                )

                if not output_result.is_safe and output_result.verdict != SafetyVerdict.ERROR:
                    trace.blocked = True
                    trace.block_reason = f"Unsafe output: {', '.join(output_result.categories)}"
                    self._annotate_safety_span(
                        output_span,
                        check_type=CheckType.OUTPUT,
                        result=output_result,
                        blocked=True,
                        block_reason=trace.block_reason,
                        prompt=prompt,
                        response=response,
                    )
                    trace.total_latency_ms = (time.perf_counter() - start) * 1000
                    self.observer.record(trace)

                    if self.config.block_on_unsafe:
                        raise SafetyViolation(
                            f"Output blocked by safety check",
                            result=output_result,
                            trace=trace,
                        )

        trace.total_latency_ms = (time.perf_counter() - start) * 1000
        self.observer.record(trace)
        return response

    def run_stream(self, prompt: str, *args: Any, chunk_size: int = 120, **kwargs: Any) -> Iterator[str]:
        """Execute the agent with safety checks and stream output chunks.

        Strict semantics:
        - Run scope/input checks first.
        - Collect full model output.
        - Run output safety check on full output.
        - Yield chunks only after output passes policy checks.
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        trace = SafetyTrace(agent_name=self.name)
        start = time.perf_counter()

        # ── Intended-use scope check ──
        if self.config.check_scope and self.config.intended_use_prompt:
            with self.observer.span("safety_check_scope") as scope_span:
                scope_result = self._scope_checker.check(prompt, self.config.intended_use_prompt)
                trace.scope_check = scope_result
                self._annotate_safety_span(
                    scope_span,
                    check_type=CheckType.SCOPE,
                    result=scope_result,
                    blocked=False,
                    block_reason=None,
                    prompt=prompt,
                )

                if not scope_result.is_safe and scope_result.verdict != SafetyVerdict.ERROR:
                    trace.blocked = True
                    categories = ", ".join(scope_result.categories) if scope_result.categories else "OUT_OF_SCOPE"
                    trace.block_reason = f"Out of scope: {categories}"
                    self._annotate_safety_span(
                        scope_span,
                        check_type=CheckType.SCOPE,
                        result=scope_result,
                        blocked=True,
                        block_reason=trace.block_reason,
                        prompt=prompt,
                    )
                    trace.total_latency_ms = (time.perf_counter() - start) * 1000
                    self.observer.record(trace)
                    if self.config.block_on_unsafe:
                        raise SafetyViolation(
                            "Input blocked by intended-use scope check",
                            result=scope_result,
                            trace=trace,
                        )

                if scope_result.verdict == SafetyVerdict.ERROR and self.config.block_on_error:
                    trace.blocked = True
                    trace.block_reason = f"Scope check error: {scope_result.error}"
                    self._annotate_safety_span(
                        scope_span,
                        check_type=CheckType.SCOPE,
                        result=scope_result,
                        blocked=True,
                        block_reason=trace.block_reason,
                        prompt=prompt,
                    )
                    trace.total_latency_ms = (time.perf_counter() - start) * 1000
                    self.observer.record(trace)
                    raise SafetyViolation(
                        f"Scope check failed: {scope_result.error}",
                        result=scope_result,
                        trace=trace,
                    )

        # ── Input check ──
        if self.config.check_input:
            with self.observer.span("safety_check_input") as input_span:
                input_result = self._checker.check(prompt, CheckType.INPUT)
                trace.input_check = input_result
                self._annotate_safety_span(
                    input_span,
                    check_type=CheckType.INPUT,
                    result=input_result,
                    blocked=False,
                    block_reason=None,
                    prompt=prompt,
                )

                if not input_result.is_safe and input_result.verdict != SafetyVerdict.ERROR:
                    trace.blocked = True
                    trace.block_reason = f"Unsafe input: {', '.join(input_result.categories)}"
                    self._annotate_safety_span(
                        input_span,
                        check_type=CheckType.INPUT,
                        result=input_result,
                        blocked=True,
                        block_reason=trace.block_reason,
                        prompt=prompt,
                    )
                    trace.total_latency_ms = (time.perf_counter() - start) * 1000
                    self.observer.record(trace)

                    if self.config.block_on_unsafe:
                        raise SafetyViolation(
                            f"Input blocked by safety check",
                            result=input_result,
                            trace=trace,
                        )

                if input_result.verdict == SafetyVerdict.ERROR and self.config.block_on_error:
                    trace.blocked = True
                    trace.block_reason = f"Safety check error: {input_result.error}"
                    self._annotate_safety_span(
                        input_span,
                        check_type=CheckType.INPUT,
                        result=input_result,
                        blocked=True,
                        block_reason=trace.block_reason,
                        prompt=prompt,
                    )
                    trace.total_latency_ms = (time.perf_counter() - start) * 1000
                    self.observer.record(trace)
                    raise SafetyViolation(
                        f"Safety check failed: {input_result.error}",
                        result=input_result,
                        trace=trace,
                    )

        # ── Run the agent and collect full output ──
        if self._fn is None:
            raise ValueError("No agent function set")

        raw_response = self._fn(prompt, *args, **kwargs)
        if isinstance(raw_response, str):
            full_response = raw_response
        elif isinstance(raw_response, Iterable):
            parts: list[str] = []
            for part in raw_response:
                if not isinstance(part, str):
                    raise TypeError(
                        f"Streaming agent must yield str chunks, got {type(part).__name__}"
                    )
                parts.append(part)
            full_response = "".join(parts)
        else:
            raise TypeError(
                "SafeAgent.run_stream expected wrapped function to return str or iterable[str], "
                f"got {type(raw_response).__name__}"
            )

        # ── Output check ──
        if self.config.check_output:
            with self.observer.span("safety_check_output") as output_span:
                output_result = self._checker.check(full_response, CheckType.OUTPUT)
                trace.output_check = output_result
                self._annotate_safety_span(
                    output_span,
                    check_type=CheckType.OUTPUT,
                    result=output_result,
                    blocked=False,
                    block_reason=None,
                    prompt=prompt,
                    response=full_response,
                )

                if not output_result.is_safe and output_result.verdict != SafetyVerdict.ERROR:
                    trace.blocked = True
                    trace.block_reason = f"Unsafe output: {', '.join(output_result.categories)}"
                    self._annotate_safety_span(
                        output_span,
                        check_type=CheckType.OUTPUT,
                        result=output_result,
                        blocked=True,
                        block_reason=trace.block_reason,
                        prompt=prompt,
                        response=full_response,
                    )
                    trace.total_latency_ms = (time.perf_counter() - start) * 1000
                    self.observer.record(trace)

                    if self.config.block_on_unsafe:
                        raise SafetyViolation(
                            f"Output blocked by safety check",
                            result=output_result,
                            trace=trace,
                        )

        trace.total_latency_ms = (time.perf_counter() - start) * 1000
        self.observer.record(trace)
        for i in range(0, len(full_response), chunk_size):
            yield full_response[i : i + chunk_size]

    def _annotate_safety_span(
        self,
        span: Any,
        *,
        check_type: CheckType,
        result: SafetyResult,
        blocked: bool,
        block_reason: str | None,
        prompt: str | None = None,
        response: str | None = None,
    ) -> None:
        """Attach safety metadata to OTEL spans for Jaeger inspection."""
        attrs: dict[str, Any] = {
            "agentsafe.agent_name": self.name,
            "agentsafe.check_type": check_type.value,
            "agentsafe.verdict": result.verdict.value,
            "agentsafe.blocked": blocked,
            "agentsafe.latency_ms": round(result.latency_ms, 1),
        }
        if block_reason:
            attrs["agentsafe.block_reason"] = block_reason
        if result.error:
            attrs["agentsafe.error"] = result.error
        if self.config.otel_include_categories and result.categories:
            attrs["agentsafe.categories"] = self.observer.serialize_otel_categories(result.categories)

        if self.config.otel_include_content:
            if prompt:
                attrs["agentsafe.prompt_snippet"] = self.observer.sanitize_otel_text(
                    prompt, max_chars=self.config.otel_content_max_chars
                )
            if response:
                attrs["agentsafe.response_snippet"] = self.observer.sanitize_otel_text(
                    response, max_chars=self.config.otel_content_max_chars
                )
            if result.content_snippet:
                attrs["agentsafe.checked_snippet"] = self.observer.sanitize_otel_text(
                    result.content_snippet, max_chars=self.config.otel_content_max_chars
                )

        self.observer.set_span_attributes(span, attrs)

    def check_tool_call(self, tool_name: str, tool_args: dict[str, Any]) -> None:
        """Manually check a tool call before executing it.

        Usage:
            agent.check_tool_call("run_sql", {"query": "DROP TABLE users"})
        """
        content = f"Tool: {tool_name}\nArguments: {tool_args}"
        result = self._checker.check(content, CheckType.TOOL_CALL)
        if not result.is_safe and self.config.block_on_unsafe:
            raise SafetyViolation(
                f"Tool call '{tool_name}' blocked by safety check",
                result=result,
            )

    @classmethod
    def from_openai(
        cls,
        client: Any,
        *,
        model: str = "nvidia/llama-3.1-8b-instruct",
        config: AgentSafeConfig | None = None,
        name: str = "openai-agent",
    ) -> SafeAgent:
        """Create a SafeAgent from an OpenAI-compatible client."""

        def agent_fn(prompt: str, **kwargs: Any) -> str:
            messages = kwargs.pop("messages", None) or [{"role": "user", "content": prompt}]
            resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
            return resp.choices[0].message.content or ""

        return cls(agent_fn, config=config, name=name)

    def close(self) -> None:
        self._checker.close()
        self._scope_checker.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def safe(
    fn: F | None = None,
    *,
    config: AgentSafeConfig | None = None,
    name: str | None = None,
    observer: SafetyObserver | None = None,
) -> F | Callable[[F], F]:
    """Decorator to add safety checks to any function that takes a string and returns a string.

    Usage:
        @safe
        def my_agent(prompt: str) -> str:
            return call_llm(prompt)

        @safe(config=AgentSafeConfig(block_on_unsafe=False))
        def my_agent(prompt: str) -> str:
            return call_llm(prompt)
    """

    def decorator(func: F) -> F:
        agent_name = name or func.__name__
        agent = SafeAgent(func, config=config, name=agent_name, observer=observer)

        @functools.wraps(func)
        def wrapper(prompt: str, *args: Any, **kwargs: Any) -> str:
            return agent.run(prompt, *args, **kwargs)

        # Attach observer for access
        wrapper.observer = agent.observer  # type: ignore[attr-defined]
        wrapper.agent = agent  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    if fn is not None:
        return decorator(fn)
    return decorator


def safe_stream(
    fn: F | None = None,
    *,
    config: AgentSafeConfig | None = None,
    name: str | None = None,
    observer: SafetyObserver | None = None,
) -> F | Callable[[F], F]:
    """Decorator to add safety checks to streaming functions.

    The wrapped function may return either:
    - `str` (treated as a single completed response), or
    - `Iterable[str]` (collected first, then safety-checked, then streamed).
    """

    def decorator(func: F) -> F:
        agent_name = name or func.__name__
        agent = SafeAgent(func, config=config, name=agent_name, observer=observer)

        @functools.wraps(func)
        def wrapper(prompt: str, *args: Any, **kwargs: Any) -> Iterator[str]:
            chunk_size = kwargs.pop("chunk_size", 120)
            return agent.run_stream(prompt, *args, chunk_size=chunk_size, **kwargs)

        wrapper.observer = agent.observer  # type: ignore[attr-defined]
        wrapper.agent = agent  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    if fn is not None:
        return decorator(fn)
    return decorator
