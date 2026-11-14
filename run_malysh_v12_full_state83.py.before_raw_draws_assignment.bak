#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent

INTERFACE_FILE = (
    PROJECT_DIR
    / "run_v12_real_chirality_interface.py"
)

FACT_MAIN = [5, 16, 32, 34, 38]
FACT_EURO = [8, 9]
FACT_RAW = "5.16.32.34.38.8.9"

EXPECTED_OLD_STATES = 81
EXPECTED_NEW_STATES = 82
EXPECTED_TOTAL_VALUES = 574
TARGET_STATE = 83

OUTPUT_JSON = (
    PROJECT_DIR
    / "malysh_v12_chirality_result_83.json"
)


def normalize_parsed_draw(parsed):
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
            return list(main), list(euro)

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
        "Неизвестный формат результата parse_draw: "
        + repr(parsed)
    )


def validate_fact(parse_draw):
    parsed = parse_draw(FACT_RAW)
    main, euro = normalize_parsed_draw(parsed)

    if main != FACT_MAIN:
        raise RuntimeError(
            "parse_draw неверно разобрал MAIN: "
            + repr(main)
        )

    if euro != FACT_EURO:
        raise RuntimeError(
            "parse_draw неверно разобрал EURO: "
            + repr(euro)
        )

    return parsed


def prepare_history(state_source, expert_master):
    raw_draws = state_source.RAW_DRAWS
    parse_draw = state_source.parse_draw

    if not isinstance(raw_draws, list):
        raise TypeError(
            "RAW_DRAWS должен иметь тип list, получен "
            + type(raw_draws).__name__
        )

    original_count = len(raw_draws)

    print("=" * 110)
    print(" ПОДГОТОВКА ПОЛНОГО ПЕРЕСЧЁТА МАЛЫША №83")
    print("=" * 110)
    print(
        " [✓] Полный интерфейс         : "
        + INTERFACE_FILE.name
    )
    print(
        " [✓] Состояний до добавления  : "
        + str(original_count)
    )
    print(
        " [✓] Фактический MAIN №82     : "
        + repr(FACT_MAIN)
    )
    print(
        " [✓] Фактический EURO №82     : "
        + repr(FACT_EURO)
    )

    parsed_fact = validate_fact(parse_draw)

    if original_count == EXPECTED_OLD_STATES:
        raw_draws.append(FACT_RAW)

        print(" [✓] Факт №82 добавлен")
        print(
            " [✓] RAW                      : "
            + repr(FACT_RAW)
        )
        print(
            " [✓] PARSED                   : "
            + repr(parsed_fact)
        )

    elif original_count == EXPECTED_NEW_STATES:
        last_parsed = parse_draw(raw_draws[-1])
        last_main, last_euro = normalize_parsed_draw(
            last_parsed
        )

        if (
            last_main != FACT_MAIN
            or last_euro != FACT_EURO
        ):
            raise RuntimeError(
                "В истории уже 82 состояния, но последнее "
                "не соответствует факту №82"
            )

        print(
            " [✓] Факт №82 уже находится "
            "в конце истории"
        )

    else:
        raise RuntimeError(
            "Защитный останов: ожидалось 81 или 82 "
            "состояния, получено "
            + str(original_count)
        )

    if len(raw_draws) != EXPECTED_NEW_STATES:
        raise RuntimeError(
            "После подготовки ожидалось 82 состояния, "
            "получено "
            + str(len(raw_draws))
        )

    parsed_history = [
        normalize_parsed_draw(parse_draw(raw))
        for raw in raw_draws
    ]

    total_values = sum(
        len(main) + len(euro)
        for main, euro in parsed_history
    )

    if total_values != EXPECTED_TOTAL_VALUES:
        raise RuntimeError(
            "Ожидалось 574 входных значения, получено "
            + str(total_values)
        )

    last_main, last_euro = parsed_history[-1]

    if last_main != FACT_MAIN:
        raise RuntimeError(
            "Последний MAIN не соответствует факту №82"
        )

    if last_euro != FACT_EURO:
        raise RuntimeError(
            "Последний EURO не соответствует факту №82"
        )

    # Передаём один объект истории всем слоям.
    state_source.RAW_DRAWS = raw_draws
    state_source.parse_draw = parse_draw

    expert_master.RAW_DRAWS = raw_draws
    expert_master.parse_draw = parse_draw

    print(
        " [✓] Исторических состояний   : "
        + str(len(raw_draws))
    )
    print(
        " [✓] Всего входных значений   : "
        + str(total_values)
    )
    print(
        " [✓] Последний MAIN           : "
        + repr(last_main)
    )
    print(
        " [✓] Последний EURO           : "
        + repr(last_euro)
    )
    print(
        " [✓] Целевое состояние        : №"
        + str(TARGET_STATE)
    )
    print("=" * 110)
    print()

    return raw_draws


