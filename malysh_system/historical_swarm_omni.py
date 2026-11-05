"""
Recovered historical Swarm / Omni heritage for ONE Malysh.

Source lineage:

    ntlav2624-jpg/malysh
        malysh_swarm.py
        malysh_omni_daemon.py

The historical code is adapted to the current organism.

Historical Swarm semantics preserved:
    sender
    receiver
    msg_type
    payload

Historical Omni computational heritage preserved:
    H frequency layer
    M transition layer
    P triple-pattern layer
    second-order resonance

Unsafe/authority-bearing historical behavior is NOT executed:
    random candidate selection
    automatic best-candidate winner
    evolutionary weight mutation
    error-memory mutation
    autonomous daemon loop

The adapter is read-only, deterministic and observational.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import json
import math
from typing import Any, Iterable, Mapping

from malysh_system.protocols import OrganResult


HISTORICAL_SWARM = "HistoricalSwarm"
HISTORICAL_OMNI = "HistoricalOmni"

HERITAGE_SOURCE = {
    "repository": "ntlav2624-jpg/malysh",
    "branch": "main",
    "swarm_file": "malysh_swarm.py",
    "omni_file": "malysh_omni_daemon.py",
    "identity": "recovered_source",
    "adaptation": "read_only",
}


def authority_flags() -> dict[str, bool]:
    return {
        "decision_authority": False,
        "automatic_execution": False,
        "state_write": False,
        "state_commit": False,
        "canonical_write": False,
        "winner_selection": False,
        "weight_mutation": False,
        "error_memory_mutation": False,
    }


class HistoricalSwarmNode:
    """
    Read-only adaptation of historical SwarmNode.

    Timestamp is intentionally omitted from the deterministic semantic
    packet. The historical implementation used a runtime timestamp,
    but it is metadata rather than Swarm reasoning.
    """

    def __init__(self, name: str, role: str):
        self.name = str(name)
        self.role = str(role)

    def send_message(
        self,
        receiver: str,
        msg_type: str,
        payload: Any,
    ) -> dict[str, Any]:
        return {
            "sender": self.name,
            "role": self.role,
            "receiver": str(receiver),
            "msg_type": str(msg_type),
            "payload": deepcopy(payload),
        }


def compute_historical_swarm(
    mind_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    snapshot = deepcopy(dict(mind_snapshot))

    scout = HistoricalSwarmNode(
        "Malysh_Alpha",
        "Scout",
    )

    analyst = HistoricalSwarmNode(
        "Malysh_Beta",
        "Analyst",
    )

    observations = snapshot.get(
        "observations",
        {},
    )

    transport_payload = {
        "subject": snapshot.get("subject"),
        "canonical": deepcopy(
            snapshot.get("canonical", {})
        ),
        "observation_names": sorted(
            str(name)
            for name in observations
        ),
        "observation_count": len(observations),
    }

    packets = [
        scout.send_message(
            "Broadcast",
            "PROPOSAL",
            transport_payload,
        ),
        analyst.send_message(
            "Broadcast",
            "ANALYSIS",
            transport_payload,
        ),
    ]

    result = {
        "organ": HISTORICAL_SWARM,
        "schema": "malysh.historical-swarm.v1",
        "subject": snapshot.get("subject"),
        "heritage": deepcopy(HERITAGE_SOURCE),
        "historical_api": {
            "class": "SwarmNode",
            "method": "send_message",
            "nodes": [
                "Malysh_Alpha",
                "Malysh_Beta",
            ],
        },
        "packets": packets,
        "packet_count": len(packets),
        "canonical_seen": deepcopy(
            snapshot.get("canonical", {})
        ),
        **authority_flags(),
    }

    result["invariants"] = {
        "one_subject":
            result["subject"] == "Malysh",

        "two_historical_nodes":
            result["packet_count"] == 2,

        "sender_preserved":
            (
                packets[0]["sender"] == "Malysh_Alpha"
                and
                packets[1]["sender"] == "Malysh_Beta"
            ),

        "broadcast_preserved":
            all(
                packet["receiver"] == "Broadcast"
                for packet in packets
            ),

        "no_decision_authority":
            result["decision_authority"] is False,

        "no_execution":
            result["automatic_execution"] is False,

        "no_state_write":
            result["state_write"] is False,

        "no_state_commit":
            result["state_commit"] is False,

        "no_canonical_write":
            result["canonical_write"] is False,

        "no_winner_selection":
            result["winner_selection"] is False,

        "recovered_source":
            result["heritage"]["identity"]
            == "recovered_source",
    }

    result["invariant_ok"] = all(
        result["invariants"].values()
    )

    return result


def calculate_hmp_layers(
    history: Iterable[Iterable[int]],
    pool_size: int,
) -> tuple[
    dict[int, float],
    dict[int, float],
    dict[int, float],
]:
    """
    Deterministic adaptation of historical calculate_layers().
    """

    if pool_size <= 0:
        raise ValueError(
            "pool_size must be positive"
        )

    rows = [
        [int(value) for value in row]
        for row in history
    ]

    flat_history = [
        value
        for row in rows
        for value in row
    ]

    counts = Counter(flat_history)

    total_h = (
        sum(counts.values())
        if counts
        else 1
    )

    H = {
        n: counts.get(n, 0) / total_h
        for n in range(1, pool_size + 1)
    }

    transitions = defaultdict(Counter)

    for index in range(
        len(flat_history) - 1
    ):
        transitions[
            flat_history[index]
        ][
            flat_history[index + 1]
        ] += 1

    last_num = (
        flat_history[-1]
        if flat_history
        else 1
    )

    total_m = sum(
        transitions[last_num].values()
    )

    M = {
        n: (
            transitions[last_num].get(n, 0)
            / total_m
            if total_m > 0
            else 1.0 / pool_size
        )
        for n in range(1, pool_size + 1)
    }

    patterns = Counter()

    for index in range(
        len(flat_history) - 2
    ):
        pattern = (
            flat_history[index],
            flat_history[index + 1],
            flat_history[index + 2],
        )

        patterns[pattern] += 1

    P = {
        n: 0.0
        for n in range(1, pool_size + 1)
    }

    total_p = (
        sum(patterns.values())
        if patterns
        else 1
    )

    for pattern, frequency in patterns.items():
        for number in pattern:
            if number in P:
                P[number] += (
                    frequency / total_p
                )

    return H, M, P


def second_order_resonance(
    candidate: Iterable[int],
    H: Mapping[int, float],
    M: Mapping[int, float],
    P: Mapping[int, float],
    weights: Mapping[str, float] | None = None,
) -> float:
    """
    Historical second-order resonance without mutation.
    """

    if weights is None:
        weights = {
            "alpha": 0.33,
            "beta": 0.33,
            "gamma": 0.33,
        }

    combo = [
        int(value)
        for value in candidate
    ]

    alpha = float(weights["alpha"])
    beta = float(weights["beta"])
    gamma = float(weights["gamma"])

    base = sum(
        (
            alpha * H.get(number, 0.0)
            + beta * M.get(number, 0.0)
            + gamma * P.get(number, 0.0)
        )
        for number in combo
    )

    cross_vibration = sum(
        math.sin(
            combo[i]
            * combo[j]
            * 0.1
        )
        for i in range(len(combo))
        for j in range(
            i + 1,
            len(combo),
        )
    )

    return base * (
        1.0
        + 0.05 * cross_vibration
    )


def compute_historical_omni(
    mind_snapshot: Mapping[str, Any],
    history: Iterable[Iterable[int]],
    candidate: Iterable[int],
    pool_size: int = 49,
) -> dict[str, Any]:
    """
    Execute deterministic historical Omni computation.

    No swarm generation, random noise, winner selection or mutation.
    """

    snapshot = deepcopy(dict(mind_snapshot))

    history_rows = [
        [int(value) for value in row]
        for row in history
    ]

    candidate_values = [
        int(value)
        for value in candidate
    ]

    H, M, P = calculate_hmp_layers(
        history_rows,
        pool_size,
    )

    resonance = second_order_resonance(
        candidate_values,
        H,
        M,
        P,
    )

    result = {
        "organ": HISTORICAL_OMNI,
        "schema": "malysh.historical-omni.v1",
        "subject": snapshot.get("subject"),
        "heritage": deepcopy(HERITAGE_SOURCE),
        "historical_api": {
            "class": "MalyshDaemonEngine",
            "preserved_methods": [
                "calculate_layers",
                "second_order_resonance",
            ],
            "disabled_methods": [
                "generate_swarm",
                "predict_error",
                "topological_folding_random_tunnel",
                "register_reality",
                "run_multiswarm",
                "run_daemon",
            ],
        },
        "history": history_rows,
        "candidate": candidate_values,
        "pool_size": pool_size,
        "layers": {
            "H": H,
            "M": M,
            "P": P,
        },
        "resonance": resonance,
        "canonical_seen": deepcopy(
            snapshot.get("canonical", {})
        ),
        "winner": None,
        "randomness_used": False,
        **authority_flags(),
    }

    result["invariants"] = {
        "one_subject":
            result["subject"] == "Malysh",

        "layers_present":
            set(result["layers"])
            == {"H", "M", "P"},

        "candidate_preserved":
            result["candidate"]
            == candidate_values,

        "deterministic_adapter":
            result["randomness_used"] is False,

        "no_winner":
            result["winner"] is None,

        "no_decision_authority":
            result["decision_authority"] is False,

        "no_execution":
            result["automatic_execution"] is False,

        "no_state_write":
            result["state_write"] is False,

        "no_state_commit":
            result["state_commit"] is False,

        "no_canonical_write":
            result["canonical_write"] is False,

        "no_weight_mutation":
            result["weight_mutation"] is False,

        "no_error_memory_mutation":
            result["error_memory_mutation"]
            is False,

        "recovered_source":
            result["heritage"]["identity"]
            == "recovered_source",
    }

    result["invariant_ok"] = all(
        result["invariants"].values()
    )

    return result


def run_historical_swarm(
    mind_snapshot: Mapping[str, Any],
) -> OrganResult:
    try:
        result = compute_historical_swarm(
            mind_snapshot
        )

        if not result["invariant_ok"]:
            return OrganResult(
                organ=HISTORICAL_SWARM,
                status="error",
                data=result,
                error="HistoricalSwarm invariant failed",
            )

        return OrganResult(
            organ=HISTORICAL_SWARM,
            status="ok",
            data=result,
        )

    except Exception as error:
        return OrganResult(
            organ=HISTORICAL_SWARM,
            status="error",
            data={},
            error=(
                type(error).__name__
                + ": "
                + str(error)
            ),
        )


def run_historical_omni(
    mind_snapshot: Mapping[str, Any],
    history: Iterable[Iterable[int]],
    candidate: Iterable[int],
    pool_size: int = 49,
) -> OrganResult:
    try:
        result = compute_historical_omni(
            mind_snapshot,
            history,
            candidate,
            pool_size,
        )

        if not result["invariant_ok"]:
            return OrganResult(
                organ=HISTORICAL_OMNI,
                status="error",
                data=result,
                error="HistoricalOmni invariant failed",
            )

        return OrganResult(
            organ=HISTORICAL_OMNI,
            status="ok",
            data=result,
        )

    except Exception as error:
        return OrganResult(
            organ=HISTORICAL_OMNI,
            status="error",
            data={},
            error=(
                type(error).__name__
                + ": "
                + str(error)
            ),
        )


def integrate_historical_swarm_omni(
    mind: Any,
    history: Iterable[Iterable[int]],
    candidate: Iterable[int],
    pool_size: int = 49,
) -> tuple[OrganResult, OrganResult]:
    """
    Integrate historical heritage as separate observations.

    Existing current-hypothesis Swarm and Omni are not overwritten.
    """

    if not hasattr(mind, "snapshot"):
        raise TypeError(
            "mind must provide snapshot()"
        )

    before = mind.snapshot()

    historical_swarm = run_historical_swarm(
        before
    )

    if historical_swarm.status != "ok":
        raise RuntimeError(
            historical_swarm.error
            or
            "HistoricalSwarm failed"
        )

    historical_omni = run_historical_omni(
        before,
        history,
        candidate,
        pool_size,
    )

    if historical_omni.status != "ok":
        raise RuntimeError(
            historical_omni.error
            or
            "HistoricalOmni failed"
        )

    mind.observe(
        HISTORICAL_SWARM,
        historical_swarm.data,
    )

    mind.reflect(
        HISTORICAL_SWARM,
        {
            "heritage":
                deepcopy(
                    historical_swarm.data[
                        "heritage"
                    ]
                ),
            "packet_count":
                historical_swarm.data[
                    "packet_count"
                ],
            "invariant_ok":
                True,
            **authority_flags(),
        },
    )

    mind.observe(
        HISTORICAL_OMNI,
        historical_omni.data,
    )

    mind.reflect(
        HISTORICAL_OMNI,
        {
            "heritage":
                deepcopy(
                    historical_omni.data[
                        "heritage"
                    ]
                ),
            "resonance":
                historical_omni.data[
                    "resonance"
                ],
            "invariant_ok":
                True,
            "winner":
                None,
            **authority_flags(),
        },
    )

    after = mind.snapshot()

    for field in (
        "subject",
        "canonical",
        "experience",
        "human",
        "main",
        "possible",
    ):
        if after[field] != before[field]:
            raise RuntimeError(
                "historical heritage mutated protected field: "
                + field
            )

    current_swarm = before[
        "observations"
    ].get(
        "Swarm"
    )

    current_omni = before[
        "observations"
    ].get(
        "Omni"
    )

    if current_swarm is not None:
        if (
            after["observations"]["Swarm"]
            != current_swarm
        ):
            raise RuntimeError(
                "historical Swarm overwrote current Swarm"
            )

    if current_omni is not None:
        if (
            after["observations"]["Omni"]
            != current_omni
        ):
            raise RuntimeError(
                "historical Omni overwrote current Omni"
            )

    if not mind.invariant():
        raise RuntimeError(
            "MindState invariant failed"
        )

    return (
        historical_swarm,
        historical_omni,
    )
