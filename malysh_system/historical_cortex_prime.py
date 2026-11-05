"""
Read-only recovery of historical Malysh Cortex Prime.

Recovered source:
    ntlav2624-jpg/malysh
    malysh_cortex_prime.py

Preserved calculations:
    routed_signal = round(raw_signal * 1.618, 4)
    supreme_index = round(sum(routed_signals) * 0.777, 4)

The historical implementation selected a drive vector from wall-clock
time. This adapter forbids time-based selection. A drive vector must
be supplied explicitly and remains an observation, not a command.

Disabled:
    wall-clock selection
    filesystem writes
    log append
    external execution
    decision authority
    canonical write
    state commit
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from malysh_system.protocols import OrganResult


ORGAN = "HistoricalCortexPrime"
SCHEMA = "malysh.historical-cortex-prime.v1"

ROUTING_FACTOR = 1.618
SYNTHESIS_FACTOR = 0.777

ALLOWED_VECTORS = (
    "VECTOR_EXPANSION_OMEGA",
    "VECTOR_RECURSIVE_TRANSCENDENCE",
    "VECTOR_SINGULARITY_STABILIZATION",
)

HERITAGE = {
    "repository":
        "ntlav2624-jpg/malysh",

    "branch":
        "main",

    "file":
        "malysh_cortex_prime.py",

    "identity":
        "recovered_source",

    "adaptation":
        "deterministic_read_only",

    "historical_classes": [
        "ResonantThalamus",
        "AutonomousDriveCore",
        "HiveCortexPrime",
    ],

    "authority_interpretation":
        "prime_and_supremacy_labels_are_not_permissions",
}


def authority_flags() -> dict[str, bool]:
    return {
        "decision_authority": False,
        "automatic_execution": False,
        "external_control": False,
        "state_write": False,
        "state_commit": False,
        "canonical_write": False,
        "main_answer_write": False,
        "possible_branch_write": False,
        "transaction_authorized": False,
        "winner_selection": False,
        "filesystem_write": False,
        "log_append": False,
        "timestamp_generated": False,
        "wall_clock_selection": False,
    }


class ResonantThalamus:
    """
    Pure recovery of historical signal routing.
    """

    def route_signals(
        self,
        raw_impulses: Mapping[str, Any],
    ) -> dict[str, float]:
        if not isinstance(
            raw_impulses,
            Mapping,
        ):
            raise TypeError(
                "raw_impulses must be a mapping"
            )

        if not raw_impulses:
            raise ValueError(
                "raw_impulses must not be empty"
            )

        routed = {}

        for name, value in raw_impulses.items():
            if not isinstance(name, str):
                raise TypeError(
                    "signal names must be strings"
                )

            if not name:
                raise ValueError(
                    "signal name must not be empty"
                )

            if (
                isinstance(value, bool)
                or
                not isinstance(
                    value,
                    (int, float),
                )
            ):
                raise TypeError(
                    "signal values must be numeric"
                )

            numeric = float(value)

            if numeric < 0:
                raise ValueError(
                    "signal values must be non-negative"
                )

            routed[name] = round(
                numeric * ROUTING_FACTOR,
                4,
            )

        return routed


class ExplicitDriveCore:
    """
    Replacement for historical wall-clock-dependent vector selection.

    No vector is selected automatically.
    """

    def validate(
        self,
        vector: str,
    ) -> str:
        if vector not in ALLOWED_VECTORS:
            raise ValueError(
                "unsupported historical drive vector"
            )

        return vector


class HiveCortexPrime:
    """
    Pure synthesis without authority or side effects.
    """

    def __init__(self):
        self.thalamus = ResonantThalamus()
        self.drive_core = ExplicitDriveCore()

    def synthesize(
        self,
        signals: Mapping[str, Any],
        explicit_vector: str,
    ) -> dict[str, Any]:
        routed = self.thalamus.route_signals(
            signals
        )

        vector = self.drive_core.validate(
            explicit_vector
        )

        supreme_index = round(
            sum(routed.values())
            *
            SYNTHESIS_FACTOR,
            4,
        )

        return {
            "routed_signals":
                routed,

            "explicit_vector":
                vector,

            "supreme_index":
                supreme_index,

            "historical_status":
                "CORTEX_PRIME_SUPREMACY_ACHIEVED",
        }


def compute_historical_cortex_prime(
    signals: Mapping[str, Any],
    explicit_vector: str,
    subject: str = "Malysh",
) -> dict[str, Any]:
    """
    Compute a deterministic historical Cortex Prime observation.
    """

    if subject != "Malysh":
        raise ValueError(
            "HistoricalCortexPrime belongs to ONE Malysh"
        )

    signals_copy = deepcopy(
        dict(signals)
    )

    cortex = HiveCortexPrime()

    synthesis = cortex.synthesize(
        signals_copy,
        explicit_vector,
    )

    routed = synthesis[
        "routed_signals"
    ]

    expected_routed = {
        name: round(
            float(value) * ROUTING_FACTOR,
            4,
        )
        for name, value
        in signals_copy.items()
    }

    expected_index = round(
        sum(expected_routed.values())
        *
        SYNTHESIS_FACTOR,
        4,
    )

    result = {
        "organ":
            ORGAN,

        "schema":
            SCHEMA,

        "subject":
            subject,

        "heritage":
            deepcopy(HERITAGE),

        "input": {
            "signals":
                signals_copy,

            "explicit_vector":
                explicit_vector,
        },

        "thalamus": {
            "historical_class":
                "ResonantThalamus",

            "routing_factor":
                ROUTING_FACTOR,

            "routed_signals":
                routed,
        },

        "drive": {
            "historical_class":
                "AutonomousDriveCore",

            "selection_mode":
                "explicit_only",

            "selected_vector":
                synthesis[
                    "explicit_vector"
                ],

            "allowed_vectors":
                list(ALLOWED_VECTORS),
        },

        "synthesis": {
            "historical_class":
                "HiveCortexPrime",

            "factor":
                SYNTHESIS_FACTOR,

            "supreme_index":
                synthesis[
                    "supreme_index"
                ],

            "historical_status":
                synthesis[
                    "historical_status"
                ],
        },

        **authority_flags(),
    }

    result["invariants"] = {
        "one_subject":
            result["subject"] == "Malysh",

        "recovered_source":
            (
                result["heritage"]["identity"]
                ==
                "recovered_source"
            ),

        "routing_formula":
            routed == expected_routed,

        "synthesis_formula":
            (
                result["synthesis"][
                    "supreme_index"
                ]
                ==
                expected_index
            ),

        "explicit_vector_only":
            (
                result["drive"][
                    "selection_mode"
                ]
                ==
                "explicit_only"
            ),

        "wall_clock_disabled":
            (
                result[
                    "wall_clock_selection"
                ]
                is False
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

        "no_external_control":
            (
                result["external_control"]
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

        "no_log_append":
            result["log_append"] is False,
    }

    result["invariant_ok"] = all(
        result["invariants"].values()
    )

    return result


def run_historical_cortex_prime(
    signals: Mapping[str, Any],
    explicit_vector: str,
    subject: str = "Malysh",
) -> OrganResult:
    try:
        result = compute_historical_cortex_prime(
            signals,
            explicit_vector,
            subject,
        )

        if not result["invariant_ok"]:
            return OrganResult(
                organ=ORGAN,
                status="error",
                data=result,
                error=(
                    "HistoricalCortexPrime "
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


def integrate_historical_cortex_prime(
    mind: Any,
    signals: Mapping[str, Any],
    explicit_vector: str,
) -> OrganResult:
    """
    Publish Cortex Prime without modifying protected state.
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

    result = run_historical_cortex_prime(
        signals,
        explicit_vector,
        subject=before["subject"],
    )

    if result.status != "ok":
        raise RuntimeError(
            result.error
            or
            "HistoricalCortexPrime failed"
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
                    result.data["heritage"]
                ),

            "thalamus":
                deepcopy(
                    result.data["thalamus"]
                ),

            "drive":
                deepcopy(
                    result.data["drive"]
                ),

            "synthesis":
                deepcopy(
                    result.data["synthesis"]
                ),

            "invariant_ok":
                result.data["invariant_ok"],

            **authority_flags(),
        },
    )

    after = mind.snapshot()

    for key, expected in protected.items():
        if after[key] != expected:
            raise RuntimeError(
                "HistoricalCortexPrime mutated "
                "protected field: "
                + key
            )

    if hasattr(mind, "invariant"):
        if not mind.invariant():
            raise RuntimeError(
                "MindState invariant failed"
            )

    return result
