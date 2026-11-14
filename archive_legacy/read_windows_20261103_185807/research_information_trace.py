from __future__ import annotations

import argparse
import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from malysh_system.full_reflections import (
    FullReflections,
    TAU,
)


EPS = 1e-12


def stable(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )


def digest(value):
    return hashlib.sha256(
        stable(value).encode("utf-8")
    ).hexdigest()


def sign(value, eps=EPS):
    if value > eps:
        return 1
    if value < -eps:
        return -1
    return 0


def circular_distance(a, b):
    delta = abs((a - b) % TAU)
    return min(delta, TAU - delta)


def mean(values):
    return sum(values) / len(values) if values else 0.0


def rms(values):
    if not values:
        return 0.0

    return math.sqrt(
        sum(value * value for value in values)
        / len(values)
    )


def circular_projection(phases):
    vector = sum(
        complex(
            math.cos(phase),
            math.sin(phase),
        )
        for phase in phases
    ) / len(phases)

    return abs(vector)


def center_from_phases(phases):
    return [
        0.0,
        mean([math.sin(value) for value in phases]),
        mean([math.cos(value) for value in phases]),
    ]


def pair_state(phases, frequencies, center):
    events = []
    orientation_histogram = {}

    for i in range(len(phases)):
        for j in range(i + 1, len(phases)):
            delta = (phases[j] - phases[i]) % TAU
            cosine = math.cos(delta)

            radius2 = abs(cosine)
            central = radius2 < 0.075

            sigma_p = sign(math.sin(delta))

            sigma_t = sign(
                -math.sin(delta)
                * (
                    frequencies[j]
                    - frequencies[i]
                )
            )

            sigma_u = sign(center[2])

            orientation = (
                sigma_p,
                sigma_t,
                sigma_u,
            )

            key = str(orientation)

            orientation_histogram[key] = (
                orientation_histogram.get(key, 0)
                + 1
            )

            events.append(
                {
                    "pair": [i, j],
                    "radius2": radius2,
                    "central_event": central,
                    "orientation": list(orientation),
                }
            )

    return {
        "events": events,
        "orientation_histogram":
            orientation_histogram,
        "central_pairs": [
            event["pair"]
            for event in events
            if event["central_event"]
        ],
    }


def decode_score(geometry):
    return sum(
        geometry["code"][j]
        * math.sin(geometry["phases"][j])
        for j in range(8)
    )


def write_bit(geometry, bit):
    result = deepcopy(geometry)

    for j in range(8):
        pattern = 1 if j % 2 == 0 else -1

        result["phases"][j] = (
            result["phases"][j]
            + bit * 0.14 * pattern
        ) % TAU

    return result


def evolve_one(geometry):
    result = deepcopy(geometry)

    result["phases"] = [
        (
            result["phases"][j]
            + result["frequencies"][j]
        ) % TAU
        for j in range(8)
    ]

    return result


