from copy import deepcopy

from malysh_system.interlayer_observers import (
    compute_interlayer_pass,
    integrate_interlayer_pass,
    run_interlayer_pass,
)
from malysh_system.unified_mind import MindState


def populated_mind():
    mind = MindState()

    mind.canonical = {
        "a3": 2,
        "b4": 3,
        "c5": 4,
    }

    for name in (
        "O3",
        "O4",
        "O5",
        "KMBP",
        "FullReflections",
        "HumanLayer",
        "Swarm",
        "Omni",
    ):
        mind.observe(
            name,
            {
                "organ": name,
                "verified": True,
            },
        )

    for name in (
        "O345",
        "KMBP",
        "Swarm",
        "Omni",
    ):
        mind.reflect(
            name,
            {
                "organ": name,
                "decision_authority": False,
            },
        )

    mind.set_human(
        {
            "logical": {
                "hypothesis": "main",
            },
            "possible": [
                {
                    "hypothesis": "possible",
                }
            ],
        }
    )

    return mind


def test_every_layer_observes_peers_not_itself():
    mind = populated_mind()

    result = compute_interlayer_pass(
        mind.snapshot()
    )

    assert result["invariant_ok"] is True

    for layer, observation in (
        result["layer_results"].items()
    ):
        assert layer not in observation["peers"]

        assert (
            observation["invariant_ok"]
            is True
        )


def test_all_observers_use_same_frozen_snapshot():
    mind = populated_mind()

    result = compute_interlayer_pass(
        mind.snapshot()
    )

    frozen = set(
        result["frozen_layer_names"]
    )

    for layer, observation in (
        result["layer_results"].items()
    ):
        assert (
            set(observation["peer_names"])
            ==
            frozen - {layer}
        )


def test_no_observer_selects_winner():
    mind = populated_mind()

    result = compute_interlayer_pass(
        mind.snapshot()
    )

    assert result["winner"] is None

    for observation in (
        result["layer_results"].values()
    ):
        assert (
            observation["patterns"]["winner"]
            is None
        )

        assert (
            observation[
                "affects_main_answer"
            ]
            is False
        )

        assert (
            observation[
                "affects_execution"
            ]
            is False
        )


def test_interlayer_uses_organ_result_contract():
    mind = populated_mind()

    result = run_interlayer_pass(
        mind.snapshot()
    )

    assert (
        result.organ
        ==
        "InterLayerObservers"
    )

    assert result.status == "ok"
    assert result.error is None
    assert result.data["invariant_ok"] is True


def test_integration_preserves_protected_state():
    mind = populated_mind()

    before = mind.snapshot()

    result = integrate_interlayer_pass(
        mind
    )

    after = mind.snapshot()

    assert result.status == "ok"

    for key in (
        "subject",
        "canonical",
        "observations",
        "experience",
        "human",
        "main",
        "possible",
    ):
        assert after[key] == before[key]

    assert (
        "InterLayerObservers"
        in
        after["reflections"]
    )

    for layer in (
        result.data["frozen_layer_names"]
    ):
        assert (
            "InterLayer:" + layer
            in
            after["reflections"]
        )


def test_interlayer_results_are_reference_isolated():
    mind = populated_mind()

    result = integrate_interlayer_pass(
        mind
    )

    first_layer = sorted(
        result.data["layer_results"]
    )[0]

    external = deepcopy(
        result.data
    )

    external[
        "layer_results"
    ][
        first_layer
    ][
        "peer_names"
    ].append(
        "MUTATION"
    )

    assert (
        "MUTATION"
        not in
        mind.reflections[
            "InterLayer:" + first_layer
        ][
            "peer_names"
        ]
    )
