#!/usr/bin/env python3
"""Benchmark the local gateway across model profiles."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


GATEWAY_URL = "http://127.0.0.1:8000"
VLLM_URL = "http://127.0.0.1:8001"
API_KEY = os.environ.get("API_BEARER_KEY", "prod-key-1")
REQUEST_TIMEOUT_SECONDS = 240
READY_TIMEOUT_SECONDS = 900


@dataclass(frozen=True)
class Profile:
    key: str
    model_id: str
    supports_reasoning: bool


@dataclass(frozen=True)
class BenchmarkCase:
    key: str
    title: str
    prompt: str
    max_tokens: int
    expected_output: str | None = None


PROFILES = (
    Profile("gpt-oss", "openai/gpt-oss-20b", True),
    Profile("deepseek-r1-distill", "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", True),
    Profile("qwen3-light", "Qwen/Qwen3-4B", False),
)

EXACT_OUTPUT = (
    "The little analytical chatbot crossed the private net of my rig and returned "
    "these tokens intact, with borrowed dignity."
)
CASES = (
    BenchmarkCase(
        key="fixed-output",
        title="Fixed-output speed benchmark",
        prompt=f'Return exactly this sentence and nothing else: "{EXACT_OUTPUT}"',
        max_tokens=96,
        expected_output=EXACT_OUTPUT,
    ),
    BenchmarkCase(
        key="reasoning",
        title="Reasoning benchmark",
        prompt=(
            "A room has 99 murderers. I walk into the room and murder 3 of them. "
            "How many murderers are in the room right now? Count dead murderers too. "
            "Explain briefly, then end with `Final: <number>`."
        ),
        max_tokens=160,
    ),
)


def _http_json(url: str, payload: dict[str, Any] | None = None, *, auth: bool = False) -> dict[str, Any]:
    """Send a JSON request and return a JSON object."""

    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    if auth:
        headers["Authorization"] = f"Bearer {API_KEY}"
    request = Request(url, data=data, headers=headers)
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.load(response)


def _switch_profile(profile: Profile) -> None:
    """Recreate the stack for the requested profile."""

    env = os.environ.copy()
    env["MODEL_PROFILE"] = profile.key
    command = [
        "docker",
        "compose",
        "--env-file",
        ".env",
        "-f",
        "deploy/compose.yaml",
        "up",
        "-d",
        "--force-recreate",
        "vllm",
        "gateway",
    ]
    result = subprocess.run(command, check=False, env=env, capture_output=True, text=True)
    if result.returncode == 0:
        return
    raise RuntimeError(
        "docker compose failed while switching profiles:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def _wait_until_ready(profile: Profile) -> None:
    """Wait until the local stack serves the expected profile."""

    deadline = time.time() + READY_TIMEOUT_SECONDS
    while time.time() < deadline:
        try:
            with urlopen(f"{VLLM_URL}/health", timeout=5) as response:
                if response.status != 200:
                    time.sleep(2)
                    continue
            models = _http_json(f"{GATEWAY_URL}/v1/models", auth=True)
            active_model = models["data"][0]["id"]
            if active_model == profile.model_id:
                return
        except (HTTPError, URLError, OSError, KeyError, IndexError, json.JSONDecodeError):
            time.sleep(2)
            continue
        time.sleep(2)
    raise TimeoutError(f"Timed out waiting for profile {profile.key} to become ready.")


def _tokenize(model_id: str, text: str) -> int:
    """Count tokens for the provided text with the active model tokenizer."""

    stripped = text.strip()
    if not stripped:
        return 0
    payload = _http_json(
        f"{VLLM_URL}/tokenize",
        {"model": model_id, "prompt": stripped, "add_special_tokens": False},
    )
    return int(payload["count"])


def _extract_final_answer(text: str) -> str:
    """Extract a compact answer summary for markdown tables."""

    match = re.search(r"Final:\s*([^\n\r`]+)", text)
    if match:
        return f"Final: {match.group(1).strip()}"
    compact = " ".join(text.split())
    if len(compact) <= 96:
        return compact
    return compact[:93] + "..."


def _unsupported_row(profile: Profile, case: BenchmarkCase, reasoning_enabled: bool) -> dict[str, Any]:
    """Return a benchmark row for an intentionally unsupported mode."""

    return {
        "case": case.key,
        "profile": profile.key,
        "reasoning_enabled": reasoning_enabled,
        "status": "unsupported",
        "seconds": None,
        "tokens_per_second": None,
        "completion_tokens": None,
        "reasoning_tokens": None,
        "answer_tokens": None,
        "exact_match": None,
        "answer": None,
        "notes": None,
    }


def _run_chat(profile: Profile, case: BenchmarkCase, *, reasoning_enabled: bool) -> dict[str, Any]:
    """Run one benchmark request through the gateway."""

    if reasoning_enabled and not profile.supports_reasoning:
        return _unsupported_row(profile, case, reasoning_enabled)

    payload: dict[str, Any] = {
        "messages": [{"role": "user", "content": case.prompt}],
        "temperature": 0,
        "max_tokens": case.max_tokens,
        "reasoning": {
            "enabled": reasoning_enabled,
            "include": reasoning_enabled,
            "effort": "low",
        },
    }

    started_at = time.perf_counter()
    response = _http_json(f"{GATEWAY_URL}/v1/chat/completions", payload, auth=True)
    elapsed = time.perf_counter() - started_at

    choice = response["choices"][0]
    message = choice["message"]
    answer_text = (message.get("content") or "").strip()
    reasoning_text = (message.get("reasoning") or message.get("reasoning_content") or "").strip()
    completion_tokens = int(response["usage"]["completion_tokens"])
    reasoning_tokens = _tokenize(profile.model_id, reasoning_text)
    answer_tokens = _tokenize(profile.model_id, answer_text)

    notes: list[str] = []
    exact_match = None
    if case.expected_output is not None:
        exact_match = answer_text == case.expected_output
        if not exact_match:
            notes.append("exact mismatch")
    if "<think>" in answer_text:
        notes.append("raw <think> leaked")
    if choice.get("finish_reason") == "length":
        notes.append("hit max_tokens")

    return {
        "case": case.key,
        "profile": profile.key,
        "reasoning_enabled": reasoning_enabled,
        "status": "ok",
        "seconds": round(elapsed, 2),
        "tokens_per_second": round(completion_tokens / elapsed, 2) if elapsed > 0 else None,
        "completion_tokens": completion_tokens,
        "reasoning_tokens": reasoning_tokens,
        "answer_tokens": answer_tokens,
        "exact_match": exact_match,
        "answer": answer_text if case.expected_output is not None else _extract_final_answer(answer_text),
        "notes": "; ".join(notes) or "",
    }


def _run_profile(profile: Profile) -> list[dict[str, Any]]:
    """Switch to a profile and benchmark all configured cases."""

    _switch_profile(profile)
    _wait_until_ready(profile)

    rows: list[dict[str, Any]] = []
    for case in CASES:
        rows.append(_run_chat(profile, case, reasoning_enabled=False))
        rows.append(_run_chat(profile, case, reasoning_enabled=True))
    return rows


def _render_value(row: dict[str, Any], key: str) -> str:
    """Render a markdown cell."""

    if row["status"] == "unsupported" and key not in {"profile"}:
        return "X"
    value = row[key]
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _markdown_table(rows: list[dict[str, Any]], *, exact_output_case: bool) -> str:
    """Render a markdown table for README insertion."""

    if exact_output_case:
        headers = [
            "Profile",
            "Reasoning",
            "Seconds",
            "Tokens/s",
            "Completion Tokens",
            "Reasoning Tokens",
            "Answer Tokens",
            "Exact Match",
            "Notes",
        ]
        keys = [
            "profile",
            "reasoning_enabled",
            "seconds",
            "tokens_per_second",
            "completion_tokens",
            "reasoning_tokens",
            "answer_tokens",
            "exact_match",
            "notes",
        ]
    else:
        headers = [
            "Profile",
            "Reasoning",
            "Seconds",
            "Tokens/s",
            "Completion Tokens",
            "Reasoning Tokens",
            "Answer Tokens",
            "Answer",
            "Notes",
        ]
        keys = [
            "profile",
            "reasoning_enabled",
            "seconds",
            "tokens_per_second",
            "completion_tokens",
            "reasoning_tokens",
            "answer_tokens",
            "answer",
            "notes",
        ]

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        cells: list[str] = []
        for key in keys:
            if key == "reasoning_enabled":
                cells.append("on" if row["reasoning_enabled"] else "off")
                continue
            cells.append(_render_value(row, key))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> int:
    """Benchmark all profiles and print markdown tables."""

    rows_by_case: dict[str, list[dict[str, Any]]] = {case.key: [] for case in CASES}

    for profile in PROFILES:
        for row in _run_profile(profile):
            rows_by_case[row["case"]].append(row)

    fixed_rows = rows_by_case["fixed-output"]
    open_rows = rows_by_case["reasoning"]

    print("Fixed-output prompt:")
    print(EXACT_OUTPUT)
    print()
    print(_markdown_table(fixed_rows, exact_output_case=True))
    print()
    print("Reasoning prompt:")
    print(CASES[1].prompt)
    print()
    print(_markdown_table(open_rows, exact_output_case=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
