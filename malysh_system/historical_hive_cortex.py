"""
Read-only recovery of historical Malysh Hive Cortex logic.

Recovered source lineage:

    repository:
        ntlav2624-jpg/malysh

    file:
        malysh_hive_cortex.py

Historical computations preserved:

    CognitiveLimb.manipulate(target_data)
        -> "MANIPULATED_" + target_data.upper()

    ResonanceSpine.transmit(signal_strength)
        -> round(signal_strength * 3.1415, 4)

    HiveCortex pulse synthesis
        -> limb output
        -> spine resonance
        -> cortex status

Historical side effects disabled:

    writes to ~/malysh_hive_state.json
    appends to ~/malysh_eternal.log
    runtime timestamp generation
    terminal HUD
    external execution
    state commit
    canonical write

The historical label "master" is not interpreted as authority and is
not reproduced as an operational permission.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from malysh_system.protocols import OrganResult


ORGAN = "HistoricalHiveCortex"

SCHEMA = "malysh.historical-hive-cortex.v1"

HISTORICAL_PI_FACTOR = 3.1415

HISTORICAL_STATUS = "SYNAPSE_LOCKED"

HERITAGE = {
    "repository":
        "ntlav2624-jpg/malysh",

    "branch":
        "main",

    "file":
        "malysh_hive_cortex.py",

    "identity":
        "recovered_source",

    "adaptation":
        "pure_read_only",

    "historical_classes": [
        "CognitiveLimb",
        "ResonanceSpine",
        "HiveCortex",
    ],

    "authority_interpretation":
        "historical_labels_are_not_permissions",
}


def authority_flags() -> dict[str, bool]:
    """
    Explicitly deny operational authority to the recovered organ.
    """

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

        "main_answer_write":
            False,

        "possible_branch_write":
            False,

        "transaction_authorized":
            False,

        "winner_selection":
            False,

        "filesystem_write":
            False,

        "log_append":
            False,

        "timestamp_generated":
            False,

        "external_control":
            False,
    }


class CognitiveLimb:
    """
    Pure adaptation of historical CognitiveLimb.
    """

    def manipulate(
        self,
        target_data: str,
    ) -> str:
        if not isinstance(
            target_data,
            str,
        ):
            raise TypeError(
                "target_data must be str"
            )

        if not target_data:
            raise ValueError(
                "target_data must not be empty"
            )

        return (
            "MANIPULATED_"
            +
            target_data.upper()
        )


class ResonanceSpine:
    """
    Pure adaptation of historical ResonanceSpine.
    """

    def transmit(
        self,
        signal_strength: float,
    ) -> float:
        if isinstance(
            signal_strength,
            bool,
        ):
            raise TypeError(
                "signal_strength must be numeric"
            )

        if not isinstance(
            signal_strength,
            (
                int,
                float,
            ),
        ):
            raise TypeError(
                "signal_strength must be numeric"
            )

        numeric = float(
            signal_strength
        )

        if numeric < 0:
            raise ValueError(
                "signal_strength must be non-negative"
            )

        return round(
            numeric
            *
            HISTORICAL_PI_FACTOR,
            4,
        )


class HiveCortex:
    """
    Pure deterministic synthesis of recovered Hive Cortex components.
    """

    def __init__(
        self,
    ):
        self.limb = CognitiveLimb()
        self.spine = ResonanceSpine()

    def pulse(
        self,
        target_data: str,
        signal_strength: float,
    ) -> dict[str, Any]:
        limb_action = (
            self.limb.manipulate(
                target_data
            )
        )

        spine_resonance = (
            self.spine.transmit(
                signal_strength
            )
        )

        return {
            "limb_action":
                limb_action,

            "spine_resonance":
                spine_resonance,

            "cortex_status":
                HISTORICAL_STATUS,
        }


def compute_historical_hive_cortex(
    target_data: str,
    signal_strength: float,
    subject: str = "Malysh",
) -> dict[str, Any]:
    """
    Compute one historical Hive Cortex pulse without side effects.
    """

    if subject != "Malysh":
        raise ValueError(
            "HistoricalHiveCortex belongs to ONE Malysh"
        )

    input_record = {
        "target_data":
            deepcopy(target_data),

        "signal_strength":
            deepcopy(signal_strength),
    }

    cortex = HiveCortex()

    pulse = cortex.pulse(
        target_data,
        signal_strength,
    )

    expected_action = (
        "MANIPULATED_"
        +
        target_data.upper()
    )

    expected_resonance = round(
        float(signal_strength)
        *
        HISTORICAL_PI_FACTOR,
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

        "input":
            input_record,

        "limb": {
            "historical_class":
                "CognitiveLimb",

            "operation":
                "manipulate",

            "output":
                pulse["limb_action"],
        },

        "spine": {
            "historical_class":
                "ResonanceSpine",

            "operation":
                "transmit",

            "factor":
                HISTORICAL_PI_FACTOR,

            "output":
                pulse["spine_resonance"],
        },

        "cortex": {
            "historical_class":
                "HiveCortex",

            "status":
                pulse["cortex_status"],

            "pulse_complete":
                True,
        },

        "pulse":
            deepcopy(pulse),

        **authority_flags(),
    }

    result["invariants"] = {
        "one_subject":
            result["subject"]
            ==
            "Malysh",

        "recovered_source":
            (
                result["heritage"][
                    "identity"
                ]
                ==
                "recovered_source"
            ),

        "limb_formula":
            (
                result["limb"]["output"]
                ==
                expected_action
            ),

        "spine_formula":
            (
                result["spine"]["output"]
                ==
                expected_resonance
            ),

        "historical_factor":
            (
                result["spine"]["factor"]
                ==
                3.1415
            ),

        "historical_status":
            (
                result["cortex"]["status"]
                ==
                "SYNAPSE_LOCKED"
            ),

        "pulse_complete":
            (
                result["cortex"][
                    "pulse_complete"
                ]
                is True
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
            (
                result["state_write"]
                is False
            ),

        "no_state_commit":
            (
                result["state_commit"]
                is False
            ),

        "no_canonical_write":
            (
                result["canonical_write"]
                is False
            ),

        "no_main_write":
            (
                result["main_answer_write"]
                is False
            ),

        "no_possible_write":
            (
                result[
                    "possible_branch_write"
                ]
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
            (
                result["log_append"]
                is False
            ),

        "no_timestamp_generation":
            (
                result[
                    "timestamp_generated"
                ]
                is False
            ),

        "no_external_control":
            (
                result["external_control"]
                is False
            ),
    }

    result["invariant_ok"] = all(
        result["invariants"].values()
    )

    return result


def run_historical_hive_cortex(
    target_data: str,
    signal_strength: float,
    subject: str = "Malysh",
) -> OrganResult:
    """
    Execute the recovered organ and return OrganResult.
    """

    try:
        result = (
            compute_historical_hive_cortex(
                target_data,
                signal_strength,
                subject,
            )
        )

        if not result["invariant_ok"]:
            return OrganResult(
                organ=ORGAN,
                status="error",
                data=result,
                error=(
                    "HistoricalHiveCortex "
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


def integrate_historical_hive_cortex(
    mind: Any,
    target_data: str,
    signal_strength: float,
) -> OrganResult:
    """
    Publish Hive Cortex as an internal observation and reflection.

    Existing canonical, Human Layer, main, possible and experience
    state must remain unchanged.
    """

    for method in (
        "snapshot",
        "observe",
        "reflect",
    ):
        if not hasattr(
            mind,
            method,
        ):
            raise TypeError(
                "mind must provide "
                + method
                + "()"
            )

    before = mind.snapshot()

    protected = {
        key: deepcopy(
            before[key]
        )
        for key in (
            "subject",
            "canonical",
            "experience",
            "human",
            "main",
            "possible",
        )
    }

    result = (
        run_historical_hive_cortex(
            target_data,
            signal_strength,
            subject=before["subject"],
        )
    )

    if result.status != "ok":
        raise RuntimeError(
            result.error
            or
            "HistoricalHiveCortex failed"
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

            "limb":
                deepcopy(
                    result.data["limb"]
                ),

            "spine":
                deepcopy(
                    result.data["spine"]
                ),

            "cortex":
                deepcopy(
                    result.data["cortex"]
                ),

            "invariant_ok":
                result.data[
                    "invariant_ok"
                ],

            **authority_flags(),
        },
    )

    after = mind.snapshot()

    for key, expected in (
        protected.items()
    ):
        if after[key] != expected:
            raise RuntimeError(
                "HistoricalHiveCortex mutated "
                "protected field: "
                + key
            )

    if hasattr(
        mind,
        "invariant",
    ):
        if not mind.invariant():
            raise RuntimeError(
                "MindState invariant failed"
            )

    return result
