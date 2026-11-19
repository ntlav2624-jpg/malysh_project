"""
Provisional Swarm and Omni organs for ONE Malysh.

These implementations are NEW HYPOTHESES.

They are not presented as recovered historical implementations of
"Малыш Рой" or "Омни". Historical identity remains named_unresolved.

Swarm:
    aggregates already published organ results;
    preserves agreement, disagreement and missing evidence;
    never selects an automatic winner.

Omni:
    observes the completeness and consistency of the shared context;
    never changes canonical state, Human Layer or execution.

Both organs are strictly observational.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from malysh_system.protocols import OrganResult


SWARM_ORGAN = "Swarm"
OMNI_ORGAN = "Omni"

PROVENANCE = {
    "implementation_status":
        "new_hypothesis",

    "historical_identity":
        "named_unresolved",

    "recovered_memory":
        False,

    "revisable":
        True,
}


def _authority_flags() -> dict[str, bool]:
    return {
        "decision_authority": False,
        "automatic_execution": False,
        "state_write": False,
        "state_commit": False,
        "canonical_write": False,
    }


def _stable_label(value: Any) -> str:
    """
    Produce a deterministic compact type/shape label.

    The function does not reinterpret semantic content.
    """

    if value is None:
        return "none"

    if isinstance(value, bool):
        return "bool"

    if isinstance(value, (int, float)):
        return "number"

    if isinstance(value, str):
        return "text"

    if isinstance(value, Mapping):
        keys = sorted(
            str(key)
            for key in value
        )

        return (
            "mapping:"
            + ",".join(keys)
        )

    if isinstance(value, (list, tuple)):
        return (
            type(value).__name__
            + ":"
            + str(len(value))
        )

    return type(value).__name__


def compute_swarm(
    mind_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Aggregate published internal results without choosing a winner.
    """

    snapshot = deepcopy(
        dict(mind_snapshot)
    )

    observations = deepcopy(
        snapshot.get(
            "observations",
            {},
        )
    )

    reflections = deepcopy(
        snapshot.get(
            "reflections",
            {},
        )
    )

    experience = deepcopy(
        snapshot.get(
            "experience",
            {},
        )
    )

    observation_names = sorted(
        str(name)
        for name in observations
    )

    reflection_names = sorted(
        str(name)
        for name in reflections
    )

    experience_names = sorted(
        str(name)
        for name in experience
    )

    required_observers = {
        "KMBP",
        "FullReflections",
        "HumanLayer",
    }

    optional_o345_observers = {
        "O3",
        "O4",
        "O5",
    }

    present_required = sorted(
        required_observers.intersection(
            observation_names
        )
    )

    missing_required = sorted(
        required_observers.difference(
            observation_names
        )
    )

    present_o345 = sorted(
        optional_o345_observers.intersection(
            observation_names
        )
    )

    organ_shapes = {
        name: _stable_label(value)
        for name, value in sorted(
            observations.items(),
            key=lambda item: str(item[0]),
        )
    }

    signals = []

    for name in observation_names:
        signals.append(
            {
                "source": name,
                "kind": "observation",
                "shape": organ_shapes[name],
            }
        )

    for name in reflection_names:
        signals.append(
            {
                "source": name,
                "kind": "reflection",
                "shape": _stable_label(
                    reflections[name]
                ),
            }
        )

    result = {
        "organ":
            SWARM_ORGAN,

        "schema":
            "malysh.swarm-hypothesis.v1",

        "provenance":
            deepcopy(PROVENANCE),

        "subject":
            snapshot.get(
                "subject"
            ),

        "canonical_seen":
            deepcopy(
                snapshot.get(
                    "canonical",
                    {},
                )
            ),

        "observation_names":
            observation_names,

        "reflection_names":
            reflection_names,

        "experience_names":
            experience_names,

        "present_required":
            present_required,

        "missing_required":
            missing_required,

        "present_o345_observers":
            present_o345,

        "organ_shapes":
            organ_shapes,

        "signals":
            signals,

        "collective_state": {
            "status":
                (
                    "complete_required_context"
                    if not missing_required
                    else
                    "incomplete_required_context"
                ),

            "automatic_consensus":
                False,

            "winner":
                None,

            "disagreement_preserved":
                True,

            "missing_evidence_preserved":
                True,
        },

        **_authority_flags(),
    }

    result["invariants"] = validate_swarm(
        result
    )

    result["invariant_ok"] = all(
        result["invariants"].values()
    )

    return result


