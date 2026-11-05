from copy import deepcopy

from malysh_system.swarm_omni import (
    compute_omni,
    compute_swarm,
    integrate_swarm_omni,
    run_omni,
    run_swarm,
)
from malysh_system.unified_mind import MindState


def populated_mind():
    mind = MindState()

    mind.canonical = {
        "a3": 2,
        "b4": 3,
        "c5": 4,
    }

    mind.observe(
        "O3",
        {"observer": "O3"},
    )

    mind.observe(
        "O4",
        {"observer": "O4"},
    )

    mind.observe(
        "O5",
        {"observer": "O5"},
    )

    mind.observe(
        "KMBP",
        {
            "states": [2, 2, 3, 1],
            "invariant_ok": True,
        },
    )

    mind.observe(
        "FullReflections",
        {
            "schema":
                "malysh.reflections.v2",
        },
    )

    mind.observe(
        "HumanLayer",
        {
            "both_preserved": True,
        },
    )

    mind.reflect(
        "O345",
        {
            "decision_authority": False,
            "state_commit": False,
        },
    )

    mind.set_human(
        {
            "logical": {
                "hypothesis":
                    "main may be wrong",
            },
            "possible": [
                {
                    "hypothesis":
                        "possible branch",
                }
            ],
        }
    )

    return mind


def test_swarm_aggregates_without_winner():
    mind = populated_mind()

    result = compute_swarm(
        mind.snapshot()
    )

    assert result["invariant_ok"] is True

    assert (
        result["collective_state"][
            "winner"
        ]
        is None
    )

    assert (
        result["collective_state"][
            "automatic_consensus"
        ]
        is False
    )

    assert (
        result["collective_state"][
            "disagreement_preserved"
        ]
        is True
    )


def test_swarm_reports_missing_context():
    mind = MindState()

    result = compute_swarm(
        mind.snapshot()
    )

    assert result["invariant_ok"] is True

    assert (
        result["collective_state"][
            "status"
        ]
        ==
        "incomplete_required_context"
    )

    assert result["missing_required"]


def test_omni_observes_swarm_and_human_layer():
    mind = populated_mind()

    swarm = compute_swarm(
        mind.snapshot()
    )

    mind.observe(
        "Swarm",
        swarm,
    )

    omni = compute_omni(
        mind.snapshot(),
        swarm,
    )

    assert omni["invariant_ok"] is True
    assert omni["swarm_seen"] is True

    assert (
        omni["human_layer_seen"]
        is True
    )

    assert (
        omni["context_state"][
            "winner"
        ]
        is None
    )

    assert (
        omni["context_state"][
            "forced_resolution"
        ]
        is False
    )


def test_common_organ_result_contracts():
    mind = populated_mind()

    swarm = run_swarm(
        mind.snapshot()
    )

    assert swarm.organ == "Swarm"
    assert swarm.status == "ok"
    assert swarm.error is None

    mind.observe(
        "Swarm",
        swarm.data,
    )

    omni = run_omni(
        mind.snapshot(),
        swarm.data,
    )

    assert omni.organ == "Omni"
    assert omni.status == "ok"
    assert omni.error is None


def test_integration_preserves_existing_thought():
    mind = populated_mind()

    canonical_before = deepcopy(
        mind.canonical
    )

    human_before = deepcopy(
        mind.human
    )

    main_before = deepcopy(
        mind.main
    )

    possible_before = deepcopy(
        mind.possible
    )

    swarm, omni = integrate_swarm_omni(
        mind
    )

    assert swarm.status == "ok"
    assert omni.status == "ok"

    assert mind.canonical == canonical_before
    assert mind.human == human_before
    assert mind.main == main_before
    assert mind.possible == possible_before

    snapshot = mind.snapshot()

    assert "Swarm" in snapshot["observations"]
    assert "Omni" in snapshot["observations"]

    assert "Swarm" in snapshot["reflections"]
    assert "Omni" in snapshot["reflections"]


def test_new_code_does_not_claim_recovered_heritage():
    mind = populated_mind()

    swarm, omni = integrate_swarm_omni(
        mind
    )

    for result in (
        swarm.data,
        omni.data,
    ):
        provenance = result["provenance"]

        assert (
            provenance[
                "implementation_status"
            ]
            ==
            "new_hypothesis"
        )

        assert (
            provenance[
                "historical_identity"
            ]
            ==
            "named_unresolved"
        )

        assert (
            provenance[
                "recovered_memory"
            ]
            is False
        )

        assert provenance["revisable"] is True


def test_snapshots_are_reference_isolated():
    mind = populated_mind()

    integrate_swarm_omni(
        mind
    )

    snapshot = mind.snapshot()

    snapshot[
        "observations"
    ][
        "Swarm"
    ][
        "observation_names"
    ].append(
        "MUTATION"
    )

    assert (
        "MUTATION"
        not in
        mind.observations[
            "Swarm"
        ][
            "observation_names"
        ]
    )
