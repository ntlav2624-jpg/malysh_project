from copy import deepcopy
import json

import pytest

from malysh_system.mind_persistence import (
    CODEC_VERSION,
    MIND_SCHEMA,
    MindPersistence,
    decode_snapshot,
    mind_from_snapshot,
)
from malysh_system.thinking_cycle import (
    run_thinking_cycle,
)
from malysh_system.unified_mind import MindState


def working_mind(
    tmp_path,
):
    mind = MindState()

    result = run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        o345_n=59,
        old_result={
            "source":
                "persistence-test",

            "preserved":
                True,
        },
        unresolved={
            "status":
                "hypothesis",

            "text":
                "возможно",

            "revisable":
                True,
        },
        root=tmp_path / "cycle",
        mind=mind,
    )

    assert all(
        result["invariants"].values()
    )

    return mind, result


def test_complete_snapshot_round_trip(
    tmp_path,
):
    mind, _ = working_mind(
        tmp_path
    )

    before = mind.snapshot()

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    commit = persistence.persist(
        mind,
        source="test-round-trip",
    )

    recovered, metadata = (
        persistence.recover()
    )

    after = recovered.snapshot()

    assert commit["invariant_ok"] is True
    assert metadata["invariant_ok"] is True
    assert metadata["snapshot_equal"] is True

    assert after == before
    assert recovered is not mind

    assert set(after) == {
        "subject",
        "canonical",
        "observations",
        "reflections",
        "experience",
        "human",
        "main",
        "possible",
    }


def test_round_trip_preserves_every_field(
    tmp_path,
):
    mind, _ = working_mind(
        tmp_path
    )

    before = mind.snapshot()

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    persistence.persist(
        mind
    )

    recovered, _ = (
        persistence.recover()
    )

    after = recovered.snapshot()

    for field in (
        "subject",
        "canonical",
        "observations",
        "reflections",
        "experience",
        "human",
        "main",
        "possible",
    ):
        assert after[field] == before[field]


def test_recovered_state_is_reference_isolated(
    tmp_path,
):
    mind, _ = working_mind(
        tmp_path
    )

    original = mind.snapshot()

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    persistence.persist(
        mind
    )

    recovered, _ = (
        persistence.recover()
    )

    recovered.canonical[
        "mutation"
    ] = True

    recovered.possible.append(
        {
            "mutation": True
        }
    )

    assert mind.snapshot() == original

    persisted_again, _ = (
        persistence.recover()
    )

    assert (
        "mutation"
        not in
        persisted_again.canonical
    )

    assert {
        "mutation": True
    } not in persisted_again.possible


def test_wal_event_sequence(
    tmp_path,
):
    mind, _ = working_mind(
        tmp_path
    )

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    persistence.persist(
        mind
    )

    persistence.recover()

    events = (
        persistence.wal
        .read_valid_events()
    )

    assert [
        event["type"]
        for event in events
    ] == [
        "MIND_STATE_PREPARED",
        "MIND_STATE_COMMITTED",
        "MIND_STATE_RECOVERED",
    ]


def test_checkpoint_contains_full_mind(
    tmp_path,
):
    mind, _ = working_mind(
        tmp_path
    )

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    commit = persistence.persist(
        mind
    )

    checkpoint = (
        persistence.store
        .latest_checkpoint()
    )

    assert checkpoint is not None

    envelope = json.loads(
        checkpoint.read_text(
            encoding="utf-8"
        )
    )

    assert (
        envelope["mind"]["schema"]
        ==
        MIND_SCHEMA
    )

    assert (
        envelope["mind"][
            "snapshot_encoding"
        ]
        ==
        CODEC_VERSION
    )

    decoded = decode_snapshot(
        envelope["mind"]["snapshot"]
    )

    assert decoded == mind.snapshot()

    assert (
        envelope["mind"][
            "snapshot_hash"
        ]
        ==
        commit["snapshot_hash"]
    )


