from copy import deepcopy

import pytest

from malysh_system.historical_hive_cortex import (
    CognitiveLimb,
    HISTORICAL_PI_FACTOR,
    HiveCortex,
    ResonanceSpine,
    compute_historical_hive_cortex,
    integrate_historical_hive_cortex,
    run_historical_hive_cortex,
)
from malysh_system.mind_persistence import (
    MindPersistence,
)
from malysh_system.unified_mind import (
    MindState,
)


TARGET = "entropy_stream"

SIGNAL = 42.13

EXPECTED_ACTION = (
    "MANIPULATED_ENTROPY_STREAM"
)

EXPECTED_RESONANCE = 132.3514


def test_cognitive_limb_historical_formula():
    limb = CognitiveLimb()

    assert (
        limb.manipulate(TARGET)
        ==
        EXPECTED_ACTION
    )


def test_resonance_spine_historical_formula():
    spine = ResonanceSpine()

    assert (
        spine.transmit(SIGNAL)
        ==
        EXPECTED_RESONANCE
    )

    assert HISTORICAL_PI_FACTOR == 3.1415


def test_hive_cortex_combines_components():
    cortex = HiveCortex()

    pulse = cortex.pulse(
        TARGET,
        SIGNAL,
    )

    assert pulse == {
        "limb_action":
            EXPECTED_ACTION,

        "spine_resonance":
            EXPECTED_RESONANCE,

        "cortex_status":
            "SYNAPSE_LOCKED",
    }


def test_adapter_is_deterministic():
    first = compute_historical_hive_cortex(
        TARGET,
        SIGNAL,
    )

    second = compute_historical_hive_cortex(
        TARGET,
        SIGNAL,
    )

    assert first == second
    assert first["invariant_ok"] is True


def test_adapter_has_explicit_provenance():
    result = compute_historical_hive_cortex(
        TARGET,
        SIGNAL,
    )

    assert (
        result["heritage"]["repository"]
        ==
        "ntlav2624-jpg/malysh"
    )

    assert (
        result["heritage"]["file"]
        ==
        "malysh_hive_cortex.py"
    )

    assert (
        result["heritage"]["identity"]
        ==
        "recovered_source"
    )

    assert (
        result["heritage"]["adaptation"]
        ==
        "pure_read_only"
    )


def test_historical_labels_grant_no_authority():
    result = compute_historical_hive_cortex(
        TARGET,
        SIGNAL,
    )

    for field in (
        "decision_authority",
        "automatic_execution",
        "state_write",
        "state_commit",
        "canonical_write",
        "main_answer_write",
        "possible_branch_write",
        "transaction_authorized",
        "winner_selection",
        "filesystem_write",
        "log_append",
        "timestamp_generated",
        "external_control",
    ):
        assert result[field] is False


def test_inputs_remain_unchanged():
    target = deepcopy(TARGET)
    signal = deepcopy(SIGNAL)

    target_before = deepcopy(target)
    signal_before = deepcopy(signal)

    compute_historical_hive_cortex(
        target,
        signal,
    )

    assert target == target_before
    assert signal == signal_before


def test_run_returns_verified_organ_result():
    result = run_historical_hive_cortex(
        TARGET,
        SIGNAL,
    )

    assert result.status == "ok"

    assert (
        result.data["invariant_ok"]
        is True
    )

    assert result.error is None


def test_integration_preserves_protected_state():
    mind = MindState()

    mind.canonical = {
        "a3": 2,
        "b4": 3,
        "c5": 4,
    }

    mind.set_human(
        {
            "logical": {
                "hypothesis": "main",
            },
            "possible": [
                {
                    "hypothesis":
                        "возможно",
                }
            ],
        }
    )

    mind.remember(
        "existing-experience",
        {
            "preserved": True,
        },
    )

    before = mind.snapshot()

    result = (
        integrate_historical_hive_cortex(
            mind,
            TARGET,
            SIGNAL,
        )
    )

    after = mind.snapshot()

    assert result.status == "ok"

    assert (
        "HistoricalHiveCortex"
        in
        after["observations"]
    )

    assert (
        "HistoricalHiveCortex"
        in
        after["reflections"]
    )

    for field in (
        "subject",
        "canonical",
        "experience",
        "human",
        "main",
        "possible",
    ):
        assert after[field] == before[field]


def test_hive_cortex_survives_persistence(
    tmp_path,
):
    mind = MindState()

    integrate_historical_hive_cortex(
        mind,
        TARGET,
        SIGNAL,
    )

    before = mind.snapshot()

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    commit = persistence.persist(
        mind,
        source="historical-hive-cortex-test",
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

    observation = after[
        "observations"
    ][
        "HistoricalHiveCortex"
    ]

    assert (
        observation["limb"]["output"]
        ==
        EXPECTED_ACTION
    )

    assert (
        observation["spine"]["output"]
        ==
        EXPECTED_RESONANCE
    )


@pytest.mark.parametrize(
    "target",
    [
        "",
        None,
        42,
        [],
        {},
    ],
)
def test_invalid_target_rejected(
    target,
):
    result = run_historical_hive_cortex(
        target,
        SIGNAL,
    )

    assert result.status == "error"
    assert result.data == {}
    assert result.error


@pytest.mark.parametrize(
    "signal",
    [
        -1,
        None,
        "42.13",
        True,
        [],
    ],
)
def test_invalid_signal_rejected(
    signal,
):
    result = run_historical_hive_cortex(
        TARGET,
        signal,
    )

    assert result.status == "error"
    assert result.data == {}
    assert result.error


def test_non_malysh_subject_rejected():
    result = run_historical_hive_cortex(
        TARGET,
        SIGNAL,
        subject="AnotherSubject",
    )

    assert result.status == "error"

    assert (
        "ONE Malysh"
        in result.error
    )
