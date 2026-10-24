#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ENGINE = (
    PROJECT
    / "archive_experiments"
    / "run_malysh_v12_recalculate_82.py"
)

FACT_MAIN = [5, 16, 32, 34, 38]
FACT_EURO = [8, 9]
FACT_FLAT = FACT_MAIN + FACT_EURO

EXPECTED_BEFORE = 81
EXPECTED_AFTER = 82
EXPECTED_VALUES = 574


def numbers_from(value):
    result = []

    if isinstance(value, bool):
        return result

    if isinstance(value, int):
        return [value]

    if isinstance(value, float) and value.is_integer():
        return [int(value)]

    if isinstance(value, dict):
        for item in value.values():
            result.extend(numbers_from(item))
        return result

    if isinstance(value, (list, tuple)):
        for item in value:
            result.extend(numbers_from(item))
        return result

    return result


def is_fact(parsed):
    numbers = numbers_from(parsed)

    if numbers == FACT_FLAT:
        return True

    if len(numbers) >= 7:
        for index in range(len(numbers) - 6):
            if numbers[index:index + 7] == FACT_FLAT:
                return True

    return False


def build_record(parse_draw):
    candidates = [
        "5 16 32 34 38 8 9",
        "5 16 32 34 38 + 8 9",
        "5,16,32,34,38,8,9",
        "5, 16, 32, 34, 38, 8, 9",
        "5,16,32,34,38 + 8,9",
        "5, 16, 32, 34, 38 + 8, 9",
        "5 16 32 34 38 | 8 9",
        "5,16,32,34,38|8,9",
        "5.16.32.34.38.8.9",
        FACT_FLAT.copy(),
        [FACT_MAIN.copy(), FACT_EURO.copy()],
        {
            "main": FACT_MAIN.copy(),
            "euro": FACT_EURO.copy(),
        },
    ]

    for candidate in candidates:
        try:
            parsed = parse_draw(candidate)
        except Exception:
            continue

        if is_fact(parsed):
            return candidate, parsed

    raise RuntimeError(
        "parse_draw не принял стандартные форматы факта №82"
    )


def patch_engine_source(source):
    replacements = [
        (
            'if len(history) != 81:',
            'if len(history) != 82:',
        ),
        (
            'Ожидалось 81 состояние',
            'Ожидалось 82 состояния',
        ),
        (
            '"history": 81',
            '"history": 82',
        ),
        (
            '"target_state": 82',
            '"target_state": 83',
        ),
        (
            "РАСЧЁТ №82",
            "РАСЧЁТ №83",
        ),
        (
            "СОСТОЯНИЯ №82",
            "СОСТОЯНИЯ №83",
        ),
        (
            "СОСТОЯНИЯ 82",
            "СОСТОЯНИЯ 83",
        ),
        (
            "МАЛЫША №82",
            "МАЛЫША №83",
        ),
        (
            "ВЕКТОРОВ №82",
            "ВЕКТОРОВ №83",
        ),
        (
            "TAIL №82",
            "TAIL №83",
        ),
        (
            "STATE 82",
            "STATE 83",
        ),
        (
            "STATE_82",
            "STATE_83",
        ),
        (
            "recalculated_82.json",
            "recalculated_83.json",
        ),
        (
            "result_82.json",
            "result_83.json",
        ),
    ]

    applied = []

    for old, new in replacements:
        count = source.count(old)

        if count:
            source = source.replace(old, new)
            applied.append((old, new, count))

    return source, applied


def main():
    if not ENGINE.is_file():
        raise FileNotFoundError(
            "Не найден архивный движок: " + str(ENGINE)
        )

    sys.path.insert(0, str(PROJECT))

    import run_state82_no_mirror as state_source
    import run_chiral_v12_full_master as expert_master

    raw_draws = state_source.RAW_DRAWS
    parse_draw = state_source.parse_draw

    if not isinstance(raw_draws, list):
        raise TypeError(
            "RAW_DRAWS должен иметь тип list, получен "
            + type(raw_draws).__name__
        )

    print("=" * 110)
    print(" МАЛЫШ v12: ПОДГОТОВКА РЕАЛЬНОГО ПЕРЕСЧЁТА №83")
    print("=" * 110)
    print(" [✓] Движок                  :", ENGINE.name)
    print(" [✓] История до добавления   :", len(raw_draws))
    print(" [✓] Фактический MAIN №82    :", FACT_MAIN)
    print(" [✓] Фактический EURO №82    :", FACT_EURO)

    found = False

    for raw in raw_draws:
        try:
            parsed = parse_draw(raw)
        except Exception:
            continue

        if is_fact(parsed):
            found = True
            break

    if found:
        print(" [✓] Факт №82 уже присутствует в истории")
    else:
        if len(raw_draws) != EXPECTED_BEFORE:
            raise RuntimeError(
                "Защитный останов: перед добавлением ожидалось "
                + str(EXPECTED_BEFORE)
                + " состояний, получено "
                + str(len(raw_draws))
            )

        record, parsed = build_record(parse_draw)
        raw_draws.append(record)

        print(" [✓] Добавлена RAW-запись     :", repr(record))
        print(" [✓] Разобранная запись       :", repr(parsed))

    if len(raw_draws) != EXPECTED_AFTER:
        raise RuntimeError(
            "После добавления ожидалось "
            + str(EXPECTED_AFTER)
            + " состояния, получено "
            + str(len(raw_draws))
        )

    total_values = len(raw_draws) * 7

    if total_values != EXPECTED_VALUES:
        raise RuntimeError(
            "Нарушен инвариант: ожидалось 574 значения, получено "
            + str(total_values)
        )

    # Синхронизируем один объект истории во всех импортирующих слоях.
    state_source.RAW_DRAWS = raw_draws
    expert_master.RAW_DRAWS = raw_draws
    expert_master.parse_draw = parse_draw

    print(" [✓] История после добавления :", len(raw_draws))
    print(" [✓] Всего входных значений  :", total_values)
    print(" [✓] Целевое состояние       : №83")
    print("=" * 110)
    print()

    original_source = ENGINE.read_text(encoding="utf-8")
    runtime_source, applied = patch_engine_source(original_source)

    if 'if len(history) != 82:' not in runtime_source:
        raise RuntimeError(
            "Не удалось адаптировать проверку истории с 81 на 82"
        )

    if "recalculated_83.json" not in runtime_source:
        raise RuntimeError(
            "Не удалось адаптировать имя результирующего JSON"
        )

    print("[RUNTIME] Адаптация архивного движка:")
    for old, new, count in applied:
        print(
            "  [✓]",
            repr(old),
            "->",
            repr(new),
            "x",
            count,
        )

    print()
    print("=" * 110)
    print(" ЗАПУСК ПОЛНОГО ИНТЕРФЕЙСА МАЛЫША №83")
    print("=" * 110)
    print()

    runtime_globals = {
        "__name__": "__main__",
        "__file__": str(ENGINE),
        "__package__": None,
        "__cached__": None,
    }

    compiled = compile(
        runtime_source,
        str(ENGINE),
        "exec",
    )

    exec(compiled, runtime_globals)


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
            "\n[ERROR]",
            type(error).__name__ + ":",
            error,
            file=sys.stderr,
        )
        raise SystemExit(1)