def test_hash_tampering_is_detected(
    tmp_path,
):
    mind, _ = working_mind(
        tmp_path
    )

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    persistence.persist(
        mind
    )

    checkpoint = (
        persistence.store
        .latest_checkpoint()
    )

    assert checkpoint is not None

    value = json.loads(
        checkpoint.read_text(
            encoding="utf-8"
        )
    )

    encoded_snapshot = (
        value["mind"]["snapshot"]
    )

    # Do not depend on internal position of "canonical".
    # Modify the encoded snapshot itself without updating its
    # persisted SHA-256. Recovery must therefore reject it.
    assert (
        encoded_snapshot[
            "__malysh_persistence_type__"
        ]
        ==
        "dict"
    )

    encoded_snapshot["items"].append(
        [
            "TAMPERED_KEY",
            "TAMPERED_VALUE",
        ]
    )

    checkpoint.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="hash mismatch",
    ):
        persistence.recover()

def test_damaged_wal_line_does_not_hide_valid_events(
    tmp_path,
):
    mind, _ = working_mind(
        tmp_path
    )

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    persistence.persist(
        mind
    )

    with persistence.wal.path.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            "{damaged-json\n"
        )

    events = (
        persistence.wal
        .read_valid_events()
    )

    assert [
        event["type"]
        for event in events
    ] == [
        "MIND_STATE_PREPARED",
        "MIND_STATE_COMMITTED",
    ]

    recovered, metadata = (
        persistence.recover()
    )

    assert recovered.invariant()
    assert metadata["invariant_ok"] is True


def test_recovered_mind_continues_next_cycle(
    tmp_path,
):
    mind, first = working_mind(
        tmp_path
    )

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    first_commit = persistence.persist(
        mind,
        source="cycle-t",
    )

    recovered, recovery = (
        persistence.recover()
    )

    second = run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=59,
        old_result={
            "source":
                "cycle-t-plus-one",

            "previous_snapshot_hash":
                recovery[
                    "snapshot_hash"
                ],
        },
        unresolved={
            "status":
                "hypothesis",

            "text":
                "возможно t+1",

            "revisable":
                True,
        },
        root=tmp_path / "cycle-next",
        mind=recovered,
    )

    assert all(
        second["invariants"].values()
    )

    assert (
        second["mind"]["canonical"]
        ==
        first["mind"]["canonical"]
    )

    second_commit = persistence.persist(
        recovered,
        source="cycle-t-plus-one",
    )

    assert (
        second_commit[
            "previous_snapshot_hash"
        ]
        ==
        first_commit[
            "snapshot_hash"
        ]
    )

    assert (
        second_commit["generation"]
        ==
        first_commit["generation"] + 1
    )


def test_constructor_rejects_incomplete_snapshot():
    with pytest.raises(
        ValueError,
        match="invalid MindState snapshot",
    ):
        mind_from_snapshot(
            {
                "subject": "Malysh"
            }
        )


def test_recovered_subject_cannot_be_changed():
    snapshot = {
        "subject": "AnotherSubject",
        "canonical": {},
        "observations": {},
        "reflections": {},
        "experience": {},
        "human": {},
        "main": None,
        "possible": [],
    }

    with pytest.raises(
        ValueError,
        match="one_subject",
    ):
        mind_from_snapshot(
            snapshot
        )


def test_persistence_does_not_modify_source_mind(
    tmp_path,
):
    mind, _ = working_mind(
        tmp_path
    )

    before = deepcopy(
        mind.snapshot()
    )

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    persistence.persist(
        mind
    )

    assert mind.snapshot() == before


def test_inspect_reports_recoverable_storage(
    tmp_path,
):
    mind, _ = working_mind(
        tmp_path
    )

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    before = persistence.inspect()

    assert before["recoverable"] is False

    persistence.persist(
        mind
    )

    after = persistence.inspect()

    assert after["recoverable"] is True
    assert after["snapshot_hash"]
    assert after["generation"] == 1


def test_lossless_codec_preserves_numeric_keys(
    tmp_path,
):
    mind = MindState()

    mind.observe(
        "numeric-key-test",
        {
            3: {
                4: {
                    5: "O345"
                }
            }
        },
    )

    mind.reflect(
        "tuple-test",
        {
            (3, 4, 5):
                [
                    1,
                    2,
                    3,
                ]
        },
    )

    before = mind.snapshot()

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    persistence.persist(
        mind,
        source="numeric-key-test",
    )

    recovered, metadata = (
        persistence.recover()
    )

    after = recovered.snapshot()

    assert metadata["snapshot_equal"] is True
    assert after == before

    assert (
        3
        in
        after[
            "observations"
        ][
            "numeric-key-test"
        ]
    )

    assert (
        (3, 4, 5)
        in
        after[
            "reflections"
        ][
            "tuple-test"
        ]
    )
