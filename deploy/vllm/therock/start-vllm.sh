#!/usr/bin/env bash
set -euo pipefail

MODEL_PROFILE="${MODEL_PROFILE:-qwen3.5-light}"
VLLM_HOST="${VLLM_HOST:-0.0.0.0}"
VLLM_PORT="${VLLM_PORT:-8000}"

MODEL_CACHE_DIR="${MODEL_CACHE_DIR:-/models/vllm}"
export HF_HOME="${HF_HOME:-${MODEL_CACHE_DIR}/hf}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-${MODEL_CACHE_DIR}/hub}"
export VLLM_ASSETS_CACHE="${VLLM_ASSETS_CACHE:-${MODEL_CACHE_DIR}/assets}"

mkdir -p "${MODEL_CACHE_DIR}" "${HF_HOME}" "${HUGGINGFACE_HUB_CACHE}" "${VLLM_ASSETS_CACHE}"

if [[ -n "${HF_TOKEN:-}" ]]; then
  export HUGGING_FACE_HUB_TOKEN="${HF_TOKEN}"
fi

case "${MODEL_PROFILE}" in
  qwen3.5-light)
    MODEL_ID_DEFAULT="Qwen/Qwen3.5-4B"
    SERVED_MODEL_NAME_DEFAULT="Qwen/Qwen3.5-4B"
    REASONING_PARSER="qwen3"
    ;;
  deepseek-r1-distill)
    MODEL_ID_DEFAULT="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    SERVED_MODEL_NAME_DEFAULT="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    REASONING_PARSER="deepseek_r1"
    ;;
  gpt-oss)
    MODEL_ID_DEFAULT="openai/gpt-oss-20b"
    SERVED_MODEL_NAME_DEFAULT="openai/gpt-oss-20b"
    REASONING_PARSER="gptoss"
    ;;
  *)
    echo "Unsupported MODEL_PROFILE: ${MODEL_PROFILE}" >&2
    exit 1
    ;;
esac

exec vllm serve "${MODEL_ID:-${MODEL_ID_DEFAULT}}" \
  --served-model-name "${SERVED_MODEL_NAME:-${SERVED_MODEL_NAME_DEFAULT}}" \
  --reasoning-parser "${REASONING_PARSER}" \
  --gpu-memory-utilization "${VLLM_GPU_MEMORY_UTILIZATION:-0.9}" \
  --dtype "${VLLM_DTYPE:-auto}" \
  --max-model-len "${VLLM_MAX_MODEL_LEN:-32768}" \
  --host "${VLLM_HOST}" \
  --port "${VLLM_PORT}"

