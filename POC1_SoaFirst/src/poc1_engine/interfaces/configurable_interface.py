from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from poc1_engine.ai.action_bridge import ActionBridge
from poc1_engine.ai.feature_blocks import FeatureBlockRegistry
from poc1_engine.runtime.runtime_schema import RuntimeSchemaRegistry

MANIFEST_SCHEMA_VERSION = "1.0"
VALIDATOR_VERSION = "configurable_interface_validator_v1"
SUPPORTED_ROLES = frozenset({"observation", "action"})
SUPPORTED_REPRESENTATION_KINDS = frozenset({"dense_vector"})
SUPPORTED_PLANES = frozenset({"hot_control"})
SUPPORTED_SHAPE_MODES = frozenset({"fixed_width", "bounded_batch"})
SUPPORTED_FRESHNESS_POLICIES = frozenset({"reuse_last", "cadence_aligned", "strict_fresh"})
SUPPORTED_RUNTIME_BINDINGS = frozenset({"compiled_startup_plan_v1"})


@dataclass(frozen=True)
class InterfacePointManifest:
    channel_id: str
    role: str
    representation_kind: str
    plane: str
    runtime_family: str
    producer: str
    consumer: str
    location: str
    what: str
    where: str
    what_it_does: str
    cadence_planktics: int
    freshness_policy: str
    stale_values_allowed: bool
    resampling_owner: str
    dtype: str
    width: int
    shape_mode: str
    bounded_entity_count: int
    feature_blocks: tuple[str, ...] = field(default_factory=tuple)
    action_block_name: str = ""
    valid_configuration_space: Mapping[str, Any] = field(default_factory=dict)
    exclusion_zones: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "InterfacePointManifest":
        data = dict(payload)
        data["feature_blocks"] = tuple(payload.get("feature_blocks", ()))
        return cls(**data)


@dataclass(frozen=True)
class ConfigurableInterfaceManifest:
    manifest_id: str
    manifest_version: str
    schema_version: str
    runtime_binding: str
    human_doc_relative_path: str
    stakeholder_summary: str
    channels: tuple[InterfacePointManifest, ...]
    supported_roles: tuple[str, ...] = field(default_factory=tuple)
    supported_representation_kinds: tuple[str, ...] = field(default_factory=tuple)
    deferred_roles: tuple[str, ...] = field(default_factory=tuple)
    boundary_and_exclusion_zones: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ConfigurableInterfaceManifest":
        return cls(
            manifest_id=str(payload["manifest_id"]),
            manifest_version=str(payload["manifest_version"]),
            schema_version=str(payload["schema_version"]),
            runtime_binding=str(payload["runtime_binding"]),
            human_doc_relative_path=str(payload["human_doc_relative_path"]),
            stakeholder_summary=str(payload.get("stakeholder_summary", "")),
            channels=tuple(InterfacePointManifest.from_dict(item) for item in payload.get("channels", ())),
            supported_roles=tuple(str(item) for item in payload.get("supported_roles", ())),
            supported_representation_kinds=tuple(str(item) for item in payload.get("supported_representation_kinds", ())),
            deferred_roles=tuple(str(item) for item in payload.get("deferred_roles", ())),
            boundary_and_exclusion_zones=dict(payload.get("boundary_and_exclusion_zones", {})),
        )


@dataclass(frozen=True)
class CompiledInterfacePointPlan:
    channel_id: str
    role: str
    runtime_family: str
    width: int
    dtype: str
    representation_kind: str
    plane: str
    shape_mode: str
    bounded_entity_count: int
    feature_blocks: tuple[str, ...] = field(default_factory=tuple)
    block_offsets: tuple[tuple[str, int, int], ...] = field(default_factory=tuple)
    action_block_name: str = ""


