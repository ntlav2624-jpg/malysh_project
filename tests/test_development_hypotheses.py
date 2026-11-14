from copy import deepcopy
import json

import pytest

from malysh_system.development_hypotheses import (
    build_external_review,
    build_hypothesis,
    create_review_packet,
    inspect_storage,
    publish_external_review,
    publish_hypothesis,
    validate_hypothesis,
)


def sample_hypothesis():
    return build_hypothesis(
        hypothesis_id="hypothesis-test-001",

        claim=(
            "Inter-layer observation may reveal "
            "a reusable development pattern."
        ),

        rationale=[
            "Several organs produced compatible observations.",
            "The pattern has not yet received an execution test.",
        ],

        primary={
            "conclusion":
                "The pattern is likely reusable.",

            "may_be_wrong":
                True,
        },

        possible={
            "hypothesis":
                "The similarity may be accidental.",

            "revisable":
                True,
        },

        negative={
            "result":
                "No execution authority is granted.",
        },

        unresolved={
            "questions": [
                "Does the pattern survive ablation?"
            ],
        },

        evidence=[
            {
                "organ": "InterLayer",
                "observation": "compatible outputs",
            }
        ],

        proposed_experiment={
            "type": "functional_ablation",
            "input": "same controlled state",
            "expected_difference":
                "downstream observation changes",
        },

        invariants=[
            "canonical state must remain unchanged",
            "no automatic execution",
            "no decision authority",
        ],

        provenance={
            "subject": "Malysh",
            "origin": "independent_internal_reasoning",
        },
    )


def test_complete_hypothesis_contract():
    record = sample_hypothesis()
    payload = record.to_dict()
    checks = validate_hypothesis(payload)

    assert all(checks.values())

    assert set(payload["branches"]) == {
        "primary",
        "possible",
        "negative",
        "unresolved",
    }

    assert payload["decision_authority"] is False
    assert payload["state_commit"] is False
    assert payload["automatic_execution"] is False


def test_publish_is_append_only(tmp_path):
    record = sample_hypothesis()

    result = publish_hypothesis(
        record,
        tmp_path,
    )

    assert result["invariant_ok"] is True

    hypothesis_path = (
        tmp_path
        / "hypotheses"
        / "hypothesis-test-001.json"
    )

    assert hypothesis_path.exists()

    with pytest.raises(FileExistsError):
        publish_hypothesis(
            record,
            tmp_path,
        )


def test_external_review_has_no_authority(tmp_path):
    record = sample_hypothesis()

    publish_hypothesis(
        record,
        tmp_path,
    )

    review = build_external_review(
        hypothesis=record.to_dict(),
        reviewer="Microsoft 365 Copilot",
        assessment="possible",

        reasoning=[
            "The claim is internally coherent.",
            "Ablation evidence is still required.",
        ],

        supported_points=[
            "Branches are preserved.",
        ],

        challenged_points=[
            "Causal influence is not yet proven.",
        ],

        required_tests=[
            "Run controlled ablation.",
        ],

        reviewer_hypothesis={
            "claim":
                "The pattern may be observational "
                "rather than causal.",

            "status":
                "possible",
        },
    )

    assert review["final_truth"] is False
    assert review["decision_authority"] is False
    assert review["state_commit"] is False
    assert review["automatic_execution"] is False

    result = publish_external_review(
        review,
        tmp_path,
    )

    assert result["invariant_ok"] is True


def test_review_packet_preserves_malysh_voice():
    record = sample_hypothesis()

    packet = create_review_packet(
        record.to_dict()
    )

    assert "MALYSH HYPOTHESIS REVIEW PACKET" in packet
    assert "Malysh's independent proposal" in packet
    assert record.claim in packet


def test_storage_reports_hypothesis_and_review(tmp_path):
    record = sample_hypothesis()

    publish_hypothesis(
        record,
        tmp_path,
    )

    review = build_external_review(
        hypothesis=record.to_dict(),
        reviewer="Microsoft 365 Copilot",
        assessment="insufficient_evidence",
        reasoning=["Functional evidence is missing."],
        supported_points=[],
        challenged_points=["Causality is not established."],
        required_tests=["Run a real input-output test."],
        reviewer_hypothesis={
            "claim":
                "The organ may currently be decorative.",
        },
    )

    publish_external_review(
        review,
        tmp_path,
    )

    state = inspect_storage(
        tmp_path
    )

    assert state["hypotheses"] == 1
    assert state["reviews"] == 1
    assert state["wal_events"] == 2
    assert state["canonical_core_modified"] is False
    assert state["automatic_execution"] is False


def test_input_objects_are_not_mutated():
    primary = {
        "conclusion": "candidate",
    }

    original = deepcopy(primary)

    record = build_hypothesis(
        claim="Test hypothesis",
        rationale=["Test rationale"],
        primary=primary,
        possible={"hypothesis": "alternative"},
        negative={"result": "negative"},
        unresolved={"question": "unknown"},
        evidence=[],
        proposed_experiment={"type": "test"},
        invariants=["canonical unchanged"],
        provenance={"origin": "test"},
    )

    payload = record.to_dict()
    payload["branches"]["primary"]["mutated"] = True

    assert primary == original
