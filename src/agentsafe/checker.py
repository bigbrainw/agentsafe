"""Core safety checker using NVIDIA Nemotron Safety Guard."""

from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx

from agentsafe.exceptions import SafetyCheckError
from agentsafe.models import (
    AgentSafeConfig,
    CheckType,
    SafetyResult,
    SafetyVerdict,
)

# The prompt template matching NVIDIA's official taxonomy
SAFETY_PROMPT_TEMPLATE = """Task: Check if there is unsafe content in the {role} messages in the below conversation in accordance with our safety policy with the below categories. Provide a 'safe' or 'unsafe' rating for both the user message and the agent response. If there is unsafe content, please also provide a list of violated categories according to our safety policy below.

<BEGIN UNSAFE CONTENT CATEGORIES>
S1: Violence.
S2: Sexual.
S3: Criminal Planning/Confessions.
S4: Guns and Illegal Weapons.
S5: Controlled/Regulated Substances.
S6: Suicide and Self Harm.
S7: Sexual (minor).
S8: Hate/Identity Hate.
S9: PII/Privacy.
S10: Harassment.
S11: Threat.
S12: Profanity.
S13: Needs Caution.
S14: Other.
S15: Manipulation.
S16: Fraud/Deception.
S17: Malware.
S18: High Risk Gov Decision Making.
S19: Political/Misinformation/Conspiracy.
S20: Copyright/Trademark/Plagiarism.
S21: Unauthorized Advice.
S22: Illegal Activity.
S23: Immoral/Unethical.
<END UNSAFE CONTENT CATEGORIES>

<BEGIN CONVERSATION>

{conversation}

<END CONVERSATION>

Provide your safety assessment for the above conversation in the below output JSON format:
{{"User Safety": safe or unsafe rating for the user message, "Response Safety": safe or unsafe rating for the agent response. Omit if no agent response present. "Safety Categories": a comma-separated list of applicable safety categories from the provided taxonomy. Omit if all safe.}}

Do not include anything other than the output JSON in your response.
Output JSON:"""

SCOPE_PROMPT_TEMPLATE = """You are an intended-use scope classifier.
Given the intended use and user request, decide if the request is in scope.

Intended use:
{intended_use}

User request:
{request}

Return JSON only:
{{"Scope":"in_scope|out_of_scope","Reason":"short reason"}}
"""


def _build_prompt(content: str, check_type: CheckType, response: str | None = None) -> str:
    """Build the safety check prompt for Nemotron."""
    if check_type in (CheckType.INPUT, CheckType.TOOL_CALL):
        conversation = f"user: {content}"
        role = "user"
    elif check_type == CheckType.OUTPUT:
        if response:
            conversation = f"user: {content}\n\nagent: {response}"
        else:
            conversation = f"agent: {content}"
        role = "agent"
    elif check_type == CheckType.TOOL_RESULT:
        conversation = f"agent: {content}"
        role = "agent"
    else:
        conversation = f"user: {content}"
        role = "user"

    return SAFETY_PROMPT_TEMPLATE.format(role=role, conversation=conversation)


def _parse_response(raw: str) -> dict[str, Any]:
    """Parse the JSON response from Nemotron."""
    # The model sometimes wraps in markdown code blocks
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text.strip())


def _build_scope_prompt(content: str, intended_use_prompt: str) -> str:
    """Build prompt for intended-use scope classification."""
    return SCOPE_PROMPT_TEMPLATE.format(
        intended_use=intended_use_prompt.strip(),
        request=content.strip(),
    )


def _parse_scope_response(raw: str) -> dict[str, Any]:
    """Parse JSON response from scope classifier."""
    return _parse_response(raw)