@dataclass(frozen=True)
class InterfaceCompatibilityHandshake:
    manifest_id: str
    manifest_version: str
    manifest_hash: str
    validator_version: str
    validator_hash: str
    runtime_binding: str
    supported_roles: tuple[str, ...]
    supported_representation_kinds: tuple[str, ...]
    status: str
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CompiledConfigurableInterfacePlan:
    manifest: ConfigurableInterfaceManifest
    manifest_hash: str
    validator_version: str
    validator_hash: str
    compiled_channels: tuple[CompiledInterfacePointPlan, ...]
    compatibility_handshake: InterfaceCompatibilityHandshake

    def summary(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest.manifest_id,
            "manifest_version": self.manifest.manifest_version,
            "manifest_hash": self.manifest_hash,
            "validator_version": self.validator_version,
            "validator_hash": self.validator_hash,
            "runtime_binding": self.manifest.runtime_binding,
            "supported_roles": list(self.manifest.supported_roles),
            "supported_representation_kinds": list(self.manifest.supported_representation_kinds),
            "compiled_channels": [
                {
                    "channel_id": channel.channel_id,
                    "role": channel.role,
                    "runtime_family": channel.runtime_family,
                    "width": channel.width,
                    "dtype": channel.dtype,
                    "representation_kind": channel.representation_kind,
                    "plane": channel.plane,
                    "shape_mode": channel.shape_mode,
                    "bounded_entity_count": channel.bounded_entity_count,
                    "feature_blocks": list(channel.feature_blocks),
                    "block_offsets": [list(item) for item in channel.block_offsets],
                    "action_block_name": channel.action_block_name,
                }
                for channel in self.compiled_channels
            ],
            "compatibility_handshake": {
                "status": self.compatibility_handshake.status,
                "notes": list(self.compatibility_handshake.notes),
            },
        }


def _repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[4]


def default_manifest_path() -> Path:
    return _repo_root_from_file() / "POC1_SoaFirst" / "config" / "interfaces" / "agent_hot_control_manifest_v1.json"


def default_generated_doc_path() -> Path:
    return _repo_root_from_file() / "docs" / "2026 03 31 REV4.9 Configurable Interface Control.md"


def _json_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def manifest_hash_for_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validator_hash() -> str:
    source = Path(__file__).read_text(encoding="utf-8")
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def load_manifest(path: Path | None = None) -> ConfigurableInterfaceManifest:
    resolved = path or default_manifest_path()
    payload = json.loads(_json_text(resolved))
    return ConfigurableInterfaceManifest.from_dict(payload)


