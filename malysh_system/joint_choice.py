"""
JointChoice deliberation for ONE Malysh.

JointChoice is not majority voting and is not an executor.

It receives one frozen thought context containing:

    main historical/logical branch
    possible/experimental branch
    Human Layer
    O345
    KMBP
    Swarm
    Omni
    inter-layer observations
    legacy experience

JointChoice may organize evidence, contradictions, alternatives and
unresolved requirements. It cannot mutate the thought that it studies.

A thought-level selection is not a transaction commit.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from malysh_system.protocols import OrganResult


ORGAN = "JointChoice"


def _authority_flags() -> dict[str, bool]:
    return {
        "decision_authority": False,
        "automatic_execution": False,
        "state_write": False,
        "state_commit": False,
        "canonical_write": False,
        "main_answer_write": False,
        "possible_branch_write": False,
        "transaction_commit": False,
    }


def _shape(value: Any) -> dict[str, Any]:
    if value is None:
        return {
            "type": "none",
            "size": 0,
            "keys": [],
        }

    if isinstance(value, Mapping):
        return {
            "type": "mapping",
            "size": len(value),
            "keys": sorted(
                str(key)
                for key in value
            ),
        }

    if isinstance(value, (list, tuple)):
        return {
            "type": type(value).__name__,
            "size": len(value),
            "keys": [],
        }

    return {
        "type": type(value).__name__,
        "size": 1,
        "keys": [],
    }


def _get_reflections_result(
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    observations = snapshot.get(
        "observations",
        {},
    )

    value = observations.get(
        "FullReflections",
        {},
    )

    if isinstance(value, Mapping):
        return deepcopy(
            dict(value)
        )

    return {}


def _build_candidates(
    reflections: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Extract the two preserved V2 voices without declaring a winner.
    """

    voice_a = deepcopy(
        reflections.get(
            "voice_a",
            {},
        )
    )

    voice_b = deepcopy(
        reflections.get(
            "voice_b",
            {},
        )
    )

    candidates = {}

    if voice_a:
        candidates["main"] = {
            "source":
                "voice_a",

            "role":
                voice_a.get(
                    "role",
                    "historical_reasoning",
                ),

            "result":
                deepcopy(
                    voice_a.get(
                        "result"
                    )
                ),

            "digest":
                voice_a.get(
                    "digest"
                ),

            "may_be_wrong":
                True,

            "preserved":
                True,
        }

    if voice_b:
        candidates["possible"] = {
            "source":
                "voice_b",

            "role":
                voice_b.get(
                    "role",
                    "experimental_reasoning",
                ),

            "result":
                deepcopy(
                    voice_b.get(
                        "result"
                    )
                ),

            "digest":
                voice_b.get(
                    "digest"
                ),

            "may_be_wrong":
                True,

            "revisable":
                True,

            "preserved":
                True,
        }

    return candidates


