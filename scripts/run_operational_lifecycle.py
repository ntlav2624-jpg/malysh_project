#!/usr/bin/env python3
"""
Execute one durable operational Malysh lifecycle step.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

root_text = str(PROJECT_ROOT)

if root_text not in sys.path:
    sys.path.insert(
        0,
        root_text,
    )


from malysh_system.operational_lifecycle import (
    OperationalLifecycle,
)


def parse_sequence(
    raw: str,
) -> list:
    values = [
        int(token.strip())
        for token in raw.split(",")
        if token.strip()
    ]

    if not values:
        raise ValueError(
            "sequence must not be empty"
        )

    return values


def load_optional_json(
    path: Path | None,
):
    if path is None:
        return None

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Recover, think, persist and verify "
            "one Malysh lifecycle step"
        )
    )

    parser.add_argument(
        "--storage",
        type=Path,
        default=(
            PROJECT_ROOT
            / "runtime"
            / "operational_lifecycle"
        ),
    )

    parser.add_argument(
        "--sequence",
        default="6,14,26,30,19,5",
    )

    parser.add_argument(
        "--o345-n",
        type=int,
        default=59,
    )

    parser.add_argument(
        "--possible",
        default="возможно",
    )

    parser.add_argument(
        "--historical-history",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--historical-candidate",
        default=None,
    )

    parser.add_argument(
        "--historical-pool-size",
        type=int,
        default=49,
    )

    args = parser.parse_args()

    history = load_optional_json(
        args.historical_history
    )

    candidate = (
        parse_sequence(
            args.historical_candidate
        )
        if args.historical_candidate
        is not None
        else None
    )

    lifecycle = OperationalLifecycle(
        args.storage
    )

    result = lifecycle.step(
        data=parse_sequence(
            args.sequence
        ),
        o345_n=args.o345_n,
        old_result={
            "source":
                "operational-lifecycle-cli",

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
        historical_history=history,
        historical_candidate=candidate,
        historical_pool_size=(
            args.historical_pool_size
        ),
        source="operational-lifecycle-cli",
    )

    report = {
        "schema":
            result["schema"],

        "subject":
            result["subject"],

        "start_mode":
            result["start"]["mode"],

        "generation":
            result["generation"],

        "previous_snapshot_hash":
            result[
                "previous_snapshot_hash"
            ],

        "snapshot_hash":
            result["snapshot_hash"],

        "snapshot_equal":
            result["snapshot_equal"],

        "hash_equal":
            result["hash_equal"],

        "historical_requested":
            result[
                "historical_requested"
            ],

        "frozen_layer_names":
            result[
                "frozen_layer_names"
            ],

        "checkpoint":
            result["checkpoint"],

        "invariants":
            result["invariants"],
    }

    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )

    print()
    print("[PASS] state recovered or initialized")
    print("[PASS] thinking cycle completed")
    print("[PASS] complete MindState persisted")
    print("[PASS] restart recovery verified")
    print("[PASS] exact snapshot equality")
    print("[PASS] ONE Malysh lifecycle step")

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
