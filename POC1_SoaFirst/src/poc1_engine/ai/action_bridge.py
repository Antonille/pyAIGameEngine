from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Sequence

import numpy as np

from poc1_engine.ai.transfer_planner import FamilyTransferPlan, TransferBatchPlan
from poc1_engine.interfaces.ai_api import AIActionPacket


@dataclass(frozen=True)
class ActionBlockSchema:
    block_name: str
    width: int
    application_mode: str
    semantics: str
    clip_min: float = -1.0
    clip_max: float = 1.0
    cache_hit_mode: str = "reuse_packet"


@dataclass(frozen=True)
class PacketCacheEntry:
    cache_key: tuple[str, str, str, tuple[int, ...]]
    feature_signature: str
    generation_id: int
    packet: AIActionPacket
    generated_cycle: int
    last_served_cycle: int


@dataclass(frozen=True)
class PacketOwnershipEntry:
    ownership_scope: str
    ownership_key: str
    generation_id: int
    packet: AIActionPacket
    last_cycle: int


@dataclass(frozen=True)
class ActionPacketBuildResult:
    packets: tuple[AIActionPacket, ...]
    summary: dict[str, int]


@dataclass
class ActionBridge:
    action_blocks: dict[str, ActionBlockSchema] = field(default_factory=dict)
    packet_cache: dict[tuple[str, str, str, tuple[int, ...]], PacketCacheEntry] = field(default_factory=dict)
    ownership_registry: dict[str, PacketOwnershipEntry] = field(default_factory=dict)
    next_generation_id: int = 1

    def register(self, block: ActionBlockSchema) -> None:
        self.action_blocks[block.block_name] = block

    def get(self, block_name: str) -> ActionBlockSchema:
        return self.action_blocks[block_name]

    def build_packets_for_batch(
        self,
        family_plan: FamilyTransferPlan,
        batch: TransferBatchPlan,
        staging: np.ndarray,
        cycle: int,
    ) -> ActionPacketBuildResult:
        packets: list[AIActionPacket] = []
        summary = self._new_packet_summary()
        entity_batch_signature = self._entity_batch_signature(batch)
        entity_batch_digest = self._entity_batch_digest(entity_batch_signature)
        feature_signature = self._feature_signature(staging)

        for output_block_name in batch.output_blocks:
            block = self.get(output_block_name)
            cache_key = (family_plan.family_name, family_plan.runtime_family, output_block_name, entity_batch_signature)
            cache_entry = self.packet_cache.get(cache_key)
            ownership_scope = self._ownership_scope(family_plan, batch, output_block_name)
            ownership_key = self._ownership_key(ownership_scope, entity_batch_digest)
            active_owner = self.ownership_registry.get(ownership_scope)

            cache_fresh = cache_entry is not None and (cycle - cache_entry.generated_cycle) <= max(batch.max_output_staleness, 0)
            same_features = cache_entry is not None and cache_entry.feature_signature == feature_signature

            if cache_entry is not None and cache_fresh and same_features:
                summary["cache_hits"] += 1
                if active_owner is not None and active_owner.ownership_key != ownership_key:
                    summary["cache_invalidations"] += 1
                    invalidate_packet = self._make_invalidate_packet(
                        scope_entry=active_owner,
                        family_plan=family_plan,
                        batch=batch,
                        cycle=cycle,
                        cache_outcome="ownership_scope_rebind",
                    )
                    packets.append(invalidate_packet)
                    self._accumulate_packet_summary(summary, invalidate_packet)
                reused_packet = self._packet_for_cache_hit(
                    cache_entry=cache_entry,
                    cycle=cycle,
                    family_plan=family_plan,
                    batch=batch,
                    ownership_scope=ownership_scope,
                    ownership_key=ownership_key,
                    active_owner=active_owner,
                )
                packets.append(reused_packet)
                self._accumulate_packet_summary(summary, reused_packet)
                self.packet_cache[cache_key] = PacketCacheEntry(
                    cache_key=cache_entry.cache_key,
                    feature_signature=cache_entry.feature_signature,
                    generation_id=cache_entry.generation_id,
                    packet=cache_entry.packet,
                    generated_cycle=cache_entry.generated_cycle,
                    last_served_cycle=cycle,
                )
                self._register_ownership(ownership_scope, ownership_key, cache_entry.packet, cycle)
                continue

            summary["cache_misses"] += 1
            active_generation_id = active_owner.generation_id if active_owner is not None else None
            emit_invalidate = False
            if active_owner is not None:
                if active_owner.ownership_key != ownership_key:
                    emit_invalidate = True
                elif block.application_mode == "replace" and active_owner.generation_id != (cache_entry.generation_id if cache_entry else None):
                    emit_invalidate = True

            if emit_invalidate and active_owner is not None:
                summary["cache_invalidations"] += 1
                invalidate_packet = self._make_invalidate_packet(
                    scope_entry=active_owner,
                    family_plan=family_plan,
                    batch=batch,
                    cycle=cycle,
                    cache_outcome="miss_rebuild_invalidate",
                )
                packets.append(invalidate_packet)
                self._accumulate_packet_summary(summary, invalidate_packet)

            baseline_generation_id = active_generation_id
            baseline_ownership_key = active_owner.ownership_key if active_owner is not None else ""
            supersedes_generation_id = None
            supersedes_ownership_key = ""
            baseline_reason = "active_owner" if active_owner is not None else "none"
            ownership_transition = "new_owner"
            if block.application_mode == "delta":
                ownership_transition = "overlay_existing_owner" if active_owner is not None else "overlay_without_owner"
                if active_generation_id is None and cache_entry is not None:
                    baseline_generation_id = cache_entry.generation_id
                    baseline_ownership_key = cache_entry.packet.ownership_key
                    baseline_reason = "cache_entry"
            elif block.application_mode == "delete":
                ownership_transition = "retire_existing_owner" if active_owner is not None else "retire_without_owner"
                if active_owner is not None:
                    supersedes_generation_id = active_owner.generation_id
                    supersedes_ownership_key = active_owner.ownership_key
            elif block.application_mode == "replace":
                ownership_transition = "refresh_owner" if active_owner is not None and active_owner.ownership_key == ownership_key else "acquire_owner"
                if active_owner is not None:
                    supersedes_generation_id = active_owner.generation_id
                    supersedes_ownership_key = active_owner.ownership_key

            payload = self._mock_infer_payload(
                model_family=family_plan.family_name,
                output_block_name=output_block_name,
                staging=staging,
                width=block.width,
            )
            generation_id = self._allocate_generation_id()
            packet = AIActionPacket(
                protocol_version="action_packet_v4",
                actor_family=family_plan.runtime_family,
                actor_indices=tuple(int(i) for i in batch.entity_indices.tolist()),
                action_block_name=output_block_name,
                payload=tuple(tuple(float(v) for v in row) for row in payload.tolist()),
                source_model_family=family_plan.family_name,
                generated_cycle=cycle,
                generation_id=generation_id,
                baseline_generation_id=baseline_generation_id,
                baseline_ownership_key=baseline_ownership_key,
                supersedes_generation_id=supersedes_generation_id,
                supersedes_ownership_key=supersedes_ownership_key,
                ownership_scope=ownership_scope,
                ownership_key=ownership_key,
                apply_mode=block.application_mode,
                stage_deadline=family_plan.stage_deadline,
                metadata={
                    "application_mode": block.application_mode,
                    "batch_index": batch.batch_index,
                    "feature_blocks": tuple(batch.feature_blocks),
                    "cadence_planktics": batch.cadence_planktics,
                    "fallback_policy": batch.fallback_policy,
                    "cache_outcome": "miss_build",
                    "cache_key": self._cache_key_string(cache_key),
                    "cache_hit_mode": block.cache_hit_mode,
                    "ownership_scope": ownership_scope,
                    "ownership_key": ownership_key,
                    "entity_batch_digest": entity_batch_digest,
                    "ownership_transition": ownership_transition,
                    "baseline_required": block.application_mode in {"delta", "delete"},
                    "baseline_reason": baseline_reason,
                },
            )
            packets.append(packet)
            self._accumulate_packet_summary(summary, packet)
            self.packet_cache[cache_key] = PacketCacheEntry(
                cache_key=cache_key,
                feature_signature=feature_signature,
                generation_id=generation_id,
                packet=packet,
                generated_cycle=cycle,
                last_served_cycle=cycle,
            )
            self._register_ownership(ownership_scope, ownership_key, packet, cycle)
        return ActionPacketBuildResult(packets=tuple(packets), summary=summary)

    def apply_packets(self, state, packets: Sequence[AIActionPacket]) -> dict[str, int]:
        summary = {
            "packet_count": 0,
            "entity_count": 0,
            "bytes_total": 0,
            "no_change_count": 0,
            "delete_count": 0,
            "invalidate_count": 0,
        }
        if not packets:
            return summary

        ordered = sorted(packets, key=self._application_sort_key)
        for packet in ordered:
            actor_indices = np.asarray(packet.actor_indices, dtype=np.int32)
            summary["packet_count"] += 1
            summary["entity_count"] += int(actor_indices.size)
            if actor_indices.size == 0:
                continue
            payload = np.asarray(packet.payload, dtype=np.float32)
            if payload.ndim == 1 and payload.size > 0:
                payload = payload.reshape(1, -1)
            if payload.ndim == 0:
                payload = np.zeros((actor_indices.size, 0), dtype=np.float32)
            summary["bytes_total"] += int(payload.nbytes)

            block = self.get(packet.action_block_name)
            width = min(block.width, state.action.shape[1])
            mode = packet.apply_mode
            if mode == "replace":
                clipped = np.clip(payload[:, :width], block.clip_min, block.clip_max)
                state.action[actor_indices, :width] = clipped
            elif mode == "delta":
                clipped = np.clip(payload[:, :width], block.clip_min, block.clip_max)
                state.action[actor_indices, :width] += clipped
                state.action[actor_indices, :width] = np.clip(
                    state.action[actor_indices, :width], block.clip_min, block.clip_max
                )
            elif mode == "delete":
                delete_mask = np.ones(actor_indices.size, dtype=np.bool_)
                if payload.size > 0:
                    delete_mask = payload[:, 0] > 0.5
                delete_indices = actor_indices[delete_mask]
                if delete_indices.size > 0:
                    state.action[delete_indices, :width] = 0.0
                summary["delete_count"] += int(delete_indices.size)
            elif mode == "no_change":
                summary["no_change_count"] += int(actor_indices.size)
            elif mode == "invalidate":
                summary["invalidate_count"] += int(actor_indices.size)
            else:
                raise ValueError(f"Unsupported packet apply mode: {mode}")
        return summary

    def _application_sort_key(self, packet: AIActionPacket) -> tuple[int, int, str]:
        mode_rank = {"invalidate": 0, "replace": 1, "delta": 2, "delete": 3, "no_change": 4}
        batch_index = int(packet.metadata.get("batch_index", 0))
        return (mode_rank.get(packet.apply_mode, 99), batch_index, packet.action_block_name)

    def _new_packet_summary(self) -> dict[str, int]:
        return {
            "packet_count": 0,
            "entity_count": 0,
            "bytes_total": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_invalidations": 0,
            "no_change_count": 0,
            "delete_count": 0,
            "invalidate_count": 0,
        }

    def _accumulate_packet_summary(self, summary: dict[str, int], packet: AIActionPacket) -> None:
        actor_count = len(packet.actor_indices)
        payload_bytes = int(np.asarray(packet.payload, dtype=np.float32).nbytes) if packet.payload else 0
        summary["packet_count"] += 1
        summary["entity_count"] += actor_count
        summary["bytes_total"] += payload_bytes
        if packet.apply_mode == "no_change":
            summary["no_change_count"] += actor_count
        elif packet.apply_mode == "delete":
            if packet.payload:
                payload = np.asarray(packet.payload, dtype=np.float32)
                summary["delete_count"] += int(np.count_nonzero(payload[:, 0] > 0.5))
            else:
                summary["delete_count"] += actor_count
        elif packet.apply_mode == "invalidate":
            summary["invalidate_count"] += actor_count

    def _packet_for_cache_hit(
        self,
        cache_entry: PacketCacheEntry,
        cycle: int,
        family_plan: FamilyTransferPlan,
        batch: TransferBatchPlan,
        ownership_scope: str,
        ownership_key: str,
        active_owner: PacketOwnershipEntry | None,
    ) -> AIActionPacket:
        cached_packet = cache_entry.packet
        block = self.get(cached_packet.action_block_name)
        baseline_generation_id = cache_entry.generation_id if active_owner is None else active_owner.generation_id
        baseline_owner_key = active_owner.ownership_key if active_owner is not None else cached_packet.ownership_key
        common_kwargs = dict(
            protocol_version="action_packet_v4",
            actor_family=cached_packet.actor_family,
            actor_indices=cached_packet.actor_indices,
            action_block_name=cached_packet.action_block_name,
            source_model_family=cached_packet.source_model_family,
            generated_cycle=cycle,
            generation_id=cache_entry.generation_id,
            baseline_generation_id=baseline_generation_id,
            baseline_ownership_key=baseline_owner_key,
            supersedes_generation_id=baseline_generation_id,
            supersedes_ownership_key=baseline_owner_key,
            ownership_scope=ownership_scope,
            ownership_key=ownership_key,
            stage_deadline=family_plan.stage_deadline,
        )
        if block.cache_hit_mode == "no_change":
            return AIActionPacket(
                payload=tuple(),
                apply_mode="no_change",
                metadata={
                    **dict(cached_packet.metadata),
                    "batch_index": batch.batch_index,
                    "cache_outcome": "hit_no_change",
                    "reused_generation_id": cache_entry.generation_id,
                    "ownership_scope": ownership_scope,
                    "ownership_key": ownership_key,
                    "ownership_transition": "retain_owner_no_change",
                    "baseline_reason": "cache_hit_no_change",
                },
                **common_kwargs,
            )
        return AIActionPacket(
            payload=cached_packet.payload,
            apply_mode=cached_packet.apply_mode,
            metadata={
                **dict(cached_packet.metadata),
                "batch_index": batch.batch_index,
                "cache_outcome": "hit_reuse",
                "reused_generation_id": cache_entry.generation_id,
                "ownership_scope": ownership_scope,
                "ownership_key": ownership_key,
                "ownership_transition": "reuse_owner_payload",
                "baseline_reason": "cache_hit_reuse",
            },
            **common_kwargs,
        )

    def _make_invalidate_packet(
        self,
        scope_entry: PacketOwnershipEntry,
        family_plan: FamilyTransferPlan,
        batch: TransferBatchPlan,
        cycle: int,
        cache_outcome: str,
    ) -> AIActionPacket:
        previous = scope_entry.packet
        return AIActionPacket(
            protocol_version="action_packet_v4",
            actor_family=previous.actor_family,
            actor_indices=previous.actor_indices,
            action_block_name=previous.action_block_name,
            payload=tuple(),
            source_model_family=family_plan.family_name,
            generated_cycle=cycle,
            generation_id=self._allocate_generation_id(),
            baseline_generation_id=scope_entry.generation_id,
            baseline_ownership_key=scope_entry.ownership_key,
            supersedes_generation_id=scope_entry.generation_id,
            supersedes_ownership_key=scope_entry.ownership_key,
            ownership_scope=scope_entry.ownership_scope,
            ownership_key=scope_entry.ownership_key,
            apply_mode="invalidate",
            stage_deadline=family_plan.stage_deadline,
            metadata={
                **dict(previous.metadata),
                "application_mode": "invalidate",
                "batch_index": batch.batch_index,
                "cache_outcome": cache_outcome,
                "ownership_scope": scope_entry.ownership_scope,
                "ownership_key": scope_entry.ownership_key,
                "ownership_transition": "invalidate_owner_lane",
                "baseline_reason": "ownership_scope_transition",
            },
        )

    def _register_ownership(self, scope: str, key: str, packet: AIActionPacket, cycle: int) -> None:
        if packet.generation_id is None:
            return
        self.ownership_registry[scope] = PacketOwnershipEntry(
            ownership_scope=scope,
            ownership_key=key,
            generation_id=packet.generation_id,
            packet=packet,
            last_cycle=cycle,
        )

    def _cache_key_string(self, cache_key: tuple[str, str, str, tuple[int, ...]]) -> str:
        source_family, runtime_family, block_name, entity_sig = cache_key
        return f"{source_family}|{runtime_family}|{block_name}|{len(entity_sig)}"

    def _ownership_scope(self, family_plan: FamilyTransferPlan, batch: TransferBatchPlan, block_name: str) -> str:
        return f"{family_plan.family_name}|{family_plan.runtime_family}|{block_name}|batch{batch.batch_index}"

    def _ownership_key(self, ownership_scope: str, entity_batch_digest: str) -> str:
        return f"{ownership_scope}|{entity_batch_digest}"

    def _entity_batch_signature(self, batch: TransferBatchPlan) -> tuple[int, ...]:
        return tuple(int(i) for i in batch.entity_indices.tolist())

    def _entity_batch_digest(self, entity_batch_signature: tuple[int, ...]) -> str:
        arr = np.asarray(entity_batch_signature, dtype=np.int32)
        return hashlib.blake2b(arr.view(np.uint8), digest_size=8).hexdigest()

    def _feature_signature(self, staging: np.ndarray) -> str:
        arr = np.ascontiguousarray(staging.astype(np.float32, copy=False))
        return hashlib.blake2b(arr.view(np.uint8), digest_size=16).hexdigest()

    def _allocate_generation_id(self) -> int:
        generation_id = self.next_generation_id
        self.next_generation_id += 1
        return generation_id

    def _mock_infer_payload(
        self,
        model_family: str,
        output_block_name: str,
        staging: np.ndarray,
        width: int,
    ) -> np.ndarray:
        count = int(staging.shape[0])
        payload = np.zeros((count, width), dtype=np.float32)
        if count == 0:
            return payload

        pos_x = staging[:, 0] if staging.shape[1] > 0 else 0.0
        pos_y = staging[:, 1] if staging.shape[1] > 1 else 0.0
        linvel_x = staging[:, 3] if staging.shape[1] > 3 else 0.0
        linvel_y = staging[:, 4] if staging.shape[1] > 4 else 0.0
        reward_accum = staging[:, 17] if staging.shape[1] > 17 else 0.0
        team_id = staging[:, 15] if staging.shape[1] > 15 else 0.0
        action_x = np.clip((-0.12 * pos_x) - (0.45 * linvel_x), -1.0, 1.0)
        action_y = np.clip(0.20 + (0.03 * (1.5 - pos_y)) - (0.10 * linvel_y), -1.0, 1.0)
        action_aux = np.clip(0.02 * reward_accum, -1.0, 1.0)
        team_bias = np.where(np.asarray(team_id) > 0.5, 0.08, -0.08).astype(np.float32)

        if output_block_name == "action4_v1":
            payload[:, 0] = action_x
            if width > 1:
                payload[:, 1] = action_y
            if width > 2:
                payload[:, 2] = action_aux
            if width > 3:
                payload[:, 3] = 0.0
            return payload

        if output_block_name == "action4_delta_v1":
            payload[:, 0] = np.clip(0.08 * np.sign(-pos_x) + team_bias, -0.25, 0.25)
            if width > 1:
                payload[:, 1] = np.clip(0.05 * np.sign(2.0 - pos_y), -0.25, 0.25)
            if width > 2:
                payload[:, 2] = np.clip(0.03 * np.tanh(reward_accum), -0.25, 0.25)
            if width > 3:
                payload[:, 3] = 0.0
            return payload

        if output_block_name == "action4_hold_v1":
            static_team = staging[:, 0] if staging.shape[1] > 0 else 0.0
            static_policy = staging[:, 1] if staging.shape[1] > 1 else 0.0
            team_sign = np.where(np.asarray(static_team) > 0.5, 1.0, -1.0).astype(np.float32)
            policy_bias = 0.01 * np.asarray(static_policy, dtype=np.float32)
            payload[:, 0] = np.clip(0.05 * team_sign + policy_bias, -0.2, 0.2)
            if width > 1:
                payload[:, 1] = np.clip(0.02 * (9.0 - np.asarray(static_policy, dtype=np.float32)), -0.2, 0.2)
            if width > 2:
                payload[:, 2] = 0.0
            if width > 3:
                payload[:, 3] = 0.0
            return payload

        if output_block_name == "action4_delete_v1":
            static_team = staging[:, 0] if staging.shape[1] > 0 else 0.0
            static_policy = staging[:, 1] if staging.shape[1] > 1 else 0.0
            delete_mask = (np.asarray(static_team) > 0.5) & (np.asarray(static_policy) >= 8.0)
            payload[:, 0] = delete_mask.astype(np.float32)
            if width > 1:
                payload[:, 1:] = 0.0
            return payload

        raise KeyError(f"No mock inference payload rule registered for output block {output_block_name}")


