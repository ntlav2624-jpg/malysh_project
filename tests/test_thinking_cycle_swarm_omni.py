from copy import deepcopy

from malysh_system.thinking_cycle import (
    run_thinking_cycle,
)
from malysh_system.unified_mind import MindState


def test_swarm_omni_inside_one_malysh(tmp_path):
    result = run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        o345_n=59,
        old_result={
            "historical": True
        },
        unresolved="возможно",
        root=tmp_path,
    )

    assert result["subject"] == "Malysh"

    assert result["swarm"]["status"] == "ok"
    assert result["omni"]["status"] == "ok"

    assert (
        result["swarm"]["data"][
            "invariant_ok"
        ]
        is True
    )

    assert (
        result["omni"]["data"][
            "invariant_ok"
        ]
        is True
    )

    snapshot = result["mind"]

    assert "Swarm" in snapshot["observations"]
    assert "Omni" in snapshot["observations"]

    assert "Swarm" in snapshot["reflections"]
    assert "Omni" in snapshot["reflections"]

    assert all(
        result["invariants"].values()
    )


def test_swarm_omni_preserve_o345_canonical(tmp_path):
    mind = MindState()

    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=47,
        old_result={
            "historical": True
        },
        unresolved="возможно",
        root=tmp_path,
        mind=mind,
    )

    canonical = deepcopy(
        result["o345"]["canonical"]
    )

    assert mind.canonical == canonical
    assert result["mind"]["canonical"] == canonical


def test_swarm_omni_never_select_winner(tmp_path):
    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=17,
        old_result={
            "historical": True
        },
        unresolved="возможно",
        root=tmp_path,
    )

    assert (
        result["swarm"]["data"][
            "collective_state"
        ][
            "winner"
        ]
        is None
    )

    assert (
        result["omni"]["data"][
            "context_state"
        ][
            "winner"
        ]
        is None
    )

    assert (
        result["reflections"][
            "debate"
        ][
            "winner"
        ]
        is None
    )


def test_swarm_omni_are_marked_new_hypotheses(
    tmp_path,
):
    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=17,
        old_result={
            "historical": True
        },
        unresolved="возможно",
        root=tmp_path,
    )

    for organ in (
        "swarm",
        "omni",
    ):
        provenance = (
            result[organ]
            ["data"]
            ["provenance"]
        )

        assert (
            provenance[
                "implementation_status"
            ]
            ==
            "new_hypothesis"
        )

        assert (
            provenance[
                "historical_identity"
            ]
            ==
            "named_unresolved"
        )

        assert (
            provenance[
                "recovered_memory"
            ]
            is False
        )


def test_all_layers_visible_without_authority(
    tmp_path,
):
    result = run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        o345_n=59,
        old_result={
            "historical": True
        },
        unresolved="возможно",
        root=tmp_path,
    )

    layers = set(
        result["cross_layer"][
            "layers_seen"
        ]
    )

    assert layers >= {
        "O345",
        "O3",
        "O4",
        "O5",
        "KMBP",
        "FullReflections",
        "HumanLayer",
        "Swarm",
        "Omni",
    }

    for organ in (
        result["swarm"]["data"],
        result["omni"]["data"],
    ):
        assert organ["decision_authority"] is False
        assert organ["automatic_execution"] is False
        assert organ["state_write"] is False
        assert organ["state_commit"] is False
        assert organ["canonical_write"] is False
