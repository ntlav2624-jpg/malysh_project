from __future__ import annotations

import argparse
from typing import Any

from malysh_system.capability_router import route
from malysh_system.orchestrator import (
    Orchestrator,
    synthesize,
)
from malysh_system.protocols import Command, OrganResult
from malysh_system.routed_executor import (
    execute_selected,
    load_state,
)
from malysh_system.transaction import OrganismTransaction


def consciousness(text: str) -> dict[str, Any]:
    """
    Сознательный контур.

    Выполняет быстрый семантический разбор и формирует
    целевой список органов. Сам состояние не изменяет.
    """
    routing = route(text)

    if routing["intent"] == "arithmetic":
        return {
            "mode": "reflex",
            "intent": routing["intent"],
            "selected": ["builtin_arithmetic"],
            "answer": str(routing["result"]),
            "routing": routing,
        }

    return {
        "mode": "semantic",
        "intent": routing["intent"],
        "selected": list(routing["selected"]),
        "answer": None,
        "routing": routing,
    }


def subconscious(text: str) -> dict[str, Any]:
    """
    Подсознательный контур.

    Сохраняет прежний независимый Orchestrator, но всегда
    работает в PLAN. Поэтому подсознание анализирует запрос,
    не запускает органы и не делает собственный commit.
    """
    independent_routing = route(text)

    if independent_routing["intent"] == "arithmetic":
        return {
            "plan": None,
            "mode": "reflex_observer",
            "selected": [],
            "categories": [],
            "text": (
                "Режим         : REFLEX OBSERVER\n"
                "Выбрано       : 0\n"
                "Исполнено     : 0\n"
                "Наблюдение    : арифметический рефлекс\n"
                "Результат     : "
                f"{independent_routing['result']}\n"
                "Органы не пробуждались."
            ),
        }

    orchestrator = Orchestrator()

    plan = orchestrator.process(
        text=text,
        all_organs=False,
        execute=False,
    )

    categories = sorted(
        {
            item.get("data", {}).get(
                "category",
                "unclassified",
            )
            for item in plan.get("results", [])
        }
    )

    selected_names = [
        item.get("organ", "unknown")
        for item in plan.get("results", [])
    ]

    return {
        "plan": plan,
        "mode": "plan",
        "selected": selected_names,
        "categories": categories,
        "text": synthesize(plan),
    }


