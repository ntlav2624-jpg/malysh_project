from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from malysh_system.adapters.process_adapter import build_adapters
from malysh_system.capability_router import route
from malysh_system.executor import OrganExecutor
from malysh_system.protocols import Command, OrganResult
from malysh_system.supervisor import STATE_PATH
from malysh_system.transaction import OrganismTransaction


ROOT = Path(__file__).resolve().parent.parent


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}

    return json.loads(
        STATE_PATH.read_text(encoding="utf-8")
    )


def execute_selected(
    command: Command,
    selected: list[str],
    context: dict,
) -> list:
    production = OrganExecutor()

    production_specs = {
        str(spec["id"]): spec
        for spec in production.available_organs()
    }

    adapter_objects = {
        adapter.organ_id: adapter
        for adapter in build_adapters()
    }

    def run_one(organ_id: str) -> OrganResult:
        if organ_id in production_specs:
            return production.execute_one(
                production_specs[organ_id],
                command,
                context,
            )

        if organ_id in adapter_objects:
            return adapter_objects[organ_id].invoke(
                command=command,
                context=context,
                dry_run=False,
            )

        return OrganResult(
            organ=organ_id,
            status="unavailable",
            data={
                "category": "unknown",
                "output_tail": "",
            },
            error="Орган отсутствует в исполнительных реестрах",
        )

    workers = max(1, min(len(selected), 6))
    results: dict[str, OrganResult] = {}

    with ThreadPoolExecutor(
        max_workers=workers,
        thread_name_prefix="malysh-organ",
    ) as pool:
        futures = {
            pool.submit(run_one, organ_id): organ_id
            for organ_id in selected
        }

        for future in as_completed(futures):
            organ_id = futures[future]

            try:
                results[organ_id] = future.result()
            except BaseException as error:
                results[organ_id] = OrganResult(
                    organ=organ_id,
                    status="exception",
                    data={
                        "category": "unknown",
                        "output_tail": "",
                    },
                    error=f"{type(error).__name__}: {error}",
                )

    return [
        results[organ_id]
        for organ_id in selected
    ]


def print_results(
    routing: dict,
    results: list[OrganResult],
    state: dict | None,
    checkpoint: str | None,
) -> None:
    failed = [
        result
        for result in results
        if result.status != "ok"
    ]

    print("=" * 72)
    print("МАЛЫШ: СЕМАНТИЧЕСКИЙ ЕДИНЫЙ ОРГАНИЗМ")
    print("=" * 72)
    print("Intent       :", routing["intent"])
    print("Выбрано      :", len(routing["selected"]))
    print("Исполнено    :", len(results))
    print("Успешно      :", len(results) - len(failed))
    print("Ошибок       :", len(failed))

    if state is not None:
        print("Поколение    :", state.get("generation"))
        print("Virtual time :", state.get("virtual_time"))
        print("Состояние    :", state.get("status"))
        print("Checkpoint   :", checkpoint)

    print("-" * 72)

    for result in results:
        duration = result.data.get(
            "duration_seconds",
            0,
        )

        print(
            f"[{result.status.upper():11}] "
            f"{result.organ:<28} "
            f"{duration:>8.3f} s"
        )

        if result.error:
            print("  error:", result.error)

    print("=" * 72)


def main() -> None:
    text = " ".join(sys.argv[1:]).strip()

    if not text:
        raise SystemExit(
            'Использование: python -m '
            'malysh_system.routed_executor "запрос"'
        )

    routing = route(text)

    if routing["intent"] == "arithmetic":
        print("=" * 72)
        print("МАЛЫШ: ВСТРОЕННЫЙ АРИФМЕТИЧЕСКИЙ КОНТУР")
        print("=" * 72)
        print("Запрос    :", text)
        print("Выражение :", routing["expression"])
        print("Ответ     :", routing["result"])
        print("Органы    : специализированные органы пропущены")
        print("Транзакция: не требуется")
        print("=" * 72)
        return

    selected = routing["selected"]
    command = Command(
        text=text,
        mode="semantic",
    )

    context = load_state()
    transaction = OrganismTransaction()
    transaction.begin(command)

    try:
        results = execute_selected(
            command=command,
            selected=selected,
            context=context,
        )

        state, checkpoint = transaction.commit(
            command,
            results,
        )

    except BaseException as error:
        transaction.abort(command, error)
        raise

    print_results(
        routing=routing,
        results=results,
        state=state,
        checkpoint=checkpoint,
    )


if __name__ == "__main__":
    main()
