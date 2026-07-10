from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from app.services.canonical_mt4_demo_readonly_bundle_v1_value_validator import (
    CanonicalMt4DemoReadonlyBundleV1ReadPolicy,
    validate_canonical_mt4_demo_readonly_bundle_v1_values,
)


@dataclass(frozen=True)
class CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy:
    manifest_max_bytes: int = 65536
    live_tick_max_bytes: int = 32768
    latest_bars_max_bytes: int = 2097152
    symbol_spec_max_bytes: int = 65536
    account_snapshot_max_bytes: int = 131072
    max_manifest_consistency_retries: int = 1


CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_INPUT_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_INPUT_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_POLICY_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_POLICY_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_ROOT_REJECTED = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_ROOT_REJECTED"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_DIRECTORY_REJECTED = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_DIRECTORY_REJECTED"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_PATH_ESCAPE_BLOCKED = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_PATH_ESCAPE_BLOCKED"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SYMLINK_BLOCKED = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SYMLINK_BLOCKED"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_MISSING = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_MISSING"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_TOO_LARGE = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_TOO_LARGE"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_UNREADABLE = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_UNREADABLE"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UTF8_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UTF8_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_NOT_OBJECT = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_NOT_OBJECT"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UPSTREAM_BLOCKED = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UPSTREAM_BLOCKED"
)
CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SAFE_FAILURE = (
    "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SAFE_FAILURE"
)

VALIDATION_STAGE = "canonical_bundle_v1_isolated_filesystem_reader"
CONTRACT_VERSION = "1.0"
NEXT_ALLOWED_STAGE = ["canonical_data_quality_gate_integration"]
NEXT_BLOCKED_STAGE = [
    "api_reader_activation",
    "readonly_analysis",
    "execution_chain",
]

