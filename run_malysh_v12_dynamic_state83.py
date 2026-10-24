#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parent
INTERFACE = PROJECT / "run_v12_real_chirality_interface.py"
DYNAMIC_MODULE = PROJECT / "dynamic_experts_state83.py"

OUTPUT_JSON = PROJECT / "malysh_v12_chirality_result_83.json"

FACT_RAW = "5.16.32.34.38.8.9"
FACT_MAIN = [5, 16, 32, 34, 38]
FACT_EURO = [8, 9]

EXPECTED_OLD_STATES = 81
EXPECTED_NEW_STATES = 82
EXPECTED_VALUES = 574
TARGET_STATE = 83


def normalize_draw(parsed):
    if isinstance(parsed, dict):
        main = (
            parsed.get("main")
            or parsed.get("numbers")
            or parsed.get("primary")
        )

        euro = (
            parsed.get("euro")
            or parsed.get("stars")
            or parsed.get("secondary")
        )

        if main is not None and euro is not None:
            return (
                [int(value) for value in main],
                [int(value) for value in euro],
            )

    if isinstance(parsed, (list, tuple)):
        if len(parsed) == 7:
            values = [int(value) for value in parsed]

            return (
                values[:5],
                values[5:7],
            )

        if len(parsed) == 2:
            main, euro = parsed

            if (
                isinstance(main, (list, tuple))
                and isinstance(euro, (list, tuple))
            ):
                return (
                    [int(value) for value in main],
                    [int(value) for value in euro],
                )

    raise ValueError(
        "Неизвестный формат parse_draw: "
        + repr(parsed)
    )


def validate_state(main, euro, index):
    if len(main) != 5:
        raise RuntimeError(
            "Состояние "
            + str(index)
            + ": MAIN содержит не 5 значений"
        )

    if len(euro) != 2:
        raise RuntimeError(
            "Состояние "
            + str(index)
            + ": EURO содержит не 2 значения"
        )

    if len(set(main)) != 5:
        raise RuntimeError(
            "Состояние "
            + str(index)
            + ": MAIN содержит дубли"
        )

    if len(set(euro)) != 2:
        raise RuntimeError(
            "Состояние "
            + str(index)
            + ": EURO содержит дубли"
        )

    if not all(1 <= value <= 50 for value in main):
        raise RuntimeError(
            "Состояние "
            + str(index)
            + ": MAIN вышел за диапазон 1..50"
        )

    if not all(1 <= value <= 12 for value in euro):
        raise RuntimeError(
            "Состояние "
            + str(index)
            + ": EURO вышел за диапазон 1..12"
        )


def load_and_extend_history(state_source):
    raw_draws = list(state_source.RAW_DRAWS)
    parse_draw = state_source.parse_draw

    parsed_fact = parse_draw(FACT_RAW)
    fact_main, fact_euro = normalize_draw(parsed_fact)

    if fact_main != FACT_MAIN:
        raise RuntimeError(
            "parse_draw неверно разобрал MAIN факта №82: "
            + repr(fact_main)
        )

    if fact_euro != FACT_EURO:
        raise RuntimeError(
            "parse_draw неверно разобрал EURO факта №82: "
            + repr(fact_euro)
        )

    if len(raw_draws) == EXPECTED_OLD_STATES:
        raw_draws.append(FACT_RAW)
        fact_added = True

    elif len(raw_draws) == EXPECTED_NEW_STATES:
        last_main, last_euro = normalize_draw(
            parse_draw(raw_draws[-1])
        )

        if (
            last_main != FACT_MAIN
            or last_euro != FACT_EURO
        ):
            raise RuntimeError(
                "В истории уже 82 состояния, но последнее "
                "не является фактом №82"
            )

        fact_added = False

    else:
        raise RuntimeError(
            "Ожидалась история из 81 или 82 состояний, "
            "получено "
            + str(len(raw_draws))
        )

    history = []

    for index, raw in enumerate(raw_draws, start=1):
        main, euro = normalize_draw(parse_draw(raw))

        validate_state(
            main,
            euro,
            index,
        )

        history.append((main, euro))

    total_values = sum(
        len(main) + len(euro)
        for main, euro in history
    )

    if len(history) != EXPECTED_NEW_STATES:
        raise RuntimeError(
            "После подготовки ожидалось 82 состояния, "
            "получено "
            + str(len(history))
        )

    if total_values != EXPECTED_VALUES:
        raise RuntimeError(
            "После подготовки ожидалось 574 значения, "
            "получено "
            + str(total_values)
        )

    return {
        "raw_draws": raw_draws,
        "history": history,
        "parse_draw": parse_draw,
        "total_values": total_values,
        "fact_added": fact_added,
    }


