from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

from malysh_system.full_reflections import FullReflections, TAU
from research_information_trace import (
    compare_states,
    evolve_one,
    write_bit,
)


EPS = 1e-12


def mean(values):
    return sum(values) / len(values) if values else 0.0


def safe_rate(flags):
    if not flags:
        return 0.0
    return sum(bool(value) for value in flags) / len(flags)


def circular_resultant(phases):
    if not phases:
        return 0.0

    vector = sum(
        complex(math.cos(value), math.sin(value))
        for value in phases
    ) / len(phases)

    return abs(vector)


def circular_mean(phases):
    if not phases:
        return 0.0

    vector = sum(
        complex(math.cos(value), math.sin(value))
        for value in phases
    )

    return math.atan2(vector.imag, vector.real) % TAU


def point_biserial(binary, values):
    if len(binary) != len(values) or not binary:
        return 0.0

    positive = [
        value
        for flag, value in zip(binary, values)
        if flag
    ]

    negative = [
        value
        for flag, value in zip(binary, values)
        if not flag
    ]

    if not positive or not negative:
        return 0.0

    overall = mean(values)

    variance = mean(
        [(value - overall) ** 2 for value in values]
    )

    if variance <= EPS:
        return 0.0

    standard_deviation = math.sqrt(variance)

    p = len(positive) / len(values)
    q = len(negative) / len(values)

    return (
        (mean(positive) - mean(negative))
        / standard_deviation
        * math.sqrt(p * q)
    )


def binary_autocorrelation(flags, lag):
    values = [1.0 if flag else 0.0 for flag in flags]

    if lag <= 0 or lag >= len(values):
        return 0.0

    left = values[:-lag]
    right = values[lag:]

    left_mean = mean(left)
    right_mean = mean(right)

    numerator = sum(
        (a - left_mean) * (b - right_mean)
        for a, b in zip(left, right)
    )

    left_energy = sum(
        (a - left_mean) ** 2
        for a in left
    )

    right_energy = sum(
        (b - right_mean) ** 2
        for b in right
    )

    denominator = math.sqrt(
        left_energy * right_energy
    )

    if denominator <= EPS:
        return 0.0

    return numerator / denominator


def conditional_rate(rows, predicate):
    selected = [
        row["read_separated"]
        for row in rows
        if predicate(row)
    ]

    return {
        "samples": len(selected),
        "read_window_rate": safe_rate(selected),
    }


def shifted_overlap(flags, shift):
    if shift <= 0 or shift >= len(flags):
        return 0.0

    left = flags[:-shift]
    right = flags[shift:]

    return safe_rate([
        a == b
        for a, b in zip(left, right)
    ])


