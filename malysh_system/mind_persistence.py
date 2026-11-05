"""
Durable persistence adapter for the complete MindState.

This module reuses the existing Supervisor infrastructure:

    WAL
    StateStore
    state_hash

It does not replace Supervisor state and does not modify historical
runtime files. A caller supplies an isolated storage directory.

Persisted MindState fields:

    subject
    canonical
    observations
    reflections
    experience
    human
    main
    possible
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from malysh_system.supervisor import (
    StateStore,
    WAL,
    state_hash,
    utc_now,
)
from malysh_system.unified_mind import MindState


MIND_SCHEMA = "malysh.mind-state.v1"
STORE_SCHEMA = "malysh.mind-store.v1"

SNAPSHOT_FIELDS = (
    "subject",
    "canonical",
    "observations",
    "reflections",
    "experience",
    "human",
    "main",
    "possible",
)


CODEC_MARKER = "__malysh_persistence_type__"
CODEC_VERSION = "malysh.lossless-json.v1"


def encode_lossless(
    value: Any,
) -> Any:
    """
    Convert Python containers into a JSON-compatible tagged form.

    JSON object keys are always strings. MindState observations and
    reflections may contain integer keys, so writing ordinary mappings
    directly to JSON is not a lossless operation.

    This representation preserves:

        dict key types
        mapping insertion order
        list versus tuple
        scalar values
    """

    if value is None:
        return None

    if isinstance(
        value,
        (
            bool,
            int,
            float,
            str,
        ),
    ):
        return value

    if isinstance(
        value,
        dict,
    ):
        return {
            CODEC_MARKER:
                "dict",

            "items": [
                [
                    encode_lossless(key),
                    encode_lossless(item),
                ]
                for key, item in value.items()
            ],
        }

    if isinstance(
        value,
        list,
    ):
        return {
            CODEC_MARKER:
                "list",

            "items": [
                encode_lossless(item)
                for item in value
            ],
        }

    if isinstance(
        value,
        tuple,
    ):
        return {
            CODEC_MARKER:
                "tuple",

            "items": [
                encode_lossless(item)
                for item in value
            ],
        }

    raise TypeError(
        "unsupported persistence value: "
        + type(value).__name__
    )


def decode_lossless(
    value: Any,
) -> Any:
    """
    Reverse encode_lossless() without changing stored value types.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (
            bool,
            int,
            float,
            str,
        ),
    ):
        return value

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            "invalid lossless JSON node"
        )

    node_type = value.get(
        CODEC_MARKER
    )

    items = value.get(
        "items"
    )

    if not isinstance(
        items,
        list,
    ):
        raise ValueError(
            "lossless JSON node has no item list"
        )

    if node_type == "dict":
        result = {}

        for pair in items:
            if (
                not isinstance(pair, list)
                or
                len(pair) != 2
            ):
                raise ValueError(
                    "invalid encoded mapping item"
                )

            key = decode_lossless(
                pair[0]
            )

            item = decode_lossless(
                pair[1]
            )

            result[key] = item

        return result

    if node_type == "list":
        return [
            decode_lossless(item)
            for item in items
        ]

    if node_type == "tuple":
        return tuple(
            decode_lossless(item)
            for item in items
        )

    raise ValueError(
        "unknown lossless JSON node type: "
        + str(node_type)
    )


