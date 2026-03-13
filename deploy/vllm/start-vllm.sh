#!/usr/bin/env bash
set -euo pipefail

MODEL_PROFILE="${MODEL_PROFILE:-gpt-oss}"
VLLM_HOST="${VLLM_HOST:-0.0.0.0}"
VLLM_PORT="${VLLM_PORT:-8000}"

MODEL_CACHE_DIR="${MODEL_CACHE_DIR:-/models/vllm}"
export HF_HOME="${MODEL_CACHE_DIR}/hf"
export HF_HUB_CACHE="${MODEL_CACHE_DIR}/hub"
export HF_ASSETS_CACHE="${MODEL_CACHE_DIR}/assets"

mkdir -p "${MODEL_CACHE_DIR}" "${HF_HOME}" "${HF_HUB_CACHE}" "${HF_ASSETS_CACHE}"

case "${MODEL_PROFILE}" in
  qwen3-light)
    MODEL_ID_DEFAULT="Qwen/Qwen3-4B"
    SERVED_MODEL_NAME_DEFAULT="Qwen/Qwen3-4B"
    REASONING_PARSER="qwen3"
    PROFILE_ARGS=()
    ;;
  deepseek-r1-distill)
    MODEL_ID_DEFAULT="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    SERVED_MODEL_NAME_DEFAULT="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    REASONING_PARSER="deepseek_r1"
    PROFILE_ARGS=()
    ;;
  gpt-oss)
    MODEL_ID_DEFAULT="openai/gpt-oss-20b"
    SERVED_MODEL_NAME_DEFAULT="openai/gpt-oss-20b"
    REASONING_PARSER="openai_gptoss"
    PROFILE_ARGS=()
    ;;
  *)
    echo "Unsupported MODEL_PROFILE: ${MODEL_PROFILE}" >&2
    exit 1
    ;;
esac

RUNTIME_ARGS=()
if [[ "${VLLM_ENFORCE_EAGER:-0}" == "1" || "${VLLM_ENFORCE_EAGER:-0}" == "true" ]]; then
  RUNTIME_ARGS+=(--enforce-eager)
fi

exec vllm serve "${MODEL_ID:-${MODEL_ID_DEFAULT}}" \
  --served-model-name "${SERVED_MODEL_NAME:-${SERVED_MODEL_NAME_DEFAULT}}" \
  --reasoning-parser "${REASONING_PARSER}" \
  --gpu-memory-utilization "${VLLM_GPU_MEMORY_UTILIZATION:-0.9}" \
  --dtype "${VLLM_DTYPE:-auto}" \
  --max-model-len "${VLLM_MAX_MODEL_LEN:-32768}" \
  "${PROFILE_ARGS[@]}" \
  "${RUNTIME_ARGS[@]}" \
  --host "${VLLM_HOST}" \
  --port "${VLLM_PORT}"
