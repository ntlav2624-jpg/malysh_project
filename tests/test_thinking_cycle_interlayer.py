from copy import deepcopy

from malysh_system.thinking_cycle import (
    run_thinking_cycle,
)
from malysh_system.unified_mind import MindState


def test_all_active_layers_receive_separate_views(
    tmp_path,
):
    result = run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        o345_n=59,
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
    )

    interlayer = result["interlayer"]

    assert interlayer["status"] == "ok"
    assert interlayer["data"]["invariant_ok"] is True

    layers = set(
        interlayer["data"][
            "frozen_layer_names"
        ]
    )

    assert layers >= {
        "O3",
        "O4",
        "O5",
        "O345",
        "KMBP",
        "FullReflections",
        "HumanLayer",
        "Swarm",
        "Omni",
    }

    snapshot = result["mind"]

    for layer in layers:
        key = "InterLayer:" + layer

        assert key in snapshot["reflections"]

        assert (
            snapshot["reflections"][key][
                "observer"
            ]
            ==
            layer
        )

    assert all(
        result["invariants"].values()
    )


def test_interlayer_cannot_change_canonical_or_human(
    tmp_path,
):
    mind = MindState()

    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=47,
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
        mind=mind,
    )

    canonical = deepcopy(
        result["o345"]["canonical"]
    )

    assert mind.canonical == canonical

    assert (
        result["mind"]["canonical"]
        ==
        canonical
    )

    assert (
        result["human_layer"]
        ==
        result["mind"][
            "observations"
        ][
            "HumanLayer"
        ]
    )


def test_each_layer_excludes_itself(tmp_path):
    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=17,
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
    )

    layer_results = (
        result["interlayer"]
        ["data"]
        ["layer_results"]
    )

    for layer, observation in (
        layer_results.items()
    ):
        assert layer not in observation["peers"]

        assert (
            observation["invariant_ok"]
            is True
        )


def test_interlayer_does_not_select_winner(tmp_path):
    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=17,
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
    )

    assert (
        result["interlayer"]
        ["data"]
        ["winner"]
        is None
    )

    assert (
        result["reflections"]
        ["debate"]
        ["winner"]
        is None
    )

    assert (
        result["swarm"]
        ["data"]
        ["collective_state"]
        ["winner"]
        is None
    )

    assert (
        result["omni"]
        ["data"]
        ["context_state"]
        ["winner"]
        is None
    )


def test_old_api_without_o345_remains_valid(tmp_path):
    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
    )

    assert result["o345"] is None
    assert result["interlayer"]["status"] == "ok"

    assert all(
        result["invariants"].values()
    )