def encode_snapshot(
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Encode one complete MindState snapshot.
    """

    encoded = encode_lossless(
        deepcopy(
            dict(snapshot)
        )
    )

    if not isinstance(
        encoded,
        dict,
    ):
        raise TypeError(
            "encoded snapshot must be a mapping"
        )

    return encoded


def decode_snapshot(
    encoded: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Decode one complete MindState snapshot.
    """

    decoded = decode_lossless(
        deepcopy(
            dict(encoded)
        )
    )

    if not isinstance(
        decoded,
        dict,
    ):
        raise ValueError(
            "decoded snapshot must be a mapping"
        )

    return decoded


def validate_snapshot(
    snapshot: Mapping[str, Any],
) -> dict[str, bool]:
    """
    Validate the structural invariants of one persisted MindState.
    """

    fields_present = all(
        field in snapshot
        for field in SNAPSHOT_FIELDS
    )

    mappings_valid = all(
        isinstance(
            snapshot.get(field),
            dict,
        )
        for field in (
            "canonical",
            "observations",
            "reflections",
            "experience",
            "human",
        )
    )

    possible_valid = isinstance(
        snapshot.get("possible"),
        list,
    )

    subject_valid = (
        snapshot.get("subject")
        ==
        "Malysh"
    )

    return {
        "all_fields_present":
            fields_present,

        "one_subject":
            subject_valid,

        "mapping_fields_valid":
            mappings_valid,

        "possible_is_list":
            possible_valid,
    }


def mind_from_snapshot(
    snapshot: Mapping[str, Any],
) -> MindState:
    """
    Construct an isolated MindState from a verified snapshot.
    """

    copied = deepcopy(
        dict(snapshot)
    )

    invariants = validate_snapshot(
        copied
    )

    if not all(invariants.values()):
        failed = [
            name
            for name, passed
            in invariants.items()
            if not passed
        ]

        raise ValueError(
            "invalid MindState snapshot: "
            + ", ".join(failed)
        )

    mind = MindState()

    mind.subject = copied["subject"]
    mind.canonical = copied["canonical"]
    mind.observations = copied["observations"]
    mind.reflections = copied["reflections"]
    mind.experience = copied["experience"]
    mind.human = copied["human"]
    mind.main = copied["main"]
    mind.possible = copied["possible"]

    if not mind.invariant():
        raise ValueError(
            "recovered MindState invariant failed"
        )

    if mind.snapshot() != copied:
        raise ValueError(
            "MindState reconstruction mismatch"
        )

    return mind


class MindPersistence:
    """
    Complete MindState storage using the existing WAL and StateStore.
    """

    def __init__(
        self,
        root: str | Path,
    ):
        self.root = Path(root)

        self.wal = WAL(
            self.root
            / "mind.wal.jsonl"
        )

        self.store = StateStore(
            self.root
            / "state.json",
            self.root
            / "checkpoints",
        )

    def _load_envelope(
        self,
    ) -> dict[str, Any]:
        state = self.store.load()

        if (
            state.get("schema")
            ==
            STORE_SCHEMA
        ):
            return state

        return {
            "schema":
                STORE_SCHEMA,

            "schema_version":
                1,

            "system_name":
                "Malysh Mind Persistence",

            "generation":
                0,

            "virtual_time":
                0,

            "status":
                "initialized",

            "active_cycle":
                None,

            "last_cycle":
                None,

            "modules":
                {},

            "metrics":
                {},

            "created_at":
                utc_now(),

            "updated_at":
                utc_now(),

            "mind":
                None,
        }

    def persist(
        self,
        mind: MindState,
        source: str = "thinking-cycle",
    ) -> dict[str, Any]:
        """
        Persist one complete MindState and create a checkpoint.
        """

        if not isinstance(
            mind,
            MindState,
        ):
            raise TypeError(
                "mind must be MindState"
            )

        if not mind.invariant():
            raise ValueError(
                "MindState invariant failed before persistence"
            )

        snapshot = mind.snapshot()

        snapshot_invariants = validate_snapshot(
            snapshot
        )

        if not all(
            snapshot_invariants.values()
        ):
            raise ValueError(
                "MindState snapshot failed validation"
            )

        encoded_snapshot = encode_snapshot(
            snapshot
        )

        # Hash the exact representation written to JSON. This avoids
        # collisions caused by ordinary JSON coercing non-string
        # mapping keys into strings.
        snapshot_digest = state_hash(
            encoded_snapshot
        )

        envelope = self._load_envelope()

        previous_mind = envelope.get(
            "mind"
        )

        previous_digest = None

        if isinstance(previous_mind, dict):
            previous_digest = (
                previous_mind.get(
                    "snapshot_hash"
                )
            )

        generation = (
            int(
                envelope.get(
                    "generation",
                    0,
                )
            )
            + 1
        )

        self.wal.append(
            "MIND_STATE_PREPARED",
            {
                "generation":
                    generation,

                "source":
                    source,

                "snapshot_hash":
                    snapshot_digest,

                "previous_snapshot_hash":
                    previous_digest,
            },
        )

        envelope["generation"] = generation

        envelope["virtual_time"] = (
            int(
                envelope.get(
                    "virtual_time",
                    0,
                )
            )
            + 1
        )

        envelope["status"] = "ready"

        envelope["mind"] = {
            "schema":
                MIND_SCHEMA,

            "snapshot":
                encoded_snapshot,

            "snapshot_encoding":
                CODEC_VERSION,

            "snapshot_hash":
                snapshot_digest,

            "snapshot_invariants":
                snapshot_invariants,

            "source":
                source,

            "persisted_at":
                utc_now(),

            "previous_snapshot_hash":
                previous_digest,
        }

        envelope["last_cycle"] = {
            "generation":
                generation,

            "source":
                source,

            "snapshot_hash":
                snapshot_digest,
        }

        self.store.save(
            envelope
        )

        checkpoint = self.store.checkpoint(
            envelope
        )

        committed_event = self.wal.append(
            "MIND_STATE_COMMITTED",
            {
                "generation":
                    generation,

                "source":
                    source,

                "snapshot_hash":
                    snapshot_digest,

                "checkpoint":
                    str(checkpoint),

                "previous_snapshot_hash":
                    previous_digest,
            },
        )

        return {
            "schema":
                STORE_SCHEMA,

            "generation":
                generation,

            "snapshot_hash":
                snapshot_digest,

            "previous_snapshot_hash":
                previous_digest,

            "checkpoint":
                str(checkpoint),

            "wal_event_id":
                committed_event[
                    "event_id"
                ],

            "invariant_ok":
                True,
        }

    def recover(
        self,
    ) -> tuple[
        MindState,
        dict[str, Any],
    ]:
        """
        Recover the complete MindState from the latest checkpoint.
        """

        checkpoint = (
            self.store.latest_checkpoint()
        )

        if checkpoint is None:
            raise FileNotFoundError(
                "MindState checkpoint absent"
            )

        envelope = self._read_checkpoint(
            checkpoint
        )

        if (
            envelope.get("schema")
            !=
            STORE_SCHEMA
        ):
            raise ValueError(
                "unsupported MindState store schema"
            )

        mind_record = envelope.get(
            "mind"
        )

        if not isinstance(
            mind_record,
            dict,
        ):
            raise ValueError(
                "checkpoint contains no MindState"
            )

        if (
            mind_record.get("schema")
            !=
            MIND_SCHEMA
        ):
            raise ValueError(
                "unsupported MindState schema"
            )

        encoded_snapshot = mind_record.get(
            "snapshot"
        )

        if not isinstance(
            encoded_snapshot,
            dict,
        ):
            raise ValueError(
                "checkpoint MindState snapshot is invalid"
            )

        if (
            mind_record.get(
                "snapshot_encoding"
            )
            !=
            CODEC_VERSION
        ):
            raise ValueError(
                "unsupported MindState snapshot encoding"
            )

        expected_hash = mind_record.get(
            "snapshot_hash"
        )

        actual_hash = state_hash(
            encoded_snapshot
        )

        if actual_hash != expected_hash:
            raise ValueError(
                "MindState checkpoint hash mismatch"
            )

        snapshot = decode_snapshot(
            encoded_snapshot
        )

        mind = mind_from_snapshot(
            snapshot
        )

        recovered_snapshot = mind.snapshot()

        if recovered_snapshot != snapshot:
            raise ValueError(
                "recovered MindState differs from checkpoint"
            )

        event = self.wal.append(
            "MIND_STATE_RECOVERED",
            {
                "generation":
                    envelope.get(
                        "generation"
                    ),

                "checkpoint":
                    str(checkpoint),

                "snapshot_hash":
                    actual_hash,
            },
        )

        metadata = {
            "schema":
                STORE_SCHEMA,

            "generation":
                envelope.get(
                    "generation"
                ),

            "checkpoint":
                str(checkpoint),

            "snapshot_hash":
                actual_hash,

            "wal_event_id":
                event["event_id"],

            "snapshot_equal":
                True,

            "invariant_ok":
                mind.invariant(),
        }

        return (
            mind,
            metadata,
        )

    @staticmethod
    def _read_checkpoint(
        checkpoint: Path,
    ) -> dict[str, Any]:
        import json

        with checkpoint.open(
            "r",
            encoding="utf-8",
        ) as handle:
            value = json.load(
                handle
            )

        if not isinstance(
            value,
            dict,
        ):
            raise ValueError(
                "checkpoint root must be a mapping"
            )

        return value

    def inspect(
        self,
    ) -> dict[str, Any]:
        checkpoint = (
            self.store.latest_checkpoint()
        )

        events = (
            self.wal.read_valid_events()
        )

        state = self._load_envelope()

        mind_record = state.get(
            "mind"
        )

        return {
            "schema":
                STORE_SCHEMA,

            "generation":
                state.get(
                    "generation",
                    0,
                ),

            "snapshot_hash":
                (
                    mind_record.get(
                        "snapshot_hash"
                    )
                    if isinstance(
                        mind_record,
                        dict,
                    )
                    else None
                ),

            "wal_event_count":
                len(events),

            "wal_event_types":
                [
                    event.get("type")
                    for event in events
                ],

            "latest_checkpoint":
                (
                    str(checkpoint)
                    if checkpoint is not None
                    else None
                ),

            "recoverable":
                checkpoint is not None,
        }
