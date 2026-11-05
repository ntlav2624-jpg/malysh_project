import pytest

from malysh_system.thinking_cycle import (
    run_thinking_cycle,
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


def run_with_heritage(tmp_path):
    return run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        o345_n=59,
        old_result={
            "historical": True,
        },
        unresolved="возможно",
        root=tmp_path,
        historical_history=HISTORY,
        historical_candidate=CANDIDATE,
        historical_pool_size=49,
    )


def test_historical_heritage_enters_one_cycle(
    tmp_path,
):
    result = run_with_heritage(
        tmp_path
    )

    assert (
        result["historical_swarm"]["status"]
        ==
        "ok"
    )

    assert (
        result["historical_omni"]["status"]
        ==
        "ok"
    )

    assert all(
        result["invariants"].values()
    )


def test_current_and_historical_branches_coexist(
    tmp_path,
):
    result = run_with_heritage(
        tmp_path
    )

    observations = (
        result["mind"]["observations"]
    )

    assert "Swarm" in observations
    assert "Omni" in observations

    assert (
        "HistoricalSwarm"
        in observations
    )

    assert (
        "HistoricalOmni"
        in observations
    )

    assert (
        observations["Swarm"][
            "provenance"
        ][
            "implementation_status"
        ]
        ==
        "new_hypothesis"
    )

    assert (
        observations[
            "HistoricalSwarm"
        ][
            "heritage"
        ][
            "identity"
        ]
        ==
        "recovered_source"
    )


def test_interlayer_frozen_snapshot_sees_all_four(
    tmp_path,
):
    result = run_with_heritage(
        tmp_path
    )

    layers = set(
        result["interlayer"][
            "data"
        ][
            "frozen_layer_names"
        ]
    )

    assert {
        "Swarm",
        "Omni",
        "HistoricalSwarm",
        "HistoricalOmni",
    }.issubset(layers)

    layer_results = (
        result["interlayer"][
            "data"
        ][
            "layer_results"
        ]
    )

    for name in (
        "Swarm",
        "Omni",
        "HistoricalSwarm",
        "HistoricalOmni",
    ):
        assert name in layer_results

        peers = set(
            layer_results[name][
                "peer_names"
            ]
        )

        assert name not in peers


def test_historical_omni_is_still_read_only(
    tmp_path,
):
    result = run_with_heritage(
        tmp_path
    )

    omni = result[
        "historical_omni"
    ][
        "data"
    ]

    assert omni["winner"] is None
    assert omni["randomness_used"] is False
    assert omni["weight_mutation"] is False

    assert (
        omni["error_memory_mutation"]
        is False
    )

    assert (
        omni["canonical_write"]
        is False
    )

    assert (
        omni["state_commit"]
        is False
    )


def test_no_historical_input_preserves_old_api(
    tmp_path,
):
    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=17,
        old_result={
            "historical": True,
        },
        unresolved="возможно",
        root=tmp_path,
    )

    assert result[
        "historical_swarm"
    ] is None

    assert result[
        "historical_omni"
    ] is None

    layers = set(
        result["interlayer"][
            "data"
        ][
            "frozen_layer_names"
        ]
    )

    assert (
        "HistoricalSwarm"
        not in layers
    )

    assert (
        "HistoricalOmni"
        not in layers
    )

    assert all(
        result["invariants"].values()
    )


@pytest.mark.parametrize(
    "history,candidate",
    [
        (HISTORY, None),
        (None, CANDIDATE),
    ],
)
def test_partial_historical_contract_is_rejected(
    tmp_path,
    history,
    candidate,
):
    with pytest.raises(
        ValueError,
        match=(
            "historical_history and "
            "historical_candidate"
        ),
    ):
        run_thinking_cycle(
            data=[1, 2, 3, 4],
            o345_n=17,
            old_result={
                "historical": True,
            },
            unresolved="возможно",
            root=tmp_path,
            historical_history=history,
            historical_candidate=candidate,
        )
