from __future__ import annotations

import sys

from malysh_system.capability_router import route
from malysh_system.orchestrator import Orchestrator, synthesize


def consciousness(text: str) -> dict:
    """
    Сознание:
    быстрый целевой семантический анализ запроса.
    На этом уровне органы только выбираются.
    """
    routing = route(text)

    if routing["intent"] == "arithmetic":
        return {
            "mode": "reflex",
            "intent": routing["intent"],
            "selected": ["builtin_arithmetic"],
            "answer": str(routing["result"]),
        }

    return {
        "mode": "semantic",
        "intent": routing["intent"],
        "selected": list(routing["selected"]),
        "answer": None,
    }


def subconscious(text: str) -> dict:
    """
    Подсознание:
    сохраняет прежний оркестрационный контур Малыша.

    Арифметический рефлекс наблюдается без построения
    плана всего организма. Семантические запросы
    анализируются прежним контуром в режиме PLAN.
    """
    independent_routing = route(text)

    if independent_routing["intent"] == "arithmetic":
        return {
            "plan": None,
            "mode": "reflex_observer",
            "selected": [],
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

    return {
        "plan": plan,
        "mode": "plan",
        "selected": [],
        "text": synthesize(plan),
    }


def joint(
    conscious: dict,
    subconscious_result: dict,
) -> dict:
    """
    Совместный вывод:
    синтез двух независимых ветвей.
    """
    selected = conscious.get("selected", [])

    if conscious["mode"] == "reflex":
        summary = (
            "Сознание решило запрос рефлекторно. "
            "Подсознательный контур сохранён отдельно."
        )
    else:
        summary = (
            "Сознание выбрало "
            f"{len(selected)} специализированных органов. "
            "Подсознание независимо построило свой план."
        )

    return {
        "summary": summary,
        "conscious_organs": selected,
    }


def print_report(
    text: str,
    conscious: dict,
    subconscious_result: dict,
    combined: dict,
) -> None:
    print("=" * 72)
    print("МАЛЫШ: ДВОЙНОЙ РАЗУМ")
    print("=" * 72)
    print("Запрос:", text)

    print()
    print("=== СОЗНАНИЕ ===")
    print("Intent :", conscious["intent"])
    print("Режим  :", conscious["mode"])
    print(
        "Органы :",
        ", ".join(conscious["selected"]) or "нет",
    )

    if conscious.get("answer") is not None:
        print("Ответ  :", conscious["answer"])

    print()
    print("=== ПОДСОЗНАНИЕ ===")
    print(subconscious_result["text"])

    print()
    print("=== СОВМЕСТНЫЙ ===")
    print(combined["summary"])
    print(
        "Органы сознания:",
        ", ".join(combined["conscious_organs"]) or "нет",
    )

    print()
    print("STATE_COMMIT: не выполнялся")
    print("=" * 72)


def main() -> None:
    text = " ".join(sys.argv[1:]).strip()

    if not text:
        raise SystemExit(
            'Использование: python -m '
            'malysh_system.dual_mind "запрос"'
        )

    conscious = consciousness(text)
    subconscious_result = subconscious(text)

    combined = joint(
        conscious,
        subconscious_result,
    )

    print_report(
        text,
        conscious,
        subconscious_result,
        combined,
    )


if __name__ == "__main__":
    main()
