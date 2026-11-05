from __future__ import annotations

import importlib.util
import sys

from copy import deepcopy
from pathlib import Path
from typing import Any

from malysh_system.unified_mind import (
    MindState,
    merge_o345,
)

from malysh_system.human_layer import (
    build_human_thought,
)

from malysh_system.cross_layer_observer import (
    observe_cross_layers,
)

from malysh_system.legacy_567_adapter import (
    observe_567,
)


ROOT = Path(__file__).resolve().parent.parent

O345_PATH = (
    ROOT
    / "experimental"
    / "o345"
    / "o345.py"
)


def load_o345_module():
    """
    Load existing O345 implementation without moving
    or rewriting the experimental implementation.
    """

    name = "malysh_experimental_o345"

    spec = importlib.util.spec_from_file_location(
        name,
        O345_PATH,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Cannot load O345 from {O345_PATH}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    # Needed for dataclass/module resolution when a module
    # is loaded programmatically.
    sys.modules[name] = module

    spec.loader.exec_module(
        module
    )

    return module


def observe_o345(
    n: int,
) -> dict[str, Any]:
    """
    Run O345 as an internal observer.

    No decision authority.
    No executor.
    """

    module = load_o345_module()

    state = module.Canonical345.from_n(
        int(n)
    )

    result = module.meta_observe(
        state
    )

    if not result.get(
        "invariant_ok",
        False,
    ):
        raise RuntimeError(
            "O345 invariant failed"
        )

    return result


def build_thought_cycle(
    n: int,
    text: str = "",
    consciousness: dict[str, Any] | None = None,
    subconscious: dict[str, Any] | None = None,
    joint: dict[str, Any] | None = None,
    experience: dict[str, Any] | None = None,
    observations: list[dict[str, Any]] | None = None,
    legacy_567_input: list[str] | None = None,
) -> MindState:
    """
    One passive thought cycle of ONE Malysh.

    Flow:

        canonical state
             |
            O345
             |
        O3 / O4 / O5
             |
         MindState
             |
        Human Layer
             |
        Cross-Layer

    No executor is called here.
    No transaction is committed here.
    """

    conscious = deepcopy(
        consciousness
        or {
            "selected": [],
        }
    )

    subconscious_state = deepcopy(
        subconscious
        or {
            "selected": [],
            "categories": [],
            "broad_fallback": False,
        }
    )

    joint_state = deepcopy(
        joint
        or {
            "selected": [],
        }
    )

    experience_state = deepcopy(
        experience
        or {
            "signals": [],
            "unresolved": [],
        }
    )

    external_observations = deepcopy(
        observations
        or []
    )

    # --------------------------------------------------------
    # ONE subject
    # --------------------------------------------------------

    mind = MindState()

    if mind.subject != "Malysh":
        raise RuntimeError(
            "Unified subject invariant failed"
        )

    # --------------------------------------------------------
    # O345
    # --------------------------------------------------------

    o345_result = observe_o345(
        n
    )

    merge_o345(
        mind,
        o345_result,
    )

    legacy_567_result = None

    if legacy_567_input is not None:
        legacy_567_result = observe_567(
            legacy_567_input
        )

        mind.reflect(
            "567",
            legacy_567_result,
        )

    # Publish O3/O4/O5 to the common observation interface.

    o345_observations = []

    for observer_name, value in (
        mind.observations.items()
    ):
        record = deepcopy(
            value
        )

        record[
            "observer"
        ] = observer_name

        record[
            "source"
        ] = "O345"

        record[
            "decision_authority"
        ] = False

        o345_observations.append(
            record
        )

    combined_observations = (
        external_observations
        + o345_observations
    )

    if legacy_567_result is not None:
        combined_observations.append(
            {
                "observer": "567",
                "source": "legacy_567",
                "result": deepcopy(
                    legacy_567_result
                ),
                "decision_authority": False,
            }
        )

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    mind.remember(
        "current_cycle",
        experience_state,
    )

    # --------------------------------------------------------
    # Human Layer
    # --------------------------------------------------------

    human = build_human_thought(
        text=text,
        conscious=conscious,
        subconscious=subconscious_state,
        joint=joint_state,
        observations=combined_observations,
        experience=experience_state,
    )

    human_dict = human.to_dict()

    mind.set_human(
        human_dict
    )

    # --------------------------------------------------------
    # Cross-Layer Observer
    # --------------------------------------------------------

    before = mind.snapshot()

    cross = observe_cross_layers(
        consciousness=conscious,
        subconscious=subconscious_state,
        joint=joint_state,
        experience=experience_state,
        human=human_dict,
        observations=combined_observations,
    ).to_dict()

    # Cross-Layer is strictly observational.

    for key in (
        "decision_authority",
        "automatic_execution",
        "state_write",
        "state_commit",
    ):
        if cross.get(key) is not False:
            raise RuntimeError(
                "Cross-Layer authority violation: "
                + key
            )

    mind.reflect(
        "cross_layer",
        cross,
    )

    after = mind.snapshot()

    # Cross-Layer may add its own reflection,
    # but cannot modify already formed thought.

    for key in (
        "subject",
        "canonical",
        "observations",
        "experience",
        "human",
        "main",
        "possible",
    ):
        if (
            before.get(key)
            != after.get(key)
        ):
            raise RuntimeError(
                "Cross-Layer mutated existing thought: "
                + key
            )

    if not mind.invariant():
        raise RuntimeError(
            "ONE MALYSH invariant failed"
        )

    return mind


def thought_snapshot(
    mind: MindState,
) -> dict[str, Any]:
    """
    Materialize one finished thought cycle.
    """

    snapshot = mind.snapshot()

    snapshot[
        "architecture"
    ] = {
        "subject_count": 1,
        "subject": "Malysh",

        "observer_count": len(
            snapshot.get(
                "observations",
                {},
            )
        ),

        "executor_called": False,

        "transaction_committed": False,
    }

    return snapshot