def run_long_experiment(
    data=None,
    cycles=400,
    max_lag=200,
    root=None,
):
    if data is None:
        data = [1.0, 2.0, 3.0, 4.0, 5.0]

    temporary = None

    if root is None:
        temporary = TemporaryDirectory()
        root = temporary.name

    try:
        reflections = FullReflections(root=root)
        base = reflections._geometry(data)

        positive = write_bit(base, 1)
        negative = write_bit(base, -1)

        clock_frequency = mean(base["clock"])
        rows = []

        for step in range(cycles + 1):
            comparison = compare_states(
                positive,
                negative,
                step,
            )

            clock_phase = (
                clock_frequency * step
            ) % TAU

            read_separated = (
                comparison["positive"]["read"]
                != comparison["negative"]["read"]
            )

            rows.append({
                "step": step,
                "clock_phase": clock_phase,
                "read_separated": read_separated,
                "read_positive":
                    comparison["positive"]["read"],
                "read_negative":
                    comparison["negative"]["read"],
                "D_phase_rms":
                    comparison["D_phase_rms"],
                "D_frequency_mean":
                    comparison["D_frequency_mean"],
                "D_orientation":
                    comparison["D_orientation"],
                "D_central_events":
                    comparison["D_central_events"],
                "D_zero_projection":
                    comparison["D_zero_projection"],
            })

            if step < cycles:
                positive = evolve_one(positive)
                negative = evolve_one(negative)

        flags = [
            row["read_separated"]
            for row in rows
        ]

        window_steps = [
            row["step"]
            for row in rows
            if row["read_separated"]
        ]

        window_phases = [
            row["clock_phase"]
            for row in rows
            if row["read_separated"]
        ]

        gaps = [
            right - left
            for left, right in zip(
                window_steps,
                window_steps[1:],
            )
        ]

        phase_values = [
            row["D_phase_rms"]
            for row in rows
        ]

        base_phase_distance = phase_values[0]

        phase_max_deviation = max(
            abs(value - base_phase_distance)
            for value in phase_values
        )

        orientation_flags = [
            row["D_orientation"] > 0
            for row in rows
        ]

        event_flags = [
            row["D_central_events"] > 0
            for row in rows
        ]

        autocorrelation = []

        upper_lag = min(
            max_lag,
            max(1, len(rows) - 1),
        )

        for lag in range(1, upper_lag + 1):
            autocorrelation.append({
                "lag": lag,
                "correlation":
                    binary_autocorrelation(flags, lag),
                "agreement":
                    shifted_overlap(flags, lag),
            })

        ranked_lags = sorted(
            autocorrelation,
            key=lambda item: (
                item["correlation"],
                item["agreement"],
            ),
            reverse=True,
        )

        zero_projection = [
            row["D_zero_projection"]
            for row in rows
        ]

        read_rate = safe_rate(flags)

        read_given_orientation = conditional_rate(
            rows,
            lambda row:
                row["D_orientation"] > 0,
        )

        read_without_orientation = conditional_rate(
            rows,
            lambda row:
                row["D_orientation"] == 0,
        )

        read_given_event = conditional_rate(
            rows,
            lambda row:
                row["D_central_events"] > 0,
        )

        read_without_event = conditional_rate(
            rows,
            lambda row:
                row["D_central_events"] == 0,
        )

        phase_resultant = circular_resultant(
            window_phases
        )

        if not window_steps:
            verdict = "NO_READ_WINDOWS"

        elif phase_max_deviation >= 1e-12:
            verdict = (
                "READ_WINDOWS_WITHOUT_"
                "PHASE_CONSERVATION"
            )

        elif phase_resultant >= 0.5:
            verdict = (
                "DISTINGUISHABILITY_SURVIVES_"
                "WITH_CLOCK_PHASE_CLUSTERED_"
                "READ_WINDOWS"
            )

        else:
            verdict = (
                "DISTINGUISHABILITY_SURVIVES_"
                "WITH_INTERMITTENT_OBSERVABILITY"
            )

        result = {
            "schema":
                "malysh.read-windows.v1",

            "model": {
                "cycles": cycles,
                "samples": len(rows),
                "input": data,
                "clock_frequency":
                    clock_frequency,
                "decoder_changed": False,
                "dynamics_changed": False,
                "new_physical_entity_added":
                    False,
            },

            "invariants": {
                "initial_phase_distance":
                    base_phase_distance,
                "final_phase_distance":
                    phase_values[-1],
                "phase_max_deviation":
                    phase_max_deviation,
                "phase_conserved":
                    phase_max_deviation < 1e-12,
                "frequency_distance_zero":
                    max(
                        row["D_frequency_mean"]
                        for row in rows
                    ) < 1e-12,
            },

            "read_windows": {
                "count": len(window_steps),
                "rate": read_rate,
                "steps": window_steps,
                "gaps": gaps,
                "mean_gap": mean(gaps),
                "clock_phases": window_phases,
                "clock_phase_mean":
                    circular_mean(window_phases),
                "clock_phase_resultant":
                    phase_resultant,
            },

            "channel_association": {
                "orientation": {
                    "active_samples":
                        sum(orientation_flags),
                    "read_given_active":
                        read_given_orientation,
                    "read_given_inactive":
                        read_without_orientation,
                },
                "central_events": {
                    "active_samples":
                        sum(event_flags),
                    "read_given_active":
                        read_given_event,
                    "read_given_inactive":
                        read_without_event,
                },
                "zero_projection": {
                    "point_biserial":
                        point_biserial(
                            flags,
                            zero_projection,
                        ),
                    "mean_when_readable":
                        mean([
                            row["D_zero_projection"]
                            for row in rows
                            if row["read_separated"]
                        ]),
                    "mean_when_not_readable":
                        mean([
                            row["D_zero_projection"]
                            for row in rows
                            if not row["read_separated"]
                        ]),
                },
            },

            "periodicity": {
                "max_lag": upper_lag,
                "top_lags": ranked_lags[:20],
                "all_lags": autocorrelation,
                "interpretation":
                    (
                        "Candidate periodicities only; "
                        "not proof of a clock mechanism."
                    ),
            },

            "trace": rows,

            "diagnosis": {
                "verdict": verdict,
                "information_destroyed": False,
                "observability_intermittent":
                    0 < len(window_steps) < len(rows),
                "clock_phase_clustered":
                    phase_resultant >= 0.5,
                "claims_physical_proof": False,
            },

            "malysh_debate": {
                "voice_a": {
                    "rights": "equal",
                    "position":
                        (
                            "The conserved phase distance "
                            "is the primary evidence that "
                            "the written distinction survives."
                        ),
                },
                "voice_b": {
                    "rights": "equal",
                    "position":
                        (
                            "Visibility through READ is "
                            "state-dependent and must be "
                            "tested against clock phase and "
                            "event channels."
                        ),
                },
                "winner": None,
                "state": "COMPLEMENTARY",
            },
        }

        return result

    finally:
        if temporary is not None:
            temporary.cleanup()


def print_summary(result):
    windows = result["read_windows"]
    invariants = result["invariants"]
    channels = result["channel_association"]
    diagnosis = result["diagnosis"]

    print("=" * 70)
    print("MALYSH LONG READ-WINDOW RESULT")
    print("=" * 70)

    print("Verdict:",
          diagnosis["verdict"])
    print("Samples:",
          result["model"]["samples"])
    print("Read windows:",
          windows["count"])
    print("Read-window rate:",
          f"{windows['rate']:.6f}")
    print("Phase max deviation:",
          f"{invariants['phase_max_deviation']:.16e}")
    print("Clock-phase resultant:",
          f"{windows['clock_phase_resultant']:.6f}")
    print("Clock-phase mean:",
          f"{windows['clock_phase_mean']:.6f}")

    print()
    print("Orientation active samples:",
          channels["orientation"]["active_samples"])
    print("Central-event active samples:",
          channels["central_events"]["active_samples"])
    print("D_zero point-biserial:",
          f"{channels['zero_projection']['point_biserial']:.6f}")

    print()
    print("TOP PERIOD CANDIDATES")

    for item in result["periodicity"]["top_lags"][:10]:
        print(
            f"lag={item['lag']:4d} "
            f"corr={item['correlation']:+.6f} "
            f"agreement={item['agreement']:.6f}"
        )

    print()
    print("FIRST READ WINDOWS")
    print(windows["steps"][:40])


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cycles",
        type=int,
        default=400,
    )

    parser.add_argument(
        "--max-lag",
        type=int,
        default=200,
    )

    parser.add_argument(
        "--output",
        default=(
            "runtime/reflections/"
            "read_windows_latest.json"
        ),
    )

    args = parser.parse_args()

    result = run_long_experiment(
        cycles=args.cycles,
        max_lag=args.max_lag,
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