_MANIFEST_FILENAME = "snapshot_manifest.json"
_PAYLOAD_FILENAMES = (
    "live_tick.json",
    "latest_bars.json",
    "symbol_spec.json",
    "account_snapshot.json",
)
_COMPONENTS = (
    "filesystem_boundary",
    "snapshot_manifest",
    "live_tick",
    "latest_bars",
    "symbol_spec",
    "account_snapshot",
    "manifest_consistency",
    "checksum",
    "upstream_value_validation",
)
_FILE_COMPONENTS = {
    _MANIFEST_FILENAME: "snapshot_manifest",
    "live_tick.json": "live_tick",
    "latest_bars.json": "latest_bars",
    "symbol_spec.json": "symbol_spec",
    "account_snapshot.json": "account_snapshot",
}
_FILE_LIMIT_FIELDS = {
    _MANIFEST_FILENAME: "manifest_max_bytes",
    "live_tick.json": "live_tick_max_bytes",
    "latest_bars.json": "latest_bars_max_bytes",
    "symbol_spec.json": "symbol_spec_max_bytes",
    "account_snapshot.json": "account_snapshot_max_bytes",
}
_MANIFEST_CONSISTENCY_FIELDS = (
    "bundle_id",
    "sequence",
    "committed_at_utc",
    "required_files",
    "commit_state",
)
_SAFE_UPSTREAM_WARNING_CODES = frozenset({"IDEMPOTENT_REPEAT", "SEQUENCE_GAP"})
_SAFE_UPSTREAM_STATUS_PATTERN = re.compile(
    r"^CANONICAL_MT4_BUNDLE_V1_[A-Z0-9_]+$"
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_UTF8_BOM = b"\xef\xbb\xbf"


def read_and_validate_canonical_mt4_demo_readonly_bundle_v1(
    *,
    allowed_root: object,
    bundle_dir: object,
    now_utc: object,
    previous_identity: object | None = None,
    read_policy: CanonicalMt4DemoReadonlyBundleV1ReadPolicy | None = None,
    filesystem_policy: (
        CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy | None
    ) = None,
) -> dict[str, Any]:
    """Read and validate one canonical bundle inside an explicit safe root."""

    context = _ReaderContext()
    unexpected_component = "filesystem_boundary"
    try:
        policy = (
            CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy()
            if filesystem_policy is None
            else filesystem_policy
        )
        if not _is_valid_filesystem_policy(policy):
            context.fail("filesystem_boundary", "FILESYSTEM_POLICY_INVALID")
            return context.result(
                status_code=CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_POLICY_INVALID
            )

        resolved_root = _resolve_allowed_root(allowed_root, context)
        resolved_bundle = _resolve_bundle_dir(
            bundle_dir,
            resolved_root,
            context,
        )
        context.pass_component("filesystem_boundary")

        last_changed_context: _ReaderContext | None = None
        for attempt_number in range(policy.max_manifest_consistency_retries + 1):
            attempt_context = _ReaderContext()
            attempt_context.pass_component("filesystem_boundary")
            context = attempt_context
            attempt = _read_one_complete_attempt(
                bundle_dir=resolved_bundle,
                policy=policy,
                context=attempt_context,
            )
            if attempt is None:
                return attempt_context.result(
                    status_code=attempt_context.failure_status_code
                    or CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SAFE_FAILURE
                )
            if attempt.manifest_changed:
                last_changed_context = attempt_context
                if attempt_number < policy.max_manifest_consistency_retries:
                    continue
                attempt_context.fail(
                    "manifest_consistency",
                    "MANIFEST_UNSTABLE",
                )
                return attempt_context.result(
                    status_code=(
                        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE
                    )
                )

            unexpected_component = "upstream_value_validation"
            upstream = validate_canonical_mt4_demo_readonly_bundle_v1_values(
                manifest=attempt.manifest,
                payloads_by_filename=attempt.payloads,
                now_utc=now_utc,
                previous_identity=previous_identity,
                read_policy=read_policy,
            )
            upstream_passed = upstream.get("passed") is True
            upstream_status = _safe_upstream_status(upstream.get("status_code"))
            upstream_warnings = _safe_upstream_warnings(
                upstream.get("warning_codes")
            )
            attempt_context.upstream_value_passed = upstream_passed
            attempt_context.upstream_value_status_code = upstream_status
            for warning_code in upstream_warnings:
                attempt_context.warn(
                    warning_code,
                    component_name="upstream_value_validation",
                )

            if not upstream_passed:
                attempt_context.fail(
                    "upstream_value_validation",
                    "UPSTREAM_VALUE_VALIDATION_BLOCKED",
                )
                return attempt_context.result(
                    status_code=(
                        CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UPSTREAM_BLOCKED
                    )
                )

            attempt_context.pass_component("upstream_value_validation")
            return attempt_context.result(
                status_code=(
                    CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID_WITH_WARNINGS
                    if upstream_warnings
                    else CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_VALID
                ),
                passed=True,
                reader_status="validated_isolated",
            )

        context = last_changed_context or context
        context.fail("manifest_consistency", "MANIFEST_UNSTABLE")
        return context.result(
            status_code=CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_MANIFEST_UNSTABLE
        )
    except _ReaderRejected as rejection:
        return rejection.context.result(status_code=rejection.status_code)
    except Exception:
        context.fail(
            unexpected_component,
            "FILESYSTEM_READER_EXCEPTION_SANITIZED",
        )
        return context.result(
            status_code=CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SAFE_FAILURE
        )


def _is_valid_filesystem_policy(value: object) -> bool:
    if not isinstance(value, CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy):
        return False
    size_limits = (
        value.manifest_max_bytes,
        value.live_tick_max_bytes,
        value.latest_bars_max_bytes,
        value.symbol_spec_max_bytes,
        value.account_snapshot_max_bytes,
    )
    return all(_is_positive_int(limit) for limit in size_limits) and (
        _is_retry_count(value.max_manifest_consistency_retries)
    )


def _resolve_allowed_root(value: object, context: "_ReaderContext") -> Path:
    path = _path_from_input(value)
    if path is None:
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_INPUT_INVALID,
            "filesystem_boundary",
            "ALLOWED_ROOT_INPUT_INVALID",
        )
    try:
        resolved = path.resolve(strict=True)
        if not resolved.is_dir():
            raise NotADirectoryError
    except (OSError, RuntimeError):
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_ROOT_REJECTED,
            "filesystem_boundary",
            "ALLOWED_ROOT_REJECTED",
        )
    return resolved


