from copy import deepcopy

from malysh_system.acoustic_alphabet_observer import (
    compose_modes,
    compose_numbers,
    interaction_record,
    observe,
    temporal_predict,
    zero_identity,
)
from malysh_system.acoustic_alphabet_integration import (
    attach_acoustic_alphabet,
)
from malysh_system.kmbp_acoustic_alphabet import (
    observe_kmbp_acoustic_alphabet,
)


def test_number_composition():
    assert compose_numbers(1, 1) == 2
    assert compose_numbers(1, 2) == 3
    assert compose_numbers(2, 3) == 5
    assert compose_numbers(4, 5) == 9


def test_zero_identity():
    for value in range(10):
        assert zero_identity(value)


def test_mode_composition():
    assert compose_modes(
        (1, 0, 0),
        (0, 1, 0),
    ) == (1, 1, 0)

    assert compose_modes(
        (1, 1, 1),
        (1, -1, 1),
    ) == (2, 0, 2)


def test_weighted_interaction():
    positive = interaction_record(
        (1, 1, 1),
        (1, -1, 1),
        transfer=0.25,
    )

    negative = interaction_record(
        (1, 1, 1),
        (-1, 1, 1),
        transfer=-0.10,
    )

    assert positive["k"] == [2, 0, 2]
    assert positive["direction"] == "into_k"
    assert positive["invariant"] is True

    assert negative["direction"] == "out_of_k"
    assert negative["invariant"] is True


def test_temporal_alphabet():
    predicted = temporal_predict(
        [1.0, 2.0],
        [2.0, 4.0],
        [4.0, 8.0],
    )

    assert predicted == [7.0, 14.0]


def test_observer_structured_prediction():
    snapshots = [
        {
            "cumulative_flux": [1.0, 2.0],
            "energy_spectrum": [4.0, 8.0],
        },
        {
            "cumulative_flux": [2.0, 4.0],
            "energy_spectrum": [5.0, 10.0],
        },
        {
            "cumulative_flux": [4.0, 8.0],
            "energy_spectrum": [7.0, 14.0],
        },
    ]

    result = observe(
        data=[1, 2, 3],
        old_result={
            "semantic_context": {
                "visible_snapshots": snapshots,
            },
        },
    )

    assert result["prediction"]["available"] is True
    assert result["decision_authority"] is False
    assert result["main_answer_write"] is False
    assert result["winner_selection"] is False


def test_kmbp_bridge_preserves_kmbp():
    kmbp = {
        "legacy": True,
        "value": 567,
    }

    before = deepcopy(kmbp)

    bridge = observe_kmbp_acoustic_alphabet(
        data=[1, 2, 3],
        kmbp_result=kmbp,
    )

    assert kmbp == before
    assert bridge["decision_authority"] is False
    assert (
        bridge["invariants"]
        ["existing_kmbp_logic_preserved"]
        is True
    )


def test_cycle_attachment_does_not_mutate_source():
    source = {
        "main_answer": "unchanged",
        "kmbp": {
            "legacy": True,
        },
        "invariants": {
            "old": True,
        },
    }

    before = deepcopy(source)

    result = attach_acoustic_alphabet(
        source,
        data=[1, 2, 3],
    )

    assert source == before
    assert result["main_answer"] == "unchanged"
    assert result["kmbp"] == source["kmbp"]
    assert (
        result["invariants"]
        ["acoustic_alphabet_observer_present"]
        is True
    )
    assert (
        result["invariants"]
        ["acoustic_alphabet_no_decision_authority"]
        is True
    )
