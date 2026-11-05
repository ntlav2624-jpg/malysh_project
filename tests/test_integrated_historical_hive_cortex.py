from copy import deepcopy

import pytest

from malysh_system.operational_lifecycle import (
    OperationalLifecycle,
)
from malysh_system.thinking_cycle import (
    run_thinking_cycle,
)


TARGET = "entropy_stream"

SIGNAL = 42.13

EXPECTED_ACTION = (
    "MANIPULATED_ENTROPY_STREAM"
)

EXPECTED_RESONANCE = 132.3514


def cycle_with_hive(
    tmp_path,
):
    return run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        o345_n=59,
        old_result={
            "source":
                "integrated-hive-cortex-test",
        },
        unresolved="возможно",
        root=tmp_path,
        hive_target=TARGET,
        hive_signal=SIGNAL,
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
        hive_target=TARGET,
        hive_signal=SIGNAL,
        source=source,
    )


def test_hive_cortex_enters_thinking_cycle(
    tmp_path,
):
    result = cycle_with_hive(
        tmp_path
    )

    hive = result[
        "historical_hive_cortex"
    ]

    assert hive["status"] == "ok"

    assert (
        hive["data"]["invariant_ok"]
        is True
    )

    assert (
        "HistoricalHiveCortex"
        in
        result["mind"]["observations"]
    )

    assert (
        "HistoricalHiveCortex"
        in
        result["mind"]["reflections"]
    )

    assert all(
        result["invariants"].values()
    )


def test_frozen_interlayer_sees_hive_cortex(
    tmp_path,
):
    result = cycle_with_hive(
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
        "HistoricalHiveCortex"
        in layers
    )

    hive_view = (
        result["interlayer"][
            "data"
        ][
            "layer_results"
        ][
            "HistoricalHiveCortex"
        ]
    )

    assert (
        hive_view["observer"]
        ==
        "HistoricalHiveCortex"
    )

    assert (
        "HistoricalHiveCortex"
        not in
        hive_view["peer_names"]
    )


def test_hive_cortex_does_not_replace_o345(
    tmp_path,
):
    result = cycle_with_hive(
        tmp_path
    )

    assert (
        result["mind"]["canonical"]
        ==
        result["o345"]["canonical"]
    )

    hive = result[
        "historical_hive_cortex"
    ][
        "data"
    ]

    assert hive["canonical_write"] is False
    assert hive["state_commit"] is False

    assert (
        hive["decision_authority"]
        is False
    )

    assert (
        hive["external_control"]
        is False
    )


def test_hive_cortex_real_outputs(
    tmp_path,
):
    result = cycle_with_hive(
        tmp_path
    )

    hive = result[
        "historical_hive_cortex"
    ][
        "data"
    ]

    assert (
        hive["limb"]["output"]
        ==
        EXPECTED_ACTION
    )

    assert (
        hive["spine"]["factor"]
        ==
        3.1415
    )

    assert (
        hive["spine"]["output"]
        ==
        EXPECTED_RESONANCE
    )

    assert (
        hive["cortex"]["status"]
        ==
        "SYNAPSE_LOCKED"
    )


def test_hive_inputs_are_not_mutated(
    tmp_path,
):
    target = deepcopy(TARGET)
    signal = deepcopy(SIGNAL)

    target_before = deepcopy(target)
    signal_before = deepcopy(signal)

    run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=17,
        old_result={"source": "test"},
        unresolved="возможно",
        root=tmp_path,
        hive_target=target,
        hive_signal=signal,
    )

    assert target == target_before
    assert signal == signal_before


@pytest.mark.parametrize(
    "target,signal",
    [
        (TARGET, None),
        (None, SIGNAL),
    ],
)
def test_partial_hive_contract_rejected(
    tmp_path,
    target,
    signal,
):
    with pytest.raises(
        ValueError,
        match=(
            "hive_target and hive_signal "
            "must be supplied together"
        ),
    ):
        run_thinking_cycle(
            data=[1, 2, 3, 4],
            o345_n=17,
            old_result={"source": "test"},
            unresolved="возможно",
            root=tmp_path,
            hive_target=target,
            hive_signal=signal,
        )


def test_old_api_without_hive_remains_valid(
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
            "historical_hive_cortex"
        ]
        is None
    )

    assert (
        "HistoricalHiveCortex"
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


def test_hive_cortex_survives_restart(
    tmp_path,
):
    storage = tmp_path / "storage"

    first = lifecycle_step(
        OperationalLifecycle(storage),
        "hive-generation-one",
    )

    second = lifecycle_step(
        OperationalLifecycle(storage),
        "hive-generation-two",
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
                "hive_cortex_requested"
            ]
            is True
        )

        assert (
            "HistoricalHiveCortex"
            in
            result["snapshot"][
                "observations"
            ]
        )

        assert (
            "HistoricalHiveCortex"
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


def test_recovered_hive_result_exact(
    tmp_path,
):
    storage = tmp_path / "storage"

    first = lifecycle_step(
        OperationalLifecycle(storage),
        "hive-generation-one",
    )

    second = lifecycle_step(
        OperationalLifecycle(storage),
        "hive-generation-two",
    )

    first_hive = first[
        "snapshot"
    ][
        "observations"
    ][
        "HistoricalHiveCortex"
    ]

    second_hive = second[
        "snapshot"
    ][
        "observations"
    ][
        "HistoricalHiveCortex"
    ]

    assert second_hive == first_hive

    assert (
        second_hive[
            "limb"
        ][
            "output"
        ]
        ==
        EXPECTED_ACTION
    )

    assert (
        second_hive[
            "spine"
        ][
            "output"
        ]
        ==
        EXPECTED_RESONANCE
    )
