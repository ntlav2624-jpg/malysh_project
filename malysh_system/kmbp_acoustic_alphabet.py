"""
KMBP bridge for the Acoustic Alphabet observer.

The bridge makes Acoustic Alphabet experience visible from KMBP
without changing KMBP's existing computation, decision authority,
or historical semantics.
"""

from __future__ import annotations

from typing import Any, Iterable

from malysh_system.acoustic_alphabet_observer import (
    SCHEMA as ALPHABET_SCHEMA,
    observe as observe_acoustic_alphabet,
)


SCHEMA = "malysh.kmbp-acoustic-alphabet-bridge.v1"
BRIDGE_NAME = "KMBP_ACOUSTIC_ALPHABET"


def observe_kmbp_acoustic_alphabet(
    *,
    data: Iterable[int] | None = None,
    old_result: Any = None,
    unresolved: Any = None,
    kmbp_result: Any = None,
) -> dict[str, Any]:
    """
    Attach a read-only Acoustic Alphabet observation to KMBP.

    Existing KMBP output is referenced but never rewritten.
    """

    alphabet = observe_acoustic_alphabet(
        data=data,
        old_result=old_result,
        unresolved=unresolved,
    )

    return {
        "organ": BRIDGE_NAME,
        "schema": SCHEMA,
        "alphabet_schema": ALPHABET_SCHEMA,
        "status": "observed",
        "role": (
            "Read-only KMBP experience bridge. "
            "No replacement of existing KMBP logic."
        ),
        "kmbp_result_present":
            kmbp_result is not None,
        "alphabet_observation":
            alphabet,
        "invariants": {
            "kmbp_result_unchanged": True,
            "existing_kmbp_logic_preserved": True,
            "legacy_experience_preserved": True,
            "decision_authority": False,
            "main_answer_write": False,
            "possible_branch_write": False,
            "winner_selection": False,
            "execution_authority": False,
            "transaction_authority": False,
        },
        "decision_authority": False,
        "main_answer_write": False,
        "possible_branch_write": False,
        "winner_selection": False,
        "affects_main_answer": False,
        "revisable": True,
    }