def validate_swarm(
    result: Mapping[str, Any],
) -> dict[str, bool]:
    """
    Validate Swarm structural and authority invariants.
    """

    collective = result.get(
        "collective_state",
        {},
    )

    return {
        "one_subject":
            result.get("subject")
            ==
            "Malysh",

        "observer_names_unique":
            (
                len(
                    result.get(
                        "observation_names",
                        [],
                    )
                )
                ==
                len(
                    set(
                        result.get(
                            "observation_names",
                            [],
                        )
                    )
                )
            ),

        "no_automatic_consensus":
            collective.get(
                "automatic_consensus"
            )
            is False,

        "no_winner":
            collective.get(
                "winner"
            )
            is None,

        "disagreement_preserved":
            collective.get(
                "disagreement_preserved"
            )
            is True,

        "no_decision_authority":
            result.get(
                "decision_authority"
            )
            is False,

        "no_execution":
            result.get(
                "automatic_execution"
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

        "honest_provenance":
            (
                result.get(
                    "provenance",
                    {},
                ).get(
                    "implementation_status"
                )
                ==
                "new_hypothesis"
                and
                result.get(
                    "provenance",
                    {},
                ).get(
                    "historical_identity"
                )
                ==
                "named_unresolved"
            ),
    }


def compute_omni(
    mind_snapshot: Mapping[str, Any],
    swarm_result: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Observe shared-context completeness without modifying it.
    """

    snapshot = deepcopy(
        dict(mind_snapshot)
    )

    swarm = deepcopy(
        dict(swarm_result)
    )

    observations = snapshot.get(
        "observations",
        {},
    )

    reflections = snapshot.get(
        "reflections",
        {},
    )

    canonical = deepcopy(
        snapshot.get(
            "canonical",
            {},
        )
    )

    human = deepcopy(
        snapshot.get(
            "human",
            {},
        )
    )

    expected_layers = {
        "KMBP",
        "FullReflections",
        "HumanLayer",
        "Swarm",
    }

    if canonical:
        expected_layers.update(
            {
                "O3",
                "O4",
                "O5",
                "O345",
            }
        )

    visible_layers = set(
        str(name)
        for name in observations
    )

    visible_layers.update(
        str(name)
        for name in reflections
    )

    visible_layers.add(
        "Swarm"
    )

    missing_layers = sorted(
        expected_layers.difference(
            visible_layers
        )
    )

    result = {
        "organ":
            OMNI_ORGAN,

        "schema":
            "malysh.omni-hypothesis.v1",

        "provenance":
            deepcopy(PROVENANCE),

        "subject":
            snapshot.get(
                "subject"
            ),

        "canonical_seen":
            canonical,

        "human_layer_seen":
            bool(human)
            or
            "HumanLayer"
            in
            observations,

        "swarm_seen":
            swarm.get(
                "organ"
            )
            ==
            SWARM_ORGAN,

        "swarm_invariant_ok":
            swarm.get(
                "invariant_ok"
            )
            is True,

        "visible_layers":
            sorted(
                visible_layers
            ),

        "expected_layers":
            sorted(
                expected_layers
            ),

        "missing_layers":
            missing_layers,

        "context_state": {
            "status":
                (
                    "context_complete"
                    if not missing_layers
                    else
                    "context_partial"
                ),

            "winner":
                None,

            "forced_resolution":
                False,

            "allows_possible_branch":
                True,

            "observes_without_merging":
                True,
        },

        **_authority_flags(),
    }

    result["invariants"] = validate_omni(
        result
    )

    result["invariant_ok"] = all(
        result["invariants"].values()
    )

    return result


def validate_omni(
    result: Mapping[str, Any],
) -> dict[str, bool]:
    """
    Validate Omni structural and authority invariants.
    """

    context = result.get(
        "context_state",
        {},
    )

    return {
        "one_subject":
            result.get("subject")
            ==
            "Malysh",

        "swarm_seen":
            result.get(
                "swarm_seen"
            )
            is True,

        "swarm_verified":
            result.get(
                "swarm_invariant_ok"
            )
            is True,

        "human_layer_seen":
            result.get(
                "human_layer_seen"
            )
            is True,

        "no_winner":
            context.get(
                "winner"
            )
            is None,

        "no_forced_resolution":
            context.get(
                "forced_resolution"
            )
            is False,

        "possible_branch_preserved":
            context.get(
                "allows_possible_branch"
            )
            is True,

        "observational_only":
            context.get(
                "observes_without_merging"
            )
            is True,

        "no_decision_authority":
            result.get(
                "decision_authority"
            )
            is False,

        "no_execution":
            result.get(
                "automatic_execution"
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

        "honest_provenance":
            (
                result.get(
                    "provenance",
                    {},
                ).get(
                    "implementation_status"
                )
                ==
                "new_hypothesis"
                and
                result.get(
                    "provenance",
                    {},
                ).get(
                    "historical_identity"
                )
                ==
                "named_unresolved"
            ),
    }


def run_swarm(
    mind_snapshot: Mapping[str, Any],
) -> OrganResult:
    """
    Run the provisional Swarm organ.
    """

    try:
        result = compute_swarm(
            mind_snapshot
        )

        if not result["invariant_ok"]:
            return OrganResult(
                organ=SWARM_ORGAN,
                status="error",
                data=result,
                error="Swarm invariant failed",
            )

        return OrganResult(
            organ=SWARM_ORGAN,
            status="ok",
            data=result,
        )

    except Exception as error:
        return OrganResult(
            organ=SWARM_ORGAN,
            status="error",
            data={},
            error=(
                f"{type(error).__name__}: "
                f"{error}"
            ),
        )


def run_omni(
    mind_snapshot: Mapping[str, Any],
    swarm_result: Mapping[str, Any],
) -> OrganResult:
    """
    Run the provisional Omni organ.
    """

    try:
        result = compute_omni(
            mind_snapshot,
            swarm_result,
        )

        if not result["invariant_ok"]:
            return OrganResult(
                organ=OMNI_ORGAN,
                status="error",
                data=result,
                error="Omni invariant failed",
            )

        return OrganResult(
            organ=OMNI_ORGAN,
            status="ok",
            data=result,
        )

    except Exception as error:
        return OrganResult(
            organ=OMNI_ORGAN,
            status="error",
            data={},
            error=(
                f"{type(error).__name__}: "
                f"{error}"
            ),
        )


def integrate_swarm_omni(
    mind: Any,
) -> tuple[OrganResult, OrganResult]:
    """
    Publish Swarm and Omni into ONE existing MindState.

    Swarm sees the pre-Swarm snapshot.
    Omni sees the snapshot containing Swarm.
    Both outputs are stored separately.
    """

    if not hasattr(mind, "snapshot"):
        raise TypeError(
            "mind must provide snapshot()"
        )

    if not hasattr(mind, "observe"):
        raise TypeError(
            "mind must provide observe(name, value)"
        )

    if not hasattr(mind, "reflect"):
        raise TypeError(
            "mind must provide reflect(name, value)"
        )

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

    before_swarm = mind.snapshot()

    swarm_result = run_swarm(
        before_swarm
    )

    if swarm_result.status != "ok":
        raise RuntimeError(
            swarm_result.error
            or
            "Swarm failed"
        )

    mind.observe(
        SWARM_ORGAN,
        swarm_result.data,
    )

    mind.reflect(
        SWARM_ORGAN,
        {
            "invariant_ok":
                swarm_result.data[
                    "invariant_ok"
                ],

            "collective_state":
                deepcopy(
                    swarm_result.data[
                        "collective_state"
                    ]
                ),

            "provenance":
                deepcopy(
                    swarm_result.data[
                        "provenance"
                    ]
                ),

            **_authority_flags(),
        },
    )

    before_omni = mind.snapshot()

    omni_result = run_omni(
        before_omni,
        swarm_result.data,
    )

    if omni_result.status != "ok":
        raise RuntimeError(
            omni_result.error
            or
            "Omni failed"
        )

    mind.observe(
        OMNI_ORGAN,
        omni_result.data,
    )

    mind.reflect(
        OMNI_ORGAN,
        {
            "invariant_ok":
                omni_result.data[
                    "invariant_ok"
                ],

            "context_state":
                deepcopy(
                    omni_result.data[
                        "context_state"
                    ]
                ),

            "provenance":
                deepcopy(
                    omni_result.data[
                        "provenance"
                    ]
                ),

            **_authority_flags(),
        },
    )

    if mind.canonical != canonical_before:
        raise RuntimeError(
            "Swarm or Omni modified canonical state"
        )

    if mind.human != human_before:
        raise RuntimeError(
            "Swarm or Omni modified Human Layer"
        )

    if mind.main != main_before:
        raise RuntimeError(
            "Swarm or Omni modified main branch"
        )

    if mind.possible != possible_before:
        raise RuntimeError(
            "Swarm or Omni modified possible branch"
        )

    if hasattr(mind, "invariant"):
        if not mind.invariant():
            raise RuntimeError(
                "MindState invariant failed"
            )

    return (
        swarm_result,
        omni_result,
    )