def _resolve_bundle_dir(
    value: object,
    resolved_root: Path,
    context: "_ReaderContext",
) -> Path:
    path = _path_from_input(value)
    if path is None:
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_INPUT_INVALID,
            "filesystem_boundary",
            "BUNDLE_DIRECTORY_INPUT_INVALID",
        )
    try:
        if path.is_symlink():
            _reject(
                context,
                CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SYMLINK_BLOCKED,
                "filesystem_boundary",
                "SYMLINK_BLOCKED",
            )
        resolved = path.resolve(strict=True)
        if not resolved.is_dir():
            raise NotADirectoryError
    except _ReaderRejected:
        raise
    except (OSError, RuntimeError):
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_DIRECTORY_REJECTED,
            "filesystem_boundary",
            "BUNDLE_DIRECTORY_REJECTED",
        )

    if not _is_within(resolved, resolved_root):
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_PATH_ESCAPE_BLOCKED,
            "filesystem_boundary",
            "PATH_ESCAPE_BLOCKED",
        )
    return resolved


def _path_from_input(value: object) -> Path | None:
    if not isinstance(value, (str, Path)):
        return None
    if isinstance(value, str) and (not value or value != value.strip()):
        return None
    try:
        return Path(value)
    except (OSError, TypeError, ValueError):
        return None


def _read_one_complete_attempt(
    *,
    bundle_dir: Path,
    policy: CanonicalMt4DemoReadonlyBundleV1FilesystemPolicy,
    context: "_ReaderContext",
) -> "_ReadAttempt | None":
    manifest_a, _ = _load_json_object(
        bundle_dir=bundle_dir,
        filename=_MANIFEST_FILENAME,
        max_bytes=policy.manifest_max_bytes,
        context=context,
    )

    payloads: dict[str, dict[str, Any]] = {}
    payload_bytes: dict[str, bytes] = {}
    for filename in _PAYLOAD_FILENAMES:
        payload, raw_bytes = _load_json_object(
            bundle_dir=bundle_dir,
            filename=filename,
            max_bytes=getattr(policy, _FILE_LIMIT_FIELDS[filename]),
            context=context,
        )
        payloads[filename] = payload
        payload_bytes[filename] = raw_bytes

    checksums = _declared_checksums(manifest_a)
    context.checksum_checked = bool(checksums)
    for filename, expected_checksum in checksums.items():
        actual_checksum = hashlib.sha256(payload_bytes[filename]).hexdigest()
        if actual_checksum != expected_checksum:
            context.checksum_passed = False
            context.fail("checksum", "CHECKSUM_MISMATCH")
            context.failure_status_code = (
                CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_CHECKSUM_MISMATCH
            )
            return None
    context.checksum_passed = True
    context.pass_component(
        "checksum",
        status_suffix="VALID" if checksums else "NOT_REQUIRED",
    )

    manifest_b, _ = _load_json_object(
        bundle_dir=bundle_dir,
        filename=_MANIFEST_FILENAME,
        max_bytes=policy.manifest_max_bytes,
        context=context,
    )
    context.manifest_consistency_checked = True
    if not _manifests_match(manifest_a, manifest_b):
        context.manifest_consistency_passed = False
        context.fail(
            "manifest_consistency",
            "MANIFEST_CHANGED_DURING_READ",
        )
        return _ReadAttempt(
            manifest=manifest_b,
            payloads=payloads,
            manifest_changed=True,
        )

    context.manifest_consistency_passed = True
    context.pass_component("manifest_consistency")
    return _ReadAttempt(
        manifest=manifest_b,
        payloads=payloads,
        manifest_changed=False,
    )


