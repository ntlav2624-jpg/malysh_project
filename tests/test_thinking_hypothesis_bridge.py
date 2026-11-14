from copy import deepcopy

from malysh_system.thinking_hypothesis_bridge import (
    build_from_thinking_cycle,
    publish_from_thinking_cycle,
)


def cycle_result():
    return {
        "schema":
            "malysh.thinking-cycle.v1",

        "subject":
            "Malysh",

        "mind": {
            "subject":
                "Malysh",

            "canonical": {
                "a3": 2,
                "b4": 3,
                "c5": 4,
            },

            "main": {
                "conclusion":
                    "A cross-layer pattern may be reusable.",

                "may_be_wrong":
                    True,
            },

            "possible": {
                "hypothesis":
                    "The similarity may be incidental.",

                "revisable":
                    True,
            },

            "negative": {
                "result":
                    "Causal influence is not yet proven.",
            },

            "unresolved": {
                "questions": [
                    "Does the pattern survive ablation?"
                ],
            },

            "observations": {
                "O3": {
                    "verified": True,
                },

                "O4": {
                    "verified": True,
                },

                "O5": {
                    "verified": True,
                },

                "KMBP": {
                    "verified": True,
                },

                "Swarm": {
                    "verified": True,
                },

                "Omni": {
                    "verified": True,
                },
            },

            "reflections": {
                "O345": {
                    "decision_authority": False,
                },

                "HumanLayer": {
                    "possible_preserved": True,
                },
            },
        },

        "interlayer": {
            "status": "ok",
            "winner": None,
        },

        "joint_choice": {
            "candidates": {
                "main": {
                    "conclusion":
                        "A cross-layer pattern "
                        "may be reusable.",

                    "may_be_wrong":
                        True,
                },

                "possible": {
                    "hypothesis":
                        "The similarity "
                        "may be incidental.",

                    "revisable":
                        True,
                },
            },

            "deliberation": {
                "state": "DEFERRED",
                "selected_for_reasoning": None,
                "execution_authorized": False,
                "majority_vote_used": False,
            },
        },
    }


def test_builds_hypothesis_from_real_cycle_shape():
    source = cycle_result()

    record, bridge = build_from_thinking_cycle(
        source,
        hypothesis_id="cycle-hypothesis-001",
    )

    value = record.to_dict()

    assert value["subject"] == "Malysh"

    assert value["claim"] == (
        "A cross-layer pattern may be reusable."
    )

    assert set(value["branches"]) == {
        "primary",
        "possible",
        "negative",
        "unresolved",
    }

    assert bridge[
        "joint_deliberation_state"
    ] == "DEFERRED"

    assert bridge[
        "decision_authority"
    ] is False

    assert bridge[
        "automatic_execution"
    ] is False


def test_cycle_input_is_not_modified():
    source = cycle_result()
    original = deepcopy(source)

    build_from_thinking_cycle(
        source
    )

    assert source == original


def test_real_organs_become_evidence():
    record, bridge = build_from_thinking_cycle(
        cycle_result()
    )

    organs = {
        item["organ"]
        for item
        in record.to_dict()["evidence"]
    }

    assert {
        "O3",
        "O4",
        "O5",
        "KMBP",
        "Swarm",
        "Omni",
        "InterLayer",
        "JointChoice",
    }.issubset(organs)

    assert bridge["evidence_count"] >= 8


def test_publication_is_isolated(tmp_path):
    source = cycle_result()
    original = deepcopy(source)

    result = publish_from_thinking_cycle(
        source,
        tmp_path / "storage",
        hypothesis_id=
            "cycle-hypothesis-002",
        review_packet_path=
            tmp_path / "review.txt",
    )

    assert result["status"] == "published"
    assert result["source_unchanged"] is True
    assert result["automatic_execution"] is False
    assert result["canonical_core_modified"] is False
    assert source == original

    assert (
        tmp_path
        / "storage"
        / "hypotheses"
        / "cycle-hypothesis-002.json"
    ).exists()

    assert (
        tmp_path
        / "review.txt"
    ).exists()


def test_possible_branch_survives():
    record, _ = build_from_thinking_cycle(
        cycle_result()
    )

    possible = (
        record.to_dict()
        ["branches"]
        ["possible"]
    )

    assert possible["revisable"] is True
    assert (
        "incidental"
        in possible["hypothesis"]
    )


def test_no_cycle_execution_authority():
    record, bridge = build_from_thinking_cycle(
        cycle_result()
    )

    value = record.to_dict()

    assert value["decision_authority"] is False
    assert value["state_commit"] is False
    assert value["automatic_execution"] is False

    assert bridge["decision_authority"] is False
    assert bridge["state_commit"] is False
