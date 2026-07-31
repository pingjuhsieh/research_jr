"""Shared LLM helpers for the ICMID joking-relationship pipeline.

Path configuration for the active pipeline lives in ``code/llm_ehraf/config.py``
and ``code/visualization/config.py``. This module only provides OpenAI helpers used
by ``code/llm_ehraf/extract.py``.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
LLM_SEED = int(os.getenv("LLM_SEED", "42"))

REASONING_EFFORT_DISCOVERY = os.getenv("OPENAI_REASONING_EFFORT_DISCOVERY", "minimal")
REASONING_EFFORT_EXTRACT = os.getenv("OPENAI_REASONING_EFFORT_EXTRACT", "low")


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set (see .env)")
    return OpenAI(api_key=api_key)


def _uses_completion_token_param(model: str) -> bool:
    lowered = model.lower()
    return lowered.startswith("gpt-5") or lowered.startswith("o")


def _supports_sampling_params(model: str) -> bool:
    """gpt-5 / o-series only accept default temperature; omit temperature and seed."""
    return not _uses_completion_token_param(model)


def effective_max_output_tokens(model: str, requested: int, *, stage: str) -> int:
    # Reasoning models consume part of the budget on hidden reasoning tokens.
    if _uses_completion_token_param(model):
        floor = 2000 if stage == "discovery" else 4000
        return max(requested, floor)
    return requested


def reasoning_effort_for_model(model: str, stage: str) -> str | None:
    if not _uses_completion_token_param(model):
        return None
    if stage == "discovery":
        return REASONING_EFFORT_DISCOVERY
    if stage == "extract":
        return REASONING_EFFORT_EXTRACT
    return None


def create_chat_completion(client: OpenAI, *, model: str, messages: list[dict[str, Any]], **kwargs: Any):
    max_output_tokens = kwargs.pop("max_output_tokens", None)
    response_format = kwargs.pop("response_format", None)
    reasoning_effort = kwargs.pop("reasoning_effort", None)
    temperature = kwargs.pop("temperature", LLM_TEMPERATURE)
    seed = kwargs.pop("seed", LLM_SEED)

    params: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    if _supports_sampling_params(model):
        params["temperature"] = temperature
        if seed is not None:
            params["seed"] = seed
    if response_format is not None:
        params["response_format"] = response_format
    if reasoning_effort is not None:
        params["reasoning_effort"] = reasoning_effort

    if max_output_tokens is not None:
        token_key = "max_completion_tokens" if _uses_completion_token_param(model) else "max_tokens"
        params[token_key] = max_output_tokens

    params.update(kwargs)
    return client.chat.completions.create(**params)


def message_content_from_response(resp: Any) -> tuple[str, str | None, str | None]:
    choice = resp.choices[0]
    message = choice.message
    content = message.content or ""
    refusal = getattr(message, "refusal", None)
    finish_reason = getattr(choice, "finish_reason", None)
    return content, finish_reason, refusal


_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def parse_llm_json_content(content: str) -> Any:
    text = content.strip()
    text = _JSON_FENCE_RE.sub("", text).strip()
    if not text:
        raise ValueError("no json content")
    return json.loads(text)


def llm_error_signature(err: Exception) -> str:
    return f"{type(err).__name__}:{err}"


def same_llm_error_twice(prev: str | None, err: Exception) -> bool:
    return prev is not None and prev == llm_error_signature(err)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
