#!/usr/bin/env python3
"""
Run one complete thinking cycle, persist the full MindState, recover it
as a new object, and prove equality across the restart boundary.
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

project_root_text = str(
    PROJECT_ROOT
)

if project_root_text not in sys.path:
    sys.path.insert(
        0,
        project_root_text,
    )


from malysh_system.mind_persistence import (
    MindPersistence,
)
from malysh_system.thinking_cycle import (
    run_thinking_cycle,
)
from malysh_system.unified_mind import (
    MindState,
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


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--storage",
        type=Path,
        default=(
            PROJECT_ROOT
            / "runtime"
            / "mind_persistence"
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

    arguments = parser.parse_args()

    sequence = parse_sequence(
        arguments.sequence
    )

    mind = MindState()

    cycle = run_thinking_cycle(
        data=sequence,
        o345_n=arguments.o345_n,
        old_result={
            "source":
                "persistent-operational-cycle",

            "preserved":
                True,
        },
        unresolved={
            "status":
                "hypothesis",

            "text":
                "возможно",

            "revisable":
                True,
        },
        mind=mind,
    )

    if not all(
        cycle["invariants"].values()
    ):
        raise RuntimeError(
            "thinking-cycle invariant failed"
        )

    before = mind.snapshot()

    persistence = MindPersistence(
        arguments.storage
    )

    committed = persistence.persist(
        mind,
        source=(
            "persistent-operational-cycle"
        ),
    )

    recovered, metadata = (
        persistence.recover()
    )

    after = recovered.snapshot()

    equal = before == after

    report = {
        "schema":
            "malysh.persistence-run.v1",

        "subject":
            recovered.subject,

        "generation":
            committed["generation"],

        "snapshot_hash":
            committed["snapshot_hash"],

        "recovered_hash":
            metadata["snapshot_hash"],

        "snapshot_equal":
            equal,

        "mind_invariant":
            recovered.invariant(),

        "canonical":
            after["canonical"],

        "observation_count":
            len(
                after["observations"]
            ),

        "reflection_count":
            len(
                after["reflections"]
            ),

        "experience_count":
            len(
                after["experience"]
            ),

        "main_preserved":
            (
                after["main"]
                ==
                before["main"]
            ),

        "possible_preserved":
            (
                after["possible"]
                ==
                before["possible"]
            ),

        "checkpoint":
            committed["checkpoint"],

        "wal_event_types":
            persistence.inspect()[
                "wal_event_types"
            ],
    }

    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )

    if not (
        equal
        and
        recovered.invariant()
        and
        report["main_preserved"]
        and
        report["possible_preserved"]
    ):
        return 1

    print()
    print("[PASS] S_t persisted")
    print("[PASS] restart boundary simulated")
    print("[PASS] S_t recovered")
    print("[PASS] complete snapshot equality")
    print("[PASS] ONE Malysh")

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
