from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

GENOME = ROOT / "malysh_system" / "genome_registry.json"
QUEUE = ROOT / "malysh_system" / "integration_queue.json"
STATE = ROOT / "runtime" / "state.json"

OUTPUT = ROOT / "malysh_system" / "completion_plan.json"


TARGET = 52


def load(path: Path) -> dict:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def main() -> None:
    genome = load(GENOME)
    queue = load(QUEUE)
    state = load(STATE)

    modules = genome["modules"]
    pending = queue["queue"]

    by_integration = Counter(
        item["integration"]
        for item in modules
    )

    by_strategy = Counter(
        item["strategy"]
        for item in pending
    )

    pending_ids = {
        item["id"]
        for item in pending
    }

    discovered_ids = {
        item["id"]
        for item in modules
        if item["integration"] == "discovered"
    }

    missing_from_queue = sorted(
        discovered_ids - pending_ids
    )

    stale_queue = sorted(
        pending_ids - discovered_ids
    )

    duplicate_ids = sorted(
        item
        for item, count in Counter(
            module["id"]
            for module in modules
        ).items()
        if count > 1
    )

    phases = {
        "phase_1_organs": [],
        "phase_2_api": [],
        "phase_3_observers": [],
        "phase_4_workflows": [],
        "phase_5_libraries": [],
        "phase_6_diagnostics": [],
        "phase_7_infrastructure": [],
        "phase_8_memory": [],
    }

    mapping = {
        "certify_process_adapter":
            "phase_1_organs",
        "build_api_adapter":
            "phase_2_api",
        "integrate_as_observer":
            "phase_3_observers",
        "analyze_as_composite_workflow":
            "phase_4_workflows",
        "register_as_library":
            "phase_5_libraries",
        "integrate_as_diagnostic":
            "phase_6_diagnostics",
        "keep_as_infrastructure":
            "phase_7_infrastructure",
        "integrate_as_memory_provider":
            "phase_8_memory",
    }

    for item in sorted(
        pending,
        key=lambda x: (
            -int(x.get("priority", 0)),
            x["id"],
        ),
    ):
        strategy = item["strategy"]

        phase = mapping.get(strategy)

        if phase is None:
            raise SystemExit(
                "UNKNOWN STRATEGY: "
                f"{strategy}"
            )

        phases[phase].append(
            {
                "id": item["id"],
                "path": item["path"],
                "role": item["role"],
                "category": item["category"],
                "strategy": strategy,
                "priority": item["priority"],
            }
        )

    report = {
        "schema_version": 1,
        "system": "Malysh Completion Plan",
        "target": TARGET,
        "current": {
            "total": len(modules),
            "production": by_integration["production"],
            "adapted": by_integration["adapted"],
            "discovered": by_integration["discovered"],
        },
        "runtime_guard": {
            "generation": state.get("generation"),
            "virtual_time": state.get("virtual_time"),
            "status": state.get("status"),
            "active_cycle": state.get("active_cycle"),
        },
        "queue": {
            "pending": len(pending),
            "strategies": dict(
                sorted(by_strategy.items())
            ),
        },
        "integrity": {
            "genome_is_52": len(modules) == TARGET,
            "queue_matches_discovered": (
                not missing_from_queue
                and not stale_queue
            ),
            "duplicate_genome_ids": duplicate_ids,
            "missing_from_queue": missing_from_queue,
            "stale_queue_entries": stale_queue,
        },
        "phases": phases,
    }

    OUTPUT.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("=" * 72)
    print("МАЛЫШ: ПЛАН ЗАВЕРШЕНИЯ 52/52")
    print("=" * 72)

    print("Genome total :", len(modules))
    print(
        "Production   :",
        by_integration["production"],
    )
    print(
        "Adapted      :",
        by_integration["adapted"],
    )
    print(
        "Pending      :",
        by_integration["discovered"],
    )

    print()
    print("=== INTEGRITY ===")

    print(
        "Genome 52    :",
        "OK"
        if len(modules) == TARGET
        else "FAIL",
    )

    print(
        "Queue match  :",
        "OK"
        if (
            not missing_from_queue
            and not stale_queue
        )
        else "FAIL",
    )

    print(
        "Duplicate IDs:",
        len(duplicate_ids),
    )

    print()
    print("=== COMPLETION PHASES ===")

    for phase, items in phases.items():
        print(
            f"{phase:<26}: {len(items)}"
        )

        for item in items:
            print(
                "   "
                f"{item['priority']:>3} "
                f"{item['id']}"
            )

    print()
    print("=== STATE GUARD ===")

    print(
        "generation  :",
        state.get("generation"),
    )
    print(
        "virtual_time:",
        state.get("virtual_time"),
    )
    print(
        "status      :",
        state.get("status"),
    )
    print(
        "active_cycle:",
        state.get("active_cycle"),
    )

    assert len(modules) == TARGET
    assert not duplicate_ids
    assert not missing_from_queue
    assert not stale_queue
    assert len(pending) == by_integration["discovered"]

    assert state.get("status") == "ready"
    assert state.get("active_cycle") is None

    print()
    print("COMPLETION PLAN: VALID")
    print(
        "STATE_COMMIT: не выполнялся"
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
