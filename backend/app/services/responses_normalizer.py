"""Responses API normalization helpers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import AsyncIterator

from app.core.types import JsonObject, JsonValue
from app.models.common import ReasoningConfig

_THINK_TAG_PATTERN = re.compile(r"(?s)<think>.*?</think>")


def should_hide_reasoning(reasoning: ReasoningConfig | None) -> bool:
    """Return whether reasoning traces should be removed from Responses output."""

    if reasoning is None:
        return False
    return reasoning.enabled is False or reasoning.include is False


def normalize_responses_payload(payload: JsonObject, reasoning: ReasoningConfig | None) -> JsonObject:
    """Drop hidden reasoning items from a non-streaming Responses payload."""

    if not should_hide_reasoning(reasoning):
        return payload
    return _normalize_response_object(payload)


async def normalize_responses_sse(
    source: AsyncIterator[bytes],
    reasoning: ReasoningConfig | None,
) -> AsyncIterator[bytes]:
    """Drop hidden reasoning events from a streaming Responses SSE feed."""

    if not should_hide_reasoning(reasoning):
        async for chunk in source:
            if chunk:
                yield chunk
        return

    normalizer = ResponsesSseNormalizer()
    buffer = ""

    async for chunk in source:
        if not chunk:
            continue

        buffer += chunk.decode("utf-8")
        while "\n\n" in buffer:
            block, buffer = buffer.split("\n\n", 1)
            normalized = normalizer.normalize_block(block)
            if normalized is not None:
                yield normalized.encode("utf-8")

    if buffer:
        normalized = normalizer.normalize_block(buffer)
        if normalized is not None:
            yield normalized.encode("utf-8")


@dataclass(slots=True)
class ResponsesSseNormalizer:
    """Stateful normalizer for Responses SSE events."""

    hidden_item_ids: set[str] = field(default_factory=set)
    hidden_output_items: int = 0
    visible_output_indices: dict[str, int] = field(default_factory=dict)

    def normalize_block(self, block: str) -> str | None:
        """Normalize one SSE event block."""

        lines = [line for line in block.splitlines() if line]
        if not lines:
            return None

        event_name: str | None = None
        data_text: str | None = None
        passthrough_lines: list[str] = []

        for line in lines:
            if line.startswith("event:"):
                event_name = line.partition(":")[2].strip()
            elif line.startswith("data:"):
                data_text = line.partition(":")[2].lstrip()
            else:
                passthrough_lines.append(line)

        if data_text is None or data_text == "[DONE]":
            return f"{block}\n\n"

        try:
            payload = json.loads(data_text)
        except json.JSONDecodeError:
            return f"{block}\n\n"

        if not isinstance(payload, dict):
            return f"{block}\n\n"

        if self._should_drop_event(payload):
            return None

        normalized = self._normalize_event_payload(payload)
        lines_out: list[str] = []
        if event_name is not None:
            lines_out.append(f"event: {event_name}")
        lines_out.extend(passthrough_lines)
        lines_out.append(f"data: {json.dumps(normalized, separators=(',', ':'))}")
        return "\n".join(lines_out) + "\n\n"

    def _should_drop_event(self, payload: JsonObject) -> bool:
        """Return whether an SSE event should be removed."""

        item = payload.get("item")
        if isinstance(item, dict) and item.get("type") == "reasoning":
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id not in self.hidden_item_ids:
                self.hidden_item_ids.add(item_id)
                self.hidden_output_items += 1
            return True

        item_id = payload.get("item_id")
        if isinstance(item_id, str) and item_id in self.hidden_item_ids:
            return True

        event_type = payload.get("type")
        return isinstance(event_type, str) and event_type.startswith("response.reasoning_")

    def _normalize_event_payload(self, payload: JsonObject) -> JsonObject:
        """Rewrite an SSE event after reasoning items were removed."""

        normalized = dict(payload)
        item_id = _extract_item_id(normalized)

        output_index = normalized.get("output_index")
        if isinstance(output_index, int):
            visible_index = max(0, output_index - self.hidden_output_items)
            if item_id is not None and normalized.get("type") == "response.output_item.added":
                self.visible_output_indices[item_id] = visible_index
            normalized["output_index"] = self.visible_output_indices.get(item_id, visible_index)

        content_index = normalized.get("content_index")
        if isinstance(content_index, int):
            normalized["content_index"] = max(0, content_index - self.hidden_output_items)

        response = normalized.get("response")
        if isinstance(response, dict):
            normalized["response"] = _normalize_response_object(response)

        item = normalized.get("item")
        if isinstance(item, dict):
            normalized["item"] = _normalize_output_item(item)

        return normalized


def _normalize_response_object(response: JsonObject) -> JsonObject:
    """Remove hidden reasoning items from a response object."""

    normalized = dict(response)
    output = normalized.get("output")
    if not isinstance(output, list):
        return normalized

    cleaned_output: list[JsonValue] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "reasoning":
            continue
        cleaned_output.append(_normalize_output_item(item))

    normalized["output"] = cleaned_output
    return normalized


def _normalize_output_item(item: JsonObject) -> JsonObject:
    """Strip reasoning tag leakage from visible output items."""

    normalized = dict(item)
    content = normalized.get("content")
    if not isinstance(content, list):
        return normalized

    cleaned_content: list[JsonValue] = []
    for part in content:
        if not isinstance(part, dict):
            continue
        cleaned_part = dict(part)
        text = cleaned_part.get("text")
        if isinstance(text, str):
            cleaned_part["text"] = _strip_think_tags(text)
        cleaned_content.append(cleaned_part)

    normalized["content"] = cleaned_content
    return normalized


def _strip_think_tags(text: str) -> str:
    """Remove Qwen-style think blocks from visible output text."""

    stripped = _THINK_TAG_PATTERN.sub("", text).strip()
    return stripped or text.strip()


def _extract_item_id(payload: JsonObject) -> str | None:
    """Return the current event item ID when present."""

    item_id = payload.get("item_id")
    if isinstance(item_id, str):
        return item_id

    item = payload.get("item")
    if isinstance(item, dict):
        nested_item_id = item.get("id")
        if isinstance(nested_item_id, str):
            return nested_item_id

    return None
