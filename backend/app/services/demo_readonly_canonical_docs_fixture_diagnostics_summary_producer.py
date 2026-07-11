from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services.demo_readonly_canonical_diagnostics_pipeline import (
    build_demo_readonly_canonical_diagnostics_summary,
)


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_ROOT = _REPOSITORY_ROOT / "docs" / "architecture" / "fixtures"
_FIXTURE_BUNDLE_DIR = (
    _FIXTURE_ROOT / "canonical-mt4-demo-readonly-bundle-v1"
)
_FIXTURE_REFERENCE_TIME = datetime(2026, 7, 10, 2, 30, 5, tzinfo=UTC)


def build_demo_readonly_canonical_docs_fixture_diagnostics_summary() -> dict[
    str, Any
]:
    """Build the canonical summary from the fixed repository docs fixture."""

    return build_demo_readonly_canonical_diagnostics_summary(
        allowed_root=_FIXTURE_ROOT,
        bundle_dir=_FIXTURE_BUNDLE_DIR,
        now_utc=_FIXTURE_REFERENCE_TIME,
    )
