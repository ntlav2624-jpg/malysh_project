#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import json
from pathlib import Path

from malysh_system.orchestrator import Orchestrator

WIDTH = 110
STATE = Path("runtime/state.json")

BASE_TASK = """
Рассчитать состояние №82 по имеющейся исторической памяти.

Работай как актуальный Малыш, единый организм.
Используй доступные органы, общую память, прежний опыт,
наблюдателей, Dual Mind и Human Layer.

Нужен итоговый числовой результат:

MAIN: 5 уникальных целых чисел 1..50
EURO: 2 уникальных целых числа 1..12

Покажи результаты участвующих контуров и векторов.
Не подменяй вычисление заранее заданным итогом.
"""

TASK_NO_CHIRALITY = BASE_TASK + """

=== ВЕТВЬ A: БЕЗ ХИРАЛЬНОСТИ ===

Хиральность, chirality, chiral, mirror и reflected
НЕ должны участвовать в формировании этой ветви.

Если хиральный контур что-либо обнаружит,
разрешается показать это только как отдельное наблюдение.

influence_on_answer = false
decision_authority = false

Сформируй окончательный MAIN + EURO без его влияния.
"""

TASK_WITH_CHIRALITY = BASE_TASK + """

=== ВЕТВЬ B: С ХИРАЛЬНОСТЬЮ ===

Используй штатные доступные хиральные, chirality/chiral,
mirror/reflected контуры вместе с остальными механизмами.

Хиральный результат показать отдельно.
Его вклад разрешено учитывать в итоговом выборе.

Сформируй окончательный MAIN + EURO.
"""


def snapshot():
    if STATE.exists():
        return STATE.read_bytes()
    return None


def restore(data):
    if data is None:
        if STATE.exists():
            STATE.unlink()
        return

    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_bytes(data)


def short(value, limit=500):
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False)

    text = " ".join(text.split())

    if len(text) > limit:
        return text[:limit] + "..."

    return text


def show(title, plan):

    print()
    print("=" * WIDTH)
    print(" МАЛЫШ:", title)
    print("=" * WIDTH)

    print(
        " Поколение :",
        plan.get("organism_generation")
    )

    print(
        " Состояние :",
        plan.get("organism_status")
    )

    print(
        " Выбрано органов :",
        plan.get("selected_organs")
    )

    print(
        " Исполнено       :",
        plan.get("executed_organs")
    )

    print(
        " Checkpoint      :",
        plan.get("checkpoint")
    )

    print("-" * WIDTH)

    for i, item in enumerate(
        plan.get("results", []),
        1
    ):

        print(
            f" [{i:02d}] "
            f"{item.get('organ')} "
            f"| status={item.get('status')}"
        )

        data = item.get("data") or {}

        interesting = [
            "category",
            "mode",
            "signal_class",
            "strategy",
            "prediction",
            "forecast",
            "main",
            "euro",
            "answer",
            "logical",
            "possible",
            "observations",
            "output_tail",
        ]

        shown = False

        for key in interesting:

            value = data.get(key)

            if value not in [
                None,
                "",
                [],
                {}
            ]:

                print(
                    f"      {key:<14}: "
                    f"{short(value)}"
                )

                shown = True

        if not shown and data:
            print(
                "      DATA:",
                short(data)
            )

        error = item.get("error")

        if error:
            print(
                "      ERROR:",
                short(error)
            )

        print(
            " " + "─" * (WIDTH - 2)
        )


def run_branch(task):

    organism = Orchestrator()

    return organism.process(
        text=task,
        all_organs=True,
        execute=True,
    )


def main():

    original = snapshot()

    reports = {}

    try:

        restore(original)

        no_chiral = run_branch(
            TASK_NO_CHIRALITY
        )

        reports[
            "WITHOUT_CHIRALITY"
        ] = copy.deepcopy(no_chiral)

        show(
            "ВЕТВЬ A / БЕЗ ХИРАЛЬНОСТИ",
            no_chiral
        )

        restore(original)

        with_chiral = run_branch(
            TASK_WITH_CHIRALITY
        )

        reports[
            "WITH_CHIRALITY"
        ] = copy.deepcopy(with_chiral)

        show(
            "ВЕТВЬ B / С ХИРАЛЬНОСТЬЮ",
            with_chiral
        )

    finally:

        restore(original)

    print()
    print("=" * WIDTH)
    print(
        " СРАВНЕНИЕ: ХИРАЛЬНОСТЬ OFF / ON"
    )
    print("=" * WIDTH)

    print(
        " A = без хиральности"
    )

    print(
        " B = с хиральностью"
    )

    print(
        " Обе ветви стартовали "
        "из одного runtime/state.json"
    )

    print(
        " Рабочее состояние восстановлено "
        "после эксперимента"
    )

    outfile = Path(
        "malysh_chirality_compare_82.json"
    )

    outfile.write_text(
        json.dumps(
            reports,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print(
        " Полный JSON:",
        outfile
    )

    print("=" * WIDTH)


if __name__ == "__main__":
    main()