def install_dynamic_experts(
    expert_master,
    history,
):
    import dynamic_experts_state83

    vectors, changed_count = (
        dynamic_experts_state83.install(
            expert_master,
            history,
        )
    )

    if len(vectors) != 18:
        raise RuntimeError(
            "Динамический слой вернул "
            + str(len(vectors))
            + " экспертов вместо 18"
        )

    if changed_count <= 0:
        raise RuntimeError(
            "Ни один эксперт не изменился относительно №82"
        )

    for index, vector in enumerate(
        vectors,
        start=1,
    ):
        if len(vector) != 5:
            raise RuntimeError(
                "V"
                + str(index)
                + " вернул не 5 значений"
            )

        if len(set(vector)) != 5:
            raise RuntimeError(
                "V"
                + str(index)
                + " содержит дубли"
            )

        if not all(
            1 <= value <= 50
            for value in vector
        ):
            raise RuntimeError(
                "V"
                + str(index)
                + " вышел за диапазон 1..50"
            )

    return vectors, changed_count


def adapt_interface(source):
    source = source.replace(
        "malysh_v12_chirality_result_82.json",
        "malysh_v12_chirality_result_83.json",
    )

    source = source.replace(
        '"target_state": 82',
        '"target_state": 83',
    )

    source = source.replace(
        "'target_state': 82",
        "'target_state': 83",
    )

    source = source.replace(
        "№82",
        "№83",
    )

    return source


def validate_json(dynamic_vectors):
    if not OUTPUT_JSON.is_file():
        raise RuntimeError(
            "Итоговый JSON №83 не создан"
        )

    data = json.loads(
        OUTPUT_JSON.read_text(encoding="utf-8")
    )

    if data.get("target_state") != TARGET_STATE:
        raise RuntimeError(
            "JSON: target_state не равен 83"
        )

    if (
        data.get("historical_states")
        != EXPECTED_NEW_STATES
    ):
        raise RuntimeError(
            "JSON: historical_states не равен 82"
        )

    if data.get("total_values") != EXPECTED_VALUES:
        raise RuntimeError(
            "JSON: total_values не равен 574"
        )

    records = data.get("vectors", [])

    if len(records) != 18:
        raise RuntimeError(
            "JSON: число векторов не равно 18"
        )

    json_source_vectors = []

    for record in records:
        source = record.get("source", {})
        main = source.get("main")

        if main is not None:
            json_source_vectors.append(main)

    if len(json_source_vectors) == 18:
        mismatches = []

        for index, (
            expected,
            actual,
        ) in enumerate(
            zip(
                dynamic_vectors,
                json_source_vectors,
            ),
            start=1,
        ):
            if expected != actual:
                mismatches.append(index)

        if mismatches:
            raise RuntimeError(
                "JSON не получил динамические векторы V: "
                + repr(mismatches)
            )

    return data


