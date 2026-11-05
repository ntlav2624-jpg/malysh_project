"""
Independent inter-layer observation pass for ONE Malysh.

Every configured layer examines the same frozen MindState snapshot.
Each layer receives the results of the other layers and writes its own
reflection separately.

Important:

* Observer results do not feed other observers in the same pass.
* No observer changes canonical state.
* No observer changes Human Layer.
* No observer changes the main or possible branch.
* No observer selects a winner.
* No observer executes or commits a transaction.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from malysh_system.protocols import OrganResult


ORGAN = "InterLayerObservers"

DEFAULT_LAYERS = (
    "O3",
    "O4",
    "O5",
    "O345",
    "KMBP",
    "FullReflections",
    "HumanLayer",
    "Swarm",
    "Omni",
)


def _authority_flags() -> dict[str, bool]:
    return {
        "decision_authority": False,
        "automatic_execution": False,
        "state_write": False,
        "state_commit": False,
        "canonical_write": False,
        "main_answer_write": False,
        "possible_branch_write": False,
    }


def _shape(value: Any) -> dict[str, Any]:
    """
    Return deterministic structural metadata.

    This intentionally avoids assigning new semantic meaning to
    another organ's result.
    """

    if value is None:
        return {
            "type": "none",
            "size": 0,
            "keys": [],
        }

    if isinstance(value, Mapping):
        keys = sorted(
            str(key)
            for key in value
        )

        return {
            "type": "mapping",
            "size": len(value),
            "keys": keys,
        }

    if isinstance(value, (list, tuple)):
        return {
            "type": type(value).__name__,
            "size": len(value),
            "keys": [],
        }

    return {
        "type": type(value).__name__,
        "size": 1,
        "keys": [],
    }


def collect_layer_outputs(
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Resolve each layer from observations or reflections.

    Observation is used as the primary published result.
    Reflection is retained as a parallel view where available.
    """

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

    outputs = {}

    for layer in DEFAULT_LAYERS:
        observation = observations.get(
            layer
        )

        reflection = reflections.get(
            layer
        )

        if (
            observation is None
            and
            reflection is None
        ):
            continue

        outputs[layer] = {
            "observation":
                observation,

            "reflection":
                reflection,

            "observation_present":
                observation is not None,

            "reflection_present":
                reflection is not None,
        }

    return outputs


