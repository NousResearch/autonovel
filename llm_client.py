"""OpenAI/Anthropic compatibility helper for Autonovel.

The project was originally wired to Anthropic's Messages API. Hermes is currently
running through a local 9router/OpenAI-compatible endpoint at localhost:20128, so
this helper routes local calls to `/v1/chat/completions` while preserving the old
Anthropic path when `AUTONOVEL_API_PROVIDER=anthropic` or the base URL is
Anthropic.

Environment variables:
- AUTONOVEL_API_BASE_URL: default http://localhost:20128/v1
- AUTONOVEL_API_PROVIDER: openai or anthropic; inferred from the base URL
- AUTONOVEL_API_KEY: bearer key for local/OpenAI-compatible providers
- ANTHROPIC_API_KEY: retained for Anthropic compatibility
- AUTONOVEL_WRITER_MODEL / AUTONOVEL_JUDGE_MODEL / AUTONOVEL_REVIEW_MODEL
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _base_url() -> str:
    return os.environ.get("AUTONOVEL_API_BASE_URL", "http://localhost:20128/v1").rstrip("/")


def _provider() -> str:
    configured = os.environ.get("AUTONOVEL_API_PROVIDER", "").strip().lower()
    if configured:
        return configured
    base = _base_url().lower()
    if "anthropic.com" in base:
        return "anthropic"
    return "openai"


def _api_key(provider: str) -> str:
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_API_KEY", "")
    return os.environ.get("AUTONOVEL_API_KEY", os.environ.get("ANTHROPIC_API_KEY", "local"))


def call_llm(
    *,
    system: str,
    prompt: str,
    model: str,
    max_tokens: int,
    temperature: float,
    api_base: str | None = None,
    api_key: str | None = None,
    timeout: int = 600,
) -> str:
    """Call either Anthropic Messages or OpenAI-compatible chat completions."""
    import httpx

    base = (api_base or _base_url()).rstrip("/")
    provider = _provider()
    key = api_key if api_key is not None else _api_key(provider)

    if provider == "anthropic" or "anthropic.com" in base.lower():
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "context-1m-2025-08-07",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        url = f"{base}/v1/messages"
        response = httpx.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()["content"][0]["text"]

    headers = {
        "Authorization": f"Bearer {key or 'local'}",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    url = f"{base}/chat/completions"
    response = httpx.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    raw = response.text.strip()
    if "data: [DONE]" in raw:
        raw = raw.split("data: [DONE]", 1)[0].strip()
    if raw.startswith("data:"):
        raw = "\n".join(line[5:].strip() for line in raw.splitlines() if line.startswith("data:")).strip()
    data = response.json() if not raw else __import__("json").loads(raw)
    return data["choices"][0]["message"]["content"]


def local_config_summary() -> dict:
    """Return non-secret config values for diagnostics."""
    base = _base_url()
    provider = _provider()
    return {
        "api_base_url": base,
        "provider": provider,
        "writer_model": os.environ.get("AUTONOVEL_WRITER_MODEL", "openrouter/nex-agi/nex-n2-pro:free"),
        "judge_model": os.environ.get("AUTONOVEL_JUDGE_MODEL", "openrouter/nex-agi/nex-n2-pro:free"),
        "review_model": os.environ.get("AUTONOVEL_REVIEW_MODEL", "openrouter/nex-agi/nex-n2-pro:free"),
        "has_api_key": bool(_api_key(provider)),
    }
