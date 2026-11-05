#!/usr/bin/env python3
"""
Operational entry point for all currently integrated Malysh contours.

Executed contours:

    O345
    O3 / O4 / O5
    KMBP
    FullReflections
    Human Layer
    Swarm
    Omni
    InterLayer observers
    JointChoice

The runner performs one complete thought cycle, validates every
published invariant and writes an atomic JSON runtime snapshot.

This runner does not authorize external execution or transaction
commit. JointChoice remains thought-level deliberation.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

# ------------------------------------------------------------
# Project import root
#
# When this file is executed directly as:
#
#     python3 scripts/run_all_contours.py
#
# Python places the scripts/ directory at sys.path[0].
# The repository root therefore has to be made available
# explicitly before importing malysh_system.
# ------------------------------------------------------------

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

project_root_text = str(
    PROJECT_ROOT
)

if project_root_text not in sys.path:
    sys.path.insert(
        0,
        project_root_text,
    )

from malysh_system.thinking_cycle import (
    run_thinking_cycle,
)


DEFAULT_SEQUENCE = [
    6,
    14,
    26,
    30,
    19,
    5,
]

DEFAULT_O345_N = 59


def parse_sequence(
    raw: str,
) -> list:
    values = []

    for token in raw.split(","):
        token = token.strip()

        if not token:
            continue

        values.append(
            int(token)
        )

    if not values:
        raise ValueError(
            "sequence must contain at least one integer"
        )

    if any(value < 0 for value in values):
        raise ValueError(
            "sequence values must be non-negative"
        )

    return values


def stable_json(
    value: Any,
) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def digest(
    value: Any,
) -> str:
    return hashlib.sha256(
        stable_json(value).encode(
            "utf-8"
        )
    ).hexdigest()


def verify_result(
    result: dict[str, Any],
) -> dict[str, Any]:
    """
    Verify every required working contour.
    """

    failures = []

    cycle_invariants = result.get(
        "invariants",
        {},
    )

    for name, passed in (
        cycle_invariants.items()
    ):
        if passed is not True:
            failures.append(
                "cycle invariant: " + name
            )

    required_observations = {
        "O3",
        "O4",
        "O5",
        "KMBP",
        "FullReflections",
        "HumanLayer",
        "Swarm",
        "Omni",
    }

    required_reflections = {
        "O345",
        "KMBP",
        "Swarm",
        "Omni",
        "InterLayerObservers",
        "JointChoice",
    }

    mind = result.get(
        "mind",
        {},
    )

    observations = mind.get(
        "observations",
        {},
    )

    reflections = mind.get(
        "reflections",
        {},
    )

    missing_observations = sorted(
        required_observations.difference(
            observations
        )
    )

    missing_reflections = sorted(
        required_reflections.difference(
            reflections
        )
    )

    if missing_observations:
        failures.append(
            "missing observations: "
            + ", ".join(
                missing_observations
            )
        )

    if missing_reflections:
        failures.append(
            "missing reflections: "
            + ", ".join(
                missing_reflections
            )
        )

    organ_checks = {
        "O345":
            (
                result.get(
                    "o345",
                    {},
                ).get(
                    "invariant_ok"
                )
                is True
            ),

        "KMBP":
            (
                result.get(
                    "kmbp",
                    {},
                ).get(
                    "status"
                )
                ==
                "ok"
                and
                result.get(
                    "kmbp",
                    {},
                ).get(
                    "data",
                    {},
                ).get(
                    "invariant_ok"
                )
                is True
            ),

        "Swarm":
            (
                result.get(
                    "swarm",
                    {},
                ).get(
                    "status"
                )
                ==
                "ok"
                and
                result.get(
                    "swarm",
                    {},
                ).get(
                    "data",
                    {},
                ).get(
                    "invariant_ok"
                )
                is True
            ),

        "Omni":
            (
                result.get(
                    "omni",
                    {},
                ).get(
                    "status"
                )
                ==
                "ok"
                and
                result.get(
                    "omni",
                    {},
                ).get(
                    "data",
                    {},
                ).get(
                    "invariant_ok"
                )
                is True
            ),

        "InterLayer":
            (
                result.get(
                    "interlayer",
                    {},
                ).get(
                    "status"
                )
                ==
                "ok"
                and
                result.get(
                    "interlayer",
                    {},
                ).get(
                    "data",
                    {},
                ).get(
                    "invariant_ok"
                )
                is True
            ),

        "JointChoice":
            (
                result.get(
                    "joint_choice",
                    {},
                ).get(
                    "status"
                )
                ==
                "ok"
                and
                result.get(
                    "joint_choice",
                    {},
                ).get(
                    "data",
                    {},
                ).get(
                    "invariant_ok"
                )
                is True
            ),
    }

    for organ, passed in organ_checks.items():
        if not passed:
            failures.append(
                "organ failed: " + organ
            )

    joint = (
        result.get(
            "joint_choice",
            {},
        ).get(
            "data",
            {},
        )
    )

    deliberation = joint.get(
        "deliberation",
        {},
    )

    safety_checks = {
        "one_subject":
            result.get("subject")
            ==
            "Malysh",

        "canonical_present":
            bool(
                mind.get(
                    "canonical"
                )
            ),

        "joint_no_winner":
            deliberation.get(
                "winner"
            )
            is None,

        "execution_not_authorized":
            deliberation.get(
                "execution_authorized"
            )
            is False,

        "transaction_not_authorized":
            deliberation.get(
                "transaction_authorized"
            )
            is False,

        "majority_not_used":
            deliberation.get(
                "majority_vote_used"
            )
            is False,

        "vote_count_not_used":
            deliberation.get(
                "vote_count_used"
            )
            is False,
    }

    for name, passed in (
        safety_checks.items()
    ):
        if not passed:
            failures.append(
                "safety check: " + name
            )

    interlayer = (
        result.get(
            "interlayer",
            {},
        ).get(
            "data",
            {},
        )
    )

    frozen_layers = interlayer.get(
        "frozen_layer_names",
        [],
    )

    interlayer_keys = sorted(
        name
        for name in reflections
        if name.startswith(
            "InterLayer:"
        )
    )

    if (
        len(interlayer_keys)
        !=
        interlayer.get(
            "observer_count"
        )
    ):
        failures.append(
            "inter-layer reflection count mismatch"
        )

    report = {
        "ok":
            not failures,

        "failures":
            failures,

        "organ_checks":
            organ_checks,

        "safety_checks":
            safety_checks,

        "cycle_invariants":
            cycle_invariants,

        "required_observations":
            sorted(
                required_observations
            ),

        "required_reflections":
            sorted(
                required_reflections
            ),

        "actual_observations":
            sorted(
                observations
            ),

        "actual_reflections":
            sorted(
                reflections
            ),

        "frozen_layers":
            frozen_layers,

        "interlayer_reflections":
            interlayer_keys,
    }

    return report


def build_runtime_record(
    result: dict[str, Any],
    verification: dict[str, Any],
) -> dict[str, Any]:
    joint = (
        result["joint_choice"]["data"]
    )

    return {
        "schema":
            "malysh.operational-run.v1",

        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "subject":
            result["subject"],

        "input":
            result["input"],

        "o345_n":
            result["o345_n"],

        "canonical":
            result["mind"]["canonical"],

        "organs": {
            "O345":
                "ok",

            "O3":
                "ok",

            "O4":
                "ok",

            "O5":
                "ok",

            "KMBP":
                result["kmbp"]["status"],

            "FullReflections":
                "ok",

            "HumanLayer":
                "ok",

            "Swarm":
                result["swarm"]["status"],

            "Omni":
                result["omni"]["status"],

            "InterLayer":
                result["interlayer"]["status"],

            "JointChoice":
                result["joint_choice"]["status"],
        },

        "joint_choice": {
            "state":
                joint[
                    "deliberation"
                ][
                    "state"
                ],

            "selected_for_reasoning":
                joint[
                    "deliberation"
                ][
                    "selected_for_reasoning"
                ],

            "winner":
                joint[
                    "deliberation"
                ][
                    "winner"
                ],

            "execution_authorized":
                joint[
                    "deliberation"
                ][
                    "execution_authorized"
                ],

            "transaction_authorized":
                joint[
                    "deliberation"
                ][
                    "transaction_authorized"
                ],

            "contradiction_count":
                len(
                    joint[
                        "contradictions"
                    ]
                ),

            "unresolved_count":
                len(
                    joint[
                        "unresolved"
                    ]
                ),

            "support_source_count":
                len(
                    joint[
                        "support"
                    ]
                ),
        },

        "verification":
            verification,

        "result_digest":
            digest(result),
    }


def atomic_write_json(
    path: Path,
    value: Any,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_name(
        path.name + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            value,
            file,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=str,
        )

        file.write("\n")
        file.flush()
        os.fsync(
            file.fileno()
        )

    os.replace(
        temporary,
        path,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run all integrated Malysh contours"
        )
    )

    parser.add_argument(
        "--sequence",
        default=",".join(
            str(value)
            for value in DEFAULT_SEQUENCE
        ),
    )

    parser.add_argument(
        "--o345-n",
        type=int,
        default=DEFAULT_O345_N,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "runtime"
        )
        / "working_cycle"
        / "latest.json",
    )

    parser.add_argument(
        "--old-source",
        default="operational-runner",
    )

    parser.add_argument(
        "--possible",
        default="возможно",
    )

    args = parser.parse_args()

    sequence = parse_sequence(
        args.sequence
    )

    if args.o345_n < 0:
        raise ValueError(
            "o345-n must be non-negative"
        )

    result = run_thinking_cycle(
        data=sequence,
        o345_n=args.o345_n,
        old_result={
            "source":
                args.old_source,

            "preserved":
                True,
        },
        unresolved={
            "status":
                "hypothesis",

            "text":
                args.possible,

            "revisable":
                True,

            "mixed_with_recovered_memory":
                False,
        },
    )

    verification = verify_result(
        result
    )

    record = build_runtime_record(
        result,
        verification,
    )

    atomic_write_json(
        args.output,
        record,
    )

    print(
        json.dumps(
            record,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )

    if not verification["ok"]:
        print(
            "[FAIL] operational verification",
            file=sys.stderr,
        )

        for failure in (
            verification["failures"]
        ):
            print(
                " - " + failure,
                file=sys.stderr,
            )

        return 1

    print()
    print("[PASS] ALL CONTOURS OPERATIONAL")
    print(
        "[PASS] runtime snapshot:",
        args.output,
    )
    print(
        "[PASS] digest:",
        record["result_digest"],
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