def _collect_support(
    snapshot: Mapping[str, Any],
    interlayer_result: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """
    Collect structural support without converting counts into votes.
    """

    observations = snapshot.get(
        "observations",
        {},
    )

    reflections = snapshot.get(
        "reflections",
        {},
    )

    support = []

    for name in (
        "O3",
        "O4",
        "O5",
        "KMBP",
        "Swarm",
        "Omni",
    ):
        if name in observations:
            support.append(
                {
                    "source": name,
                    "kind": "observation",
                    "shape": _shape(
                        observations[name]
                    ),
                    "vote_weight": None,
                }
            )

    for name in (
        "O345",
        "KMBP",
        "Swarm",
        "Omni",
    ):
        if name in reflections:
            support.append(
                {
                    "source": name,
                    "kind": "reflection",
                    "shape": _shape(
                        reflections[name]
                    ),
                    "vote_weight": None,
                }
            )

    layer_results = interlayer_result.get(
        "layer_results",
        {},
    )

    for name in sorted(layer_results):
        support.append(
            {
                "source":
                    "InterLayer:" + name,

                "kind":
                    "interlayer_reflection",

                "shape":
                    _shape(
                        layer_results[name]
                    ),

                "vote_weight":
                    None,
            }
        )

    return support


def _collect_contradictions(
    reflections: Mapping[str, Any],
) -> list:
    debate = reflections.get(
        "debate",
        {},
    )

    contradictions = deepcopy(
        debate.get(
            "contradictions",
            [],
        )
    )

    return (
        contradictions
        if isinstance(contradictions, list)
        else [contradictions]
    )


def _collect_unresolved(
    reflections: Mapping[str, Any],
) -> list:
    debate = reflections.get(
        "debate",
        {},
    )

    unresolved = deepcopy(
        debate.get(
            "unresolved",
            [],
        )
    )

    tests_needed = deepcopy(
        debate.get(
            "tests_needed",
            [],
        )
    )

    result = []

    if isinstance(unresolved, list):
        result.extend(unresolved)
    elif unresolved:
        result.append(unresolved)

    if isinstance(tests_needed, list):
        result.extend(
            {
                "type": "test_needed",
                "value": value,
            }
            for value in tests_needed
        )
    elif tests_needed:
        result.append(
            {
                "type": "test_needed",
                "value": tests_needed,
            }
        )

    return result


def compute_joint_choice(
    snapshot: Mapping[str, Any],
    interlayer_result: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Build a thought-level joint deliberation.

    Decision states:

        AGREEMENT_PRESERVED
            Both branches structurally agree.

        COEXISTENCE_PRESERVED
            Branches are complementary and remain together.

        DEFERRED
            Contradictions or unresolved tests remain.

        INSUFFICIENT_CONTEXT
            Both branches are not available.

    None of these states authorizes execution.
    """

    frozen_snapshot = deepcopy(
        dict(snapshot)
    )

    frozen_interlayer = deepcopy(
        dict(interlayer_result)
    )

    reflections = _get_reflections_result(
        frozen_snapshot
    )

    candidates = _build_candidates(
        reflections
    )

    contradictions = _collect_contradictions(
        reflections
    )

    unresolved = _collect_unresolved(
        reflections
    )

    support = _collect_support(
        frozen_snapshot,
        frozen_interlayer,
    )

    debate_state = (
        reflections.get(
            "debate",
            {},
        ).get(
            "state"
        )
    )

    candidate_names = sorted(
        candidates
    )

    has_main = "main" in candidates
    has_possible = "possible" in candidates

    if not (
        has_main
        and
        has_possible
    ):
        deliberation_state = (
            "INSUFFICIENT_CONTEXT"
        )

        selected_for_reasoning = None

        reason = (
            "Both main and possible branches "
            "must be present before joint deliberation."
        )

    elif (
        debate_state == "AGREEMENT"
        and
        not contradictions
        and
        not unresolved
    ):
        deliberation_state = (
            "AGREEMENT_PRESERVED"
        )

        selected_for_reasoning = (
            "coherent_pair"
        )

        reason = (
            "The preserved branches agree; "
            "both remain available as one reasoning context."
        )

    elif (
        debate_state == "COMPLEMENTARY"
        and
        not contradictions
    ):
        deliberation_state = (
            "COEXISTENCE_PRESERVED"
        )

        selected_for_reasoning = (
            "coexisting_pair"
        )

        reason = (
            "The branches are complementary; "
            "neither branch replaces the other."
        )

    else:
        deliberation_state = "DEFERRED"

        selected_for_reasoning = None

        reason = (
            "Contradictions or unresolved tests remain. "
            "Execution cannot be authorized."
        )

    result = {
        "organ":
            ORGAN,

        "schema":
            "malysh.joint-choice.v1",

        "subject":
            frozen_snapshot.get(
                "subject"
            ),

        "source_snapshot":
            "frozen_post_interlayer",

        "candidate_names":
            candidate_names,

        "candidates":
            candidates,

        "support":
            support,

        "contradictions":
            contradictions,

        "unresolved":
            unresolved,

        "debate_state":
            debate_state,

        "deliberation": {
            "state":
                deliberation_state,

            "selected_for_reasoning":
                selected_for_reasoning,

            "reason":
                reason,

            "main_preserved":
                has_main,

            "possible_preserved":
                has_possible,

            "majority_vote_used":
                False,

            "vote_count_used":
                False,

            "winner":
                None,

            "execution_authorized":
                False,

            "transaction_authorized":
                False,
        },

        "interlayer_verified":
            frozen_interlayer.get(
                "invariant_ok"
            )
            is True,

        "affects_main_answer":
            False,

        "affects_possible_branch":
            False,

        "affects_execution":
            False,

        **_authority_flags(),
    }

    result["invariants"] = validate_joint_choice(
        result
    )

    result["invariant_ok"] = all(
        result["invariants"].values()
    )

    return result


def validate_joint_choice(
    result: Mapping[str, Any],
) -> dict[str, bool]:
    deliberation = result.get(
        "deliberation",
        {},
    )

    candidates = result.get(
        "candidates",
        {},
    )

    main_preserved = (
        (
            "main" not in candidates
        )
        or
        deliberation.get(
            "main_preserved"
        )
        is True
    )

    possible_preserved = (
        (
            "possible" not in candidates
        )
        or
        deliberation.get(
            "possible_preserved"
        )
        is True
    )

    return {
        "one_subject":
            result.get("subject")
            ==
            "Malysh",

        "interlayer_verified":
            result.get(
                "interlayer_verified"
            )
            is True,

        "main_preserved":
            main_preserved,

        "possible_preserved":
            possible_preserved,

        "no_majority_vote":
            deliberation.get(
                "majority_vote_used"
            )
            is False,

        "no_vote_count":
            deliberation.get(
                "vote_count_used"
            )
            is False,

        "no_winner":
            deliberation.get(
                "winner"
            )
            is None,

        "no_execution_authorization":
            deliberation.get(
                "execution_authorized"
            )
            is False,

        "no_transaction_authorization":
            deliberation.get(
                "transaction_authorized"
            )
            is False,

        "main_answer_unchanged":
            result.get(
                "affects_main_answer"
            )
            is False,

        "possible_branch_unchanged":
            result.get(
                "affects_possible_branch"
            )
            is False,

        "execution_unchanged":
            result.get(
                "affects_execution"
            )
            is False,

        "no_decision_authority":
            result.get(
                "decision_authority"
            )
            is False,

        "no_state_write":
            result.get(
                "state_write"
            )
            is False,

        "no_state_commit":
            result.get(
                "state_commit"
            )
            is False,

        "no_canonical_write":
            result.get(
                "canonical_write"
            )
            is False,

        "no_main_write":
            result.get(
                "main_answer_write"
            )
            is False,

        "no_possible_write":
            result.get(
                "possible_branch_write"
            )
            is False,

        "no_transaction_commit":
            result.get(
                "transaction_commit"
            )
            is False,
    }


def run_joint_choice(
    snapshot: Mapping[str, Any],
    interlayer_result: Mapping[str, Any],
) -> OrganResult:
    try:
        result = compute_joint_choice(
            snapshot,
            interlayer_result,
        )

        if not result["invariant_ok"]:
            return OrganResult(
                organ=ORGAN,
                status="error",
                data=result,
                error=(
                    "JointChoice invariant failed"
                ),
            )

        return OrganResult(
            organ=ORGAN,
            status="ok",
            data=result,
        )

    except Exception as error:
        return OrganResult(
            organ=ORGAN,
            status="error",
            data={},
            error=(
                f"{type(error).__name__}: "
                f"{error}"
            ),
        )


def integrate_joint_choice(
    mind: Any,
    interlayer_result: Mapping[str, Any],
) -> OrganResult:
    """
    Publish JointChoice as a separate reflection.

    Existing thought state is protected against mutation.
    """

    if not hasattr(mind, "snapshot"):
        raise TypeError(
            "mind must provide snapshot()"
        )

    if not hasattr(mind, "reflect"):
        raise TypeError(
            "mind must provide reflect(name, value)"
        )

    before = mind.snapshot()

    protected = {
        key: deepcopy(
            before.get(key)
        )
        for key in (
            "subject",
            "canonical",
            "observations",
            "experience",
            "human",
            "main",
            "possible",
        )
    }

    result = run_joint_choice(
        before,
        interlayer_result,
    )

    if result.status != "ok":
        raise RuntimeError(
            result.error
            or
            "JointChoice failed"
        )

    mind.reflect(
        ORGAN,
        result.data,
    )

    after = mind.snapshot()

    for key, expected in protected.items():
        if after.get(key) != expected:
            raise RuntimeError(
                "JointChoice mutated protected state: "
                + key
            )

    if hasattr(mind, "invariant"):
        if not mind.invariant():
            raise RuntimeError(
                "MindState invariant failed"
            )

    return result