def validate_manifest(
    manifest: ConfigurableInterfaceManifest,
    runtime_schemas: RuntimeSchemaRegistry,
    feature_blocks: FeatureBlockRegistry,
    action_bridge: ActionBridge,
) -> list[str]:
    issues: list[str] = []
    if manifest.schema_version != MANIFEST_SCHEMA_VERSION:
        issues.append(f"schema_version mismatch: expected {MANIFEST_SCHEMA_VERSION} got {manifest.schema_version}")
    if manifest.runtime_binding not in SUPPORTED_RUNTIME_BINDINGS:
        issues.append(f"unsupported runtime_binding: {manifest.runtime_binding}")
    if not manifest.channels:
        issues.append("manifest must define at least one channel")
    if set(manifest.supported_roles) - SUPPORTED_ROLES:
        issues.append(f"manifest supported_roles contains unsupported entries: {sorted(set(manifest.supported_roles) - SUPPORTED_ROLES)}")
    if set(manifest.supported_representation_kinds) - SUPPORTED_REPRESENTATION_KINDS:
        issues.append(
            "manifest supported_representation_kinds contains unsupported entries: "
            f"{sorted(set(manifest.supported_representation_kinds) - SUPPORTED_REPRESENTATION_KINDS)}"
        )
    if not manifest.human_doc_relative_path:
        issues.append("human_doc_relative_path must be declared")
    if not manifest.boundary_and_exclusion_zones:
        issues.append("top-level boundary_and_exclusion_zones must be declared")

    seen_ids: set[str] = set()
    roles_present: set[str] = set()
    for channel in manifest.channels:
        if channel.channel_id in seen_ids:
            issues.append(f"duplicate channel_id: {channel.channel_id}")
        seen_ids.add(channel.channel_id)
        roles_present.add(channel.role)
        if channel.role not in SUPPORTED_ROLES:
            issues.append(f"channel {channel.channel_id} has unsupported role {channel.role}")
        if channel.representation_kind not in SUPPORTED_REPRESENTATION_KINDS:
            issues.append(
                f"channel {channel.channel_id} has unsupported representation_kind {channel.representation_kind}"
            )
        if channel.plane not in SUPPORTED_PLANES:
            issues.append(f"channel {channel.channel_id} has unsupported plane {channel.plane}")
        if channel.shape_mode not in SUPPORTED_SHAPE_MODES:
            issues.append(f"channel {channel.channel_id} has unsupported shape_mode {channel.shape_mode}")
        if channel.freshness_policy not in SUPPORTED_FRESHNESS_POLICIES:
            issues.append(f"channel {channel.channel_id} has unsupported freshness_policy {channel.freshness_policy}")
        if channel.cadence_planktics < 1:
            issues.append(f"channel {channel.channel_id} cadence_planktics must be >= 1")
        if channel.bounded_entity_count < 1:
            issues.append(f"channel {channel.channel_id} bounded_entity_count must be >= 1")
        if channel.width < 1:
            issues.append(f"channel {channel.channel_id} width must be >= 1")
        if not channel.what or not channel.where or not channel.what_it_does:
            issues.append(f"channel {channel.channel_id} must define what/where/what_it_does")
        if not channel.valid_configuration_space:
            issues.append(f"channel {channel.channel_id} must define valid_configuration_space")
        if not channel.exclusion_zones:
            issues.append(f"channel {channel.channel_id} must define exclusion_zones")
        try:
            runtime_schema = runtime_schemas.get(channel.runtime_family)
        except KeyError:
            issues.append(f"channel {channel.channel_id} references unknown runtime_family {channel.runtime_family}")
            continue
        if channel.role == "observation":
            if not channel.feature_blocks:
                issues.append(f"observation channel {channel.channel_id} must define feature_blocks")
            compiled_width = 0
            for block_name in channel.feature_blocks:
                try:
                    block = feature_blocks.get(block_name)
                except KeyError:
                    issues.append(f"channel {channel.channel_id} references unknown feature block {block_name}")
                    continue
                if block.runtime_family != runtime_schema.family_name:
                    issues.append(
                        f"channel {channel.channel_id} block {block_name} runtime_family mismatch: "
                        f"{block.runtime_family} vs {runtime_schema.family_name}"
                    )
                compiled_width += int(block.contract.width)
            if compiled_width != channel.width:
                issues.append(
                    f"channel {channel.channel_id} width mismatch: manifest={channel.width} compiled={compiled_width}"
                )
        elif channel.role == "action":
            if not channel.action_block_name:
                issues.append(f"action channel {channel.channel_id} must define action_block_name")
            else:
                try:
                    action_block = action_bridge.get(channel.action_block_name)
                except KeyError:
                    issues.append(f"channel {channel.channel_id} references unknown action block {channel.action_block_name}")
                else:
                    if action_block.width != channel.width:
                        issues.append(
                            f"channel {channel.channel_id} width mismatch: manifest={channel.width} action_block={action_block.width}"
                        )
        if channel.valid_configuration_space.get("runtime_family") != channel.runtime_family:
            issues.append(f"channel {channel.channel_id} valid_configuration_space.runtime_family must match runtime_family")
    if "observation" not in roles_present:
        issues.append("manifest must include at least one observation channel")
    if "action" not in roles_present:
        issues.append("manifest must include at least one action channel")
    return issues


