from copy import deepcopy

import pytest

from malysh_system.thinking_cycle import (
    MalyshThinkingCycle,
    run_thinking_cycle,
)
from malysh_system.unified_mind import MindState


def test_o345_explicit_scalar_inside_one_malysh(tmp_path):
    result = run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
        o345_n=59,
    )

    assert result["subject"] == "Malysh"
    assert result["o345_n"] == 59

    assert result["o345"] is not None
    assert result["o345"]["invariant_ok"] is True

    snapshot = result["mind"]

    assert (
        snapshot["canonical"]
        ==
        result["o345"]["canonical"]
    )

    for name in ("O3", "O4", "O5"):
        assert name in snapshot["observations"]

    assert "O345" in snapshot["reflections"]

    assert all(
        result["invariants"].values()
    )


def test_o345_does_not_replace_kmbp(tmp_path):
    result = run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
        o345_n=42,
    )

    assert result["o345"]["invariant_ok"] is True

    assert result["kmbp"]["status"] == "ok"

    assert (
        result["kmbp"]["data"]["states"]
        ==
        [2, 2, 2, 2, 3, 1]
    )

    snapshot = result["mind"]

    assert "O3" in snapshot["observations"]
    assert "O4" in snapshot["observations"]
    assert "O5" in snapshot["observations"]
    assert "KMBP" in snapshot["observations"]

    assert "O345" in snapshot["reflections"]
    assert "KMBP" in snapshot["reflections"]


def test_o345_and_human_layer_coexist(tmp_path):
    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
        o345_n=17,
    )

    snapshot = result["mind"]

    assert "O3" in snapshot["observations"]
    assert "O4" in snapshot["observations"]
    assert "O5" in snapshot["observations"]

    assert "HumanLayer" in snapshot["observations"]
    assert "FullReflections" in snapshot["observations"]

    layers = set(
        result["cross_layer"]["layers_seen"]
    )

    assert layers >= {
        "O345",
        "O3",
        "O4",
        "O5",
        "KMBP",
        "FullReflections",
        "HumanLayer",
    }


def test_o345_has_no_decision_authority(tmp_path):
    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
        o345_n=31,
    )

    reflection = (
        result["mind"]
        ["reflections"]
        ["O345"]
    )

    assert reflection["decision_authority"] is False
    assert reflection["state_write"] is False
    assert reflection["state_commit"] is False

    assert (
        result["reflections"]
        ["debate"]
        ["winner"]
        is None
    )


def test_existing_same_canonical_is_accepted(tmp_path):
    first = run_thinking_cycle(
        data=[1, 2, 3, 4],
        old_result={"cycle": 1},
        unresolved="возможно",
        root=tmp_path / "one",
        o345_n=23,
    )

    mind = MindState()
    mind.canonical = deepcopy(
        first["o345"]["canonical"]
    )

    second = run_thinking_cycle(
        data=[1, 2, 3, 4],
        old_result={"cycle": 2},
        unresolved="возможно",
        root=tmp_path / "two",
        mind=mind,
        o345_n=23,
    )

    assert (
        second["mind"]["canonical"]
        ==
        first["o345"]["canonical"]
    )

    assert all(
        second["invariants"].values()
    )


def test_conflicting_canonical_is_rejected(tmp_path):
    mind = MindState()

    mind.canonical = {
        "conflict": True
    }

    cycle = MalyshThinkingCycle(
        root=tmp_path,
        mind=mind,
    )

    with pytest.raises(
        ValueError,
        match="canonical conflict",
    ):
        cycle.run(
            data=[1, 2, 3, 4],
            old_result={"historical": True},
            unresolved="возможно",
            o345_n=23,
        )


def test_o345_remains_optional_for_old_api(tmp_path):
    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
    )

    assert result["o345"] is None
    assert result["o345_n"] is None

    assert result["mind"]["canonical"] == {}

    assert result["kmbp"]["status"] == "ok"

    assert all(
        result["invariants"].values()
    )


def test_result_snapshot_isolated(tmp_path):
    mind = MindState()

    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
        mind=mind,
        o345_n=7,
    )

    original = deepcopy(
        mind.canonical
    )

    result["mind"]["canonical"]["mutated"] = True

    assert mind.canonical == original
