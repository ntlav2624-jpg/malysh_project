from copy import deepcopy

import pytest

from malysh_system.operational_lifecycle import (
    OperationalLifecycle,
)
from malysh_system.thinking_cycle import (
    run_thinking_cycle,
)


SIGNALS = {
    "entropy": 42.13,
    "resonance": 132.35,
    "ontological_weight": 121.23,
}

VECTOR = (
    "VECTOR_SINGULARITY_STABILIZATION"
)

EXPECTED_ROUTED = {
    "entropy": 68.1663,
    "resonance": 214.1423,
    "ontological_weight": 196.1501,
}

EXPECTED_INDEX = 371.7624


def cycle_with_prime(
    tmp_path,
):
    return run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        o345_n=59,
        old_result={
            "source":
                "integrated-cortex-prime-test",
        },
        unresolved="возможно",
        root=tmp_path,
        cortex_prime_signals=SIGNALS,
        cortex_prime_vector=VECTOR,
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
        cortex_prime_signals=SIGNALS,
        cortex_prime_vector=VECTOR,
        source=source,
    )


def test_cortex_prime_enters_thinking_cycle(
    tmp_path,
):
    result = cycle_with_prime(
        tmp_path
    )

    prime = result[
        "historical_cortex_prime"
    ]

    assert prime["status"] == "ok"

    assert (
        prime["data"]["invariant_ok"]
        is True
    )

    assert (
        "HistoricalCortexPrime"
        in
        result["mind"]["observations"]
    )

    assert (
        "HistoricalCortexPrime"
        in
        result["mind"]["reflections"]
    )

    assert all(
        result["invariants"].values()
    )


def test_frozen_interlayer_sees_cortex_prime(
    tmp_path,
):
    result = cycle_with_prime(
        tmp_path
    )

    layers = set(
        result["interlayer"][
            "data"
        ][
            "frozen_layer_names"
        ]
    )

    assert (
        "HistoricalCortexPrime"
        in layers
    )

    view = result[
        "interlayer"
    ][
        "data"
    ][
        "layer_results"
    ][
        "HistoricalCortexPrime"
    ]

    assert (
        view["observer"]
        ==
        "HistoricalCortexPrime"
    )

    assert (
        "HistoricalCortexPrime"
        not in
        view["peer_names"]
    )


def test_cortex_prime_real_outputs(
    tmp_path,
):
    result = cycle_with_prime(
        tmp_path
    )

    prime = result[
        "historical_cortex_prime"
    ][
        "data"
    ]

    assert (
        prime["thalamus"][
            "routed_signals"
        ]
        ==
        EXPECTED_ROUTED
    )

    assert (
        prime["synthesis"][
            "supreme_index"
        ]
        ==
        EXPECTED_INDEX
    )

    assert (
        prime["drive"][
            "selected_vector"
        ]
        ==
        VECTOR
    )

    assert (
        prime["drive"][
            "selection_mode"
        ]
        ==
        "explicit_only"
    )


def test_cortex_prime_has_no_authority(
    tmp_path,
):
    result = cycle_with_prime(
        tmp_path
    )

    prime = result[
        "historical_cortex_prime"
    ][
        "data"
    ]

    assert prime["decision_authority"] is False
    assert prime["automatic_execution"] is False
    assert prime["external_control"] is False
    assert prime["canonical_write"] is False
    assert prime["state_commit"] is False

    assert (
        prime["wall_clock_selection"]
        is False
    )

    assert (
        result["mind"]["canonical"]
        ==
        result["o345"]["canonical"]
    )


def test_cortex_prime_inputs_not_mutated(
    tmp_path,
):
    signals = deepcopy(SIGNALS)
    before = deepcopy(signals)

    run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=17,
        old_result={"source": "test"},
        unresolved="возможно",
        root=tmp_path,
        cortex_prime_signals=signals,
        cortex_prime_vector=VECTOR,
    )

    assert signals == before


@pytest.mark.parametrize(
    "signals,vector",
    [
        (SIGNALS, None),
        (None, VECTOR),
    ],
)
def test_partial_contract_rejected(
    tmp_path,
    signals,
    vector,
):
    with pytest.raises(
        ValueError,
        match=(
            "cortex_prime_signals and "
            "cortex_prime_vector"
        ),
    ):
        run_thinking_cycle(
            data=[1, 2, 3, 4],
            o345_n=17,
            old_result={"source": "test"},
            unresolved="возможно",
            root=tmp_path,
            cortex_prime_signals=signals,
            cortex_prime_vector=vector,
        )


def test_old_api_without_prime_remains_valid(
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
        result[
            "historical_cortex_prime"
        ]
        is None
    )

    assert (
        "HistoricalCortexPrime"
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


def test_cortex_prime_survives_restart(
    tmp_path,
):
    storage = tmp_path / "storage"

    first = lifecycle_step(
        OperationalLifecycle(storage),
        "prime-generation-one",
    )

    second = lifecycle_step(
        OperationalLifecycle(storage),
        "prime-generation-two",
    )

    assert first["generation"] == 1
    assert second["generation"] == 2

    assert (
        second[
            "previous_snapshot_hash"
        ]
        ==
        first["snapshot_hash"]
    )

    for result in (
        first,
        second,
    ):
        assert (
            result[
                "cortex_prime_requested"
            ]
            is True
        )

        assert (
            "HistoricalCortexPrime"
            in
            result["snapshot"][
                "observations"
            ]
        )

        assert (
            "HistoricalCortexPrime"
            in
            result[
                "frozen_layer_names"
            ]
        )

        assert result["snapshot_equal"]
        assert result["hash_equal"]

        assert all(
            result["invariants"].values()
        )


def test_recovered_cortex_prime_exact(
    tmp_path,
):
    storage = tmp_path / "storage"

    first = lifecycle_step(
        OperationalLifecycle(storage),
        "prime-generation-one",
    )

    second = lifecycle_step(
        OperationalLifecycle(storage),
        "prime-generation-two",
    )

    first_prime = first[
        "snapshot"
    ][
        "observations"
    ][
        "HistoricalCortexPrime"
    ]

    second_prime = second[
        "snapshot"
    ][
        "observations"
    ][
        "HistoricalCortexPrime"
    ]

    assert second_prime == first_prime

    assert (
        second_prime["thalamus"][
            "routed_signals"
        ]
        ==
        EXPECTED_ROUTED
    )

    assert (
        second_prime["synthesis"][
            "supreme_index"
        ]
        ==
        EXPECTED_INDEX
    )