def adapt_full_interface(source):
    # Меняются только метки расчёта и имя результата.
    # Все функции, циклы и секции интерфейса сохраняются.
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


def validate_result():
    if not OUTPUT_JSON.is_file():
        raise RuntimeError(
            "Интерфейс завершился, но JSON №83 не создан: "
            + str(OUTPUT_JSON)
        )

    with OUTPUT_JSON.open(
        "r",
        encoding="utf-8",
    ) as stream:
        report = json.load(stream)

    target_state = report.get("target_state")
    historical_states = report.get(
        "historical_states"
    )
    total_values = report.get("total_values")
    vectors = report.get("vectors", [])

    if target_state != TARGET_STATE:
        raise RuntimeError(
            "В JSON неверный target_state: "
            + repr(target_state)
        )

    if historical_states != EXPECTED_NEW_STATES:
        raise RuntimeError(
            "В JSON неверное число исторических состояний: "
            + repr(historical_states)
        )

    if total_values != EXPECTED_TOTAL_VALUES:
        raise RuntimeError(
            "В JSON неверное число входных значений: "
            + repr(total_values)
        )

    if len(vectors) != 18:
        raise RuntimeError(
            "В JSON ожидалось 18 экспертных векторов, "
            "получено "
            + str(len(vectors))
        )

    print()
    print("=" * 110)
    print(" КОНТРОЛЬ РЕЗУЛЬТАТА №83")
    print("=" * 110)
    print(
        " [✓] target_state             : "
        + str(target_state)
    )
    print(
        " [✓] historical_states        : "
        + str(historical_states)
    )
    print(
        " [✓] total_values             : "
        + str(total_values)
    )
    print(
        " [✓] экспертных векторов      : "
        + str(len(vectors))
    )
    print(
        " [✓] JSON                     : "
        + OUTPUT_JSON.name
    )
    print("=" * 110)


def main():
    if not INTERFACE_FILE.is_file():
        raise FileNotFoundError(
            "Не найден полный интерфейс: "
            + str(INTERFACE_FILE)
        )

    sys.path.insert(0, str(PROJECT_DIR))

    import run_state82_no_mirror as state_source
    import run_chiral_v12_full_master as expert_master

    raw_draws = prepare_history(
        state_source,
        expert_master,
    )

    # Устанавливаем реальные исторически зависимые V1-V18.
    import dynamic_experts_state83

    parsed_for_experts = [
        normalize_parsed_draw(parse_draw(raw))
        for raw in raw_draws
    ]

    dynamic_vectors, changed_count = (
        dynamic_experts_state83.install(
            expert_master,
            parsed_for_experts,
        )
    )

    # Интерфейс импортирует expert_v1...expert_v18 через
    # from run_chiral_v12_full_master import ..., поэтому
    # модуль должен быть обновлён до выполнения интерфейса.
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

    original_source = INTERFACE_FILE.read_text(
        encoding="utf-8"
    )

    runtime_source = adapt_full_interface(
        original_source
    )

    if (
        "malysh_v12_chirality_result_83.json"
        not in runtime_source
    ):
        raise RuntimeError(
            "Не удалось адаптировать имя JSON №83"
        )

    if '"target_state": 83' not in runtime_source:
        raise RuntimeError(
            "Не удалось адаптировать target_state №83"
        )

    namespace = {
        "__name__": "__main__",
        "__file__": str(INTERFACE_FILE),
        "__package__": None,
        "__cached__": None,
    }

    compiled = compile(
        runtime_source,
        str(INTERFACE_FILE),
        "exec",
    )

    # Запускается весь исходный интерфейс:
    # V1-V18, обе ветви, плотности, карты,
    # аттракторы, человеческий итог и зоны.
    exec(compiled, namespace)

    validate_result()


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
