from copy import deepcopy

from malysh_system.thinking_cycle import (
    MalyshThinkingCycle,
    run_thinking_cycle,
)
from malysh_system.unified_mind import MindState


def test_complete_thinking_cycle(tmp_path):
    old_result = {
        "old_engine": True,
        "value": 42,
    }

    result = run_thinking_cycle(
        data=[0, 1, 2, 3],
        old_result=old_result,
        unresolved="возможно",
        root=tmp_path,
    )

    assert (
        result["schema"]
        ==
        "malysh.thinking-cycle.v1"
    )

    assert result["subject"] == "Malysh"

    assert result["kmbp"]["status"] == "ok"

    assert (
        result["kmbp"]["data"]["states"]
        ==
        [0, 1, 2, 3]
    )

    assert (
        result["kmbp"]["data"][
            "invariant_ok"
        ]
        is True
    )

    assert (
        result["reflections"][
            "as_before"
        ][
            "result"
        ]
        ==
        old_result
    )

    assert (
        result["reflections"]["schema"]
        ==
        "malysh.reflections.v2"
    )

    assert (
        result["reflections"][
            "voice_a"
        ][
            "rights"
        ]
        ==
        "equal"
    )

    assert (
        result["reflections"][
            "voice_b"
        ][
            "rights"
        ]
        ==
        "equal"
    )

    assert (
        result["reflections"][
            "debate"
        ][
            "winner"
        ]
        is None
    )

    assert (
        result["reflections"][
            "execution_gate"
        ][
            "automatic_winner_forbidden"
        ]
        is True
    )

    assert all(
        result["invariants"].values()
    )


def test_working_kmbp_reaches_full_reflections(tmp_path):
    result = run_thinking_cycle(
        data=[4, 5, 6, 7],
        old_result={
            "old_engine": True
        },
        unresolved={
            "status": "hypothesis",
            "revisable": True,
        },
        root=tmp_path,
    )

    legacy_experience = (
        result["reflections"]
        ["voice_b"]
        ["result"]
        ["legacy_experience"]
    )

    assert (
        legacy_experience["called"]
        is True
    )

    assert (
        legacy_experience["error"]
        is None
    )

    bridge_result = (
        legacy_experience["result"]
    )

    assert (
        bridge_result["source"]
        ==
        "working_kmbp"
    )

    assert bridge_result["organ"] == "KMBP"
    assert bridge_result["status"] == "ok"

    assert (
        bridge_result["data"]["states"]
        ==
        [0, 1, 2, 3]
    )

    assert (
        bridge_result["data"][
            "invariant_ok"
        ]
        is True
    )

    assert (
        bridge_result[
            "decision_authority"
        ]
        is False
    )

    assert (
        bridge_result["state_write"]
        is False
    )

    assert (
        bridge_result["state_commit"]
        is False
    )


def test_all_organs_share_one_mindstate(tmp_path):
    mind = MindState()
    canonical_before = deepcopy(
        mind.canonical
    )

    cycle = MalyshThinkingCycle(
        root=tmp_path,
        mind=mind,
    )

    result = cycle.run(
        data=[8, 9, 10, 11],
        old_result={
            "historical": True
        },
        unresolved="возможно",
    )

    snapshot = result["mind"]

    assert snapshot["subject"] == "Malysh"
    assert mind.invariant() is True

    assert (
        snapshot["canonical"]
        ==
        canonical_before
    )

    assert (
        "KMBP"
        in
        snapshot["observations"]
    )

    assert (
        "FullReflections"
        in
        snapshot["observations"]
    )

    assert (
        "HumanLayer"
        in
        snapshot["observations"]
    )

    assert (
        "KMBP"
        in
        snapshot["reflections"]
    )

    assert (
        "KMBP_FULL_REFLECTIONS_PATTERN"
        in
        snapshot["reflections"]
    )

    assert (
        "KMBP_LEGACY_BRIDGE"
        in
        snapshot["experience"]
    )


def test_cross_layer_observer_has_no_execution_power(
    tmp_path,
):
    result = run_thinking_cycle(
        data=[12, 13, 14, 15],
        old_result={
            "historical": True
        },
        unresolved="возможно",
        root=tmp_path,
    )

    cross_layer = result["cross_layer"]

    assert (
        cross_layer[
            "observer_outputs_separate"
        ]
        is True
    )

    assert (
        cross_layer[
            "observer_changes_execution"
        ]
        is False
    )

    assert (
        cross_layer[
            "decision_authority"
        ]
        is False
    )

    assert (
        cross_layer["state_write"]
        is False
    )

    assert (
        cross_layer["state_commit"]
        is False
    )


def test_result_is_reference_isolated(tmp_path):
    mind = MindState()

    result = run_thinking_cycle(
        data=[0, 1, 2, 3],
        old_result={
            "historical": True
        },
        unresolved="возможно",
        root=tmp_path,
        mind=mind,
    )

    result["mind"][
        "observations"
    ][
        "KMBP"
    ][
        "states"
    ][0] = 99

    assert (
        mind.observations[
            "KMBP"
        ][
            "states"
        ][0]
        ==
        0
    )
