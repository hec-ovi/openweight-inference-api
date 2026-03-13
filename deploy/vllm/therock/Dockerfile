FROM python:3.12-slim

ARG THEROCK_WHEEL_INDEX=https://repo.amd.com/rocm/whl/gfx1151/
ARG THEROCK_TORCH_INDEX=https://repo.amd.com/rocm/whl/gfx1151/torch/
ARG THEROCK_TORCHVISION_INDEX=https://repo.amd.com/rocm/whl/gfx1151/torchvision/
ARG VLLM_WHEEL_INDEX=https://wheels.vllm.ai/rocm/0.14.1/rocm700

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libgomp1 libnuma1 tini \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel
RUN python -m pip install --no-cache-dir --index-url ${THEROCK_WHEEL_INDEX} "rocm[libraries,devel]"
RUN python -m pip install --no-cache-dir --index-url ${THEROCK_TORCH_INDEX} "torch==2.9.1+rocm7.11.0"
RUN python -m pip install --no-cache-dir --index-url ${THEROCK_TORCHVISION_INDEX} "torchvision==0.22.1+rocm7.11.0"
RUN python -m pip install --no-cache-dir --extra-index-url ${VLLM_WHEEL_INDEX} "vllm==0.14.1"

COPY deploy/vllm/therock/start-vllm.sh /usr/local/bin/start-vllm.sh

RUN chmod +x /usr/local/bin/start-vllm.sh

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/start-vllm.sh"]
