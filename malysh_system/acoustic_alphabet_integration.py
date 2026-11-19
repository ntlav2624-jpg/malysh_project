"""
Safe attachment of Acoustic Alphabet observations to a cycle result.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from malysh_system.acoustic_alphabet_observer import (
    observe as observe_acoustic_alphabet,
)
from malysh_system.kmbp_acoustic_alphabet import (
    observe_kmbp_acoustic_alphabet,
)


SCHEMA = "malysh.acoustic-alphabet-integration.v1"


def _read_kmbp_result(result: Mapping[str, Any]) -> Any:
    for key in (
        "kmbp",
        "KMBP",
    ):
        if key in result:
            return result[key]

    mind = result.get("mind")

    if isinstance(mind, Mapping):
        observations = mind.get("observations")

        if isinstance(observations, Mapping):
            return observations.get("KMBP")

    return None


def attach_acoustic_alphabet(
    cycle_result: Any,
    *,
    data: Iterable[int] | None = None,
    old_result: Any = None,
    unresolved: Any = None,
) -> dict[str, Any]:
    """
    Return an augmented copy.

    The original result is not mutated. Existing fields are preserved.
    """

    if not isinstance(cycle_result, Mapping):
        return {
            "original_result": cycle_result,
            "acoustic_alphabet_integration_error":
                "cycle_result_is_not_mapping",
        }

    augmented = deepcopy(dict(cycle_result))

    kmbp_result = _read_kmbp_result(augmented)

    layer = observe_acoustic_alphabet(
        data=data,
        old_result=old_result,
        unresolved=unresolved,
    )

    kmbp_bridge = observe_kmbp_acoustic_alphabet(
        data=data,
        old_result=old_result,
        unresolved=unresolved,
        kmbp_result=kmbp_result,
    )

    augmented["acoustic_alphabet"] = layer

    experience = augmented.setdefault(
        "experience",
        {},
    )

    if isinstance(experience, dict):
        experience[
            "KMBP_ACOUSTIC_ALPHABET"
        ] = kmbp_bridge

    mind = augmented.setdefault(
        "mind",
        {},
    )

    if isinstance(mind, dict):
        observations = mind.setdefault(
            "observations",
            {},
        )

        if isinstance(observations, dict):
            observations[
                "AcousticAlphabet"
            ] = layer

            observations[
                "KMBP_AcousticAlphabet"
            ] = kmbp_bridge

    invariants = augmented.setdefault(
        "invariants",
        {},
    )

    if isinstance(invariants, dict):
        invariants.update({
            "acoustic_alphabet_observer_present":
                True,
            "kmbp_acoustic_alphabet_bridge_present":
                True,
            "acoustic_alphabet_no_decision_authority":
                True,
            "acoustic_alphabet_no_main_answer_write":
                True,
            "acoustic_alphabet_no_possible_write":
                True,
            "acoustic_alphabet_no_winner_selection":
                True,
            "acoustic_alphabet_existing_logic_preserved":
                True,
        })

    augmented[
        "acoustic_alphabet_integration"
    ] = {
        "schema": SCHEMA,
        "status": "attached",
        "original_result_mutated": False,
        "decision_authority": False,
        "main_answer_write": False,
        "possible_branch_write": False,
        "winner_selection": False,
        "replace_existing_logic": False,
    }

    return augmented