def joint(
    conscious: dict[str, Any],
    subconscious_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Совместный контур.

    Сознание предоставляет точные ID адаптеров.
    Подсознание предоставляет независимую проверку контуров.

    В первой исполнительной версии право запуска получают
    только ID, явно выбранные сознательным Semantic Router.
    Это не позволяет старому fallback разбудить весь организм.
    """
    if conscious["mode"] == "reflex":
        return {
            "mode": "reflex_consensus",
            "execute": False,
            "selected": [],
            "summary": (
                "Сознание вычислило арифметический результат. "
                "Подсознание подтвердило рефлекторный режим. "
                "Специализированные органы не требуются."
            ),
        }

    selected = list(
        dict.fromkeys(
            conscious.get("selected", [])
        )
    )

    categories = subconscious_result.get(
        "categories",
        [],
    )

    return {
        "mode": "semantic_consensus",
        "execute": bool(selected),
        "selected": selected,
        "subconscious_categories": categories,
        "summary": (
            "Сознание выполнило точный выбор органов. "
            "Подсознание независимо проверило смысловые "
            "контуры. Совместный контур разрешил запуск "
            f"{len(selected)} органов."
        ),
    }


def execute_joint(
    text: str,
    combined: dict[str, Any],
    execute: bool,
) -> dict[str, Any]:
    """
    Выполнение совместного решения.

    Здесь находится единственная транзакция Dual Mind:
      begin
      parallel execute_selected
      one commit

    При execute=False возвращается PLAN без мутации state.
    """
    selected = combined.get("selected", [])

    if not execute:
        return {
            "executed": False,
            "results": [],
            "state": load_state(),
            "checkpoint": None,
        }

    if not combined.get("execute"):
        return {
            "executed": False,
            "results": [],
            "state": load_state(),
            "checkpoint": None,
        }

    if not selected:
        return {
            "executed": False,
            "results": [],
            "state": load_state(),
            "checkpoint": None,
        }

    command = Command(
        text=text,
        mode="dual_mind",
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

    return {
        "executed": True,
        "results": results,
        "state": state,
        "checkpoint": checkpoint,
    }


def result_counts(
    results: list[OrganResult],
) -> tuple[int, int]:
    successful = sum(
        1
        for result in results
        if result.status == "ok"
    )

    failed = len(results) - successful
    return successful, failed


def print_consciousness(
    conscious: dict[str, Any],
    execution: dict[str, Any],
) -> None:
    print("=== СОЗНАНИЕ ===")
    print("Intent :", conscious["intent"])
    print("Режим  :", conscious["mode"])
    print(
        "Органы :",
        ", ".join(conscious["selected"]) or "нет",
    )

    if conscious.get("answer") is not None:
        print("Ответ  :", conscious["answer"])

    results = execution.get("results", [])

    if results:
        successful, failed = result_counts(results)

        print("Исполнено:", len(results))
        print("Успешно  :", successful)
        print("Ошибок   :", failed)

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


def print_subconscious(
    subconscious_result: dict[str, Any],
) -> None:
    print("=== ПОДСОЗНАНИЕ ===")
    print(subconscious_result["text"])


def print_joint(
    combined: dict[str, Any],
    execution: dict[str, Any],
) -> None:
    print("=== СОВМЕСТНЫЙ ===")
    print("Режим  :", combined["mode"])
    print(combined["summary"])

    print(
        "Итоговые органы:",
        ", ".join(combined["selected"]) or "нет",
    )

    categories = combined.get(
        "subconscious_categories",
        [],
    )

    if categories:
        print(
            "Контуры подсознания:",
            ", ".join(categories),
        )

    if execution["executed"]:
        state = execution["state"]

        print("STATE_COMMIT : выполнен один раз")
        print(
            "generation   :",
            state.get("generation"),
        )
        print(
            "virtual_time :",
            state.get("virtual_time"),
        )
        print(
            "status       :",
            state.get("status"),
        )
        print(
            "active_cycle :",
            state.get("active_cycle"),
        )
        print(
            "checkpoint   :",
            execution["checkpoint"],
        )
    else:
        print("STATE_COMMIT : не выполнялся")


def run(
    text: str,
    execute: bool = False,
) -> dict[str, Any]:
    """
    Полный цикл двойного разума.

    Всегда возвращает три логических результата:
      consciousness
      subconscious
      joint

    Физическая мутация state допускается только
    внутри execute_joint().
    """
    conscious = consciousness(text)
    subconscious_result = subconscious(text)

    combined = joint(
        conscious,
        subconscious_result,
    )

    execution = execute_joint(
        text=text,
        combined=combined,
        execute=execute,
    )

    print("=" * 72)
    print("МАЛЫШ: ДВОЙНОЙ РАЗУМ")
    print("=" * 72)
    print("Запрос:", text)
    print()

    print_consciousness(
        conscious,
        execution,
    )

    print()
    print_subconscious(
        subconscious_result,
    )

    print()
    print_joint(
        combined,
        execution,
    )

    print("=" * 72)

    return {
        "consciousness": conscious,
        "subconscious": subconscious_result,
        "joint": combined,
        "execution": execution,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="malysh-dual-mind",
        description=(
            "Сознание, подсознание и совместный "
            "контур Малыша"
        ),
    )

    parser.add_argument(
        "text",
        help="Запрос Малышу",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Выполнить совместно выбранные органы "
            "с одним STATE_COMMIT"
        ),
    )

    return parser


def main() -> None:
    arguments = build_parser().parse_args()

    run(
        text=arguments.text,
        execute=arguments.execute,
    )


if __name__ == "__main__":
    main()
