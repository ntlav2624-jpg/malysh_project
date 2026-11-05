import copy

import pytest

from malysh_system.kmbp import (
    STATE_TO_VOLTAGE,
    STATE_TO_ZONE,
    compute_kmbp,
    integrate_kmbp,
    run_kmbp,
)
from malysh_system.unified_mind import MindState


def test_real_numeric_input_produces_all_four_states():
    result = compute_kmbp([0, 1, 2, 3])

    assert result["states"] == [0, 1, 2, 3]
    assert result["invariant_ok"] is True
    assert all(result["invariants"].values())


def test_modulo_projection_is_verifiable():
    values = [4, 5, 6, 7, 8, 9]

    result = compute_kmbp(values)

    assert result["states"] == [
        value % 4
        for value in values
    ]


def test_zone_and_voltage_are_functions_of_state():
    result = compute_kmbp([0, 1, 2, 3])

    for node in result["nodes"]:
        state = node["quaternary_state"]

        assert node["zone"] == STATE_TO_ZONE[state]
        assert (
            node["voltage_v"]
            == STATE_TO_VOLTAGE[state]
        )
        assert (
            node["logic_level"]
            == f"PAM-4_L{state}"
        )


def test_string_input_is_real_and_deterministic():
    first = compute_kmbp("6EQUJ5")
    second = compute_kmbp("6EQUJ5")

    assert first == second
    assert first["input_length"] == 6


def test_zero_input_has_defined_normalization():
    result = compute_kmbp([0, 0, 0, 0])

    assert result["total_power"] == 0
    assert result["energy_weight_sum"] == 0.0
    assert result["invariant_ok"] is True


def test_empty_input_is_rejected():
    with pytest.raises(ValueError):
        compute_kmbp([])


def test_negative_amplitude_is_rejected():
    with pytest.raises(ValueError):
        compute_kmbp([1, -1, 2])


def test_common_organ_contract():
    result = run_kmbp([0, 1, 2, 3])

    assert result.organ == "KMBP"
    assert result.status == "ok"
    assert result.error is None
    assert result.data["invariant_ok"] is True


def test_kmbp_integrates_into_one_mindstate():
    mind = MindState()
    canonical_before = copy.deepcopy(mind.canonical)

    result = integrate_kmbp(
        mind,
        [0, 1, 2, 3],
    )

    snapshot = mind.snapshot()

    assert result.status == "ok"
    assert mind.invariant() is True
    assert mind.subject == "Malysh"

    assert snapshot["canonical"] == canonical_before
    assert "KMBP" in snapshot["observations"]
    assert "KMBP" in snapshot["reflections"]

    reflection = snapshot["reflections"]["KMBP"]

    assert reflection["decision_authority"] is False
    assert reflection["state_write"] is False
    assert reflection["state_commit"] is False


def test_snapshot_is_reference_isolated():
    mind = MindState()

    integrate_kmbp(
        mind,
        [0, 1, 2, 3],
    )

    snapshot = mind.snapshot()
    snapshot["observations"]["KMBP"]["states"][0] = 99

    assert (
        mind.observations["KMBP"]["states"][0]
        == 0
    )
