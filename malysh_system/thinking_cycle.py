"""
Integrated thinking cycle of ONE Malysh.

The cycle connects:

    real numeric input
        -> working KMBP
        -> shared MindState
        -> FullReflections
        -> Human Layer observation
        -> cross-layer reflection
        -> isolated snapshot

Important invariants:

* KMBP is an internal organ, not an independent subject.
* FullReflections is an internal organ, not an independent subject.
* Human Layer remains a parallel thought context.
* No observer receives direct execution authority.
* KMBP cannot write or commit canonical state.
* Existing legacy-hook compatibility remains callable.
* The working KMBP calculation executes exactly once per cycle.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

from malysh_system.full_reflections import FullReflections
from malysh_system.kmbp import integrate_kmbp
from malysh_system.protocols import OrganResult
from malysh_system.unified_mind import MindState


class MalyshThinkingCycle:
    """
    One deterministic integration cycle of ONE Malysh.

    This class coordinates organs. It does not create another subject
    and does not grant decision authority to any observer.
    """

    def __init__(
        self,
        root: str | Path | None = None,
        mind: MindState | None = None,
    ):
        self.root = (
            Path(root)
            if root is not None
            else (
                Path(__file__)
                .resolve()
                .parent
                .parent
            )
        )

        self.mind = (
            mind
            if mind is not None
            else MindState()
        )

        if not self.mind.invariant():
            raise ValueError(
                "MindState invariant failed before cycle"
            )

    def run(
        self,
        data: Iterable[int],
        old_result: Any,
        unresolved: Any = None,
    ) -> dict[str, Any]:
        """
        Execute a complete internal thinking cycle.

        KMBP is invoked through the existing FullReflections callable
        bridge. The callable publishes the verified KMBP computation
        into the shared MindState and returns the same computation to
        FullReflections as internal experience.

        No KMBP result is recomputed elsewhere in this cycle.
        """

        canonical_before = deepcopy(
            self.mind.canonical
        )

        kmbp_call_count = 0
        kmbp_organ_result: OrganResult | None = None

        def working_kmbp_bridge(
            bridge_data: Iterable[int],
        ) -> dict[str, Any]:
            nonlocal kmbp_call_count
            nonlocal kmbp_organ_result

            kmbp_call_count += 1

            if kmbp_call_count != 1:
                raise RuntimeError(
                    "working KMBP executed more than once "
                    "inside one thinking cycle"
                )

            kmbp_organ_result = integrate_kmbp(
                self.mind,
                bridge_data,
            )

            if kmbp_organ_result.status != "ok":
                raise RuntimeError(
                    kmbp_organ_result.error
                    or
                    "working KMBP failed"
                )

            if not kmbp_organ_result.data.get(
                "invariant_ok"
            ):
                raise RuntimeError(
                    "working KMBP invariant failed"
                )

            return {
                "source":
                    "working_kmbp",

                "organ":
                    kmbp_organ_result.organ,

                "status":
                    kmbp_organ_result.status,

                "data":
                    deepcopy(
                        kmbp_organ_result.data
                    ),

                "error":
                    kmbp_organ_result.error,

                "canonical_claim":
                    False,

                "decision_authority":
                    False,

                "state_write":
                    False,

                "state_commit":
                    False,
            }

        reflections = FullReflections(
            root=self.root,
            legacy_hook=working_kmbp_bridge,
        )

        reflection_result = reflections.think(
            data,
            old_result,
            unresolved,
        )

        if kmbp_call_count != 1:
            raise RuntimeError(
                "working KMBP was not executed exactly once"
            )

        if kmbp_organ_result is None:
            raise RuntimeError(
                "working KMBP produced no OrganResult"
            )

        if kmbp_organ_result.status != "ok":
            raise RuntimeError(
                kmbp_organ_result.error
                or
                "working KMBP status is not ok"
            )

        # FullReflections remains an observation of the same subject.
        self.mind.observe(
            "FullReflections",
            reflection_result,
        )

        # Human Layer remains separately visible to other layers.
        human_layer = deepcopy(
            reflection_result.get(
                "human_layer",
                {},
            )
        )

        self.mind.observe(
            "HumanLayer",
            human_layer,
        )

        # Historical access mechanism is preserved as experience.
        # It is not confused with the working KMBP computation itself.
        self.mind.remember(
            "KMBP_LEGACY_BRIDGE",
            {
                "callable_preserved":
                    True,

                "working_organ":
                    "KMBP",

                "working_result_verified":
                    True,

                "canonical_heritage":
                    "unresolved",

                "decision_authority":
                    False,
            },
        )

        # Cross-layer comparison is stored separately.
        # It cannot directly modify execution.
        cross_layer_observation = {
            "layers_seen": [
                "KMBP",
                "FullReflections",
                "HumanLayer",
            ],

            "kmbp_invariant_ok":
                kmbp_organ_result.data[
                    "invariant_ok"
                ],

            "reflection_schema":
                reflection_result.get(
                    "schema"
                ),

            "debate_state":
                reflection_result.get(
                    "debate",
                    {},
                ).get(
                    "state"
                ),

            "human_layer_present":
                bool(human_layer),

            "observer_outputs_separate":
                True,

            "observer_changes_execution":
                False,

            "decision_authority":
                False,

            "state_write":
                False,

            "state_commit":
                False,
        }

        self.mind.reflect(
            "KMBP_FULL_REFLECTIONS_PATTERN",
            cross_layer_observation,
        )

        # The cycle must not allow KMBP or reflections to overwrite
        # the canonical state.
        if self.mind.canonical != canonical_before:
            raise RuntimeError(
                "thinking cycle modified canonical state"
            )

        if not self.mind.invariant():
            raise RuntimeError(
                "MindState invariant failed after cycle"
            )

        snapshot = self.mind.snapshot()

        return {
            "schema":
                "malysh.thinking-cycle.v1",

            "subject":
                snapshot["subject"],

            "input":
                list(data),

            "kmbp":
                deepcopy(
                    kmbp_organ_result.to_dict()
                ),

            "reflections":
                deepcopy(
                    reflection_result
                ),

            "human_layer":
                human_layer,

            "cross_layer":
                deepcopy(
                    cross_layer_observation
                ),

            "mind":
                snapshot,

            "invariants": {
                "one_subject":
                    snapshot["subject"]
                    ==
                    "Malysh",

                "mind_invariant":
                    self.mind.invariant(),

                "kmbp_called_once":
                    kmbp_call_count
                    ==
                    1,

                "kmbp_verified":
                    (
                        kmbp_organ_result.status
                        ==
                        "ok"
                        and
                        kmbp_organ_result.data[
                            "invariant_ok"
                        ]
                    ),

                "kmbp_observed":
                    "KMBP"
                    in
                    snapshot["observations"],

                "reflections_observed":
                    "FullReflections"
                    in
                    snapshot["observations"],

                "human_layer_observed":
                    "HumanLayer"
                    in
                    snapshot["observations"],

                "cross_layer_separate":
                    (
                        "KMBP_FULL_REFLECTIONS_PATTERN"
                        in
                        snapshot["reflections"]
                    ),

                "canonical_unchanged":
                    snapshot["canonical"]
                    ==
                    canonical_before,

                "no_decision_authority":
                    (
                        kmbp_organ_result.data[
                            "decision_authority"
                        ]
                        is False
                        and
                        cross_layer_observation[
                            "decision_authority"
                        ]
                        is False
                    ),

                "no_state_commit":
                    (
                        kmbp_organ_result.data[
                            "state_commit"
                        ]
                        is False
                        and
                        cross_layer_observation[
                            "state_commit"
                        ]
                        is False
                    ),

                "v1_reflection_contract":
                    all(
                        key in reflection_result
                        for key in (
                            "as_before",
                            "as_now",
                            "joint_choice",
                        )
                    ),

                "v2_reflection_contract":
                    all(
                        key in reflection_result
                        for key in (
                            "voice_a",
                            "voice_b",
                            "debate",
                            "human_layer",
                            "execution_gate",
                            "compatibility",
                        )
                    ),
            },
        }


def run_thinking_cycle(
    data: Iterable[int],
    old_result: Any,
    unresolved: Any = None,
    root: str | Path | None = None,
    mind: MindState | None = None,
) -> dict[str, Any]:
    """
    Convenience entry point for one integrated thinking cycle.
    """

    cycle = MalyshThinkingCycle(
        root=root,
        mind=mind,
    )

    result = cycle.run(
        data=data,
        old_result=old_result,
        unresolved=unresolved,
    )

    if not all(
        result["invariants"].values()
    ):
        failed = [
            name
            for name, passed
            in result["invariants"].items()
            if not passed
        ]

        raise RuntimeError(
            "thinking-cycle invariants failed: "
            + ", ".join(failed)
        )

    return result