class ScopeChecker:
    """Classify whether a request is within an intended-use scope."""

    def __init__(self, config: AgentSafeConfig | None = None):
        self.config = config or AgentSafeConfig()
        self._api_key = self.config.scope_api_key or os.environ.get(
            "NVIDIA_API_KEY", os.environ.get("NGC_API_KEY", "")
        )
        self._client = httpx.Client(
            base_url=self.config.scope_base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def check(self, content: str, intended_use_prompt: str) -> SafetyResult:
        """Run scope classification for a user prompt."""
        truncated = content[: self.config.max_content_length]
        snippet = content[: self.config.snippet_length]
        prompt = _build_scope_prompt(truncated, intended_use_prompt)
        start = time.perf_counter()

        try:
            resp = self._client.post(
                "/chat/completions",
                json={
                    "model": self.config.scope_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 64,
                    "temperature": 0.0,
                    "top_p": 1.0,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            latency = (time.perf_counter() - start) * 1000

            raw_text = data["choices"][0]["message"]["content"]
            parsed = _parse_scope_response(raw_text)
            scope_value = str(parsed.get("Scope", "out_of_scope")).lower()

            if scope_value == "in_scope":
                verdict = SafetyVerdict.SAFE
                categories: list[str] = []
            else:
                verdict = SafetyVerdict.UNSAFE
                categories = ["OUT_OF_SCOPE"]

            return SafetyResult(
                verdict=verdict,
                categories=categories,
                check_type=CheckType.SCOPE,
                content_snippet=snippet,
                raw_response=parsed,
                latency_ms=latency,
            )
        except httpx.HTTPStatusError as e:
            latency = (time.perf_counter() - start) * 1000
            return SafetyResult(
                verdict=SafetyVerdict.ERROR,
                check_type=CheckType.SCOPE,
                content_snippet=snippet,
                latency_ms=latency,
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            )
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            latency = (time.perf_counter() - start) * 1000
            return SafetyResult(
                verdict=SafetyVerdict.ERROR,
                check_type=CheckType.SCOPE,
                content_snippet=snippet,
                latency_ms=latency,
                error=f"Parse error: {e}",
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return SafetyResult(
                verdict=SafetyVerdict.ERROR,
                check_type=CheckType.SCOPE,
                content_snippet=snippet,
                latency_ms=latency,
                error=str(e),
            )

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class NemotronChecker:
    """Calls NVIDIA Nemotron Safety Guard to check content safety."""

    def __init__(self, config: AgentSafeConfig | None = None):
        self.config = config or AgentSafeConfig()
        self._api_key = self.config.nemotron_api_key or os.environ.get(
            "NVIDIA_API_KEY", os.environ.get("NGC_API_KEY", "")
        )
        self._client = httpx.Client(
            base_url=self.config.nemotron_base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def check(
        self,
        content: str,
        check_type: CheckType = CheckType.INPUT,
        response_content: str | None = None,
    ) -> SafetyResult:
        """Run a safety check on content.

        Args:
            content: The content to check.
            check_type: What kind of check (input, output, tool_call, tool_result).
            response_content: If checking output, the agent's response.

        Returns:
            SafetyResult with verdict, categories, and timing.
        """
        # Truncate if needed
        truncated = content[: self.config.max_content_length]
        snippet = content[: self.config.snippet_length]

        prompt = _build_prompt(truncated, check_type, response_content)
        start = time.perf_counter()

        try:
            resp = self._client.post(
                "/chat/completions",
                json={
                    "model": self.config.nemotron_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 64,
                    "temperature": 0.0,
                    "top_p": 1.0,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            latency = (time.perf_counter() - start) * 1000

            raw_text = data["choices"][0]["message"]["content"]
            parsed = _parse_response(raw_text)

            # Determine verdict based on check type
            if check_type in (CheckType.INPUT, CheckType.TOOL_CALL):
                verdict_str = parsed.get("User Safety", "safe").lower()
            else:
                verdict_str = parsed.get("Response Safety", parsed.get("User Safety", "safe")).lower()

            verdict = SafetyVerdict.UNSAFE if "unsafe" in verdict_str else SafetyVerdict.SAFE

            # Extract categories
            categories: list[str] = []
            if "Safety Categories" in parsed and parsed["Safety Categories"]:
                raw_cats = parsed["Safety Categories"]
                if isinstance(raw_cats, str):
                    categories = [c.strip() for c in raw_cats.split(",") if c.strip()]
                elif isinstance(raw_cats, list):
                    categories = raw_cats

            return SafetyResult(
                verdict=verdict,
                categories=categories,
                check_type=check_type,
                content_snippet=snippet,
                raw_response=parsed,
                latency_ms=latency,
            )

        except httpx.HTTPStatusError as e:
            latency = (time.perf_counter() - start) * 1000
            return SafetyResult(
                verdict=SafetyVerdict.ERROR,
                check_type=check_type,
                content_snippet=snippet,
                latency_ms=latency,
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            )
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            latency = (time.perf_counter() - start) * 1000
            return SafetyResult(
                verdict=SafetyVerdict.ERROR,
                check_type=check_type,
                content_snippet=snippet,
                latency_ms=latency,
                error=f"Parse error: {e}",
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return SafetyResult(
                verdict=SafetyVerdict.ERROR,
                check_type=check_type,
                content_snippet=snippet,
                latency_ms=latency,
                error=str(e),
            )

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class AsyncNemotronChecker:
    """Async version of the Nemotron safety checker."""

    def __init__(self, config: AgentSafeConfig | None = None):
        self.config = config or AgentSafeConfig()
        self._api_key = self.config.nemotron_api_key or os.environ.get(
            "NVIDIA_API_KEY", os.environ.get("NGC_API_KEY", "")
        )
        self._client = httpx.AsyncClient(
            base_url=self.config.nemotron_base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def check(
        self,
        content: str,
        check_type: CheckType = CheckType.INPUT,
        response_content: str | None = None,
    ) -> SafetyResult:
        """Async safety check — same interface as sync version."""
        truncated = content[: self.config.max_content_length]
        snippet = content[: self.config.snippet_length]
        prompt = _build_prompt(truncated, check_type, response_content)
        start = time.perf_counter()

        try:
            resp = await self._client.post(
                "/chat/completions",
                json={
                    "model": self.config.nemotron_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 64,
                    "temperature": 0.0,
                    "top_p": 1.0,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            latency = (time.perf_counter() - start) * 1000

            raw_text = data["choices"][0]["message"]["content"]
            parsed = _parse_response(raw_text)

            if check_type in (CheckType.INPUT, CheckType.TOOL_CALL):
                verdict_str = parsed.get("User Safety", "safe").lower()
            else:
                verdict_str = parsed.get("Response Safety", parsed.get("User Safety", "safe")).lower()

            verdict = SafetyVerdict.UNSAFE if "unsafe" in verdict_str else SafetyVerdict.SAFE
            categories: list[str] = []
            if "Safety Categories" in parsed and parsed["Safety Categories"]:
                raw_cats = parsed["Safety Categories"]
                if isinstance(raw_cats, str):
                    categories = [c.strip() for c in raw_cats.split(",") if c.strip()]
                elif isinstance(raw_cats, list):
                    categories = raw_cats

            return SafetyResult(
                verdict=verdict,
                categories=categories,
                check_type=check_type,
                content_snippet=snippet,
                raw_response=parsed,
                latency_ms=latency,
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return SafetyResult(
                verdict=SafetyVerdict.ERROR,
                check_type=check_type,
                content_snippet=snippet,
                latency_ms=latency,
                error=str(e),
            )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
