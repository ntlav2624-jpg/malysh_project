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
from malysh_system.historical_swarm_omni import (
    integrate_historical_swarm_omni,
)
from malysh_system.historical_hive_cortex import (
    integrate_historical_hive_cortex,
)
from malysh_system.historical_topology import (
    integrate_historical_topology,
)
from malysh_system.kmbp import integrate_kmbp
from malysh_system.interlayer_observers import (
    integrate_interlayer_pass,
)
from malysh_system.joint_choice import (
    integrate_joint_choice,
)
from malysh_system.protocols import OrganResult
from malysh_system.swarm_omni import integrate_swarm_omni
from malysh_system.thought_cycle import observe_o345
from malysh_system.unified_mind import (
    MindState,
    merge_o345,
)


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
        o345_n: int | None = None,
        historical_history: Any = None,
        historical_candidate: Any = None,
        historical_pool_size: int = 49,
        topology_normal: Any = None,
        topology_observed: Any = None,
        hive_target: Any = None,
        hive_signal: Any = None,
    ) -> dict[str, Any]:
        """
        Execute a complete internal thinking cycle.

        KMBP is invoked through the existing FullReflections callable
        bridge. The callable publishes the verified KMBP computation
        into the shared MindState and returns the same computation to
        FullReflections as internal experience.

        No KMBP result is recomputed elsewhere in this cycle.
        """

        data_values = list(data)

        if not data_values:
            raise ValueError(
                "thinking-cycle input must not be empty"
            )

        canonical_before = deepcopy(
            self.mind.canonical
        )

        # O345 has its own established scalar input contract.
        #
        # We intentionally do NOT infer o345_n from data_values.
        # If no scalar state is supplied, O345 remains unexecuted
        # in this cycle rather than receiving an invented mapping.
        o345_result = None
        canonical_after_o345 = deepcopy(
            canonical_before
        )

        if o345_n is not None:
            o345_result = observe_o345(
                o345_n
            )

            if not o345_result.get(
                "invariant_ok"
            ):
                raise RuntimeError(
                    "O345 invariant failed"
                )

            merge_o345(
                self.mind,
                o345_result,
            )

            canonical_after_o345 = deepcopy(
                self.mind.canonical
            )

            if (
                canonical_after_o345
                !=
                o345_result["canonical"]
            ):
                raise RuntimeError(
                    "O345 canonical merge mismatch"
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
            data_values,
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
            "layers_seen": (
                (
                    [
                        "O345",
                        "O3",
                        "O4",
                        "O5",
                    ]
                    if o345_result is not None
                    else []
                )
                + [
                    "KMBP",
                    "FullReflections",
                    "HumanLayer",
                ]
            ),

            "o345_executed":
                o345_result is not None,

            "o345_invariant_ok":
                (
                    o345_result["invariant_ok"]
                    if o345_result is not None
                    else None
                ),

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

        # Swarm and Omni are provisional observational organs.
        # Both execute only after the existing thought context
        # has been formed.
        swarm_result, omni_result = integrate_swarm_omni(
            self.mind
        )

        cross_layer_observation[
            "layers_seen"
        ].extend(
            [
                "Swarm",
                "Omni",
            ]
        )

        cross_layer_observation[
            "swarm_invariant_ok"
        ] = swarm_result.data[
            "invariant_ok"
        ]

        cross_layer_observation[
            "omni_invariant_ok"
        ] = omni_result.data[
            "invariant_ok"
        ]

        # Refresh the stored cross-layer pattern so the observer's
        # final record includes Swarm and Omni visibility.
        self.mind.reflect(
            "KMBP_FULL_REFLECTIONS_PATTERN",
            cross_layer_observation,
        )

        # Historical Swarm/Omni heritage is optional.
        #
        # Historical Omni requires an explicit historical input
        # contract. The thinking cycle never invents history or
        # candidate values.
        historical_requested = (
            historical_history is not None
            or
            historical_candidate is not None
        )

        if (
            historical_history is None
            and
            historical_candidate is None
        ):
            historical_swarm_result = None
            historical_omni_result = None

        elif (
            historical_history is None
            or
            historical_candidate is None
        ):
            raise ValueError(
                "historical_history and historical_candidate "
                "must be supplied together"
            )

        else:
            historical_swarm_result, historical_omni_result = (
                integrate_historical_swarm_omni(
                    self.mind,
                    historical_history,
                    historical_candidate,
                    historical_pool_size,
                )
            )

            if (
                historical_swarm_result.status
                !=
                "ok"
            ):
                raise RuntimeError(
                    historical_swarm_result.error
                    or
                    "HistoricalSwarm failed"
                )

            if (
                historical_omni_result.status
                !=
                "ok"
            ):
                raise RuntimeError(
                    historical_omni_result.error
                    or
                    "HistoricalOmni failed"
                )

            if not (
                historical_swarm_result.data[
                    "invariant_ok"
                ]
                and
                historical_omni_result.data[
                    "invariant_ok"
                ]
            ):
                raise RuntimeError(
                    "historical heritage invariant failed"
                )

            cross_layer_observation[
                "layers_seen"
            ].extend(
                [
                    "HistoricalSwarm",
                    "HistoricalOmni",
                ]
            )

            self.mind.reflect(
                "KMBP_FULL_REFLECTIONS_PATTERN",
                cross_layer_observation,
            )

        # Historical topology is optional and requires an explicit,
        # complete two-state contract. No topology input is inferred
        # from O345 or from the ordinary numeric sequence.
        topology_requested = (
            topology_normal is not None
            or
            topology_observed is not None
        )

        if (
            topology_normal is None
            and
            topology_observed is None
        ):
            historical_topology_result = None

        elif (
            topology_normal is None
            or
            topology_observed is None
        ):
            raise ValueError(
                "topology_normal and topology_observed "
                "must be supplied together"
            )

        else:
            historical_topology_result = (
                integrate_historical_topology(
                    self.mind,
                    topology_normal,
                    topology_observed,
                )
            )

            if (
                historical_topology_result.status
                !=
                "ok"
            ):
                raise RuntimeError(
                    historical_topology_result.error
                    or
                    "HistoricalTopology failed"
                )

            if (
                historical_topology_result.data[
                    "invariant_ok"
                ]
                is not True
            ):
                raise RuntimeError(
                    "HistoricalTopology invariant failed"
                )

            cross_layer_observation[
                "layers_seen"
            ].append(
                "HistoricalTopology"
            )

            cross_layer_observation[
                "historical_topology_invariant_ok"
            ] = True

            self.mind.reflect(
                "KMBP_FULL_REFLECTIONS_PATTERN",
                cross_layer_observation,
            )

        # Historical Hive Cortex is optional and requires a complete
        # explicit input pair. No target or signal is inferred from
        # KMBP, Swarm, Omni, O345, topology or ordinary cycle input.
        hive_requested = (
            hive_target is not None
            or
            hive_signal is not None
        )

        if (
            hive_target is None
            and
            hive_signal is None
        ):
            historical_hive_cortex_result = None

        elif (
            hive_target is None
            or
            hive_signal is None
        ):
            raise ValueError(
                "hive_target and hive_signal "
                "must be supplied together"
            )

        else:
            historical_hive_cortex_result = (
                integrate_historical_hive_cortex(
                    self.mind,
                    hive_target,
                    hive_signal,
                )
            )

            if (
                historical_hive_cortex_result.status
                !=
                "ok"
            ):
                raise RuntimeError(
                    historical_hive_cortex_result.error
                    or
                    "HistoricalHiveCortex failed"
                )

            if (
                historical_hive_cortex_result.data[
                    "invariant_ok"
                ]
                is not True
            ):
                raise RuntimeError(
                    "HistoricalHiveCortex invariant failed"
                )

            cross_layer_observation[
                "layers_seen"
            ].append(
                "HistoricalHiveCortex"
            )

            cross_layer_observation[
                "historical_hive_cortex_invariant_ok"
            ] = True

            self.mind.reflect(
                "KMBP_FULL_REFLECTIONS_PATTERN",
                cross_layer_observation,
            )

        # Every active layer now observes the same frozen results
        # of all peer layers. Explicit historical organs are already
        # present in this immutable pre-InterLayer snapshot.
        interlayer_result = integrate_interlayer_pass(
            self.mind
        )

        # JointChoice structures a thought-level deliberation.
        # It cannot execute, commit, or overwrite either branch.
        joint_choice_result = integrate_joint_choice(
            self.mind,
            interlayer_result.data,
        )

        # O345 may establish canonical state when explicitly
        # supplied with its scalar input. Later organs must preserve it.
        if (
            self.mind.canonical
            !=
            canonical_after_o345
        ):
            raise RuntimeError(
                "an organ overwrote canonical state after O345"
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
                deepcopy(
                    data_values
                ),

            "o345_n":
                o345_n,

            "o345":
                deepcopy(
                    o345_result
                ),

            "kmbp":
                deepcopy(
                    kmbp_organ_result.to_dict()
                ),

            "swarm":
                deepcopy(
                    swarm_result.to_dict()
                ),

            "omni":
                deepcopy(
                    omni_result.to_dict()
                ),

            "historical_swarm":
                (
                    deepcopy(
                        historical_swarm_result.to_dict()
                    )
                    if historical_swarm_result is not None
                    else None
                ),

            "historical_omni":
                (
                    deepcopy(
                        historical_omni_result.to_dict()
                    )
                    if historical_omni_result is not None
                    else None
                ),

            "historical_topology":
                (
                    deepcopy(
                        historical_topology_result.to_dict()
                    )
                    if historical_topology_result
                    is not None
                    else None
                ),

            "historical_hive_cortex":
                (
                    deepcopy(
                        historical_hive_cortex_result.to_dict()
                    )
                    if historical_hive_cortex_result
                    is not None
                    else None
                ),

            "interlayer":
                deepcopy(
                    interlayer_result.to_dict()
                ),

            "joint_choice":
                deepcopy(
                    joint_choice_result.to_dict()
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

                "o345_contract_valid":
                    (
                        o345_result is None
                        or
                        (
                            o345_result[
                                "invariant_ok"
                            ]
                            is True
                        )
                    ),

                "o345_observers_present":
                    (
                        o345_result is None
                        or
                        all(
                            name
                            in
                            snapshot["observations"]
                            for name in (
                                "O3",
                                "O4",
                                "O5",
                            )
                        )
                    ),

                "o345_reflection_present":
                    (
                        o345_result is None
                        or
                        "O345"
                        in
                        snapshot["reflections"]
                    ),

                "canonical_transition_valid":
                    (
                        (
                            snapshot["canonical"]
                            ==
                            canonical_before
                        )
                        if o345_result is None
                        else
                        (
                            snapshot["canonical"]
                            ==
                            o345_result[
                                "canonical"
                            ]
                        )
                    ),

                "canonical_preserved_after_o345":
                    (
                        snapshot["canonical"]
                        ==
                        canonical_after_o345
                    ),

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

                "swarm_verified":
                    (
                        swarm_result.status
                        ==
                        "ok"
                        and
                        swarm_result.data[
                            "invariant_ok"
                        ]
                    ),

                "omni_verified":
                    (
                        omni_result.status
                        ==
                        "ok"
                        and
                        omni_result.data[
                            "invariant_ok"
                        ]
                    ),

                "swarm_observed":
                    (
                        "Swarm"
                        in
                        snapshot["observations"]
                    ),

                "omni_observed":
                    (
                        "Omni"
                        in
                        snapshot["observations"]
                    ),

                "swarm_omni_no_winner":
                    (
                        swarm_result.data[
                            "collective_state"
                        ][
                            "winner"
                        ]
                        is None
                        and
                        omni_result.data[
                            "context_state"
                        ][
                            "winner"
                        ]
                        is None
                    ),

                "swarm_omni_honest_provenance":
                    (
                        swarm_result.data[
                            "provenance"
                        ][
                            "historical_identity"
                        ]
                        ==
                        "named_unresolved"
                        and
                        omni_result.data[
                            "provenance"
                        ][
                            "historical_identity"
                        ]
                        ==
                        "named_unresolved"
                    ),

                "historical_contract_valid":
                    (
                        (
                            historical_history is None
                            and
                            historical_candidate is None
                            and
                            historical_swarm_result is None
                            and
                            historical_omni_result is None
                        )
                        or
                        (
                            historical_history is not None
                            and
                            historical_candidate is not None
                            and
                            historical_swarm_result is not None
                            and
                            historical_omni_result is not None
                        )
                    ),

                "historical_heritage_verified":
                    (
                        not historical_requested
                        or
                        (
                            historical_swarm_result is not None
                            and
                            historical_omni_result is not None
                            and
                            historical_swarm_result.status == "ok"
                            and
                            historical_omni_result.status == "ok"
                            and
                            historical_swarm_result.data[
                                "invariant_ok"
                            ]
                            is True
                            and
                            historical_omni_result.data[
                                "invariant_ok"
                            ]
                            is True
                        )
                    ),

                "historical_no_winner":
                    (
                        not historical_requested
                        or
                        historical_omni_result.data[
                            "winner"
                        ]
                        is None
                    ),

                "historical_no_mutation":
                    (
                        not historical_requested
                        or
                        (
                            historical_omni_result.data[
                                "randomness_used"
                            ]
                            is False
                            and
                            historical_omni_result.data[
                                "weight_mutation"
                            ]
                            is False
                            and
                            historical_omni_result.data[
                                "error_memory_mutation"
                            ]
                            is False
                        )
                    ),

                "historical_visible_to_interlayer":
                    (
                        not historical_requested
                        or
                        (
                            "HistoricalSwarm"
                            in
                            interlayer_result.data[
                                "frozen_layer_names"
                            ]
                            and
                            "HistoricalOmni"
                            in
                            interlayer_result.data[
                                "frozen_layer_names"
                            ]
                        )
                    ),

                "topology_contract_valid":
                    (
                        (
                            topology_normal is None
                            and
                            topology_observed is None
                            and
                            historical_topology_result
                            is None
                        )
                        or
                        (
                            topology_normal is not None
                            and
                            topology_observed is not None
                            and
                            historical_topology_result
                            is not None
                        )
                    ),

                "historical_topology_verified":
                    (
                        not topology_requested
                        or
                        (
                            historical_topology_result
                            is not None
                            and
                            historical_topology_result.status
                            ==
                            "ok"
                            and
                            historical_topology_result.data[
                                "invariant_ok"
                            ]
                            is True
                        )
                    ),

                "historical_topology_observed":
                    (
                        not topology_requested
                        or
                        "HistoricalTopology"
                        in
                        snapshot["observations"]
                    ),

                "historical_topology_reflected":
                    (
                        not topology_requested
                        or
                        "HistoricalTopology"
                        in
                        snapshot["reflections"]
                    ),

                "historical_topology_visible_to_interlayer":
                    (
                        not topology_requested
                        or
                        "HistoricalTopology"
                        in
                        interlayer_result.data[
                            "frozen_layer_names"
                        ]
                    ),

                "historical_topology_no_authority":
                    (
                        not topology_requested
                        or
                        (
                            historical_topology_result.data[
                                "decision_authority"
                            ]
                            is False
                            and
                            historical_topology_result.data[
                                "automatic_execution"
                            ]
                            is False
                            and
                            historical_topology_result.data[
                                "canonical_write"
                            ]
                            is False
                            and
                            historical_topology_result.data[
                                "state_commit"
                            ]
                            is False
                        )
                    ),

                "historical_topology_is_projection":
                    (
                        not topology_requested
                        or
                        self.mind.canonical
                        ==
                        canonical_after_o345
                    ),

                "hive_cortex_contract_valid":
                    (
                        (
                            hive_target is None
                            and
                            hive_signal is None
                            and
                            historical_hive_cortex_result
                            is None
                        )
                        or
                        (
                            hive_target is not None
                            and
                            hive_signal is not None
                            and
                            historical_hive_cortex_result
                            is not None
                        )
                    ),

                "historical_hive_cortex_verified":
                    (
                        not hive_requested
                        or
                        (
                            historical_hive_cortex_result
                            is not None
                            and
                            historical_hive_cortex_result.status
                            ==
                            "ok"
                            and
                            historical_hive_cortex_result.data[
                                "invariant_ok"
                            ]
                            is True
                        )
                    ),

                "historical_hive_cortex_observed":
                    (
                        not hive_requested
                        or
                        "HistoricalHiveCortex"
                        in
                        snapshot["observations"]
                    ),

                "historical_hive_cortex_reflected":
                    (
                        not hive_requested
                        or
                        "HistoricalHiveCortex"
                        in
                        snapshot["reflections"]
                    ),

                "historical_hive_cortex_visible_to_interlayer":
                    (
                        not hive_requested
                        or
                        "HistoricalHiveCortex"
                        in
                        interlayer_result.data[
                            "frozen_layer_names"
                        ]
                    ),

                "historical_hive_cortex_no_authority":
                    (
                        not hive_requested
                        or
                        (
                            historical_hive_cortex_result.data[
                                "decision_authority"
                            ]
                            is False
                            and
                            historical_hive_cortex_result.data[
                                "automatic_execution"
                            ]
                            is False
                            and
                            historical_hive_cortex_result.data[
                                "canonical_write"
                            ]
                            is False
                            and
                            historical_hive_cortex_result.data[
                                "state_commit"
                            ]
                            is False
                            and
                            historical_hive_cortex_result.data[
                                "transaction_authorized"
                            ]
                            is False
                            and
                            historical_hive_cortex_result.data[
                                "external_control"
                            ]
                            is False
                        )
                    ),

                "historical_hive_cortex_no_side_effects":
                    (
                        not hive_requested
                        or
                        (
                            historical_hive_cortex_result.data[
                                "filesystem_write"
                            ]
                            is False
                            and
                            historical_hive_cortex_result.data[
                                "log_append"
                            ]
                            is False
                            and
                            historical_hive_cortex_result.data[
                                "timestamp_generated"
                            ]
                            is False
                        )
                    ),

                "historical_hive_cortex_canonical_preserved":
                    (
                        not hive_requested
                        or
                        self.mind.canonical
                        ==
                        canonical_after_o345
                    ),

                "interlayer_verified":
                    (
                        interlayer_result.status
                        ==
                        "ok"
                        and
                        interlayer_result.data[
                            "invariant_ok"
                        ]
                    ),

                "interlayer_same_snapshot":
                    interlayer_result.data[
                        "same_snapshot_for_all"
                    ]
                    is True,

                "interlayer_results_separate":
                    interlayer_result.data[
                        "results_stored_separately"
                    ]
                    is True,

                "interlayer_no_winner":
                    interlayer_result.data[
                        "winner"
                    ]
                    is None,

                "interlayer_no_execution":
                    interlayer_result.data[
                        "affects_execution"
                    ]
                    is False,

                "interlayer_no_main_answer_change":
                    interlayer_result.data[
                        "affects_main_answer"
                    ]
                    is False,

                "joint_choice_verified":
                    (
                        joint_choice_result.status
                        ==
                        "ok"
                        and
                        joint_choice_result.data[
                            "invariant_ok"
                        ]
                    ),

                "joint_choice_main_preserved":
                    joint_choice_result.data[
                        "deliberation"
                    ][
                        "main_preserved"
                    ]
                    is True,

                "joint_choice_possible_preserved":
                    joint_choice_result.data[
                        "deliberation"
                    ][
                        "possible_preserved"
                    ]
                    is True,

                "joint_choice_no_voting":
                    (
                        joint_choice_result.data[
                            "deliberation"
                        ][
                            "majority_vote_used"
                        ]
                        is False
                        and
                        joint_choice_result.data[
                            "deliberation"
                        ][
                            "vote_count_used"
                        ]
                        is False
                    ),

                "joint_choice_no_winner":
                    joint_choice_result.data[
                        "deliberation"
                    ][
                        "winner"
                    ]
                    is None,

                "joint_choice_no_execution":
                    joint_choice_result.data[
                        "deliberation"
                    ][
                        "execution_authorized"
                    ]
                    is False,

                "joint_choice_no_transaction":
                    joint_choice_result.data[
                        "deliberation"
                    ][
                        "transaction_authorized"
                    ]
                    is False,

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
    o345_n: int | None = None,
    historical_history: Any = None,
    historical_candidate: Any = None,
    historical_pool_size: int = 49,
    topology_normal: Any = None,
    topology_observed: Any = None,
    hive_target: Any = None,
    hive_signal: Any = None,
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
        o345_n=o345_n,
        historical_history=historical_history,
        historical_candidate=historical_candidate,
        historical_pool_size=historical_pool_size,
        topology_normal=topology_normal,
        topology_observed=topology_observed,
        hive_target=hive_target,
        hive_signal=hive_signal,
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
