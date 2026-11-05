from copy import deepcopy

import pytest

from malysh_system.operational_lifecycle import (
    OperationalLifecycle,
)
from malysh_system.thinking_cycle import (
    run_thinking_cycle,
)


NORMAL = {
    "name": "StableNode",
    "degree": 4,
    "entropy": 0.12,
    "resonance_noise": 0.03,
    "topology": "compact",
}

CHAOTIC = {
    "name": "ChaoticNode",
    "degree": 17,
    "entropy": 0.87,
    "resonance_noise": 0.41,
    "topology": "fractal",
}


def cycle_with_topology(
    tmp_path,
):
    return run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        o345_n=59,
        old_result={
            "source":
                "integrated-topology-test",
        },
        unresolved="возможно",
        root=tmp_path,
        topology_normal=NORMAL,
        topology_observed=CHAOTIC,
    )


def lifecycle_step(
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
        topology_normal=NORMAL,
        topology_observed=CHAOTIC,
        source=source,
    )


def test_topology_enters_thinking_cycle(
    tmp_path,
):
    result = cycle_with_topology(
        tmp_path
    )

    topology = result[
        "historical_topology"
    ]

    assert topology["status"] == "ok"

    assert (
        topology["data"][
            "invariant_ok"
        ]
        is True
    )

    assert (
        "HistoricalTopology"
        in
        result["mind"]["observations"]
    )

    assert all(
        result["invariants"].values()
    )


def test_frozen_interlayer_sees_topology(
    tmp_path,
):
    result = cycle_with_topology(
        tmp_path
    )

    layers = set(
        result["interlayer"][
            "data"
        ][
            "frozen_layer_names"
        ]
    )

    assert "HistoricalTopology" in layers

    topology_view = (
        result["interlayer"][
            "data"
        ][
            "layer_results"
        ][
            "HistoricalTopology"
        ]
    )

    assert (
        topology_view["observer"]
        ==
        "HistoricalTopology"
    )

    assert (
        "HistoricalTopology"
        not in
        topology_view["peer_names"]
    )


def test_topology_does_not_replace_o345(
    tmp_path,
):
    result = cycle_with_topology(
        tmp_path
    )

    assert (
        result["mind"]["canonical"]
        ==
        result["o345"]["canonical"]
    )

    assert (
        result["historical_topology"][
            "data"
        ][
            "canonical_write"
        ]
        is False
    )


def test_topology_inputs_are_not_mutated(
    tmp_path,
):
    normal = deepcopy(NORMAL)
    chaotic = deepcopy(CHAOTIC)

    normal_before = deepcopy(normal)
    chaotic_before = deepcopy(chaotic)

    run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=17,
        old_result={"source": "test"},
        unresolved="возможно",
        root=tmp_path,
        topology_normal=normal,
        topology_observed=chaotic,
    )

    assert normal == normal_before
    assert chaotic == chaotic_before


@pytest.mark.parametrize(
    "normal,observed",
    [
        (NORMAL, None),
        (None, CHAOTIC),
    ],
)
def test_partial_topology_contract_rejected(
    tmp_path,
    normal,
    observed,
):
    with pytest.raises(
        ValueError,
        match=(
            "topology_normal and "
            "topology_observed"
        ),
    ):
        run_thinking_cycle(
            data=[1, 2, 3, 4],
            o345_n=17,
            old_result={"source": "test"},
            unresolved="возможно",
            root=tmp_path,
            topology_normal=normal,
            topology_observed=observed,
        )


def test_old_api_without_topology_still_valid(
    tmp_path,
):
    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=17,
        old_result={"source": "test"},
        unresolved="возможно",
        root=tmp_path,
    )

    assert (
        result["historical_topology"]
        is None
    )

    assert (
        "HistoricalTopology"
        not in
        result["interlayer"][
            "data"
        ][
            "frozen_layer_names"
        ]
    )

    assert all(
        result["invariants"].values()
    )


def test_topology_survives_lifecycle_restart(
    tmp_path,
):
    storage = tmp_path / "storage"

    first = lifecycle_step(
        OperationalLifecycle(storage),
        "topology-generation-one",
    )

    second = lifecycle_step(
        OperationalLifecycle(storage),
        "topology-generation-two",
    )

    assert first["generation"] == 1
    assert second["generation"] == 2

    assert (
        second["previous_snapshot_hash"]
        ==
        first["snapshot_hash"]
    )

    for result in (
        first,
        second,
    ):
        assert result[
            "topology_requested"
        ] is True

        assert (
            "HistoricalTopology"
            in
            result["snapshot"][
                "observations"
            ]
        )

        assert (
            "HistoricalTopology"
            in
            result[
                "frozen_layer_names"
            ]
        )

        assert all(
            result["invariants"].values()
        )


def test_recovered_topology_result_exact(
    tmp_path,
):
    storage = tmp_path / "storage"

    first = lifecycle_step(
        OperationalLifecycle(storage),
        "topology-generation-one",
    )

    second = lifecycle_step(
        OperationalLifecycle(storage),
        "topology-generation-two",
    )

    expected = first[
        "snapshot"
    ][
        "observations"
    ][
        "HistoricalTopology"
    ][
        "corrected_state"
    ]

    actual = second[
        "snapshot"
    ][
        "observations"
    ][
        "HistoricalTopology"
    ][
        "corrected_state"
    ]

    assert actual == expected

    assert actual == {
        "name": "ChaoticNode",
        "degree": 5.95,
        "entropy": 0.2436,
        "resonance_noise": 0.0902,
        "topology": "compact",
    }