def _load_json_object(
    *,
    bundle_dir: Path,
    filename: str,
    max_bytes: int,
    context: "_ReaderContext",
) -> tuple[dict[str, Any], bytes]:
    component_name = _FILE_COMPONENTS[filename]
    path = _resolve_canonical_file(
        bundle_dir=bundle_dir,
        filename=filename,
        component_name=component_name,
        context=context,
    )
    try:
        if path.stat().st_size > max_bytes:
            _reject(
                context,
                CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_TOO_LARGE,
                component_name,
                "FILE_SIZE_LIMIT_EXCEEDED",
            )
        raw_bytes = _read_file_bytes(path)
    except _ReaderRejected:
        raise
    except OSError:
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_UNREADABLE,
            component_name,
            "FILE_UNREADABLE",
        )

    if len(raw_bytes) > max_bytes:
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_TOO_LARGE,
            component_name,
            "FILE_SIZE_LIMIT_EXCEEDED",
        )
    if raw_bytes.startswith(_UTF8_BOM):
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UTF8_INVALID,
            component_name,
            "UTF8_BOM_REJECTED",
        )

    try:
        text = raw_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_UTF8_INVALID,
            component_name,
            "UTF8_DECODE_INVALID",
        )
    try:
        parsed = json.loads(
            text,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_object_pairs,
        )
    except _DuplicateJsonKeyDetected:
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID,
            component_name,
            "JSON_DUPLICATE_KEY",
        )
    except (json.JSONDecodeError, ValueError):
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_INVALID,
            component_name,
            "JSON_INVALID",
        )
    if not isinstance(parsed, dict):
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_JSON_NOT_OBJECT,
            component_name,
            "JSON_NOT_OBJECT",
        )

    context.pass_component(component_name)
    return parsed, raw_bytes


def _resolve_canonical_file(
    *,
    bundle_dir: Path,
    filename: str,
    component_name: str,
    context: "_ReaderContext",
) -> Path:
    candidate = bundle_dir / filename
    try:
        if candidate.is_symlink():
            _reject(
                context,
                CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_SYMLINK_BLOCKED,
                component_name,
                "SYMLINK_BLOCKED",
            )
        resolved = candidate.resolve(strict=True)
    except _ReaderRejected:
        raise
    except FileNotFoundError:
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_MISSING,
            component_name,
            "FILE_NOT_FOUND",
        )
    except (OSError, RuntimeError):
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_UNREADABLE,
            component_name,
            "FILE_UNREADABLE",
        )

    if not _is_within(resolved, bundle_dir):
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_PATH_ESCAPE_BLOCKED,
            component_name,
            "PATH_ESCAPE_BLOCKED",
        )
    try:
        if not resolved.is_file():
            raise OSError
    except OSError:
        _reject(
            context,
            CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_FILE_UNREADABLE,
            component_name,
            "FILE_UNREADABLE",
        )
    return resolved


def _read_file_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _declared_checksums(manifest: dict[str, Any]) -> dict[str, str]:
    required_files = manifest.get("required_files")
    if not isinstance(required_files, list):
        return {}

    checksums: dict[str, str] = {}
    for descriptor in required_files:
        if not isinstance(descriptor, dict):
            continue
        filename = descriptor.get("filename")
        checksum = descriptor.get("content_sha256")
        if (
            filename in _PAYLOAD_FILENAMES
            and isinstance(checksum, str)
            and _SHA256_PATTERN.fullmatch(checksum) is not None
        ):
            checksums[filename] = checksum
    return checksums


def _manifests_match(
    manifest_a: dict[str, Any],
    manifest_b: dict[str, Any],
) -> bool:
    return all(
        manifest_a.get(field_name) == manifest_b.get(field_name)
        for field_name in _MANIFEST_CONSISTENCY_FIELDS
    )


def _safe_upstream_status(value: object) -> str:
    if isinstance(value, str) and _SAFE_UPSTREAM_STATUS_PATTERN.fullmatch(value):
        return value
    return "CANONICAL_MT4_BUNDLE_V1_VALUE_INPUT_INVALID"


def _safe_upstream_warnings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        warning_code
        for warning_code in value
        if isinstance(warning_code, str)
        and warning_code in _SAFE_UPSTREAM_WARNING_CODES
    ]


def _reject_json_constant(_: str) -> None:
    raise ValueError