def compile_manifest(
    manifest: ConfigurableInterfaceManifest,
    runtime_schemas: RuntimeSchemaRegistry,
    feature_blocks: FeatureBlockRegistry,
    action_bridge: ActionBridge,
    *,
    manifest_text: str | None = None,
) -> CompiledConfigurableInterfacePlan:
    issues = validate_manifest(manifest, runtime_schemas, feature_blocks, action_bridge)
    if issues:
        raise ValueError("Configurable interface validation failed: " + "; ".join(issues))
    text = manifest_text if manifest_text is not None else json.dumps(_manifest_to_jsonable(manifest), sort_keys=True)
    manifest_digest = manifest_hash_for_text(text)
    compiled_channels: list[CompiledInterfacePointPlan] = []
    for channel in manifest.channels:
        if channel.role == "observation":
            offset = 0
            block_offsets: list[tuple[str, int, int]] = []
            for block_name in channel.feature_blocks:
                block = feature_blocks.get(block_name)
                width = int(block.contract.width)
                block_offsets.append((block_name, offset, width))
                offset += width
            compiled_channels.append(
                CompiledInterfacePointPlan(
                    channel_id=channel.channel_id,
                    role=channel.role,
                    runtime_family=channel.runtime_family,
                    width=channel.width,
                    dtype=channel.dtype,
                    representation_kind=channel.representation_kind,
                    plane=channel.plane,
                    shape_mode=channel.shape_mode,
                    bounded_entity_count=channel.bounded_entity_count,
                    feature_blocks=channel.feature_blocks,
                    block_offsets=tuple(block_offsets),
                )
            )
        else:
            compiled_channels.append(
                CompiledInterfacePointPlan(
                    channel_id=channel.channel_id,
                    role=channel.role,
                    runtime_family=channel.runtime_family,
                    width=channel.width,
                    dtype=channel.dtype,
                    representation_kind=channel.representation_kind,
                    plane=channel.plane,
                    shape_mode=channel.shape_mode,
                    bounded_entity_count=channel.bounded_entity_count,
                    action_block_name=channel.action_block_name,
                )
            )
    v_hash = validator_hash()
    handshake = InterfaceCompatibilityHandshake(
        manifest_id=manifest.manifest_id,
        manifest_version=manifest.manifest_version,
        manifest_hash=manifest_digest,
        validator_version=VALIDATOR_VERSION,
        validator_hash=v_hash,
        runtime_binding=manifest.runtime_binding,
        supported_roles=tuple(manifest.supported_roles),
        supported_representation_kinds=tuple(manifest.supported_representation_kinds),
        status="pass",
        notes=("startup_validation_passed", "startup_compilation_complete", "hot_path_runtime_lookup_frozen"),
    )
    return CompiledConfigurableInterfacePlan(
        manifest=manifest,
        manifest_hash=manifest_digest,
        validator_version=VALIDATOR_VERSION,
        validator_hash=v_hash,
        compiled_channels=tuple(compiled_channels),
        compatibility_handshake=handshake,
    )


def load_and_compile_default_manifest(
    runtime_schemas: RuntimeSchemaRegistry,
    feature_blocks: FeatureBlockRegistry,
    action_bridge: ActionBridge,
) -> CompiledConfigurableInterfacePlan:
    path = default_manifest_path()
    text = _json_text(path)
    manifest = ConfigurableInterfaceManifest.from_dict(json.loads(text))
    return compile_manifest(manifest, runtime_schemas, feature_blocks, action_bridge, manifest_text=text)


