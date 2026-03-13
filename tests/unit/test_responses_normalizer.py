"""Responses normalization tests."""

from __future__ import annotations

import asyncio

from app.models.common import ReasoningConfig
from app.services.responses_normalizer import (
    ResponsesSseNormalizer,
    normalize_responses_payload,
    normalize_responses_sse,
)


def test_non_streaming_plain_mode_drops_reasoning_items() -> None:
    """Hidden reasoning should not leak through the Responses API payload."""

    payload = {
        "id": "resp_123",
        "object": "response",
        "model": "openai/gpt-oss-20b",
        "output": [
            {"id": "rs_1", "type": "reasoning", "content": [{"type": "reasoning_text", "text": "secret"}]},
            {
                "id": "msg_1",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": "visible"}],
            },
        ],
    }

    normalized = normalize_responses_payload(payload, ReasoningConfig(enabled=False, include=False))

    assert len(normalized["output"]) == 1
    assert normalized["output"][0]["type"] == "message"
    assert normalized["output"][0]["content"][0]["text"] == "visible"


def test_non_streaming_plain_mode_strips_think_tags() -> None:
    """Visible output should not contain Qwen think tags when reasoning is off."""

    payload = {
        "id": "resp_123",
        "object": "response",
        "model": "Qwen/Qwen3-4B",
        "output": [
            {
                "id": "msg_1",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": "<think>hidden</think>\nplain"}],
            }
        ],
    }

    normalized = normalize_responses_payload(payload, ReasoningConfig(enabled=False, include=False))

    assert normalized["output"][0]["content"][0]["text"] == "plain"


def test_sse_normalizer_reindexes_after_dropping_reasoning() -> None:
    """Streaming events should keep a stable output index after reasoning is hidden."""

    normalizer = ResponsesSseNormalizer()

    hidden_block = """event: response.output_item.added
data: {"type":"response.output_item.added","output_index":0,"item":{"id":"rs_1","type":"reasoning","content":[]}}
"""
    message_block = """event: response.output_item.added
data: {"type":"response.output_item.added","output_index":1,"item":{"id":"msg_1","type":"message","role":"assistant","content":[]}}
"""
    completed_block = """event: response.completed
data: {"type":"response.completed","response":{"id":"resp_1","object":"response","model":"openai/gpt-oss-20b","output":[{"id":"rs_1","type":"reasoning","content":[]},{"id":"msg_1","type":"message","role":"assistant","content":[{"type":"output_text","text":"visible"}]}]}}
"""
    output_done_block = """event: response.output_text.done
data: {"type":"response.output_text.done","item_id":"msg_1","output_index":1,"content_index":1,"text":"visible"}
"""

    assert normalizer.normalize_block(hidden_block) is None
    normalized_message = normalizer.normalize_block(message_block)
    normalized_output_done = normalizer.normalize_block(output_done_block)
    normalized_completed = normalizer.normalize_block(completed_block)

    assert normalized_message is not None
    assert '"output_index":0' in normalized_message
    assert normalized_output_done is not None
    assert '"output_index":0' in normalized_output_done
    assert '"content_index":0' in normalized_output_done
    assert normalized_completed is not None
    assert '"type":"reasoning"' not in normalized_completed
    assert '"text":"visible"' in normalized_completed


def test_stream_wrapper_filters_hidden_reasoning_events() -> None:
    """Chunked SSE output should still be filtered correctly."""

    async def source():
        yield (
            b'event: response.output_item.added\n'
            b'data: {"type":"response.output_item.added","output_index":0,'
            b'"item":{"id":"rs_1","type":"reasoning","content":[]}}\n\n'
            b'event: response.output_item.added\n'
        )
        yield (
            b'data: {"type":"response.output_item.added","output_index":1,'
            b'"item":{"id":"msg_1","type":"message","role":"assistant","content":[]}}\n\n'
        )

    async def collect() -> str:
        chunks: list[bytes] = []
        async for chunk in normalize_responses_sse(source(), ReasoningConfig(enabled=False, include=False)):
            chunks.append(chunk)
        return b"".join(chunks).decode("utf-8")

    output = asyncio.run(collect())

    assert '"type":"reasoning"' not in output
    assert '"output_index":0' in output