def _reject_duplicate_object_pairs(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    seen: set[str] = set()
    for key, value in pairs:
        if key in seen:
            raise _DuplicateJsonKeyDetected
        seen.add(key)
        result[key] = value
    return result


def _is_within(candidate: Path, parent: Path) -> bool:
    try:
        candidate.relative_to(parent)
        return True
    except ValueError:
        return False


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_retry_count(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value in (0, 1)
    )


def _reject(
    context: "_ReaderContext",
    status_code: str,
    component_name: str,
    reason_code: str,
) -> None:
    context.fail(component_name, reason_code)
    raise _ReaderRejected(status_code=status_code, context=context)


@dataclass(frozen=True)
class _ReadAttempt:
    manifest: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    manifest_changed: bool


class _ReaderRejected(Exception):
    def __init__(self, *, status_code: str, context: "_ReaderContext") -> None:
        super().__init__()
        self.status_code = status_code
        self.context = context


class _DuplicateJsonKeyDetected(ValueError):
    pass


class _ReaderContext:
    def __init__(self) -> None:
        self.reason_codes: list[str] = []
        self.warning_codes: list[str] = []
        self.components: dict[str, dict[str, Any]] = {
            component_name: {
                "component_name": component_name,
                "passed": False,
                "status_code": self._component_status(
                    component_name,
                    "NOT_CHECKED",
                ),
                "reason_codes": [],
                "warning_codes": [],
            }
            for component_name in _COMPONENTS
        }
        self.manifest_consistency_checked = False
        self.manifest_consistency_passed = False
        self.checksum_checked = False
        self.checksum_passed = False
        self.upstream_value_passed = False
        self.upstream_value_status_code: str | None = None
        self.failure_status_code: str | None = None

    def pass_component(self, component_name: str, *, status_suffix: str = "VALID") -> None:
        component = self.components[component_name]
        component["passed"] = True
        component["status_code"] = self._component_status(
            component_name,
            status_suffix,
        )
        component["reason_codes"] = []

    def fail(self, component_name: str, reason_code: str) -> None:
        if reason_code not in self.reason_codes:
            self.reason_codes.append(reason_code)
        component = self.components[component_name]
        component["passed"] = False
        component["status_code"] = self._component_status(
            component_name,
            "INVALID",
        )
        if reason_code not in component["reason_codes"]:
            component["reason_codes"].append(reason_code)

    def warn(self, warning_code: str, *, component_name: str) -> None:
        if warning_code not in self.warning_codes:
            self.warning_codes.append(warning_code)
        component = self.components[component_name]
        if warning_code not in component["warning_codes"]:
            component["warning_codes"].append(warning_code)

    def result(
        self,
        *,
        status_code: str,
        passed: bool = False,
        reader_status: str = "blocked",
    ) -> dict[str, Any]:
        return {
            "passed": passed,
            "status_code": status_code,
            "validation_stage": VALIDATION_STAGE,
            "contract_version": CONTRACT_VERSION,
            "reader_status": reader_status,
            "reason_codes": list(self.reason_codes),
            "warning_codes": list(self.warning_codes),
            "component_statuses": [
                {
                    "component_name": component["component_name"],
                    "passed": component["passed"],
                    "status_code": component["status_code"],
                    "reason_codes": list(component["reason_codes"]),
                    "warning_codes": list(component["warning_codes"]),
                }
                for component in self.components.values()
            ],
            "manifest_consistency_checked": self.manifest_consistency_checked,
            "manifest_consistency_passed": self.manifest_consistency_passed,
            "checksum_checked": self.checksum_checked,
            "checksum_passed": self.checksum_passed,
            "upstream_value_passed": self.upstream_value_passed,
            "upstream_value_status_code": self.upstream_value_status_code,
            "ready_for_readonly_analysis": False,
            "next_allowed_stage": list(NEXT_ALLOWED_STAGE) if passed else [],
            "next_blocked_stage": list(NEXT_BLOCKED_STAGE),
            "read_only": True,
            "demo_only": True,
            "is_tradable": False,
            "can_execute": False,
            "is_trading_permission": False,
            "is_execution_instruction": False,
            "allowed_to_call_ea": False,
            "allowed_to_modify_risk": False,
        }

    @staticmethod
    def _component_status(component_name: str, suffix: str) -> str:
        return (
            "CANONICAL_MT4_BUNDLE_V1_FILESYSTEM_"
            f"{component_name.upper()}_{suffix}"
        )
