from malysh_system.cognitive_flow_integration import (
    get_cognitive_flow,
)
from malysh_system.cognitive_organ_bridge import (
    integrate_cognitive_organ_bridge,
)
from malysh_system.mind_persistence import (
    MindPersistence,
)
from malysh_system.thinking_cycle import (
    run_thinking_cycle,
)
from malysh_system.unified_mind import (
    MindState,
)


def test_bridge_uses_one_existing_controller():
    mind = MindState()

    mind.observe(
        "RealOrgan",
        {
            "value": 42,
            "invariant_ok": True,
        },
    )

    result = integrate_cognitive_organ_bridge(
        mind
    )

    assert result.status == "ok"

    first = get_cognitive_flow(
        mind
    )

    second = get_cognitive_flow(
        mind
    )

    assert first is second

    assert (
        result.data[
            "second_controller_created"
        ]
        is False
    )


def test_bridge_imports_real_observations():
    mind = MindState()

    mind.observe(
        "O3",
        {"remainder": 2},
    )

    mind.observe(
        "KMBP",
        {"invariant_ok": True},
    )

    result = integrate_cognitive_organ_bridge(
        mind
    )

    assert result.status == "ok"

    assert set(
        result.data[
            "imported_organs"
        ]
    ) == {
        "KMBP",
        "O3",
    }

    assert (
        result.data[
            "source"
        ]
        ==
        "real_mind_state_organs"
    )


def test_bridge_preserves_protected_state():
    mind = MindState()

    mind.canonical = {
        "a3": 2,
        "b4": 3,
        "c5": 4,
    }

    mind.set_human(
        {
            "logical": {
                "hypothesis": "primary",
            },
            "possible": [
                {
                    "hypothesis":
                        "возможно",
                }
            ],
        }
    )

    mind.observe(
        "RealOrgan",
        {"value": 1},
    )

    before = mind.snapshot()

    result = integrate_cognitive_organ_bridge(
        mind
    )

    after = mind.snapshot()

    assert result.status == "ok"

    for field in (
        "subject",
        "canonical",
        "experience",
        "human",
        "main",
        "possible",
    ):
        assert after[field] == before[field]


def test_full_cycle_contains_cognitive_flow(
    tmp_path,
):
    result = run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        o345_n=59,
        old_result={
            "source": "cognitive-organ-test",
        },
        unresolved={
            "status": "hypothesis",
            "text": "возможно",
            "revisable": True,
        },
        root=tmp_path,
    )

    cognitive = result[
        "cognitive_flow"
    ]

    assert cognitive["status"] == "ok"

    assert (
        cognitive["data"][
            "invariant_ok"
        ]
        is True
    )

    assert (
        "CognitiveFlow"
        in
        result["mind"][
            "observations"
        ]
    )

    assert (
        "CognitiveFlow"
        in
        result["interlayer"][
            "data"
        ][
            "frozen_layer_names"
        ]
    )

    assert (
        result["mind"]["canonical"]
        ==
        result["o345"]["canonical"]
    )

    assert all(
        result["invariants"].values()
    )


def test_cognitive_snapshot_survives_persistence(
    tmp_path,
):
    mind = MindState()

    result = run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        o345_n=59,
        old_result={
            "source": "persistence-test",
        },
        unresolved="возможно",
        root=tmp_path,
        mind=mind,
    )

    before = mind.snapshot()

    persistence = MindPersistence(
        tmp_path / "state"
    )

    commit = persistence.persist(
        mind,
        source="cognitive-organ-bridge-test",
    )

    recovered, metadata = (
        persistence.recover()
    )

    after = recovered.snapshot()

    assert after == before

    assert (
        commit["snapshot_hash"]
        ==
        metadata["snapshot_hash"]
    )

    assert (
        "CognitiveFlow"
        in
        after["observations"]
    )

    assert (
        result["cognitive_flow"][
            "data"
        ][
            "invariant_ok"
        ]
        is True
    )
