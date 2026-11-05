"""
Operational lifecycle of ONE Malysh.

Lifecycle:

    recover previous MindState if a checkpoint exists
        -> execute one complete thinking cycle
        -> verify all cycle invariants
        -> persist the resulting complete MindState
        -> recover it across a simulated restart boundary
        -> prove exact snapshot equality

The lifecycle does not authorize external execution, voting,
transaction commit or canonical overwrite.

Historical Swarm/Omni receive data only through the explicit
historical input contract of run_thinking_cycle().
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

from malysh_system.mind_persistence import (
    MindPersistence,
)
from malysh_system.thinking_cycle import (
    run_thinking_cycle,
)
from malysh_system.unified_mind import (
    MindState,
)


LIFECYCLE_SCHEMA = "malysh.operational-lifecycle.v1"


def _protected_snapshot(
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    """
    Return fields that establish continuity of one subject.
    """

    return {
        key: deepcopy(snapshot[key])
        for key in (
            "subject",
            "canonical",
            "experience",
            "human",
            "main",
            "possible",
        )
    }


class OperationalLifecycle:
    """
    Durable thinking lifecycle for ONE Malysh.
    """

    def __init__(
        self,
        storage: str | Path,
    ):
        self.storage = Path(storage)
        self.persistence = MindPersistence(
            self.storage
        )

    def recover_or_initialize(
        self,
    ) -> tuple[
        MindState,
        dict[str, Any],
    ]:
        """
        Recover the last committed state or initialize generation zero.
        """

        inspection = self.persistence.inspect()

        if inspection["recoverable"]:
            mind, metadata = (
                self.persistence.recover()
            )

            return (
                mind,
                {
                    "mode":
                        "recovered",

                    "previous_generation":
                        metadata["generation"],

                    "previous_snapshot_hash":
                        metadata["snapshot_hash"],

                    "checkpoint":
                        metadata["checkpoint"],

                    "recovery_invariant_ok":
                        metadata["invariant_ok"],

                    "snapshot_equal":
                        metadata["snapshot_equal"],
                },
            )

        mind = MindState()

        if not mind.invariant():
            raise RuntimeError(
                "new MindState invariant failed"
            )

        return (
            mind,
            {
                "mode":
                    "initialized",

                "previous_generation":
                    0,

                "previous_snapshot_hash":
                    None,

                "checkpoint":
                    None,

                "recovery_invariant_ok":
                    True,

                "snapshot_equal":
                    True,
            },
        )

    def step(
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
        source: str = "operational-lifecycle",
    ) -> dict[str, Any]:
        """
        Recover S(t-1), compute S(t), commit it and verify recovery.
        """

        mind, start = self.recover_or_initialize()

        before_cycle = mind.snapshot()
        protected_before = _protected_snapshot(
            before_cycle
        )

        cycle = run_thinking_cycle(
            data=data,
            old_result=old_result,
            unresolved=unresolved,
            o345_n=o345_n,
            mind=mind,
            historical_history=historical_history,
            historical_candidate=historical_candidate,
            historical_pool_size=historical_pool_size,
            topology_normal=topology_normal,
            topology_observed=topology_observed,
            hive_target=hive_target,
            hive_signal=hive_signal,
        )

        failed_cycle_invariants = [
            name
            for name, passed
            in cycle["invariants"].items()
            if passed is not True
        ]

        if failed_cycle_invariants:
            raise RuntimeError(
                "thinking-cycle invariants failed: "
                + ", ".join(
                    failed_cycle_invariants
                )
            )

        if not mind.invariant():
            raise RuntimeError(
                "MindState invariant failed after thought"
            )

        after_cycle = mind.snapshot()

        if (
            start["mode"] == "recovered"
            and
            after_cycle["subject"]
            !=
            protected_before["subject"]
        ):
            raise RuntimeError(
                "subject continuity failed"
            )

        if (
            before_cycle["canonical"]
            and
            after_cycle["canonical"]
            !=
            before_cycle["canonical"]
        ):
            raise RuntimeError(
                "existing canonical state was overwritten"
            )

        commit = self.persistence.persist(
            mind,
            source=source,
        )

        expected_generation = (
            int(
                start["previous_generation"]
            )
            + 1
        )

        if (
            commit["generation"]
            !=
            expected_generation
        ):
            raise RuntimeError(
                "generation continuity failed"
            )

        recovered, recovery = (
            self.persistence.recover()
        )

        recovered_snapshot = (
            recovered.snapshot()
        )

        snapshot_equal = (
            recovered_snapshot
            ==
            after_cycle
        )

        hash_equal = (
            recovery["snapshot_hash"]
            ==
            commit["snapshot_hash"]
        )

        previous_hash_linked = (
            commit[
                "previous_snapshot_hash"
            ]
            ==
            start[
                "previous_snapshot_hash"
            ]
        )

        historical_requested = (
            historical_history is not None
            or
            historical_candidate is not None
        )

        topology_requested = (
            topology_normal is not None
            or
            topology_observed is not None
        )

        hive_requested = (
            hive_target is not None
            or
            hive_signal is not None
        )

        historical_visible = (
            not historical_requested
            or
            (
                "HistoricalSwarm"
                in
                after_cycle["observations"]
                and
                "HistoricalOmni"
                in
                after_cycle["observations"]
            )
        )

        frozen_layers = set(
            cycle["interlayer"][
                "data"
            ][
                "frozen_layer_names"
            ]
        )

        historical_visible_to_interlayer = (
            not historical_requested
            or
            {
                "HistoricalSwarm",
                "HistoricalOmni",
            }.issubset(frozen_layers)
        )

        topology_visible = (
            not topology_requested
            or
            "HistoricalTopology"
            in
            after_cycle["observations"]
        )

        topology_visible_to_interlayer = (
            not topology_requested
            or
            "HistoricalTopology"
            in
            frozen_layers
        )

        topology_survived_recovery = (
            not topology_requested
            or
            (
                "HistoricalTopology"
                in
                recovered_snapshot[
                    "observations"
                ]
                and
                recovered_snapshot[
                    "observations"
                ][
                    "HistoricalTopology"
                ]
                ==
                after_cycle[
                    "observations"
                ][
                    "HistoricalTopology"
                ]
            )
        )

        hive_visible = (
            not hive_requested
            or
            "HistoricalHiveCortex"
            in
            after_cycle["observations"]
        )

        hive_visible_to_interlayer = (
            not hive_requested
            or
            "HistoricalHiveCortex"
            in
            frozen_layers
        )

        hive_survived_recovery = (
            not hive_requested
            or
            (
                "HistoricalHiveCortex"
                in
                recovered_snapshot[
                    "observations"
                ]
                and
                recovered_snapshot[
                    "observations"
                ][
                    "HistoricalHiveCortex"
                ]
                ==
                after_cycle[
                    "observations"
                ][
                    "HistoricalHiveCortex"
                ]
            )
        )

        invariants = {
            "one_subject":
                recovered.subject == "Malysh",

            "start_state_valid":
                start[
                    "recovery_invariant_ok"
                ]
                is True,

            "cycle_verified":
                not failed_cycle_invariants,

            "mind_verified":
                recovered.invariant(),

            "generation_continuity":
                (
                    commit["generation"]
                    ==
                    expected_generation
                ),

            "previous_hash_linked":
                previous_hash_linked,

            "commit_recovery_hash_equal":
                hash_equal,

            "exact_snapshot_recovery":
                snapshot_equal,

            "historical_visibility":
                historical_visible,

            "historical_interlayer_visibility":
                historical_visible_to_interlayer,

            "topology_visibility":
                topology_visible,

            "topology_interlayer_visibility":
                topology_visible_to_interlayer,

            "topology_survived_recovery":
                topology_survived_recovery,

            "topology_did_not_replace_canonical":
                (
                    not topology_requested
                    or
                    recovered_snapshot[
                        "canonical"
                    ]
                    ==
                    after_cycle["canonical"]
                ),

            "hive_cortex_visibility":
                hive_visible,

            "hive_cortex_interlayer_visibility":
                hive_visible_to_interlayer,

            "hive_cortex_survived_recovery":
                hive_survived_recovery,

            "hive_cortex_canonical_preserved":
                (
                    not hive_requested
                    or
                    recovered_snapshot[
                        "canonical"
                    ]
                    ==
                    after_cycle["canonical"]
                ),

            "hive_cortex_no_authority":
                (
                    not hive_requested
                    or
                    (
                        cycle[
                            "historical_hive_cortex"
                        ][
                            "data"
                        ][
                            "decision_authority"
                        ]
                        is False
                        and
                        cycle[
                            "historical_hive_cortex"
                        ][
                            "data"
                        ][
                            "canonical_write"
                        ]
                        is False
                        and
                        cycle[
                            "historical_hive_cortex"
                        ][
                            "data"
                        ][
                            "state_commit"
                        ]
                        is False
                    )
                ),

            "joint_choice_no_winner":
                (
                    cycle["joint_choice"][
                        "data"
                    ][
                        "deliberation"
                    ][
                        "winner"
                    ]
                    is None
                ),

            "execution_not_authorized":
                (
                    cycle["joint_choice"][
                        "data"
                    ][
                        "deliberation"
                    ][
                        "execution_authorized"
                    ]
                    is False
                ),

            "transaction_not_authorized":
                (
                    cycle["joint_choice"][
                        "data"
                    ][
                        "deliberation"
                    ][
                        "transaction_authorized"
                    ]
                    is False
                ),
        }

        failed = [
            name
            for name, passed
            in invariants.items()
            if passed is not True
        ]

        if failed:
            raise RuntimeError(
                "operational lifecycle invariants failed: "
                + ", ".join(failed)
            )

        return {
            "schema":
                LIFECYCLE_SCHEMA,

            "subject":
                recovered.subject,

            "start":
                start,

            "generation":
                commit["generation"],

            "previous_snapshot_hash":
                commit[
                    "previous_snapshot_hash"
                ],

            "snapshot_hash":
                commit["snapshot_hash"],

            "checkpoint":
                commit["checkpoint"],

            "cycle":
                cycle,

            "snapshot":
                recovered_snapshot,

            "snapshot_equal":
                snapshot_equal,

            "hash_equal":
                hash_equal,

            "historical_requested":
                historical_requested,

            "topology_requested":
                topology_requested,

            "historical_topology":
                (
                    deepcopy(
                        cycle[
                            "historical_topology"
                        ]
                    )
                    if topology_requested
                    else None
                ),

            "hive_cortex_requested":
                hive_requested,

            "historical_hive_cortex":
                (
                    deepcopy(
                        cycle[
                            "historical_hive_cortex"
                        ]
                    )
                    if hive_requested
                    else None
                ),

            "frozen_layer_names":
                sorted(frozen_layers),

            "invariants":
                invariants,
        }
