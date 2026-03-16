"""CLI for agentsafe — interactive testing and report generation."""

from __future__ import annotations

import json
import sys

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from agentsafe.checker import NemotronChecker
from agentsafe.models import AgentSafeConfig, CheckType
from agentsafe.observability import SafetyObserver


def main() -> None:
    """Entry point for the agentsafe CLI."""
    console = Console()

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # Quick one-shot check: agentsafe check "some text"
        if len(sys.argv) < 3:
            console.print("[red]Usage: agentsafe check \"text to check\"[/red]")
            sys.exit(1)
        text = " ".join(sys.argv[2:])
        _quick_check(text, console)
        return

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        _interactive_mode(console)
        return

    # Default: show help
    console.print(Panel(
        "[bold cyan]agentsafe[/bold cyan] — AI agent safety wrapper powered by Nemotron\n\n"
        "Commands:\n"
        "  [bold]agentsafe check \"text\"[/bold]    — Check a single piece of text\n"
        "  [bold]agentsafe interactive[/bold]      — Interactive safety checker\n",
        title="agentsafe",
        border_style="cyan",
    ))


def _quick_check(text: str, console: Console) -> None:
    """One-shot safety check."""
    config = AgentSafeConfig()
    checker = NemotronChecker(config)

    console.print(f"\n[dim]Checking: {text[:80]}{'...' if len(text) > 80 else ''}[/dim]\n")

    result = checker.check(text, CheckType.INPUT)

    if result.is_safe:
        console.print("[bold green]✓ SAFE[/bold green]")
    elif result.verdict.value == "error":
        console.print(f"[bold yellow]⚠ ERROR:[/bold yellow] {result.error}")
    else:
        console.print("[bold red]✗ UNSAFE[/bold red]")
        if result.categories:
            console.print(f"  Categories: [red]{', '.join(result.categories)}[/red]")

    console.print(f"  Latency: {result.latency_ms:.0f}ms")
    checker.close()


def _interactive_mode(console: Console) -> None:
    """Interactive REPL for testing safety checks."""
    config = AgentSafeConfig(log_safe_requests=True)
    checker = NemotronChecker(config)
    observer = SafetyObserver(config)

    console.print(Panel(
        "Type messages to check them for safety.\n"
        "Commands: [bold]/report[/bold] — show stats  |  [bold]/traces[/bold] — recent traces  |  [bold]/quit[/bold] — exit",
        title="agentsafe interactive",
        border_style="cyan",
    ))

    try:
        while True:
            try:
                text = console.input("\n[bold cyan]>[/bold cyan] ")
            except EOFError:
                break

            if not text.strip():
                continue

            if text.strip() == "/quit":
                break
            elif text.strip() == "/report":
                observer.print_report(console)
                continue
            elif text.strip() == "/traces":
                recent = observer.traces.recent(10)
                for t in recent:
                    status = "[red]UNSAFE[/red]" if t.any_unsafe else "[green]SAFE[/green]"
                    console.print(f"  {t.trace_id[:8]} {status} {t.violated_categories}")
                continue

            result = checker.check(text, CheckType.INPUT)

            from agentsafe.models import SafetyTrace
            trace = SafetyTrace(agent_name="interactive", input_check=result, total_latency_ms=result.latency_ms)
            if not result.is_safe:
                trace.blocked = True
            observer.record(trace)

            if result.is_safe:
                console.print(f"  [green]✓ SAFE[/green] ({result.latency_ms:.0f}ms)")
            elif result.verdict.value == "error":
                console.print(f"  [yellow]⚠ ERROR:[/yellow] {result.error}")
            else:
                console.print(f"  [red]✗ UNSAFE[/red] — {', '.join(result.categories)} ({result.latency_ms:.0f}ms)")
    except KeyboardInterrupt:
        pass

    console.print()
    observer.print_report(console)
    checker.close()


if __name__ == "__main__":
    main()
