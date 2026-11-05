"""
Read-only recovery of historical Malysh topology logic.

Recovered source lineage:

    repository:
        ntlav2624-jpg/malysh

    file:
        malysh_topology_engine.py

Historical computation preserved:

    degree'  = max(3, round(degree * 0.35, 2))
    entropy' = round(entropy * 0.28, 4)
    noise'   = round(noise * 0.22, 4)
    topology'= "compact"

Historical side effects disabled:

    mutation of the caller's node
    sleep()
    terminal HUD
    writes to ~/malysh_topological_state.json

This adapter is deterministic, observational and has no execution,
decision, canonical-write or transaction authority.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

from malysh_system.protocols import OrganResult


ORGAN = "HistoricalTopology"

SCHEMA = "malysh.historical-topology.v1"

HERITAGE = {
    "repository":
        "ntlav2624-jpg/malysh",

    "branch":
        "main",

    "file":
        "malysh_topology_engine.py",

    "identity":
        "recovered_source",

    "adaptation":
        "pure_read_only",

    "historical_classes": [
        "TopologicalNode",
        "TopoStabilinOperator",
        "TopologicalAutoStabilizer",
    ],
}


def authority_flags() -> dict[str, bool]:
    return {
        "decision_authority":
            False,

        "automatic_execution":
            False,

        "state_write":
            False,

        "state_commit":
            False,

        "canonical_write":
            False,

        "transaction_authorized":
            False,

        "winner_selection":
            False,

        "input_mutation":
            False,

        "filesystem_write":
            False,

        "sleep_used":
            False,
    }


@dataclass(frozen=True)
class TopologicalState:
    """
    Immutable topological state used by the recovered adapter.
    """

    name: str
    degree: float
    entropy: float
    resonance_noise: float
    topology: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
    ) -> "TopologicalState":
        required = {
            "name",
            "degree",
            "entropy",
            "resonance_noise",
            "topology",
        }

        missing = sorted(
            required.difference(value)
        )

        if missing:
            raise ValueError(
                "missing topology fields: "
                + ", ".join(missing)
            )

        state = cls(
            name=str(value["name"]),
            degree=float(value["degree"]),
            entropy=float(value["entropy"]),
            resonance_noise=float(
                value["resonance_noise"]
            ),
            topology=str(value["topology"]),
        )

        state.validate()

        return state

    def validate(self) -> None:
        if not self.name:
            raise ValueError(
                "topological state name is empty"
            )

        for name, number in (
            ("degree", self.degree),
            ("entropy", self.entropy),
            (
                "resonance_noise",
                self.resonance_noise,
            ),
        ):
            if number < 0:
                raise ValueError(
                    name + " must be non-negative"
                )

        if not self.topology:
            raise ValueError(
                "topology label is empty"
            )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "name":
                self.name,

            "degree":
                self.degree,

            "entropy":
                self.entropy,

            "resonance_noise":
                self.resonance_noise,

            "topology":
                self.topology,
        }


def compute_defect_vector(
    normal: TopologicalState,
    observed: TopologicalState,
) -> dict[str, Any]:
    """
    Recover the historical defect-vector computation.
    """

    return {
        "degree_excess":
            round(
                observed.degree
                -
                normal.degree,
                2,
            ),

        "entropy_excess":
            round(
                observed.entropy
                -
                normal.entropy,
                4,
            ),

        "noise_excess":
            round(
                observed.resonance_noise
                -
                normal.resonance_noise,
                4,
            ),

        "topology_shift":
            (
                observed.topology
                + "_to_"
                + normal.topology
            ),
    }


def apply_topo_stabilin(
    observed: TopologicalState,
) -> TopologicalState:
    """
    Pure adaptation of historical TopoStabilinOperator.apply().

    The input object is immutable and cannot be modified.
    """

    return TopologicalState(
        name=observed.name,

        degree=max(
            3.0,
            round(
                observed.degree * 0.35,
                2,
            ),
        ),

        entropy=round(
            observed.entropy * 0.28,
            4,
        ),

        resonance_noise=round(
            observed.resonance_noise * 0.22,
            4,
        ),

        topology="compact",
    )


def compute_historical_topology(
    normal_state: Mapping[str, Any],
    observed_state: Mapping[str, Any],
    subject: str = "Malysh",
) -> dict[str, Any]:
    """
    Execute historical topology analysis without side effects.
    """

    if subject != "Malysh":
        raise ValueError(
            "historical topology belongs to ONE Malysh"
        )

    normal_input = deepcopy(
        dict(normal_state)
    )

    observed_input = deepcopy(
        dict(observed_state)
    )

    normal = TopologicalState.from_mapping(
        normal_input
    )

    observed = TopologicalState.from_mapping(
        observed_input
    )

    defect = compute_defect_vector(
        normal,
        observed,
    )

    corrected = apply_topo_stabilin(
        observed
    )

    corrected_dict = corrected.to_dict()

    result = {
        "organ":
            ORGAN,

        "schema":
            SCHEMA,

        "subject":
            subject,

        "heritage":
            deepcopy(HERITAGE),

        "normal_state":
            normal.to_dict(),

        "observed_state":
            observed.to_dict(),

        "defect_vector":
            defect,

        "corrected_state":
            corrected_dict,

        "operator": {
            "name":
                "TopoStabilinOperator",

            "degree_factor":
                0.35,

            "degree_floor":
                3.0,

            "entropy_factor":
                0.28,

            "noise_factor":
                0.22,

            "target_topology":
                "compact",
        },

        "correction_applied":
            True,

        **authority_flags(),
    }

    result["invariants"] = {
        "one_subject":
            result["subject"] == "Malysh",

        "source_recovered":
            (
                result["heritage"]["identity"]
                ==
                "recovered_source"
            ),

        "input_not_mutated":
            (
                normal_input
                ==
                dict(normal_state)
                and
                observed_input
                ==
                dict(observed_state)
            ),

        "degree_formula":
            (
                corrected.degree
                ==
                max(
                    3.0,
                    round(
                        observed.degree * 0.35,
                        2,
                    ),
                )
            ),

        "entropy_formula":
            (
                corrected.entropy
                ==
                round(
                    observed.entropy * 0.28,
                    4,
                )
            ),

        "noise_formula":
            (
                corrected.resonance_noise
                ==
                round(
                    observed.resonance_noise
                    * 0.22,
                    4,
                )
            ),

        "compact_projection":
            (
                corrected.topology
                ==
                "compact"
            ),

        "no_decision_authority":
            (
                result["decision_authority"]
                is False
            ),

        "no_execution":
            (
                result["automatic_execution"]
                is False
            ),

        "no_state_write":
            result["state_write"] is False,

        "no_state_commit":
            result["state_commit"] is False,

        "no_canonical_write":
            (
                result["canonical_write"]
                is False
            ),

        "no_transaction":
            (
                result[
                    "transaction_authorized"
                ]
                is False
            ),

        "no_winner":
            (
                result["winner_selection"]
                is False
            ),

        "no_filesystem_write":
            (
                result["filesystem_write"]
                is False
            ),

        "no_sleep":
            result["sleep_used"] is False,
    }

    result["invariant_ok"] = all(
        result["invariants"].values()
    )

    return result


def run_historical_topology(
    normal_state: Mapping[str, Any],
    observed_state: Mapping[str, Any],
    subject: str = "Malysh",
) -> OrganResult:
    """
    Return historical topology computation as OrganResult.
    """

    try:
        result = compute_historical_topology(
            normal_state,
            observed_state,
            subject,
        )

        if not result["invariant_ok"]:
            return OrganResult(
                organ=ORGAN,
                status="error",
                data=result,
                error=(
                    "HistoricalTopology "
                    "invariant failed"
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
                type(error).__name__
                + ": "
                + str(error)
            ),
        )


def integrate_historical_topology(
    mind: Any,
    normal_state: Mapping[str, Any],
    observed_state: Mapping[str, Any],
) -> OrganResult:
    """
    Publish historical topology as an internal observation.

    Protected MindState fields must remain unchanged.
    """

    for method in (
        "snapshot",
        "observe",
        "reflect",
    ):
        if not hasattr(mind, method):
            raise TypeError(
                "mind must provide "
                + method
                + "()"
            )

    before = mind.snapshot()

    protected = {
        key: deepcopy(before[key])
        for key in (
            "subject",
            "canonical",
            "experience",
            "human",
            "main",
            "possible",
        )
    }

    result = run_historical_topology(
        normal_state,
        observed_state,
        subject=before["subject"],
    )

    if result.status != "ok":
        raise RuntimeError(
            result.error
            or
            "HistoricalTopology failed"
        )

    mind.observe(
        ORGAN,
        result.data,
    )

    mind.reflect(
        ORGAN,
        {
            "schema":
                result.data["schema"],

            "heritage":
                deepcopy(
                    result.data[
                        "heritage"
                    ]
                ),

            "defect_vector":
                deepcopy(
                    result.data[
                        "defect_vector"
                    ]
                ),

            "corrected_state":
                deepcopy(
                    result.data[
                        "corrected_state"
                    ]
                ),

            "invariant_ok":
                result.data[
                    "invariant_ok"
                ],

            **authority_flags(),
        },
    )

    after = mind.snapshot()

    for key, expected in protected.items():
        if after[key] != expected:
            raise RuntimeError(
                "HistoricalTopology mutated "
                "protected field: "
                + key
            )

    if hasattr(mind, "invariant"):
        if not mind.invariant():
            raise RuntimeError(
                "MindState invariant failed"
            )

    return result