def compare_states(positive, negative, step):
    phase_delta = [
        circular_distance(
            positive["phases"][j],
            negative["phases"][j],
        )
        for j in range(8)
    ]

    frequency_delta = [
        abs(
            positive["frequencies"][j]
            - negative["frequencies"][j]
        )
        for j in range(8)
    ]

    center_positive = center_from_phases(
        positive["phases"]
    )

    center_negative = center_from_phases(
        negative["phases"]
    )

    geometry_distance = math.sqrt(
        sum(
            (
                center_positive[index]
                - center_negative[index]
            ) ** 2
            for index in range(3)
        )
    )

    pairs_positive = pair_state(
        positive["phases"],
        positive["frequencies"],
        center_positive,
    )

    pairs_negative = pair_state(
        negative["phases"],
        negative["frequencies"],
        center_negative,
    )

    orientations_positive = {
        tuple(event["orientation"])
        for event in pairs_positive["events"]
    }

    orientations_negative = {
        tuple(event["orientation"])
        for event in pairs_negative["events"]
    }

    orientation_difference = len(
        orientations_positive
        ^ orientations_negative
    )

    central_positive = {
        tuple(pair)
        for pair in pairs_positive["central_pairs"]
    }

    central_negative = {
        tuple(pair)
        for pair in pairs_negative["central_pairs"]
    }

    central_event_difference = len(
        central_positive
        ^ central_negative
    )

    projection_positive = circular_projection(
        positive["phases"]
    )

    projection_negative = circular_projection(
        negative["phases"]
    )

    score_positive = decode_score(positive)
    score_negative = decode_score(negative)

    read_positive = (
        1 if score_positive >= 0 else -1
    )

    read_negative = (
        1 if score_negative >= 0 else -1
    )

    trace_payload = {
        "step": step,
        "positive_phases": positive["phases"],
        "negative_phases": negative["phases"],
        "positive_central_pairs":
            pairs_positive["central_pairs"],
        "negative_central_pairs":
            pairs_negative["central_pairs"],
    }

    return {
        "step": step,

        "D_G": geometry_distance,

        "D_phase_mean": mean(phase_delta),
        "D_phase_rms": rms(phase_delta),
        "D_phase_max": max(phase_delta),

        "D_frequency_mean":
            mean(frequency_delta),

        "D_orientation":
            orientation_difference,

        "D_zero_projection":
            abs(
                projection_positive
                - projection_negative
            ),

        "D_central_events":
            central_event_difference,

        "D_history":
            (
                0
                if digest(trace_payload)[0:16]
                == digest(
                    {
                        **trace_payload,
                        "positive_phases":
                            negative["phases"],
                        "negative_phases":
                            positive["phases"],
                    }
                )[0:16]
                else 1
            ),

        "positive": {
            "projection": projection_positive,
            "decode_score": score_positive,
            "read": read_positive,
            "central_pairs":
                pairs_positive["central_pairs"],
            "orientation_histogram":
                pairs_positive[
                    "orientation_histogram"
                ],
        },

        "negative": {
            "projection": projection_negative,
            "decode_score": score_negative,
            "read": read_negative,
            "central_pairs":
                pairs_negative["central_pairs"],
            "orientation_histogram":
                pairs_negative[
                    "orientation_histogram"
                ],
        },
    }


def classify_trace(trace):
    phase_values = [
        item["D_phase_rms"]
        for item in trace
    ]

    frequency_values = [
        item["D_frequency_mean"]
        for item in trace
    ]

    orientation_values = [
        item["D_orientation"]
        for item in trace
    ]

    event_values = [
        item["D_central_events"]
        for item in trace
    ]

    reads_separated = [
        (
            item["positive"]["read"]
            != item["negative"]["read"]
        )
        for item in trace
    ]

    full_distinguishability = [
        (
            item["D_G"]
            + item["D_phase_rms"]
            + item["D_frequency_mean"]
            + item["D_orientation"]
            + item["D_zero_projection"]
            + item["D_central_events"]
        )
        for item in trace
    ]

    information_destroyed = all(
        value <= EPS
        for value in full_distinguishability[1:]
    )

    phase_survives = all(
        value > EPS
        for value in phase_values
    )

    frequency_carries_bit = any(
        value > EPS
        for value in frequency_values
    )

    orientation_carries_bit = any(
        value > 0
        for value in orientation_values
    )

    events_carry_bit = any(
        value > 0
        for value in event_values
    )

    reader_ever_separates = any(
        reads_separated
    )

    if information_destroyed:
        verdict = "INFORMATION_DESTROYED"

    elif (
        phase_survives
        and not reader_ever_separates
    ):
        verdict = (
            "INFORMATION_SURVIVES_IN_PHASE_"
            "BUT_READER_DOES_NOT_SEPARATE"
        )

    elif reader_ever_separates:
        verdict = (
            "INFORMATION_IS_READABLE_"
            "AT_SOME_STEPS"
        )

    else:
        verdict = (
            "INFORMATION_SURVIVES_"
            "IN_NON_READER_CHANNEL"
        )

    return {
        "verdict": verdict,

        "information_destroyed":
            information_destroyed,

        "phase_survives":
            phase_survives,

        "frequency_carries_bit":
            frequency_carries_bit,

        "orientation_carries_bit":
            orientation_carries_bit,

        "central_events_carry_bit":
            events_carry_bit,

        "reader_ever_separates":
            reader_ever_separates,

        "candidate_channels": [
            name
            for name, active in (
                ("phase", phase_survives),
                ("frequency", frequency_carries_bit),
                (
                    "orientation",
                    orientation_carries_bit,
                ),
                (
                    "central_events",
                    events_carry_bit,
                ),
            )
            if active
        ],
    }


