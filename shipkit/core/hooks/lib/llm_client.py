"""LLM client for hook scripts.

Lightweight Claude API client for hooks. Uses Haiku for speed and cost-efficiency.
No external dependencies beyond stdlib.
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from typing import Any


def call_claude(
    prompt: str,
    model: str = "claude-haiku-4",
    max_tokens: int = 4096,
    temperature: float = 0.0,
) -> str:
    """Call Claude API with a prompt.

    Args:
        prompt: The prompt to send
        model: Model to use (default: haiku for speed/cost)
        max_tokens: Max response tokens
        temperature: Sampling temperature (0 = deterministic)

    Returns:
        Response text from Claude

    Raises:
        RuntimeError: If API call fails or API key not configured
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Set it in ~/.claude/settings.json:\n"
            '  "env": {"ANTHROPIC_API_KEY": "sk-ant-..."}'
        )

    # Build request
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "anthropic-version": "2023-06-01",
        "x-api-key": api_key,
        "content-type": "application/json",
    }

    data = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["content"][0]["text"]

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"Claude API error ({e.code}): {error_body}")
    except Exception as e:
        raise RuntimeError(f"Claude API call failed: {e}")


def is_llm_available() -> bool:
    """Check if LLM client is available (API key configured)."""
    return os.environ.get("ANTHROPIC_API_KEY") is not None