def observe_from_layer(
    layer: str,
    frozen_outputs: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Form one layer's independent view of all peer layers.
    """

    peers = {}

    for peer_name, peer_value in sorted(
        frozen_outputs.items()
    ):
        if peer_name == layer:
            continue

        peers[peer_name] = {
            "observation_shape":
                _shape(
                    peer_value.get(
                        "observation"
                    )
                ),

            "reflection_shape":
                _shape(
                    peer_value.get(
                        "reflection"
                    )
                ),

            "observation_present":
                peer_value.get(
                    "observation_present"
                )
                is True,

            "reflection_present":
                peer_value.get(
                    "reflection_present"
                )
                is True,
        }

    peer_names = sorted(peers)

    fully_published = sorted(
        name
        for name, value in peers.items()
        if (
            value["observation_present"]
            and
            value["reflection_present"]
        )
    )

    observation_only = sorted(
        name
        for name, value in peers.items()
        if (
            value["observation_present"]
            and
            not value["reflection_present"]
        )
    )

    reflection_only = sorted(
        name
        for name, value in peers.items()
        if (
            value["reflection_present"]
            and
            not value["observation_present"]
        )
    )

    result = {
        "observer":
            layer,

        "schema":
            "malysh.interlayer-observer.v1",

        "source_snapshot":
            "frozen_pre_interlayer",

        "peer_names":
            peer_names,

        "peer_count":
            len(peer_names),

        "peers":
            peers,

        "patterns": {
            "fully_published":
                fully_published,

            "observation_only":
                observation_only,

            "reflection_only":
                reflection_only,

            "shared_subject":
                "Malysh",

            "winner":
                None,

            "disagreement_preserved":
                True,

            "missing_views_preserved":
                True,
        },

        "affects_main_answer":
            False,

        "affects_execution":
            False,

        **_authority_flags(),
    }

    result["invariants"] = {
        "self_excluded":
            layer not in peers,

        "peer_names_unique":
            len(peer_names)
            ==
            len(set(peer_names)),

        "no_winner":
            result["patterns"]["winner"]
            is None,

        "disagreement_preserved":
            result[
                "patterns"
            ][
                "disagreement_preserved"
            ]
            is True,

        "main_answer_unchanged":
            result["affects_main_answer"]
            is False,

        "execution_unchanged":
            result["affects_execution"]
            is False,

        "no_decision_authority":
            result["decision_authority"]
            is False,

        "no_state_write":
            result["state_write"]
            is False,

        "no_state_commit":
            result["state_commit"]
            is False,

        "no_canonical_write":
            result["canonical_write"]
            is False,

        "no_main_answer_write":
            result["main_answer_write"]
            is False,

        "no_possible_branch_write":
            result["possible_branch_write"]
            is False,
    }

    result["invariant_ok"] = all(
        result["invariants"].values()
    )

    return result


def compute_interlayer_pass(
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Compute all independent layer reflections.

    All layer reflections are derived from one frozen input snapshot.
    """

    frozen_snapshot = deepcopy(
        dict(snapshot)
    )

    frozen_outputs = collect_layer_outputs(
        frozen_snapshot
    )

    layer_results = {}

    for layer in sorted(
        frozen_outputs
    ):
        layer_results[layer] = (
            observe_from_layer(
                layer,
                frozen_outputs,
            )
        )

    result = {
        "organ":
            ORGAN,

        "schema":
            "malysh.interlayer-pass.v1",

        "subject":
            frozen_snapshot.get(
                "subject"
            ),

        "frozen_layer_names":
            sorted(
                frozen_outputs
            ),

        "observer_count":
            len(layer_results),

        "layer_results":
            layer_results,

        "winner":
            None,

        "same_snapshot_for_all":
            True,

        "results_stored_separately":
            True,

        "affects_main_answer":
            False,

        "affects_execution":
            False,

        **_authority_flags(),
    }

    result["invariants"] = {
        "one_subject":
            result["subject"]
            ==
            "Malysh",

        "one_result_per_layer":
            (
                result["observer_count"]
                ==
                len(
                    result["frozen_layer_names"]
                )
                ==
                len(result["layer_results"])
            ),

        "all_layers_verified":
            all(
                value.get(
                    "invariant_ok"
                )
                is True
                for value in
                result["layer_results"].values()
            ),

        "same_snapshot_for_all":
            result["same_snapshot_for_all"]
            is True,

        "results_stored_separately":
            result[
                "results_stored_separately"
            ]
            is True,

        "no_winner":
            result["winner"]
            is None,

        "main_answer_unchanged":
            result["affects_main_answer"]
            is False,

        "execution_unchanged":
            result["affects_execution"]
            is False,

        "no_decision_authority":
            result["decision_authority"]
            is False,

        "no_state_write":
            result["state_write"]
            is False,

        "no_state_commit":
            result["state_commit"]
            is False,

        "no_canonical_write":
            result["canonical_write"]
            is False,
    }

    result["invariant_ok"] = all(
        result["invariants"].values()
    )

    return result


def run_interlayer_pass(
    snapshot: Mapping[str, Any],
) -> OrganResult:
    """
    Execute the multi-layer observer pass.
    """

    try:
        result = compute_interlayer_pass(
            snapshot
        )

        if not result["invariant_ok"]:
            return OrganResult(
                organ=ORGAN,
                status="error",
                data=result,
                error=(
                    "inter-layer invariant failed"
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
                f"{type(error).__name__}: "
                f"{error}"
            ),
        )


def integrate_interlayer_pass(
    mind: Any,
) -> OrganResult:
    """
    Publish separate layer reflections to ONE MindState.
    """

    if not hasattr(mind, "snapshot"):
        raise TypeError(
            "mind must provide snapshot()"
        )

    if not hasattr(mind, "reflect"):
        raise TypeError(
            "mind must provide reflect(name, value)"
        )

    before = mind.snapshot()

    protected = {
        key: deepcopy(
            before.get(key)
        )
        for key in (
            "subject",
            "canonical",
            "observations",
            "experience",
            "human",
            "main",
            "possible",
        )
    }

    result = run_interlayer_pass(
        before
    )

    if result.status != "ok":
        raise RuntimeError(
            result.error
            or
            "inter-layer pass failed"
        )

    for layer, value in (
        result.data[
            "layer_results"
        ].items()
    ):
        mind.reflect(
            "InterLayer:" + layer,
            value,
        )

    mind.reflect(
        ORGAN,
        {
            "schema":
                result.data["schema"],

            "observer_count":
                result.data[
                    "observer_count"
                ],

            "frozen_layer_names":
                deepcopy(
                    result.data[
                        "frozen_layer_names"
                    ]
                ),

            "invariant_ok":
                result.data[
                    "invariant_ok"
                ],

            "winner":
                None,

            **_authority_flags(),
        },
    )

    after = mind.snapshot()

    for key, expected in protected.items():
        if after.get(key) != expected:
            raise RuntimeError(
                "inter-layer pass mutated protected state: "
                + key
            )

    if hasattr(mind, "invariant"):
        if not mind.invariant():
            raise RuntimeError(
                "MindState invariant failed"
            )

    return result
