FROM rocm/vllm-dev:rocm7.2_navi_ubuntu24.04_py3.12_pytorch_2.9_vllm_0.14.0rc0

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates tini \
    && rm -rf /var/lib/apt/lists/*

COPY deploy/vllm/stable/start-vllm.sh /usr/local/bin/start-vllm.sh

RUN chmod +x /usr/local/bin/start-vllm.sh

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/start-vllm.sh"]

