from __future__ import annotations

from typing import Any

from app.services import (
    canonical_mt4_demo_readonly_bundle_v1_filesystem_reader as filesystem_reader,
)
from app.services import (
    canonical_mt4_demo_readonly_bundle_v1_value_validator as value_validator,
)
from app.services import data_quality_gate
from app.services import demo_readonly_canonical_diagnostics_summary_adapter as adapter


def build_demo_readonly_canonical_diagnostics_summary(
    *,
    allowed_root: object,
    bundle_dir: object,
    now_utc: object,
    previous_identity: object | None = None,
    read_policy: (
        value_validator.CanonicalMt4DemoReadonlyBundleV1ReadPolicy | None
    ) = None,
    filesystem_policy: (
        filesystem_reader.CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy | None
    ) = None,
    data_quality_policy: (
        data_quality_gate.CanonicalMt4DemoReadonlyBundleV1DataQualityPolicy | None
    ) = None,
) -> dict[str, Any]:
    """Build a safe diagnostics summary through the canonical readonly chain."""

    try:
        reader_result: object = (
            filesystem_reader.read_and_validate_canonical_mt4_demo_readonly_bundle_v1(
                allowed_root=allowed_root,
                bundle_dir=bundle_dir,
                now_utc=now_utc,
                previous_identity=previous_identity,
                read_policy=read_policy,
                filesystem_policy=filesystem_policy,
            )
        )
    except Exception:
        reader_result = None

    try:
        data_quality_result: object = (
            data_quality_gate.evaluate_canonical_mt4_demo_readonly_bundle_v1_data_quality_gate(
                reader_result=reader_result,
                policy=data_quality_policy,
            )
        )
    except Exception:
        data_quality_result = None

    return adapter.adapt_canonical_data_quality_gate_to_demo_readonly_diagnostics_summary(
        data_quality_result=data_quality_result,
    )
