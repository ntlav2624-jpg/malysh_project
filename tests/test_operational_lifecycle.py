import json

from malysh_system.operational_lifecycle import (
    OperationalLifecycle,
)


HISTORY = [
    [5, 12, 23, 34, 42, 48],
    [3, 12, 18, 25, 34, 45],
    [5, 11, 23, 30, 42, 49],
]

CANDIDATE = [
    6,
    14,
    21,
    32,
    41,
    49,
]


def step(
    lifecycle,
    source,
):
    return lifecycle.step(
        data=[6, 14, 26, 30, 19, 5],
        o345_n=59,
        old_result={
            "source": source,
            "preserved": True,
        },
        unresolved={
            "status": "hypothesis",
            "text": "возможно",
            "revisable": True,
        },
        historical_history=HISTORY,
        historical_candidate=CANDIDATE,
        source=source,
    )


def test_first_step_initializes_and_commits(
    tmp_path,
):
    lifecycle = OperationalLifecycle(
        tmp_path / "storage"
    )

    result = step(
        lifecycle,
        "generation-one",
    )

    assert (
        result["start"]["mode"]
        ==
        "initialized"
    )

    assert result["generation"] == 1

    assert (
        result[
            "previous_snapshot_hash"
        ]
        is None
    )

    assert result["snapshot_equal"]
    assert result["hash_equal"]

    assert all(
        result["invariants"].values()
    )


def test_second_step_recovers_previous_generation(
    tmp_path,
):
    storage = tmp_path / "storage"

    first_lifecycle = (
        OperationalLifecycle(storage)
    )

    first = step(
        first_lifecycle,
        "generation-one",
    )

    # New object simulates process restart.
    second_lifecycle = (
        OperationalLifecycle(storage)
    )

    second = step(
        second_lifecycle,
        "generation-two",
    )

    assert (
        second["start"]["mode"]
        ==
        "recovered"
    )

    assert (
        second["start"][
            "previous_generation"
        ]
        ==
        1
    )

    assert second["generation"] == 2

    assert (
        second[
            "previous_snapshot_hash"
        ]
        ==
        first["snapshot_hash"]
    )

    assert second["snapshot_equal"]
    assert second["hash_equal"]

    assert all(
        second["invariants"].values()
    )


def test_historical_organs_survive_restart(
    tmp_path,
):
    storage = tmp_path / "storage"

    first = step(
        OperationalLifecycle(storage),
        "generation-one",
    )

    second = step(
        OperationalLifecycle(storage),
        "generation-two",
    )

    for result in (
        first,
        second,
    ):
        snapshot = result["snapshot"]

        assert (
            "HistoricalSwarm"
            in snapshot["observations"]
        )

        assert (
            "HistoricalOmni"
            in snapshot["observations"]
        )

        assert {
            "HistoricalSwarm",
            "HistoricalOmni",
        }.issubset(
            result[
                "frozen_layer_names"
            ]
        )


def test_canonical_continuity_across_restart(
    tmp_path,
):
    storage = tmp_path / "storage"

    first = step(
        OperationalLifecycle(storage),
        "generation-one",
    )

    second = step(
        OperationalLifecycle(storage),
        "generation-two",
    )

    assert (
        second["snapshot"]["canonical"]
        ==
        first["snapshot"]["canonical"]
    )


def test_wal_contains_two_commits_and_recoveries(
    tmp_path,
):
    storage = tmp_path / "storage"

    first_lifecycle = (
        OperationalLifecycle(storage)
    )

    step(
        first_lifecycle,
        "generation-one",
    )

    second_lifecycle = (
        OperationalLifecycle(storage)
    )

    step(
        second_lifecycle,
        "generation-two",
    )

    events = (
        second_lifecycle
        .persistence
        .wal
        .read_valid_events()
    )

    event_types = [
        event["type"]
        for event in events
    ]

    assert (
        event_types.count(
            "MIND_STATE_PREPARED"
        )
        ==
        2
    )

    assert (
        event_types.count(
            "MIND_STATE_COMMITTED"
        )
        ==
        2
    )

    # First step recovers after commit.
    # Second step recovers at start and after commit.
    assert (
        event_types.count(
            "MIND_STATE_RECOVERED"
        )
        ==
        3
    )


def test_checkpoint_generation_chain(
    tmp_path,
):
    storage = tmp_path / "storage"

    lifecycle = OperationalLifecycle(
        storage
    )

    first = step(
        lifecycle,
        "generation-one",
    )

    second = step(
        OperationalLifecycle(storage),
        "generation-two",
    )

    assert first["generation"] == 1
    assert second["generation"] == 2

    state = json.loads(
        (
            storage
            / "state.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert state["generation"] == 2

    assert (
        state["mind"][
            "previous_snapshot_hash"
        ]
        ==
        first["snapshot_hash"]
    )
