"""Observability for agentsafe — traces, metrics, structured logs, and OTEL export."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable

from rich.console import Console
from rich.table import Table
from rich.text import Text

from agentsafe.models import (
    AgentSafeConfig,
    CheckType,
    SafetyResult,
    SafetyTrace,
    SafetyVerdict,
)

logger = logging.getLogger("agentsafe")


# ──────────────────────────────────────────────
# Metrics — lightweight, no external deps needed
# ──────────────────────────────────────────────


@dataclass
class SafetyMetrics:
    """Aggregated safety metrics with thread-safe counters."""

    _lock: Lock = field(default_factory=Lock, repr=False)

    total_checks: int = 0
    safe_count: int = 0
    unsafe_count: int = 0
    error_count: int = 0
    blocked_count: int = 0

    # Per-category violation counts
    category_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Per-check-type counts
    check_type_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Latency tracking
    _latencies: list[float] = field(default_factory=list, repr=False)

    def record_check(self, result: SafetyResult) -> None:
        with self._lock:
            self.total_checks += 1
            self.check_type_counts[result.check_type.value] += 1
            self._latencies.append(result.latency_ms)

            if result.verdict == SafetyVerdict.SAFE:
                self.safe_count += 1
            elif result.verdict == SafetyVerdict.UNSAFE:
                self.unsafe_count += 1
                for cat in result.categories:
                    self.category_counts[cat] += 1
            else:
                self.error_count += 1

    def record_block(self) -> None:
        with self._lock:
            self.blocked_count += 1

    @property
    def avg_latency_ms(self) -> float:
        if not self._latencies:
            return 0.0
        return sum(self._latencies) / len(self._latencies)

    @property
    def p99_latency_ms(self) -> float:
        if not self._latencies:
            return 0.0
        sorted_l = sorted(self._latencies)
        idx = int(len(sorted_l) * 0.99)
        return sorted_l[min(idx, len(sorted_l) - 1)]

    @property
    def unsafe_rate(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return self.unsafe_count / self.total_checks

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_checks": self.total_checks,
            "safe": self.safe_count,
            "unsafe": self.unsafe_count,
            "errors": self.error_count,
            "blocked": self.blocked_count,
            "unsafe_rate": round(self.unsafe_rate, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "p99_latency_ms": round(self.p99_latency_ms, 1),
            "top_categories": dict(
                sorted(self.category_counts.items(), key=lambda x: -x[1])[:10]
            ),
            "checks_by_type": dict(self.check_type_counts),
        }


# ──────────────────────────────────────────────
# Trace Store — in-memory ring buffer of traces
# ──────────────────────────────────────────────


class TraceStore:
    """Thread-safe in-memory store for safety traces."""

    def __init__(self, max_size: int = 10000):
        self._traces: deque[SafetyTrace] = deque(maxlen=max_size)
        self._lock = Lock()

    def add(self, trace: SafetyTrace) -> None:
        with self._lock:
            self._traces.append(trace)

    def recent(self, n: int = 50) -> list[SafetyTrace]:
        with self._lock:
            items = list(self._traces)
        return items[-n:]

    def unsafe_traces(self, n: int = 50) -> list[SafetyTrace]:
        with self._lock:
            items = [t for t in self._traces if t.any_unsafe]
        return items[-n:]

    def search(
        self,
        category: str | None = None,
        agent_name: str | None = None,
        blocked_only: bool = False,
    ) -> list[SafetyTrace]:
        with self._lock:
            results = list(self._traces)
        if category:
            results = [t for t in results if category in t.violated_categories]
        if agent_name:
            results = [t for t in results if t.agent_name == agent_name]
        if blocked_only:
            results = [t for t in results if t.blocked]
        return results

    def __len__(self) -> int:
        return len(self._traces)

    def export_jsonl(self) -> str:
        """Export all traces as JSON Lines."""
        with self._lock:
            items = list(self._traces)
        return "\n".join(t.model_dump_json() for t in items)


# ──────────────────────────────────────────────
# Callbacks — hook system for custom integrations
# ──────────────────────────────────────────────

OnTraceCallback = Callable[[SafetyTrace], None]
OnViolationCallback = Callable[[SafetyTrace, SafetyResult], None]


# ──────────────────────────────────────────────
# Observer — the main observability hub
# ──────────────────────────────────────────────


class SafetyObserver:
    """Central observability hub — collects traces, computes metrics, dispatches callbacks.

    Usage:
        observer = SafetyObserver()
        observer.on_violation(lambda trace, result: send_alert(result))

        # After each agent interaction:
        observer.record(trace)

        # Get metrics:
        print(observer.metrics.to_dict())

        # Get recent violations:
        for t in observer.traces.unsafe_traces(10):
            print(t.trace_id, t.violated_categories)
    """

    def __init__(self, config: AgentSafeConfig | None = None):
        self.config = config or AgentSafeConfig()
        self.metrics = SafetyMetrics()
        self.traces = TraceStore(max_size=self.config.trace_store_max)

        self._on_trace_callbacks: list[OnTraceCallback] = []
        self._on_violation_callbacks: list[OnViolationCallback] = []

        # Set up structured logging
        if self.config.enable_logging:
            self._setup_logging()

        # Set up OpenTelemetry if requested
        self._tracer = None
        self._meter = None
        if self.config.enable_otel:
            self._setup_otel()

    def _setup_logging(self) -> None:
        """Configure structured JSON logging."""
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(_JsonFormatter())
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

    def _setup_otel(self) -> None:
        """Set up OpenTelemetry tracing and metrics (optional dependency)."""
        try:
            from opentelemetry import metrics, trace
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                OTLPMetricExporter as OtlpGrpcMetricExporter,
            )
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter as OtlpGrpcSpanExporter,
            )
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
                OTLPMetricExporter as OtlpHttpMetricExporter,
            )
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter as OtlpHttpSpanExporter,
            )
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            service_name, protocol, endpoint, insecure = self._resolve_otel_config()
            resource = Resource.create({"service.name": service_name})

            # Build exporters for the chosen local-first OTLP protocol.
            if protocol == "grpc":
                span_exporter = OtlpGrpcSpanExporter(endpoint=endpoint, insecure=insecure)
                metric_exporter = OtlpGrpcMetricExporter(endpoint=endpoint, insecure=insecure)
            else:
                span_exporter = OtlpHttpSpanExporter(
                    endpoint=self._build_http_otlp_endpoint(endpoint, "traces")
                )
                metric_exporter = OtlpHttpMetricExporter(
                    endpoint=self._build_http_otlp_endpoint(endpoint, "metrics")
                )

            # Tracing
            if not isinstance(trace.get_tracer_provider(), TracerProvider):
                tracer_provider = TracerProvider(resource=resource)
                tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
                trace.set_tracer_provider(tracer_provider)
            self._tracer = trace.get_tracer("agentsafe")

            # Metrics
            if not isinstance(metrics.get_meter_provider(), MeterProvider):
                metric_reader = PeriodicExportingMetricReader(metric_exporter)
                metrics.set_meter_provider(
                    MeterProvider(resource=resource, metric_readers=[metric_reader])
                )
            self._meter = metrics.get_meter("agentsafe")

            # Create OTEL counters
            self._otel_checks = self._meter.create_counter(
                "agentsafe.checks.total",
                description="Total safety checks performed",
            )
            self._otel_unsafe = self._meter.create_counter(
                "agentsafe.checks.unsafe",
                description="Unsafe content detected",
            )
            self._otel_blocked = self._meter.create_counter(
                "agentsafe.blocks.total",
                description="Requests blocked by safety",
            )
            self._otel_latency = self._meter.create_histogram(
                "agentsafe.check.latency_ms",
                description="Safety check latency in milliseconds",
            )
            logger.info(
                "OpenTelemetry initialized for agentsafe protocol=%s endpoint=%s service=%s",
                protocol,
                endpoint,
                service_name,
            )
        except ImportError:
            logger.warning(
                "OpenTelemetry not installed. Run: uv add agentsafe[otel]"
            )
        except Exception as e:
            logger.warning("OpenTelemetry setup failed: %s", e)

    def _resolve_otel_config(self) -> tuple[str, str, str, bool]:
        """Resolve OTEL settings from config with environment fallbacks."""
        service_name = getattr(self.config, "otel_service_name", "agentsafe")
        protocol = getattr(self.config, "otel_exporter_protocol", "http/protobuf")
        endpoint = getattr(self.config, "otel_exporter_endpoint", None) or os.environ.get(
            "OTEL_EXPORTER_OTLP_ENDPOINT"
        )
        insecure = bool(getattr(self.config, "otel_exporter_insecure", True))

        if not endpoint:
            endpoint = "localhost:4317" if protocol == "grpc" else "http://localhost:4318"
        return service_name, protocol, endpoint, insecure

    @staticmethod
    def _build_http_otlp_endpoint(base_endpoint: str, signal: str) -> str:
        """Normalize HTTP OTLP endpoint for a given signal path."""
        endpoint = base_endpoint.rstrip("/")
        if endpoint.endswith("/v1/traces") or endpoint.endswith("/v1/metrics"):
            return endpoint
        return f"{endpoint}/v1/{signal}"

    def sanitize_otel_text(self, value: str, *, max_chars: int | None = None) -> str:
        """Normalize and truncate text before adding to span attributes."""
        cleaned = value.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        limit = max_chars if max_chars is not None else self.config.otel_content_max_chars
        if limit > 0 and len(cleaned) > limit:
            return f"{cleaned[:limit]}..."
        return cleaned

    @staticmethod
    def serialize_otel_categories(categories: list[str]) -> str:
        """Serialize category lists into a compact attribute string."""
        return ", ".join(c for c in categories if c)

    def set_span_attributes(self, span: Any, attrs: dict[str, Any]) -> None:
        """Set span attributes safely without propagating OTEL errors."""
        if not span:
            return
        for key, value in attrs.items():
            if value is None:
                continue
            try:
                span.set_attribute(key, value)
            except Exception:
                # Never break request flow due to observability attribute issues.
                continue

    # ── Callback registration ──

    def on_trace(self, callback: OnTraceCallback) -> None:
        """Register a callback for every trace (safe or unsafe)."""
        self._on_trace_callbacks.append(callback)

    def on_violation(self, callback: OnViolationCallback) -> None:
        """Register a callback for unsafe detections."""
        self._on_violation_callbacks.append(callback)

    # ── Recording ──

    def record(self, trace: SafetyTrace) -> None:
        """Record a completed trace — updates metrics, store, and fires callbacks."""
        self.traces.add(trace)

        for check in trace.all_checks:
            self.metrics.record_check(check)

            # OTEL metrics
            if self._meter:
                self._otel_checks.add(1, {"check_type": check.check_type.value})
                self._otel_latency.record(check.latency_ms, {"check_type": check.check_type.value})
                if check.verdict == SafetyVerdict.UNSAFE:
                    self._otel_unsafe.add(1, {"check_type": check.check_type.value})

        if trace.blocked:
            self.metrics.record_block()
            if self._meter:
                self._otel_blocked.add(1)

        # Structured log
        if self.config.enable_logging:
            if trace.any_unsafe or self.config.log_safe_requests:
                self._log_trace(trace)

        # Fire callbacks
        for cb in self._on_trace_callbacks:
            try:
                cb(trace)
            except Exception as e:
                logger.error(f"Trace callback error: {e}")

        if trace.any_unsafe:
            for check in trace.all_checks:
                if check.verdict == SafetyVerdict.UNSAFE:
                    for cb in self._on_violation_callbacks:
                        try:
                            cb(trace, check)
                        except Exception as e:
                            logger.error(f"Violation callback error: {e}")

    def _log_trace(self, trace: SafetyTrace) -> None:
        """Emit structured log for a trace."""
        level = logging.WARNING if trace.any_unsafe else logging.INFO
        logger.log(
            level,
            "safety_check",
            extra={
                "trace_id": trace.trace_id,
                "agent": trace.agent_name,
                "blocked": trace.blocked,
                "unsafe": trace.any_unsafe,
                "categories": trace.violated_categories,
                "latency_ms": round(trace.total_latency_ms, 1),
                "checks": len(trace.all_checks),
            },
        )

    # ── OTEL span context manager ──

    def span(self, name: str = "safety_check") -> Any:
        """Create an OTEL span for a safety check. Returns a context manager."""
        if self._tracer:
            return self._tracer.start_as_current_span(name)
        return _NoOpSpan()

    # ── Reporting ──

    def print_report(self, console: Console | None = None) -> None:
        """Print a rich summary report to the terminal."""
        console = console or Console()
        m = self.metrics

        # Header
        console.print()
        console.print("[bold cyan]═══ agentsafe Safety Report ═══[/bold cyan]")
        console.print()

        # Summary table
        summary = Table(title="Summary", show_header=False, border_style="dim")
        summary.add_column("Metric", style="bold")
        summary.add_column("Value", justify="right")
        summary.add_row("Total Checks", str(m.total_checks))
        summary.add_row("Safe", f"[green]{m.safe_count}[/green]")
        summary.add_row("Unsafe", f"[red]{m.unsafe_count}[/red]")
        summary.add_row("Errors", f"[yellow]{m.error_count}[/yellow]")
        summary.add_row("Blocked", f"[red bold]{m.blocked_count}[/red bold]")
        summary.add_row("Unsafe Rate", f"{m.unsafe_rate:.1%}")
        summary.add_row("Avg Latency", f"{m.avg_latency_ms:.0f}ms")
        summary.add_row("P99 Latency", f"{m.p99_latency_ms:.0f}ms")
        console.print(summary)

        # Category breakdown
        if m.category_counts:
            console.print()
            cat_table = Table(title="Top Violated Categories", border_style="dim")
            cat_table.add_column("Category", style="bold")
            cat_table.add_column("Count", justify="right", style="red")
            for cat, count in sorted(m.category_counts.items(), key=lambda x: -x[1])[:10]:
                cat_table.add_row(cat, str(count))
            console.print(cat_table)

        # Recent violations
        recent_unsafe = self.traces.unsafe_traces(5)
        if recent_unsafe:
            console.print()
            viol_table = Table(title="Recent Violations", border_style="dim")
            viol_table.add_column("Trace ID", style="dim")
            viol_table.add_column("Agent")
            viol_table.add_column("Categories", style="red")
            viol_table.add_column("Blocked")
            viol_table.add_column("Snippet", max_width=40)
            for t in recent_unsafe[-5:]:
                snippet = ""
                for c in t.all_checks:
                    if c.content_snippet:
                        snippet = c.content_snippet[:40]
                        break
                viol_table.add_row(
                    t.trace_id[:8],
                    t.agent_name,
                    ", ".join(t.violated_categories)[:50],
                    "🚫" if t.blocked else "⚠️",
                    snippet,
                )
            console.print(viol_table)

        console.print()


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────


class _NoOpSpan:
    """No-op context manager when OTEL is not installed."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set_attribute(self, key: str, value: Any) -> None:
        pass


class _JsonFormatter(logging.Formatter):
    """Structured JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Add extra fields
        for key in ("trace_id", "agent", "blocked", "unsafe", "categories", "latency_ms", "checks"):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)
        return json.dumps(log_data)
