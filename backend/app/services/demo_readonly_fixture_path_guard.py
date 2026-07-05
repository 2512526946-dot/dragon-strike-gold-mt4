from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath


PATH_ALLOWED = "PATH_ALLOWED"
PATH_BLOCKED = "PATH_BLOCKED"

ALLOWED_DEMO_READONLY_FIXTURE_PATHS = frozenset(
    {
        "docs/implementation_plans/demo_account_readonly_snapshot.example.json",
        "docs/implementation_plans/demo_positions_order_history.example.json",
        "docs/implementation_plans/demo_market_symbol_readonly.example.json",
    }
)

SENSITIVE_PATH_KEYWORDS = (
    "password",
    "credential",
    "secret",
    "token",
    "key",
    "login",
    "real_account",
    "live_account",
)


@dataclass(frozen=True)
class DemoReadOnlyFixturePathGuardResult:
    passed: bool
    status_code: str
    relative_path: str | None
    resolved_path: str | None
    block_reasons: list[str]
    warning_reasons: list[str]
    read_only: bool
    demo_only: bool
    is_tradable: bool
    can_execute: bool


def validate_demo_readonly_fixture_path(
    relative_path: str | Path | None,
    *,
    project_root: Path | str | None = None,
) -> DemoReadOnlyFixturePathGuardResult:
    block_reasons: list[str] = []
    normalized_path = _normalize_path(relative_path)

    if normalized_path is None:
        block_reasons.append("path must be a non-empty relative path")
        return _blocked_result(None, None, block_reasons)

    _append_path_rejections(relative_path, normalized_path, block_reasons)

    resolved_path: str | None = None
    if not block_reasons:
        project_root_path = _project_root(project_root)
        candidate_path = (project_root_path / normalized_path).resolve(strict=False)
        resolved_path = str(candidate_path)

        if not _is_relative_to(candidate_path, project_root_path):
            block_reasons.append("resolved path must stay inside project root")

    if normalized_path not in ALLOWED_DEMO_READONLY_FIXTURE_PATHS:
        block_reasons.append("path must be one of the allowed demo readonly fixtures")

    if block_reasons:
        return _blocked_result(normalized_path, resolved_path, block_reasons)

    return DemoReadOnlyFixturePathGuardResult(
        passed=True,
        status_code=PATH_ALLOWED,
        relative_path=normalized_path,
        resolved_path=resolved_path,
        block_reasons=[],
        warning_reasons=[],
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
    )


def _blocked_result(
    relative_path: str | None,
    resolved_path: str | None,
    block_reasons: list[str],
) -> DemoReadOnlyFixturePathGuardResult:
    return DemoReadOnlyFixturePathGuardResult(
        passed=False,
        status_code=PATH_BLOCKED,
        relative_path=relative_path,
        resolved_path=resolved_path,
        block_reasons=block_reasons,
        warning_reasons=[],
        read_only=True,
        demo_only=True,
        is_tradable=False,
        can_execute=False,
    )


def _normalize_path(relative_path: str | Path | None) -> str | None:
    if relative_path is None:
        return None

    path_text = str(relative_path).strip()
    if not path_text:
        return None

    return path_text.replace("\\", "/")


def _append_path_rejections(
    original_path: str | Path | None,
    normalized_path: str,
    block_reasons: list[str],
) -> None:
    path_text = str(original_path)
    windows_path = PureWindowsPath(path_text)
    posix_path = PurePosixPath(normalized_path)
    components = [part for part in normalized_path.split("/") if part]
    lower_components = [part.lower() for part in components]

    if (
        Path(path_text).is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or posix_path.is_absolute()
        or path_text.startswith("\\\\")
    ):
        block_reasons.append("absolute paths are not allowed")

    if any(".." in part for part in components):
        block_reasons.append("path traversal is not allowed")

    if any(part.startswith(".") for part in components):
        block_reasons.append("hidden files or directories are not allowed")

    if posix_path.suffix.lower() != ".json":
        block_reasons.append("path must use a .json extension")

    for keyword in SENSITIVE_PATH_KEYWORDS:
        if any(keyword in part for part in lower_components):
            block_reasons.append(f"path must not contain sensitive keyword: {keyword}")

    _append_blocked_directory_rejections(lower_components, block_reasons)


def _append_blocked_directory_rejections(
    lower_components: list[str],
    block_reasons: list[str],
) -> None:
    if not lower_components:
        return

    if lower_components[0] == "data":
        block_reasons.append("data directory is not allowed")
    if lower_components[0] == "logs":
        block_reasons.append("logs directory is not allowed")
    if lower_components[0] == "models":
        block_reasons.append("models directory is not allowed")
    if "__pycache__" in lower_components:
        block_reasons.append("__pycache__ directory is not allowed")
    if ".pytest_cache" in lower_components:
        block_reasons.append(".pytest_cache directory is not allowed")
    if lower_components[:2] == ["frontend", "dist"]:
        block_reasons.append("frontend/dist directory is not allowed")
    if lower_components[:2] == ["frontend", "node_modules"]:
        block_reasons.append("frontend/node_modules directory is not allowed")


def _project_root(project_root: Path | str | None) -> Path:
    if project_root is not None:
        return Path(project_root).resolve(strict=False)

    return Path(__file__).resolve().parents[3]


def _is_relative_to(candidate_path: Path, project_root: Path) -> bool:
    try:
        candidate_path.relative_to(project_root)
    except ValueError:
        return False
    return True
