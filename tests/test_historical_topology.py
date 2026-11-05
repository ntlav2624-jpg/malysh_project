from copy import deepcopy

import pytest

from malysh_system.historical_topology import (
    TopologicalState,
    apply_topo_stabilin,
    compute_defect_vector,
    compute_historical_topology,
    integrate_historical_topology,
)
from malysh_system.mind_persistence import (
    MindPersistence,
)
from malysh_system.unified_mind import (
    MindState,
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


def test_defect_vector_matches_historical_formula():
    normal = TopologicalState.from_mapping(
        NORMAL
    )

    chaotic = TopologicalState.from_mapping(
        CHAOTIC
    )

    defect = compute_defect_vector(
        normal,
        chaotic,
    )

    assert defect == {
        "degree_excess": 13.0,
        "entropy_excess": 0.75,
        "noise_excess": 0.38,
        "topology_shift":
            "fractal_to_compact",
    }


def test_stabilin_matches_historical_formula():
    chaotic = TopologicalState.from_mapping(
        CHAOTIC
    )

    corrected = apply_topo_stabilin(
        chaotic
    )

    assert corrected.to_dict() == {
        "name": "ChaoticNode",
        "degree": 5.95,
        "entropy": 0.2436,
        "resonance_noise": 0.0902,
        "topology": "compact",
    }


def test_adapter_is_deterministic():
    first = compute_historical_topology(
        NORMAL,
        CHAOTIC,
    )

    second = compute_historical_topology(
        NORMAL,
        CHAOTIC,
    )

    assert first == second
    assert first["invariant_ok"] is True


def test_adapter_does_not_mutate_inputs():
    normal = deepcopy(NORMAL)
    chaotic = deepcopy(CHAOTIC)

    normal_before = deepcopy(normal)
    chaotic_before = deepcopy(chaotic)

    compute_historical_topology(
        normal,
        chaotic,
    )

    assert normal == normal_before
    assert chaotic == chaotic_before


def test_adapter_has_no_side_effect_authority():
    result = compute_historical_topology(
        NORMAL,
        CHAOTIC,
    )

    assert (
        result["decision_authority"]
        is False
    )

    assert (
        result["automatic_execution"]
        is False
    )

    assert result["state_write"] is False
    assert result["state_commit"] is False
    assert result["canonical_write"] is False

    assert (
        result["transaction_authorized"]
        is False
    )

    assert (
        result["filesystem_write"]
        is False
    )

    assert result["sleep_used"] is False


def test_topology_integrates_without_overwrite():
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

    before = mind.snapshot()

    result = integrate_historical_topology(
        mind,
        NORMAL,
        CHAOTIC,
    )

    after = mind.snapshot()

    assert result.status == "ok"

    assert (
        "HistoricalTopology"
        in after["observations"]
    )

    assert (
        "HistoricalTopology"
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


def test_topology_survives_lossless_persistence(
    tmp_path,
):
    mind = MindState()

    integrate_historical_topology(
        mind,
        NORMAL,
        CHAOTIC,
    )

    before = mind.snapshot()

    persistence = MindPersistence(
        tmp_path / "storage"
    )

    commit = persistence.persist(
        mind,
        source="historical-topology-test",
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

    assert (
        "HistoricalTopology"
        in after["observations"]
    )


@pytest.mark.parametrize(
    "field",
    [
        "name",
        "degree",
        "entropy",
        "resonance_noise",
        "topology",
    ],
)
def test_missing_input_field_is_rejected(
    field,
):
    value = deepcopy(CHAOTIC)
    del value[field]

    with pytest.raises(
        ValueError,
        match="missing topology fields",
    ):
        TopologicalState.from_mapping(
            value
        )


@pytest.mark.parametrize(
    "field",
    [
        "degree",
        "entropy",
        "resonance_noise",
    ],
)
def test_negative_metric_is_rejected(
    field,
):
    value = deepcopy(CHAOTIC)
    value[field] = -1

    with pytest.raises(
        ValueError,
        match="must be non-negative",
    ):
        TopologicalState.from_mapping(
            value
        )
