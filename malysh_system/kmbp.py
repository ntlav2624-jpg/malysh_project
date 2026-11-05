"""
Working KMBP organ for ONE Malysh.

KMBP performs a deterministic transformation:

    real input
        -> amplitude
        -> quaternary state
        -> zone and PAM-4 representation
        -> verifiable result
        -> MindState observation

Historical files remain historical evidence. This module does not
claim that a filename or textual mention proves canonical heritage.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import math
from typing import Any, Iterable

from malysh_system.protocols import OrganResult


KMBP_ORGAN = "KMBP"

STATE_TO_ZONE = {
    0: "ROOT",
    1: "JILS",
    2: "TAIL",
    3: "PHASE",
}

STATE_TO_VOLTAGE = {
    0: 0.0,
    1: 1.2,
    2: 2.4,
    3: 3.6,
}


@dataclass(frozen=True)
class KMBPNode:
    index: int
    symbol: str
    amplitude: int
    quaternary_state: int
    zone: str
    voltage_v: float
    logic_level: str
    energy_weight: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_input(
    value: str | bytes | Iterable[int],
) -> tuple[list[str], list[int]]:
    """
    Convert a supported real input into symbols and amplitudes.

    str:
        each Unicode symbol is mapped through codepoint % 32

    bytes:
        every byte is used directly

    iterableevery non-negative integer is used directly
    """

    if isinstance(value, str):
        if not value:
            raise ValueError("KMBP input must not be empty")

        symbols = list(value)
        amplitudes = [
            ord(symbol) % 32
            for symbol in symbols
        ]

        return symbols, amplitudes

    if isinstance(value, bytes):
        if not value:
            raise ValueError("KMBP input must not be empty")

        amplitudes = list(value)
        symbols = [
            f"0x{amplitude:02x}"
            for amplitude in amplitudes
        ]

        return symbols, amplitudes

    try:
        amplitudes = [
            int(item)
            for item in value
        ]
    except (TypeError, ValueError) as error:
        raise TypeError(
            "KMBP input must be str, bytes, "
            "or an iterable of non-negative integers"
        ) from error

    if not amplitudes:
        raise ValueError("KMBP input must not be empty")

    if any(amplitude < 0 for amplitude in amplitudes):
        raise ValueError(
            "KMBP amplitudes must be non-negative"
        )

    symbols = [
        str(amplitude)
        for amplitude in amplitudes
    ]

    return symbols, amplitudes


def compute_kmbp(
    value: str | bytes | Iterable[int],
) -> dict[str, Any]:
    """
    Execute the deterministic KMBP calculation.
    """

    symbols, amplitudes = normalize_input(value)

    total_power = sum(amplitudes)
    denominator = total_power if total_power > 0 else 1

    nodes: list[KMBPNode] = []

    for index, (symbol, amplitude) in enumerate(
        zip(symbols, amplitudes),
        start=1,
    ):
        state = amplitude % 4
        zone = STATE_TO_ZONE[state]

        node = KMBPNode(
            index=index,
            symbol=symbol,
            amplitude=amplitude,
            quaternary_state=state,
            zone=zone,
            voltage_v=STATE_TO_VOLTAGE[state],
            logic_level=f"PAM-4_L{state}",
            energy_weight=round(
                amplitude / denominator,
                12,
            ),
        )

        nodes.append(node)

    states = [
        node.quaternary_state
        for node in nodes
    ]

    zones = {
        zone: [
            node.index
            for node in nodes
            if node.zone == zone
        ]
        for zone in STATE_TO_ZONE.values()
    }

    energy_weight_sum = math.fsum(
        node.energy_weight
        for node in nodes
    )

    result = {
        "organ": KMBP_ORGAN,
        "schema_version": 1,
        "input_type": type(value).__name__,
        "input_length": len(amplitudes),
        "amplitudes": amplitudes,
        "states": states,
        "nodes": [
            node.to_dict()
            for node in nodes
        ],
        "zones": zones,
        "total_power": total_power,
        "energy_weight_sum": energy_weight_sum,
        "decision_authority": False,
        "state_write": False,
        "state_commit": False,
    }

    result["invariants"] = validate_kmbp(result)
    result["invariant_ok"] = all(
        result["invariants"].values()
    )

    return result


def validate_kmbp(
    result: dict[str, Any],
) -> dict[str, bool]:
    """
    Validate structural and mathematical KMBP invariants.
    """

    nodes = result.get("nodes", [])
    states = result.get("states", [])
    amplitudes = result.get("amplitudes", [])

    range_ok = all(
        state in {0, 1, 2, 3}
        for state in states
    )

    modulo_ok = (
        len(states) == len(amplitudes)
        and all(
            state == amplitude % 4
            for state, amplitude in zip(
                states,
                amplitudes,
            )
        )
    )

    node_count_ok = (
        len(nodes)
        == result.get("input_length")
        == len(states)
        == len(amplitudes)
    )

    zone_ok = all(
        node.get("zone")
        == STATE_TO_ZONE.get(
            node.get("quaternary_state")
        )
        for node in nodes
    )

    voltage_ok = all(
        node.get("voltage_v")
        == STATE_TO_VOLTAGE.get(
            node.get("quaternary_state")
        )
        for node in nodes
    )

    total_power = result.get("total_power", 0)

    if total_power > 0:
        weight_ok = math.isclose(
            result.get("energy_weight_sum", 0.0),
            1.0,
            rel_tol=0.0,
            abs_tol=1e-9,
        )
    else:
        weight_ok = all(
            node.get("energy_weight") == 0.0
            for node in nodes
        )

    authority_ok = (
        result.get("decision_authority") is False
        and result.get("state_write") is False
        and result.get("state_commit") is False
    )

    return {
        "state_range": range_ok,
        "modulo_projection": modulo_ok,
        "node_count": node_count_ok,
        "zone_mapping": zone_ok,
        "voltage_mapping": voltage_ok,
        "energy_normalization": weight_ok,
        "no_decision_authority": authority_ok,
    }


def run_kmbp(
    value: str | bytes | Iterable[int],
) -> OrganResult:
    """
    Run KMBP through the common organ-result contract.
    """

    try:
        result = compute_kmbp(value)

        if not result["invariant_ok"]:
            return OrganResult(
                organ=KMBP_ORGAN,
                status="error",
                data=result,
                error="KMBP invariant failed",
            )

        return OrganResult(
            organ=KMBP_ORGAN,
            status="ok",
            data=result,
        )

    except Exception as error:
        return OrganResult(
            organ=KMBP_ORGAN,
            status="error",
            data={},
            error=f"{type(error).__name__}: {error}",
        )


def integrate_kmbp(
    mind: Any,
    value: str | bytes | Iterable[int],
) -> OrganResult:
    """
    Integrate a verified KMBP result into ONE MindState.

    KMBP is stored as:
      - an observation containing the computation;
      - a separate reflection without decision authority.

    The function does not overwrite MindState.canonical and does not
    make an executive decision.
    """

    organ_result = run_kmbp(value)

    if organ_result.status != "ok":
        return organ_result

    if not hasattr(mind, "observe"):
        raise TypeError(
            "mind must provide observe(name, value)"
        )

    if not hasattr(mind, "reflect"):
        raise TypeError(
            "mind must provide reflect(name, value)"
        )

    snapshot = deepcopy(organ_result.data)

    mind.observe(
        KMBP_ORGAN,
        snapshot,
    )

    mind.reflect(
        KMBP_ORGAN,
        {
            "states": snapshot["states"],
            "invariant_ok": snapshot["invariant_ok"],
            "decision_authority": False,
            "state_write": False,
            "state_commit": False,
        },
    )

    if hasattr(mind, "invariant"):
        if not mind.invariant():
            raise ValueError(
                "MindState invariant failed after KMBP integration"
            )

    return organ_result
