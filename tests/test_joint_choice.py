from copy import deepcopy

from malysh_system.interlayer_observers import (
    compute_interlayer_pass,
)
from malysh_system.joint_choice import (
    compute_joint_choice,
    integrate_joint_choice,
    run_joint_choice,
)
from malysh_system.unified_mind import MindState


def populated_mind(
    debate_state="DISAGREEMENT",
    contradictions=None,
    unresolved=None,
):
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

    mind.observe(
        "FullReflections",
        {
            "schema":
                "malysh.reflections.v2",

            "voice_a": {
                "role":
                    "historical_reasoning",

                "result":
                    {
                        "historical": True
                    },

                "digest":
                    "main-digest",
            },

            "voice_b": {
                "role":
                    "experimental_reasoning",

                "result":
                    {
                        "experimental": True
                    },

                "digest":
                    "possible-digest",
            },

            "debate": {
                "state":
                    debate_state,

                "winner":
                    None,

                "contradictions":
                    (
                        contradictions
                        if contradictions is not None
                        else [
                            "branches disagree"
                        ]
                    ),

                "unresolved":
                    (
                        unresolved
                        if unresolved is not None
                        else [
                            {
                                "status":
                                    "possible"
                            }
                        ]
                    ),

                "tests_needed": [
                    "functional comparison",
                ],
            },
        },
    )

    mind.reflect(
        "O345",
        {
            "decision_authority": False,
        },
    )

    mind.reflect(
        "KMBP",
        {
            "decision_authority": False,
        },
    )

    mind.reflect(
        "Swarm",
        {
            "decision_authority": False,
        },
    )

    mind.reflect(
        "Omni",
        {
            "decision_authority": False,
        },
    )

    return mind


def test_disagreement_defers_joint_choice():
    mind = populated_mind()

    interlayer = compute_interlayer_pass(
        mind.snapshot()
    )

    result = compute_joint_choice(
        mind.snapshot(),
        interlayer,
    )

    assert result["invariant_ok"] is True

    assert (
        result["deliberation"]["state"]
        ==
        "DEFERRED"
    )

    assert (
        result["deliberation"][
            "selected_for_reasoning"
        ]
        is None
    )

    assert (
        result["deliberation"][
            "execution_authorized"
        ]
        is False
    )


def test_main_and_possible_are_both_preserved():
    mind = populated_mind()

    interlayer = compute_interlayer_pass(
        mind.snapshot()
    )

    result = compute_joint_choice(
        mind.snapshot(),
        interlayer,
    )

    assert set(result["candidates"]) == {
        "main",
        "possible",
    }

    assert (
        result["candidates"]["main"][
            "may_be_wrong"
        ]
        is True
    )

    assert (
        result["candidates"]["possible"][
            "may_be_wrong"
        ]
        is True
    )

    assert (
        result["candidates"]["possible"][
            "revisable"
        ]
        is True
    )


def test_support_is_not_converted_to_votes():
    mind = populated_mind()

    interlayer = compute_interlayer_pass(
        mind.snapshot()
    )

    result = compute_joint_choice(
        mind.snapshot(),
        interlayer,
    )

    assert result["support"]

    assert all(
        item["vote_weight"] is None
        for item in result["support"]
    )

    assert (
        result["deliberation"][
            "majority_vote_used"
        ]
        is False
    )

    assert (
        result["deliberation"][
            "vote_count_used"
        ]
        is False
    )


def test_agreement_preserves_coherent_pair():
    mind = populated_mind(
        debate_state="AGREEMENT",
        contradictions=[],
        unresolved=[],
    )

    reflections = mind.observations[
        "FullReflections"
    ]

    reflections["debate"][
        "tests_needed"
    ] = []

    interlayer = compute_interlayer_pass(
        mind.snapshot()
    )

    result = compute_joint_choice(
        mind.snapshot(),
        interlayer,
    )

    assert (
        result["deliberation"]["state"]
        ==
        "AGREEMENT_PRESERVED"
    )

    assert (
        result["deliberation"][
            "selected_for_reasoning"
        ]
        ==
        "coherent_pair"
    )

    assert (
        result["deliberation"][
            "execution_authorized"
        ]
        is False
    )


def test_joint_choice_uses_organ_result_contract():
    mind = populated_mind()

    interlayer = compute_interlayer_pass(
        mind.snapshot()
    )

    result = run_joint_choice(
        mind.snapshot(),
        interlayer,
    )

    assert result.organ == "JointChoice"
    assert result.status == "ok"
    assert result.error is None
    assert result.data["invariant_ok"] is True


def test_integration_preserves_existing_thought():
    mind = populated_mind()

    interlayer = compute_interlayer_pass(
        mind.snapshot()
    )

    before = mind.snapshot()

    result = integrate_joint_choice(
        mind,
        interlayer,
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
        "JointChoice"
        in
        after["reflections"]
    )


def test_joint_choice_snapshot_isolated():
    mind = populated_mind()

    interlayer = compute_interlayer_pass(
        mind.snapshot()
    )

    result = integrate_joint_choice(
        mind,
        interlayer,
    )

    external = deepcopy(
        result.data
    )

    external["candidate_names"].append(
        "MUTATION"
    )

    assert (
        "MUTATION"
        not in
        mind.reflections[
            "JointChoice"
        ][
            "candidate_names"
        ]
    )
