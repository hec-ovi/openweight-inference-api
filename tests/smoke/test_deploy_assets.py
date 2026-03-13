"""Deployment asset smoke tests."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_compose_files_mount_persistent_model_cache() -> None:
    """Compose assets must keep the model cache on persistent host storage."""

    compose = yaml.safe_load((ROOT / "deploy/compose.yaml").read_text(encoding="utf-8"))
    vllm_service = compose["services"]["vllm"]
    assert "${MODEL_CACHE_DIR:-/home/hector/models/vllm}:/models/vllm" in vllm_service["volumes"]


def test_kubernetes_assets_define_amd_gpu_resources() -> None:
    """Stable and preview manifests must request AMD GPU resources."""

    stable = yaml.safe_load((ROOT / "deploy/kubernetes/vllm-stable-statefulset.yaml").read_text(encoding="utf-8"))
    preview = yaml.safe_load((ROOT / "deploy/kubernetes/vllm-therock-statefulset.yaml").read_text(encoding="utf-8"))

    stable_resources = stable["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]
    preview_resources = preview["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]

    assert stable_resources["amd.com/gpu"] == "1"
    assert preview_resources["amd.com/gpu"] == "1"


def test_static_docs_exist() -> None:
    """Static docs pages should be present."""

    for path in [
        ROOT / "docs/index.html",
        ROOT / "docs/redoc.html",
        ROOT / "docs/examples.html",
        ROOT / "docs/streaming.html",
    ]:
        assert path.exists()