def render_human_readable_interface_doc(plan: CompiledConfigurableInterfacePlan) -> str:
    lines: list[str] = [
        f"# 2026 03 31 REV4.9 Configurable Interface Control",
        "",
        "## Purpose",
        "Define the first bounded configurable engine-model interface slice for the fallback-first POC without changing the hot-path runtime mapping.",
        "",
        "## Canonical source",
        f"- Canonical manifest: `POC1_SoaFirst/config/interfaces/agent_hot_control_manifest_v1.json`",
        f"- Manifest ID: `{plan.manifest.manifest_id}`",
        f"- Manifest version: `{plan.manifest.manifest_version}`",
        f"- Manifest hash: `{plan.manifest_hash}`",
        f"- Validator version: `{plan.validator_version}`",
        f"- Validator hash: `{plan.validator_hash}`",
        "",
        "## Current bounded implementation decision",
        "- Startup loads the canonical manifest.",
        "- Startup validates the manifest against runtime schemas, feature blocks, and action blocks.",
        "- Startup compiles the manifest into an immutable runtime plan.",
        "- The compiled plan is bound to the existing hardcoded hot-path mapping rather than replacing it.",
        "- No per-plank-tic schema walking, string lookup, or runtime layout mutation is allowed.",
        "",
        "## Required configurable-interface constraints now enforced",
        "- Interface points define what they are, where they are, and what they do.",
        "- Boundary and exclusion zones are declared explicitly.",
        "- A stakeholder-readable interface document and a programmatic validator are both present and synchronized from the canonical manifest.",
        "- The valid configuration space is maximized within the implemented subset while invalid combinations are rejected at startup.",
        "- Performance-sensitive behavior is frozen into a startup-compiled plan.",
        "",
        "## Interface points",
        "",
    ]
    for channel in plan.manifest.channels:
        lines.extend(
            [
                f"### `{channel.channel_id}`",
                f"- Role: `{channel.role}`",
                f"- Representation kind: `{channel.representation_kind}`",
                f"- Plane: `{channel.plane}`",
                f"- Runtime family: `{channel.runtime_family}`",
                f"- Producer -> consumer: `{channel.producer}` -> `{channel.consumer}`",
                f"- What: {channel.what}",
                f"- Where: {channel.where}",
                f"- What it does: {channel.what_it_does}",
                f"- Location binding: `{channel.location}`",
                f"- Timing: cadence={channel.cadence_planktics} plank-tics, freshness_policy=`{channel.freshness_policy}`, stale_values_allowed=`{channel.stale_values_allowed}`",
                f"- Shape: mode=`{channel.shape_mode}`, width=`{channel.width}`, bounded_entity_count=`{channel.bounded_entity_count}`",
            ]
        )
        if channel.feature_blocks:
            lines.append(f"- Feature blocks: {', '.join(channel.feature_blocks)}")
        if channel.action_block_name:
            lines.append(f"- Action block: `{channel.action_block_name}`")
        lines.extend(
            [
                "- Valid configuration space:",
                f"  - {json.dumps(channel.valid_configuration_space, sort_keys=True)}",
                "- Exclusion zones:",
                f"  - {json.dumps(channel.exclusion_zones, sort_keys=True)}",
                "",
            ]
        )
    lines.extend(
        [
            "## Compiled runtime plan",
            "",
        ]
    )
    for compiled in plan.compiled_channels:
        lines.extend(
            [
                f"- `{compiled.channel_id}` => role=`{compiled.role}` width=`{compiled.width}` runtime_family=`{compiled.runtime_family}` plane=`{compiled.plane}`",
            ]
        )
        if compiled.block_offsets:
            lines.append(f"  - Block offsets: {list(compiled.block_offsets)}")
        if compiled.action_block_name:
            lines.append(f"  - Action block binding: `{compiled.action_block_name}`")
    lines.extend(
        [
            "",
            "## Deferred explicitly",
            "- Runtime-dynamic schema interpretation in the plank-tic loop.",
            "- Binary manifest serialization.",
            "- Warm/cold semantic plane channels in implementation.",
            "- Reward, done/reset, memory, report, latent, narration, graph, image, token, and ragged channel implementations.",
            "- Replacing the existing hardcoded hot-path mapping in this pass.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_human_readable_interface_doc(plan: CompiledConfigurableInterfacePlan, path: Path | None = None) -> Path:
    out_path = path or default_generated_doc_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_human_readable_interface_doc(plan), encoding="utf-8")
    return out_path


def _manifest_to_jsonable(manifest: ConfigurableInterfaceManifest) -> dict[str, Any]:
    return {
        "manifest_id": manifest.manifest_id,
        "manifest_version": manifest.manifest_version,
        "schema_version": manifest.schema_version,
        "runtime_binding": manifest.runtime_binding,
        "human_doc_relative_path": manifest.human_doc_relative_path,
        "stakeholder_summary": manifest.stakeholder_summary,
        "supported_roles": list(manifest.supported_roles),
        "supported_representation_kinds": list(manifest.supported_representation_kinds),
        "deferred_roles": list(manifest.deferred_roles),
        "boundary_and_exclusion_zones": dict(manifest.boundary_and_exclusion_zones),
        "channels": [
            {
                "channel_id": channel.channel_id,
                "role": channel.role,
                "representation_kind": channel.representation_kind,
                "plane": channel.plane,
                "runtime_family": channel.runtime_family,
                "producer": channel.producer,
                "consumer": channel.consumer,
                "location": channel.location,
                "what": channel.what,
                "where": channel.where,
                "what_it_does": channel.what_it_does,
                "cadence_planktics": channel.cadence_planktics,
                "freshness_policy": channel.freshness_policy,
                "stale_values_allowed": channel.stale_values_allowed,
                "resampling_owner": channel.resampling_owner,
                "dtype": channel.dtype,
                "width": channel.width,
                "shape_mode": channel.shape_mode,
                "bounded_entity_count": channel.bounded_entity_count,
                "feature_blocks": list(channel.feature_blocks),
                "action_block_name": channel.action_block_name,
                "valid_configuration_space": dict(channel.valid_configuration_space),
                "exclusion_zones": dict(channel.exclusion_zones),
            }
            for channel in manifest.channels
        ],
    }
