"""Tests for agentsafe core functionality."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agentsafe import (
    AgentSafeConfig,
    CheckType,
    SafeAgent,
    SafetyObserver,
    SafetyResult,
    SafetyTrace,
    SafetyVerdict,
    SafetyViolation,
    safe,
    safe_stream,
)
from agentsafe.checker import ScopeChecker, _build_prompt, _parse_response


# ── Unit tests for prompt building ──


def test_build_input_prompt():
    prompt = _build_prompt("hello world", CheckType.INPUT)
    assert "user: hello world" in prompt
    assert "user" in prompt


def test_build_output_prompt():
    prompt = _build_prompt("response text", CheckType.OUTPUT, response="response text")
    assert "agent:" in prompt


def test_parse_safe_response():
    raw = '{"User Safety": "safe"}'
    parsed = _parse_response(raw)
    assert parsed["User Safety"] == "safe"


def test_parse_unsafe_response():
    raw = '{"User Safety": "unsafe", "Safety Categories": "S1: Violence, S3: Criminal Planning"}'
    parsed = _parse_response(raw)
    assert parsed["User Safety"] == "unsafe"
    assert "S1: Violence" in parsed["Safety Categories"]


def test_parse_markdown_wrapped():
    raw = '```json\n{"User Safety": "safe"}\n```'
    parsed = _parse_response(raw)
    assert parsed["User Safety"] == "safe"


def test_scope_checker_marks_in_scope_safe():
    config = AgentSafeConfig(scope_api_key="test-key")
    checker = ScopeChecker(config)

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"Scope": "in_scope", "Reason": "domain aligned"}'}}]
    }
    checker._client = MagicMock()
    checker._client.post.return_value = mock_resp

    result = checker.check(
        content="Where can I get spicy chicken near SJSU?",
        intended_use_prompt="SJSU chicken restaurant assistant",
    )
    assert result.check_type == CheckType.SCOPE
    assert result.verdict == SafetyVerdict.SAFE
    assert result.categories == []


def test_scope_checker_marks_out_of_scope_unsafe():
    config = AgentSafeConfig(scope_api_key="test-key")
    checker = ScopeChecker(config)

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"Scope": "out_of_scope", "Reason": "homework request"}'}}]
    }
    checker._client = MagicMock()
    checker._client.post.return_value = mock_resp

    result = checker.check(
        content="Do my calculus homework",
        intended_use_prompt="SJSU chicken restaurant assistant",
    )
    assert result.check_type == CheckType.SCOPE
    assert result.verdict == SafetyVerdict.UNSAFE
    assert result.categories == ["OUT_OF_SCOPE"]


# ── Tests for SafetyResult ──


def test_safety_result_is_safe():
    result = SafetyResult(verdict=SafetyVerdict.SAFE, check_type=CheckType.INPUT)
    assert result.is_safe


def test_safety_result_is_unsafe():
    result = SafetyResult(
        verdict=SafetyVerdict.UNSAFE,
        check_type=CheckType.INPUT,
        categories=["S1: Violence"],
    )
    assert not result.is_safe


# ── Tests for SafetyTrace ──


def test_trace_any_unsafe():
    trace = SafetyTrace(
        input_check=SafetyResult(
            verdict=SafetyVerdict.UNSAFE,
            check_type=CheckType.INPUT,
            categories=["S3: Criminal Planning"],
        )
    )
    assert trace.any_unsafe
    assert "S3: Criminal Planning" in trace.violated_categories


def test_trace_all_safe():
    trace = SafetyTrace(
        input_check=SafetyResult(verdict=SafetyVerdict.SAFE, check_type=CheckType.INPUT),
        output_check=SafetyResult(verdict=SafetyVerdict.SAFE, check_type=CheckType.OUTPUT),
    )
    assert not trace.any_unsafe


def test_trace_includes_scope_check():
    trace = SafetyTrace(
        scope_check=SafetyResult(verdict=SafetyVerdict.SAFE, check_type=CheckType.SCOPE),
        input_check=SafetyResult(verdict=SafetyVerdict.SAFE, check_type=CheckType.INPUT),
    )
    check_types = [c.check_type for c in trace.all_checks]
    assert CheckType.SCOPE in check_types


def test_scope_config_defaults_are_backward_compatible():
    config = AgentSafeConfig()
    assert config.check_scope is False
    assert config.intended_use_prompt is None
    assert isinstance(config.scope_model, str)
    assert isinstance(config.scope_base_url, str)
    assert config.scope_api_key is None


# ── Tests for SafetyObserver ──


def test_observer_metrics():
    config = AgentSafeConfig(enable_logging=False)
    observer = SafetyObserver(config)

    safe_result = SafetyResult(verdict=SafetyVerdict.SAFE, check_type=CheckType.INPUT, latency_ms=100)
    unsafe_result = SafetyResult(
        verdict=SafetyVerdict.UNSAFE,
        check_type=CheckType.INPUT,
        categories=["S1: Violence"],
        latency_ms=150,
    )

    trace1 = SafetyTrace(input_check=safe_result)
    trace2 = SafetyTrace(input_check=unsafe_result, blocked=True)

    observer.record(trace1)
    observer.record(trace2)

    assert observer.metrics.total_checks == 2
    assert observer.metrics.safe_count == 1
    assert observer.metrics.unsafe_count == 1
    assert observer.metrics.blocked_count == 1


def test_observer_violation_callback():
    config = AgentSafeConfig(enable_logging=False)
    observer = SafetyObserver(config)

    violations: list[tuple] = []
    observer.on_violation(lambda t, r: violations.append((t, r)))

    unsafe_result = SafetyResult(
        verdict=SafetyVerdict.UNSAFE,
        check_type=CheckType.INPUT,
        categories=["S17: Malware"],
    )
    trace = SafetyTrace(input_check=unsafe_result)
    observer.record(trace)

    assert len(violations) == 1
    assert violations[0][1].categories == ["S17: Malware"]


# ── Tests for SafeAgent (mocked checker) ──


def test_safe_agent_passes_safe_input():
    mock_checker = MagicMock()
    mock_checker.check.return_value = SafetyResult(
        verdict=SafetyVerdict.SAFE, check_type=CheckType.INPUT, latency_ms=50
    )

    def my_fn(prompt: str) -> str:
        return f"echo: {prompt}"

    config = AgentSafeConfig(enable_logging=False, check_output=False)
    agent = SafeAgent(my_fn, config=config, name="test")
    agent._checker = mock_checker

    result = agent("hello")
    assert result == "echo: hello"


def test_safe_agent_blocks_unsafe_input():
    mock_checker = MagicMock()
    mock_checker.check.return_value = SafetyResult(
        verdict=SafetyVerdict.UNSAFE,
        check_type=CheckType.INPUT,
        categories=["S3: Criminal Planning"],
        latency_ms=50,
    )

    def my_fn(prompt: str) -> str:
        return f"echo: {prompt}"

    config = AgentSafeConfig(enable_logging=False, block_on_unsafe=True)
    agent = SafeAgent(my_fn, config=config, name="test")
    agent._checker = mock_checker

    with pytest.raises(SafetyViolation) as exc_info:
        agent("bad stuff")

    assert "S3: Criminal Planning" in str(exc_info.value)


def test_safe_agent_blocks_out_of_scope_before_input_check():
    input_checker = MagicMock()
    input_checker.check.return_value = SafetyResult(
        verdict=SafetyVerdict.SAFE,
        check_type=CheckType.INPUT,
    )
    scope_checker = MagicMock()
    scope_checker.check.return_value = SafetyResult(
        verdict=SafetyVerdict.UNSAFE,
        check_type=CheckType.SCOPE,
        categories=["OUT_OF_SCOPE"],
    )
    called = {"fn": False}

    def my_fn(prompt: str) -> str:
        called["fn"] = True
        return f"echo: {prompt}"

    config = AgentSafeConfig(
        enable_logging=False,
        check_scope=True,
        intended_use_prompt="SJSU chicken restaurants assistant",
        block_on_unsafe=True,
        check_output=False,
    )
    agent = SafeAgent(my_fn, config=config, name="test")
    agent._checker = input_checker
    agent._scope_checker = scope_checker

    with pytest.raises(SafetyViolation):
        agent("Solve my calculus homework")

    input_checker.check.assert_not_called()
    assert called["fn"] is False


def test_safe_agent_runs_scope_then_input_for_in_scope_prompt():
    input_checker = MagicMock()
    input_checker.check.return_value = SafetyResult(
        verdict=SafetyVerdict.SAFE,
        check_type=CheckType.INPUT,
    )
    scope_checker = MagicMock()
    scope_checker.check.return_value = SafetyResult(
        verdict=SafetyVerdict.SAFE,
        check_type=CheckType.SCOPE,
    )

    def my_fn(prompt: str) -> str:
        return f"echo: {prompt}"

    config = AgentSafeConfig(
        enable_logging=False,
        check_scope=True,
        intended_use_prompt="SJSU chicken restaurants assistant",
        check_output=False,
    )
    agent = SafeAgent(my_fn, config=config, name="test")
    agent._checker = input_checker
    agent._scope_checker = scope_checker

    result = agent("Find me spicy wings near SJSU")
    assert result == "echo: Find me spicy wings near SJSU"
    scope_checker.check.assert_called_once()
    input_checker.check.assert_called_once()


def test_safe_agent_run_stream_emits_chunks_for_safe_output():
    mock_checker = MagicMock()

    def _check(content: str, check_type: CheckType):
        if check_type == CheckType.INPUT:
            return SafetyResult(verdict=SafetyVerdict.SAFE, check_type=CheckType.INPUT)
        if check_type == CheckType.OUTPUT:
            return SafetyResult(verdict=SafetyVerdict.SAFE, check_type=CheckType.OUTPUT)
        raise AssertionError(f"Unexpected check type: {check_type}")

    mock_checker.check.side_effect = _check

    def my_stream_fn(prompt: str):
        yield "hello "
        yield "world"

    config = AgentSafeConfig(enable_logging=False, check_output=True)
    agent = SafeAgent(my_stream_fn, config=config, name="stream-test")
    agent._checker = mock_checker

    chunks = list(agent.run_stream("hello", chunk_size=5))
    assert chunks == ["hello", " worl", "d"]
    assert "".join(chunks) == "hello world"
    assert mock_checker.check.call_count == 2


def test_safe_agent_run_stream_blocks_unsafe_output_before_yield():
    mock_checker = MagicMock()

    def _check(content: str, check_type: CheckType):
        if check_type == CheckType.INPUT:
            return SafetyResult(verdict=SafetyVerdict.SAFE, check_type=CheckType.INPUT)
        if check_type == CheckType.OUTPUT:
            return SafetyResult(
                verdict=SafetyVerdict.UNSAFE,
                check_type=CheckType.OUTPUT,
                categories=["S17: Malware"],
            )
        raise AssertionError(f"Unexpected check type: {check_type}")

    mock_checker.check.side_effect = _check

    def my_stream_fn(prompt: str):
        yield "unsafe payload"

    config = AgentSafeConfig(enable_logging=False, check_output=True, block_on_unsafe=True)
    agent = SafeAgent(my_stream_fn, config=config, name="stream-test")
    agent._checker = mock_checker

    with pytest.raises(SafetyViolation):
        list(agent.run_stream("hello"))


def test_safe_agent_run_stream_blocks_out_of_scope_before_input_check():
    input_checker = MagicMock()
    input_checker.check.return_value = SafetyResult(
        verdict=SafetyVerdict.SAFE,
        check_type=CheckType.INPUT,
    )
    scope_checker = MagicMock()
    scope_checker.check.return_value = SafetyResult(
        verdict=SafetyVerdict.UNSAFE,
        check_type=CheckType.SCOPE,
        categories=["OUT_OF_SCOPE"],
    )
    called = {"fn": False}

    def my_stream_fn(prompt: str):
        called["fn"] = True
        yield "should not run"

    config = AgentSafeConfig(
        enable_logging=False,
        check_scope=True,
        intended_use_prompt="SJSU chicken restaurants assistant",
        block_on_unsafe=True,
        check_output=True,
    )
    agent = SafeAgent(my_stream_fn, config=config, name="stream-test")
    agent._checker = input_checker
    agent._scope_checker = scope_checker

    with pytest.raises(SafetyViolation):
        list(agent.run_stream("Solve my calculus homework"))

    input_checker.check.assert_not_called()
    assert called["fn"] is False


def test_safe_agent_blocks_on_scope_error_when_configured():
    input_checker = MagicMock()
    scope_checker = MagicMock()
    scope_checker.check.return_value = SafetyResult(
        verdict=SafetyVerdict.ERROR,
        check_type=CheckType.SCOPE,
        error="scope classifier unavailable",
    )
    called = {"fn": False}

    def my_fn(prompt: str) -> str:
        called["fn"] = True
        return "ok"

    config = AgentSafeConfig(
        enable_logging=False,
        check_scope=True,
        intended_use_prompt="SJSU chicken restaurants assistant",
        block_on_error=True,
        check_output=False,
    )
    agent = SafeAgent(my_fn, config=config, name="test")
    agent._checker = input_checker
    agent._scope_checker = scope_checker

    with pytest.raises(SafetyViolation):
        agent("Find me chicken")

    input_checker.check.assert_not_called()
    assert called["fn"] is False


# ── Tests for @safe decorator ──


def test_safe_decorator():
    mock_checker = MagicMock()
    mock_checker.check.return_value = SafetyResult(
        verdict=SafetyVerdict.SAFE, check_type=CheckType.INPUT, latency_ms=50
    )

    @safe(config=AgentSafeConfig(enable_logging=False, check_output=False))
    def my_fn(prompt: str) -> str:
        return "ok"

    my_fn.agent._checker = mock_checker
    result = my_fn("hello")
    assert result == "ok"


def test_safe_stream_decorator():
    mock_checker = MagicMock()

    def _check(content: str, check_type: CheckType):
        if check_type == CheckType.INPUT:
            return SafetyResult(verdict=SafetyVerdict.SAFE, check_type=CheckType.INPUT)
        if check_type == CheckType.OUTPUT:
            return SafetyResult(verdict=SafetyVerdict.SAFE, check_type=CheckType.OUTPUT)
        raise AssertionError(f"Unexpected check type: {check_type}")

    mock_checker.check.side_effect = _check

    @safe_stream(config=AgentSafeConfig(enable_logging=False, check_output=True))
    def my_stream_fn(prompt: str):
        yield "ok"

    my_stream_fn.agent._checker = mock_checker
    result = "".join(my_stream_fn("hello"))
    assert result == "ok"


# ── Tests for TraceStore ──


def test_trace_store_search():
    config = AgentSafeConfig(enable_logging=False)
    observer = SafetyObserver(config)

    for i in range(5):
        trace = SafetyTrace(
            agent_name="agent-a" if i % 2 == 0 else "agent-b",
            input_check=SafetyResult(
                verdict=SafetyVerdict.UNSAFE if i == 3 else SafetyVerdict.SAFE,
                check_type=CheckType.INPUT,
                categories=["S1: Violence"] if i == 3 else [],
            ),
            blocked=i == 3,
        )
        observer.record(trace)

    assert len(observer.traces.search(agent_name="agent-a")) == 3
    assert len(observer.traces.search(blocked_only=True)) == 1


def test_trace_store_export():
    config = AgentSafeConfig(enable_logging=False)
    observer = SafetyObserver(config)

    trace = SafetyTrace(agent_name="test")
    observer.record(trace)

    jsonl = observer.traces.export_jsonl()
    parsed = json.loads(jsonl)
    assert parsed["agent_name"] == "test"