def run_experiment(
    data=None,
    cycles=10,
    root=None,
):
    if data is None:
        data = [1.0, 2.0, 3.0, 4.0, 5.0]

    if root is None:
        temporary = TemporaryDirectory()
        root = temporary.name
    else:
        temporary = None

    try:
        reflections = FullReflections(root=root)

        base = reflections._geometry(data)

        positive = write_bit(base, 1)
        negative = write_bit(base, -1)

        trace = []

        for step in range(cycles + 1):
            trace.append(
                compare_states(
                    positive,
                    negative,
                    step,
                )
            )

            if step < cycles:
                positive = evolve_one(positive)
                negative = evolve_one(negative)

        diagnosis = classify_trace(trace)

        voice_a = {
            "name": "VOICE_A_BEFORE",
            "rights": "equal",
            "interpretation": (
                "Check whether historical phase, "
                "resonance and memory channels preserve "
                "the distinction."
            ),
            "evidence": {
                "phase_survives":
                    diagnosis["phase_survives"],
                "history_distinguishable":
                    any(
                        item["D_history"] > 0
                        for item in trace
                    ),
            },
        }

        voice_b = {
            "name": "VOICE_B_NOW",
            "rights": "equal",
            "interpretation": (
                "Trace distinguishability through "
                "phase, frequency, orientation, "
                "central events and decoder output."
            ),
            "evidence": {
                "candidate_channels":
                    diagnosis["candidate_channels"],
                "reader_ever_separates":
                    diagnosis[
                        "reader_ever_separates"
                    ],
            },
        }

        debate = {
            "state": (
                "AGREEMENT"
                if (
                    voice_a["evidence"][
                        "phase_survives"
                    ]
                    ==
                    (
                        "phase"
                        in voice_b["evidence"][
                            "candidate_channels"
                        ]
                    )
                )
                else "DISAGREEMENT"
            ),
            "winner": None,
            "equal_rights": True,
            "conclusion": diagnosis["verdict"],
            "forced_finality": False,
        }

        return {
            "schema":
                "malysh.information-trace.v1",

            "model": {
                "space": "B3",
                "lemniscates": 8,
                "functional_modes": [
                    "H_clock",
                    "H_code",
                ],
                "cycles": cycles,
                "input": data,
            },

            "hypothesis": (
                "The written distinction may survive "
                "in an internal channel even when "
                "WRITE-EVOLVE-READ accuracy is 0.5."
            ),

            "trace": trace,
            "diagnosis": diagnosis,

            "malysh_reflection": {
                "voice_a": voice_a,
                "voice_b": voice_b,
                "debate": debate,
            },

            "claims": {
                "physical_proof": False,
                "computational_experiment": True,
                "reader_failure_is_not_automatically_"
                "information_destruction": True,
            },
        }

    finally:
        if temporary is not None:
            temporary.cleanup()


def print_summary(result):
    diagnosis = result["diagnosis"]
    debate = result["malysh_reflection"]["debate"]

    print("==============================================")
    print("INFORMATION TRACE RESULT")
    print("==============================================")
    print("Verdict :", diagnosis["verdict"])
    print(
        "Channels:",
        diagnosis["candidate_channels"],
    )
    print(
        "Phase survives:",
        diagnosis["phase_survives"],
    )
    print(
        "Reader separates:",
        diagnosis["reader_ever_separates"],
    )
    print("Debate  :", debate["state"])
    print("Winner  :", debate["winner"])
    print()

    print(
        "STEP | D_PHASE | D_FREQ | D_SIGMA "
        "| D_ZERO | READ+ READ-"
    )

    for item in result["trace"]:
        print(
            f"{item['step']:4d} | "
            f"{item['D_phase_rms']:.6f} | "
            f"{item['D_frequency_mean']:.6f} | "
            f"{item['D_orientation']:7d} | "
            f"{item['D_zero_projection']:.6f} | "
            f"{item['positive']['read']:5d} "
            f"{item['negative']['read']:5d}"
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cycles",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--output",
        default=(
            "runtime/reflections/"
            "information_trace_latest.json"
        ),
    )

    args = parser.parse_args()

    result = run_experiment(
        cycles=args.cycles,
    )

    output = Path(args.output)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print_summary(result)

    print()
    print("Report:", output)


if __name__ == "__main__":
    main()