def build_default_action_bridge() -> ActionBridge:
    bridge = ActionBridge()
    bridge.register(
        ActionBlockSchema(
            block_name="action4_v1",
            width=4,
            application_mode="replace",
            semantics="direct action vector written by primary reflex family",
            cache_hit_mode="reuse_packet",
        )
    )
    bridge.register(
        ActionBlockSchema(
            block_name="action4_delta_v1",
            width=4,
            application_mode="delta",
            semantics="contextual delta overlay applied after primary action packets",
            clip_min=-1.0,
            clip_max=1.0,
            cache_hit_mode="reuse_packet",
        )
    )
    bridge.register(
        ActionBlockSchema(
            block_name="action4_hold_v1",
            width=4,
            application_mode="replace",
            semantics="steady/hold contract that emits an initial replace packet and then explicit no_change packets on cache hits",
            cache_hit_mode="no_change",
        )
    )
    bridge.register(
        ActionBlockSchema(
            block_name="action4_delete_v1",
            width=4,
            application_mode="delete",
            semantics="cleanup/delete contract that zeros owned actions for flagged actors",
            cache_hit_mode="reuse_packet",
        )
    )
    return bridge


def summarize_action_packets(packets: Sequence[AIActionPacket]) -> list[str]:
    lines: list[str] = []
    for packet in packets:
        rows = len(packet.actor_indices)
        cols = len(packet.payload[0]) if packet.payload else 0
        lines.append(
            "source_family={source} actor_family={actor} block={block} mode={mode} rows={rows} cols={cols} deadline={deadline} version={version} generation={generation} baseline={baseline} baseline_key={baseline_key} supersedes={supersedes} supersedes_key={supersedes_key} scope={scope} key={key} cache={cache}".format(
                source=packet.source_model_family,
                actor=packet.actor_family,
                block=packet.action_block_name,
                mode=packet.apply_mode,
                rows=rows,
                cols=cols,
                deadline=packet.stage_deadline,
                version=packet.protocol_version,
                generation=packet.generation_id,
                baseline=packet.baseline_generation_id,
                baseline_key=packet.baseline_ownership_key.split("|")[-1] if packet.baseline_ownership_key else "",
                supersedes=packet.supersedes_generation_id,
                supersedes_key=packet.supersedes_ownership_key.split("|")[-1] if packet.supersedes_ownership_key else "",
                scope=packet.ownership_scope,
                key=packet.ownership_key.split("|")[-1] if packet.ownership_key else "",
                cache=packet.metadata.get("cache_outcome", ""),
            )
        )
    return lines
