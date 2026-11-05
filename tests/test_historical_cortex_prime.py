from copy import deepcopy

import pytest

from malysh_system.historical_cortex_prime import (
    ALLOWED_VECTORS,
    HiveCortexPrime,
    ResonantThalamus,
    compute_historical_cortex_prime,
    integrate_historical_cortex_prime,
    run_historical_cortex_prime,
)
from malysh_system.mind_persistence import (
    MindPersistence,
)
from malysh_system.unified_mind import (
    MindState,
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


def test_thalamus_matches_historical_formula():
    result = ResonantThalamus().route_signals(
        SIGNALS
    )

    assert result == EXPECTED_ROUTED


def test_cortex_prime_synthesis():
    result = HiveCortexPrime().synthesize(
        SIGNALS,
        VECTOR,
    )

    assert (
        result["routed_signals"]
        ==
        EXPECTED_ROUTED
    )

    assert (
        result["explicit_vector"]
        ==
        VECTOR
    )

    assert (
        result["supreme_index"]
        ==
        EXPECTED_INDEX
    )


def test_adapter_is_deterministic():
    first = compute_historical_cortex_prime(
        SIGNALS,
        VECTOR,
    )

    second = compute_historical_cortex_prime(
        SIGNALS,
        VECTOR,
    )

    assert first == second
    assert first["invariant_ok"] is True


def test_input_is_not_mutated():
    signals = deepcopy(SIGNALS)
    before = deepcopy(signals)

    compute_historical_cortex_prime(
        signals,
        VECTOR,
    )

    assert signals == before


def test_time_selection_is_disabled():
    result = compute_historical_cortex_prime(
        SIGNALS,
        VECTOR,
    )

    assert (
        result["drive"]["selection_mode"]
        ==
        "explicit_only"
    )

    assert (
        result["wall_clock_selection"]
        is False
    )

    assert VECTOR in ALLOWED_VECTORS


def test_prime_labels_grant_no_authority():
    result = compute_historical_cortex_prime(
        SIGNALS,
        VECTOR,
    )

    for field in (
        "decision_authority",
        "automatic_execution",
        "external_control",
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
        "wall_clock_selection",
    ):
        assert result[field] is False


def test_integration_preserves_protected_state():
    mind = MindState()

    mind.canonical = {
        "a3": 2,
        "b4": 3,
        "c5": 4,
    }

    before = mind.snapshot()

    result = integrate_historical_cortex_prime(
        mind,
        SIGNALS,
        VECTOR,
    )

    after = mind.snapshot()

    assert result.status == "ok"

    assert (
        "HistoricalCortexPrime"
        in after["observations"]
    )

    assert (
        "HistoricalCortexPrime"
        in after["reflections"]
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


def test_cortex_prime_survives_persistence(
    tmp_path,
):
    mind = MindState()

    integrate_historical_cortex_prime(
        mind,
        SIGNALS,
        VECTOR,
    )

    before = mind.snapshot()

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    commit = persistence.persist(
        mind,
        source="historical-cortex-prime-test",
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
        "HistoricalCortexPrime"
    ]

    assert (
        observation["thalamus"][
            "routed_signals"
        ]
        ==
        EXPECTED_ROUTED
    )

    assert (
        observation["synthesis"][
            "supreme_index"
        ]
        ==
        EXPECTED_INDEX
    )


@pytest.mark.parametrize(
    "vector",
    [
        "",
        "VECTOR_UNKNOWN",
        None,
    ],
)
def test_unknown_vector_rejected(vector):
    result = run_historical_cortex_prime(
        SIGNALS,
        vector,
    )

    assert result.status == "error"
    assert result.data == {}


@pytest.mark.parametrize(
    "signals",
    [
        {},
        None,
        [],
        {"entropy": -1},
        {"entropy": "42.13"},
        {"entropy": True},
    ],
)
def test_invalid_signals_rejected(signals):
    result = run_historical_cortex_prime(
        signals,
        VECTOR,
    )

    assert result.status == "error"
    assert result.data == {}


def test_non_malysh_subject_rejected():
    result = run_historical_cortex_prime(
        SIGNALS,
        VECTOR,
        subject="AnotherSubject",
    )

    assert result.status == "error"

    assert (
        "ONE Malysh"
        in result.error
    )
