#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import runpy
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

FACT_MAIN = [5, 16, 32, 34, 38]
FACT_EURO = [8, 9]
FACT_FLAT = FACT_MAIN + FACT_EURO

OLD_COUNT = 81
NEW_COUNT = 82
VALUES_PER_STATE = 7


def extract_numbers(value):
    result = []

    if isinstance(value, bool):
        return result

    if isinstance(value, int):
        return [value]

    if isinstance(value, float) and value.is_integer():
        return [int(value)]

    if isinstance(value, dict):
        for item in value.values():
            result.extend(extract_numbers(item))
        return result

    if isinstance(value, (list, tuple)):
        for item in value:
            result.extend(extract_numbers(item))
        return result

    return result


def matches_fact(parsed):
    numbers = extract_numbers(parsed)

    if numbers == FACT_FLAT:
        return True

    for index in range(max(0, len(numbers) - 6)):
        if numbers[index:index + 7] == FACT_FLAT:
            return True

    return False


def choose_record(raw_draws, parse_draw):
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

        if matches_fact(parsed):
            return candidate, parsed

    last_raw = raw_draws[-1] if raw_draws else None

    try:
        last_parsed = parse_draw(last_raw)
    except Exception as error:
        last_parsed = "ERROR: " + repr(error)

    print("[ERROR] Не удалось определить формат RAW_DRAWS")
    print("[DEBUG] Последняя RAW-запись:", repr(last_raw))
    print("[DEBUG] Последняя PARSED-запись:", repr(last_parsed))

    raise RuntimeError("parse_draw не принял варианты факта №82")


def main():
    sys.path.insert(0, str(PROJECT_DIR))

    import run_state82_no_mirror as state_source
    import run_chiral_v12_full_master as expert_master

    raw_draws = state_source.RAW_DRAWS
    parse_draw = state_source.parse_draw

    if not isinstance(raw_draws, list):
        raise TypeError(
            "RAW_DRAWS имеет тип " + type(raw_draws).__name__
            + ", ожидался list"
        )

    print("=" * 110)
    print(" ПОДГОТОВКА РАСЧЁТА СОСТОЯНИЯ №83")
    print("=" * 110)
    print(" [✓] Состояний до добавления :", len(raw_draws))
    print(" [✓] Фактический MAIN №82    :", FACT_MAIN)
    print(" [✓] Фактический EURO №82    :", FACT_EURO)

    fact_found = False

    for raw in raw_draws:
        try:
            if matches_fact(parse_draw(raw)):
                fact_found = True
                break
        except Exception:
            continue

    if fact_found:
        print(" [✓] Факт №82 уже находится в RAW_DRAWS")
    else:
        if len(raw_draws) != OLD_COUNT:
            raise RuntimeError(
                "Защитный останов: ожидалось "
                + str(OLD_COUNT)
                + " состояний, получено "
                + str(len(raw_draws))
            )

        new_record, parsed = choose_record(raw_draws, parse_draw)
        raw_draws.append(new_record)

        print(" [✓] Добавлена RAW-запись     :", repr(new_record))
        print(" [✓] parse_draw               :", repr(parsed))

    if len(raw_draws) != NEW_COUNT:
        raise RuntimeError(
            "Ожидалось 82 состояния, получено "
            + str(len(raw_draws))
        )

    total_values = len(raw_draws) * VALUES_PER_STATE

    if total_values != 574:
        raise RuntimeError(
            "Ожидалось 574 значения, получено "
            + str(total_values)
        )

    state_source.RAW_DRAWS = raw_draws
    expert_master.RAW_DRAWS = raw_draws
    expert_master.parse_draw = parse_draw

    print(" [✓] Состояний после добавления:", len(raw_draws))
    print(" [✓] Всего входных значений   :", total_values)
    print(" [✓] Следующий расчёт         : №83")
    print("=" * 110)
    print()

    interface = PROJECT_DIR / "run_v12_real_chirality_interface.py"

    if not interface.is_file():
        raise FileNotFoundError(
            "Не найден " + str(interface)
        )

    # Загружаем интерфейс в память и переводим только метки
    # текущего расчета с 82 на 83. Исходный файл не изменяется.
    source = interface.read_text(encoding="utf-8")

    replacements = {
        "РАСЧЁТ №82": "РАСЧЁТ №83",
        "СОСТОЯНИЯ №82": "СОСТОЯНИЯ №83",
        "МАЛЫША №82": "МАЛЫША №83",
        "ВЕКТОРОВ №82": "ВЕКТОРОВ №83",
        "TAIL №82": "TAIL №83",
        '"target_state": 82': '"target_state": 83',
        "malysh_v12_chirality_result_82.json":
            "malysh_v12_chirality_result_83.json",
    }

    for old_value, new_value in replacements.items():
        source = source.replace(old_value, new_value)

    runtime_globals = {
        "__name__": "__main__",
        "__file__": str(interface),
        "__package__": None,
        "__cached__": None,
    }

    exec(
        compile(
            source,
            str(interface),
            "exec",
        ),
        runtime_globals,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[STOP] Остановлено пользователем")
        sys.exit(130)
    except Exception as error:
        print(
            "\n[ERROR]",
            type(error).__name__ + ":",
            error,
            file=sys.stderr,
        )
        sys.exit(1)
