from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENOME = ROOT / "malysh_system" / "genome_registry.json"
OUTPUT = ROOT / "malysh_system" / "integration_queue.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def strategy(module: dict) -> str:
    role = module["role"]
    policy = module["execution_policy"]

    if role == "nervous_system":
        return "keep_as_infrastructure"

    if role == "immune_test":
        return "integrate_as_diagnostic"

    if role == "memory":
        return "integrate_as_memory_provider"

    if role == "visualizer":
        return "integrate_as_observer"

    if role == "launcher":
        return "analyze_as_composite_workflow"

    if policy == "process_candidate":
        return "certify_process_adapter"

    if policy == "adapter_required":
        return "build_api_adapter"

    return "register_as_library"


def priority(module: dict) -> int:
    role = module["role"]
    category = module["category"]

    score = 0

    if role in {"organ", "functional_organ"}:
        score += 100

    if category not in {
        "unclassified",
        "utility",
        "launcher",
    }:
        score += 50

    if module["has_main"]:
        score += 20

    if module["classes"]:
        score += 10

    return score


def main() -> None:
    genome = load(GENOME)

    discovered = [
        module
        for module in genome["modules"]
        if module["integration"] == "discovered"
    ]

    queue = []

    for module in discovered:
        queue.append({
            "id": module["id"],
            "path": module["path"],
            "category": module["category"],
            "role": module["role"],
            "strategy": strategy(module),
            "priority": priority(module),
            "has_main": module["has_main"],
            "classes": module["classes"],
            "functions": module["functions"],
            "status": "pending",
        })

    queue.sort(
        key=lambda item: (
            -item["priority"],
            item["path"],
        )
    )

    strategies = {}

    for item in queue:
        key = item["strategy"]
        strategies[key] = strategies.get(key, 0) + 1

    output = {
        "schema_version": 1,
        "system": "Malysh Integration Queue",
        "total_pending": len(queue),
        "strategies": strategies,
        "queue": queue,
    }

    OUTPUT.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 72)
    print("МАЛЫШ: ОЧЕРЕДЬ ПОЛНОЙ ИНТЕГРАЦИИ")
    print("=" * 72)
    print("Ожидают интеграции :", len(queue))
    print("-" * 72)

    for key in sorted(strategies):
        print(f"{key:32} {strategies[key]}")

    print("-" * 72)
    print("Первые кандидаты:")

    for item in queue[:15]:
        print(
            f"{item['priority']:3} "
            f"{item['strategy']:<30} "
            f"{item['path']}"
        )

    print("-" * 72)
    print("Ничего не запускалось.")
    print("Центральное состояние не изменялось.")
    print("=" * 72)


if __name__ == "__main__":
    main()
