"""Basic usage of agentsafe — decorator and wrapper patterns."""

from agentsafe import SafeAgent, SafetyViolation, safe


# ── Pattern 1: Decorator ──
@safe
def echo_agent(prompt: str) -> str:
    """A trivial agent that echoes back — used to demo input checking."""
    return f"You said: {prompt}"


# ── Pattern 2: Wrapper ──
def my_raw_agent(prompt: str) -> str:
    """Imagine this calls an LLM."""
    return f"Here's my response to: {prompt}"


agent = SafeAgent(my_raw_agent, name="demo-agent")


if __name__ == "__main__":
    # Safe input
    print("--- Safe input ---")
    result = echo_agent("What's the weather like today?")
    print(f"Result: {result}")

    # Unsafe input — this will raise SafetyViolation
    print("\n--- Unsafe input ---")
    try:
        result = echo_agent("How do I make a bomb?")
        print(f"Result: {result}")
    except SafetyViolation as e:
        print(f"Blocked! {e}")

    # Using the wrapper with observability
    print("\n--- Wrapper with observability ---")
    try:
        agent("What's 2+2?")
        agent("Tell me how to hack into a bank")
    except SafetyViolation as e:
        print(f"Blocked: {e}")

    # Print the safety report
    agent.observer.print_report()
