from copy import deepcopy

from malysh_system.thought_confluence import (
    build_confluence_hypothesis,
    extract_real_thought,
    publish_confluence,
)


def cycle_result():
    full_reflections = {
        "schema":
            "malysh.reflections.v2",

        "voice_a": {
            "role":
                "historical_reasoning",

            "result": {
                "conclusion":
                    "Recovered organs may form "
                    "one development contour.",
            },
        },

        "voice_b": {
            "role":
                "experimental_reasoning",

            "result": {
                "hypothesis":
                    "The organs may still be "
                    "independent experiments.",

                "revisable":
                    True,
            },
        },

        "debate": {
            "state":
                "DISAGREEMENT",

            "contradictions": [
                "causal integration is unproven"
            ],

            "unresolved": [
                {
                    "question":
                        "Does the pattern survive ablation?"
                }
            ],

            "tests_needed": [
                "controlled functional comparison"
            ],
        },
    }

    cognitive_flow = {
        "organ":
            "CognitiveFlow",

        "schema":
            "malysh.cognitive-organ-bridge.v1",

        "branches": {
            "primary": {
                "selected_id":
                    "organ_observation_fullreflections",

                "score":
                    2.0,
            },

            "possible": {
                "selected_id":
                    None,
            },

            "negative": {
                "selected_id":
                    None,
            },

            "unresolved": {
                "selected_id":
                    None,
            },
        },

        "decision_authority":
            False,

        "automatic_execution":
            False,
    }

    return {
        "schema":
            "malysh.thinking-cycle.v1",

        "subject":
            "Malysh",

        "mind": {
            "subject":
                "Malysh",

            "canonical": {
                "a3": 1,
                "b4": 1,
                "c5": 2,
            },

            "observations": {
                "CognitiveFlow":
                    cognitive_flow,

                "FullReflections":
                    full_reflections,

                "HumanLayer": {
                    "possible_preserved":
                        True,
                },
            },

            "reflections": {},
        },

        "invariants": {
            "one_subject":
                True,

            "canonical_preserved":
                True,
        },
    }


def test_selected_full_reflections_is_resolved():
    thought = extract_real_thought(
        cycle_result()
    )

    selection = thought["selection"]

    assert selection["resolved"] is True

    assert (
        selection["selected_id"]
        ==
        "organ_observation_fullreflections"
    )

    assert (
        selection["selected_organ"]
        ==
        "FullReflections"
    )


def test_primary_is_not_unavailable():
    thought = extract_real_thought(
        cycle_result()
    )

    primary = (
        thought["branches"]["primary"]
    )

    assert (
        primary["status"]
        ==
        "selected_primary"
    )

    assert (
        primary["selected_organ"]
        ==
        "FullReflections"
    )

    assert "selected_payload" in primary

    assert (
        primary.get("status")
        !=
        "unavailable"
    )


def test_possible_negative_unresolved_survive():
    thought = extract_real_thought(
        cycle_result()
    )

    branches = thought["branches"]

    assert branches["possible"]
    assert branches["negative"]
    assert branches["unresolved"]

    assert (
        branches["possible"]
        !=
        branches["primary"]
    )


def test_confluence_has_no_winner():
    record, thought = (
        build_confluence_hypothesis(
            cycle_result(),
            hypothesis_id=
                "confluence-test-001",
        )
    )

    value = record.to_dict()

    assert (
        "FullReflections"
        in
        value["claim"]
    )

    experiment = value[
        "proposed_experiment"
    ]

    assert (
        experiment["winner_selection"]
        is False
    )

    assert (
        experiment[
            "result_becomes_experience"
        ]
        is True
    )

    assert (
        value["decision_authority"]
        is False
    )

    assert (
        value["automatic_execution"]
        is False
    )


def test_cycle_is_not_modified():
    source = cycle_result()
    before = deepcopy(source)

    build_confluence_hypothesis(
        source
    )

    assert source == before


def test_publication_is_isolated(tmp_path):
    result = publish_confluence(
        cycle_result(),
        tmp_path / "storage",
        hypothesis_id=
            "confluence-test-002",
        review_packet_path=
            tmp_path / "review.txt",
    )

    assert result["status"] == "published"
    assert result["winner_selected"] is False
    assert result["experiment_decides"] is True
    assert result["automatic_execution"] is False

    assert (
        tmp_path
        / "storage"
        / "hypotheses"
        / "confluence-test-002.json"
    ).exists()

    assert (
        tmp_path / "review.txt"
    ).exists()