def main():
    if not INTERFACE.is_file():
        raise FileNotFoundError(
            "Не найден полный интерфейс: "
            + str(INTERFACE)
        )

    if not DYNAMIC_MODULE.is_file():
        raise FileNotFoundError(
            "Не найден динамический модуль: "
            + str(DYNAMIC_MODULE)
        )

    sys.path.insert(0, str(PROJECT))

    import run_state82_no_mirror as state_source
    import run_chiral_v12_full_master as expert_master

    prepared = load_and_extend_history(
        state_source
    )

    raw_draws = prepared["raw_draws"]
    history = prepared["history"]
    parse_draw = prepared["parse_draw"]

    # Синхронизация истории во всех импортируемых слоях.
    state_source.RAW_DRAWS = raw_draws
    state_source.parse_draw = parse_draw

    expert_master.RAW_DRAWS = raw_draws
    expert_master.parse_draw = parse_draw

    print("=" * 110)
    print(" ПОДГОТОВКА ДИНАМИЧЕСКОГО РАСЧЁТА №83")
    print("=" * 110)
    print(
        " [✓] Исторических состояний   : "
        + str(len(history))
    )
    print(
        " [✓] Всего входных значений   : "
        + str(prepared["total_values"])
    )
    print(
        " [✓] Последний MAIN           : "
        + repr(history[-1][0])
    )
    print(
        " [✓] Последний EURO           : "
        + repr(history[-1][1])
    )
    print(
        " [✓] Факт добавлен сейчас     : "
        + (
            "ДА"
            if prepared["fact_added"]
            else "НЕТ"
        )
    )
    print(
        " [✓] Целевое состояние        : №83"
    )
    print("=" * 110)
    print()

    dynamic_vectors, changed_count = (
        install_dynamic_experts(
            expert_master,
            history,
        )
    )

    print("=" * 110)
    print(" ДИНАМИЧЕСКИЕ ЭКСПЕРТЫ №83")
    print("=" * 110)
    print(
        " [✓] Пересчитано экспертов    : "
        + str(len(dynamic_vectors))
    )
    print(
        " [✓] Изменено против №82      : "
        + str(changed_count)
        + "/18"
    )

    for index, vector in enumerate(
        dynamic_vectors,
        start=1,
    ):
        print(
            " [V"
            + str(index)
            + "] MAIN №83 : "
            + repr(vector)
        )

    print("=" * 110)
    print()

    if OUTPUT_JSON.exists():
        OUTPUT_JSON.unlink()

    source = INTERFACE.read_text(
        encoding="utf-8"
    )

    runtime_source = adapt_interface(source)

    if (
        "malysh_v12_chirality_result_83.json"
        not in runtime_source
    ):
        raise RuntimeError(
            "Не удалось адаптировать имя JSON №83"
        )

    if '"target_state": 83' not in runtime_source:
        raise RuntimeError(
            "Не удалось адаптировать target_state"
        )

    # Важно: интерфейс повторно выполнит import
    # из уже загруженного и изменённого expert_master.
    namespace = {
        "__name__": "__main__",
        "__file__": str(INTERFACE),
        "__package__": None,
        "__cached__": None,
        "RAW_DRAWS": raw_draws,
        "raw_draws": raw_draws,
        "parse_draw": parse_draw,
    }

    code = compile(
        runtime_source,
        str(INTERFACE),
        "exec",
    )

    exec(code, namespace)

    report = validate_json(
        dynamic_vectors
    )

    print()
    print("=" * 110)
    print(" КОНТРОЛЬ ДИНАМИЧЕСКОГО РАСЧЁТА №83")
    print("=" * 110)
    print(
        " [✓] target_state             : "
        + str(report.get("target_state"))
    )
    print(
        " [✓] historical_states        : "
        + str(report.get("historical_states"))
    )
    print(
        " [✓] total_values             : "
        + str(report.get("total_values"))
    )
    print(
        " [✓] экспертных векторов      : "
        + str(len(report.get("vectors", [])))
    )
    print(
        " [✓] Изменено против №82      : "
        + str(changed_count)
        + "/18"
    )
    print(
        " [✓] JSON                     : "
        + OUTPUT_JSON.name
    )
    print("=" * 110)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print(
            "\n[STOP] Расчёт остановлен пользователем",
            file=sys.stderr,
        )
        raise SystemExit(130)

    except Exception as error:
        print(
            "\n[ERROR] "
            + type(error).__name__
            + ": "
            + str(error),
            file=sys.stderr,
        )
        raise SystemExit(1)
