#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter
from contextlib import redirect_stdout
from io import StringIO
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ENGINE = (
    ROOT
    / "archive_experiments"
    / "run_malysh_v12_recalculate_82.py"
)

JSON_FILE = ROOT / "malysh_v12_recalculated_83.json"

FACT_RAW = "5.16.32.34.38.8.9"
FACT_MAIN = [5, 16, 32, 34, 38]
FACT_EURO = [8, 9]

WIDTH = 110

ZONE_POSITIONS = {
    "ROOT": (0, 1),
    "JILS": (2, 3),
    "TAIL": (4,),
}


def separator(char="="):
    print(char * WIDTH)


def heading(title):
    print()
    separator()
    print(" " + title)
    separator()


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
            return list(main), list(euro)

    if isinstance(parsed, (list, tuple)):
        if len(parsed) == 7:
            values = [int(value) for value in parsed]
            return values[:5], values[5:7]

        if len(parsed) == 2:
            main, euro = parsed
            return list(main), list(euro)

    raise ValueError(
        "Неизвестный формат состояния: "
        + repr(parsed)
    )


def validate_fact(parse_draw):
    main, euro = normalize_draw(
        parse_draw(FACT_RAW)
    )

    if main != FACT_MAIN or euro != FACT_EURO:
        raise RuntimeError(
            "parse_draw неверно разобрал факт №82: "
            + repr((main, euro))
        )


def prepare_runtime_history(master):
    validate_fact(master.parse_draw)

    runtime_draws = list(master.RAW_DRAWS)

    if len(runtime_draws) == 81:
        runtime_draws.append(FACT_RAW)

    elif len(runtime_draws) == 82:
        main, euro = normalize_draw(
            master.parse_draw(runtime_draws[-1])
        )

        if main != FACT_MAIN or euro != FACT_EURO:
            raise RuntimeError(
                "В истории уже 82 состояния, "
                "но последнее не является фактом №82"
            )

    else:
        raise RuntimeError(
            "Ожидалось 81 или 82 состояния, получено "
            + str(len(runtime_draws))
        )

    history = [
        normalize_draw(master.parse_draw(raw))
        for raw in runtime_draws
    ]

    if len(history) != 82:
        raise RuntimeError(
            "После подготовки ожидалось 82 состояния"
        )

    if sum(
        len(main) + len(euro)
        for main, euro in history
    ) != 574:
        raise RuntimeError(
            "После подготовки ожидалось 574 значения"
        )

    master.RAW_DRAWS = runtime_draws

    return runtime_draws, history


def adapt_engine(source):
    replacements = [
        (
            "if len(history) != 81:",
            "if len(history) != 82:",
        ),
        (
            "Ожидалось 81 состояние",
            "Ожидалось 82 состояния",
        ),
        (
            "[ПОЛНЫЙ ПЕРЕСЧЁТ №82:",
            "[ПОЛНЫЙ ПЕРЕСЧЁТ №83:",
        ),
        (
            '" [✓] 81 историческое состояние"',
            '" [✓] 82 исторических состояния"',
        ),
        (
            '" [✓] 567 входных значений"',
            '" [✓] 574 входных значения"',
        ),
        (
            '"target": 82',
            '"target": 83',
        ),
        (
            '"history": 81',
            '"history": 82',
        ),
        (
            "malysh_v12_recalculated_82.json",
            "malysh_v12_recalculated_83.json",
        ),
    ]

    for old, new in replacements:
        source = source.replace(old, new)

    return source


def run_real_engine(master):
    if not ENGINE.is_file():
        raise FileNotFoundError(
            "Не найден реальный движок: "
            + str(ENGINE)
        )

    if JSON_FILE.exists():
        JSON_FILE.unlink()

    source = adapt_engine(
        ENGINE.read_text(encoding="utf-8")
    )

    namespace = {
        "__name__": "__main__",
        "__file__": str(ENGINE),
        "__package__": None,
        "__cached__": None,
    }

    buffer = StringIO()

    with redirect_stdout(buffer):
        exec(
            compile(source, str(ENGINE), "exec"),
            namespace,
        )

    engine_output = buffer.getvalue()

    if not JSON_FILE.is_file():
        print(engine_output)
        raise RuntimeError(
            "Реальный движок не создал JSON №83"
        )

    return engine_output


def load_report():
    report = json.loads(
        JSON_FILE.read_text(encoding="utf-8")
    )

    if report.get("target") != 83:
        raise RuntimeError(
            "JSON: target не равен 83"
        )

    if report.get("history") != 82:
        raise RuntimeError(
            "JSON: history не равен 82"
        )

    records = report.get("vectors", [])

    if len(records) != 18:
        raise RuntimeError(
            "JSON должен содержать 18 векторов"
        )

    return report, records


def branch(record, name):
    value = record.get(name)

    if not isinstance(value, dict):
        raise RuntimeError(
            "Нет ветви "
            + name
            + " у "
            + record.get("name", "?")
        )

    return value


def source_main(record):
    source = record.get("source", {})

    if isinstance(source, dict):
        return list(source.get("main", []))

    return list(source)


def support(records, branch_name, field="main"):
    counter = Counter()

    for record in records:
        values = branch(record, branch_name).get(
            field,
            [],
        )
        counter.update(values)

    return counter


def print_density(title, counter):
    heading(title)

    groups = {}

    for number, count in counter.items():
        groups.setdefault(count, []).append(number)

    for count in sorted(groups, reverse=True):
        numbers = sorted(groups[count])

        print(
            f" • Поддержка {count:2d} векторов : "
            f"{numbers} | {'█' * count}"
        )


def ranking(counter):
    return sorted(
        counter,
        key=lambda number: (
            -counter[number],
            number,
        ),
    )


def wing_rudder(counter):
    if not counter:
        return [], 0, [], 0

    values = sorted(
        set(counter.values()),
        reverse=True,
    )

    wing_value = values[0]
    rudder_value = (
        values[1]
        if len(values) > 1
        else 0
    )

    wing = sorted(
        number
        for number, count in counter.items()
        if count == wing_value
    )

    rudder = sorted(
        number
        for number, count in counter.items()
        if count == rudder_value
    )

    return (
        wing,
        wing_value,
        rudder,
        rudder_value,
    )


def print_attractors(counter):
    text = " > ".join(
        f"{number}({counter[number]})"
        for number in ranking(counter)
    )

    print("   " + text)


def zone_counter(records, branch_name):
    zones = {
        zone: Counter()
        for zone in ZONE_POSITIONS
    }

    for record in records:
        if branch_name == "source":
            vector = source_main(record)
        else:
            vector = branch(
                record,
                branch_name,
            ).get("main", [])

        if len(vector) != 5:
            continue

        for zone, positions in ZONE_POSITIONS.items():
            zones[zone].update(
                vector[position]
                for position in positions
            )

    return zones


def print_zone_block(title, zones):
    print()
    print(" " + title)

    for zone in ("ROOT", "JILS", "TAIL"):
        counter = zones[zone]

        wing, wing_value, rudder, rudder_value = (
            wing_rudder(counter)
        )

        print(
            f" {zone} КРЫЛО : "
            f"{wing} | {wing_value}/18"
        )

        print(
            f" {zone} РУЛЬ  : "
            f"{rudder} | {rudder_value}/18"
        )

        levels = sorted(
            set(counter.values()),
            reverse=True,
        )

        print(
            f" {zone} ПОЛЕ  : "
            + " > ".join(
                str(value)
                for value in levels
            )
        )

        print()


def final_from_report(report, branch_name):
    final = report.get("final", {}).get(
        branch_name,
        {},
    )

    return (
        list(final.get("main", [])),
        list(final.get("euro", [])),
    )


def score_text(branch_data):
    tube = branch_data.get("tube_scores", {})
    euro_score = branch_data.get("euro_score")

    parts = []

    if tube:
        parts.append(
            "Tube="
            + "/".join(
                f"{zone}:{tube.get(zone, 0.0):.4f}"
                for zone in ("ROOT", "JILS", "TAIL")
            )
        )

    if euro_score is not None:
        parts.append(
            f"EuroScore={euro_score:.4f}"
        )

    return " | ".join(parts)


def render(report, records, history):
    direct_name = "without_chirality"
    chiral_name = "with_chirality"

    direct_support = support(
        records,
        direct_name,
    )

    chiral_support = support(
        records,
        chiral_name,
    )

    direct_euro_support = support(
        records,
        direct_name,
        "euro",
    )

    chiral_euro_support = support(
        records,
        chiral_name,
        "euro",
    )

    final_direct, final_direct_euro = (
        final_from_report(
            report,
            direct_name,
        )
    )

    final_chiral, final_chiral_euro = (
        final_from_report(
            report,
            chiral_name,
        )
    )

    separator()
    print(
        " МАЛЫШ v12 "
        "[РЕАЛЬНЫЙ ПЕРЕСЧЁТ №83: "
        "БЕЗ ХИРАЛЬНОСТИ / С ХИРАЛЬНОСТЬЮ]"
    )
    separator()

    print(
        " [✓] Исторических состояний : "
        + str(len(history))
    )
    print(
        " [✓] Всего входных значений : 574"
    )
    print(
        " [✓] Движок                  : "
        "bounded toroidal"
    )
    print(
        " [✓] Факт №82 MAIN           : "
        + repr(FACT_MAIN)
    )
    print(
        " [✓] Факт №82 EURO           : "
        + repr(FACT_EURO)
    )

    heading(
        "🔬 1. ДЕТАЛЬНЫЙ ВЫВОД "
        "ПО 18 ЭКСПЕРТНЫМ ВЕКТОРАМ"
    )

    for record in records:
        source = source_main(record)
        direct = branch(record, direct_name)
        chiral = branch(record, chiral_name)

        direct_main = list(direct.get("main", []))
        chiral_main = list(chiral.get("main", []))

        direct_euro = list(direct.get("euro", []))
        chiral_euro = list(chiral.get("euro", []))

        common_main = sorted(
            set(direct_main)
            & set(chiral_main)
        )

        common_euro = sorted(
            set(direct_euro)
            & set(chiral_euro)
        )

        print(
            f" [{record.get('name', '?'):<31}] "
            f"| Вес: {record.get('weight', 0):<5} "
            f"| Pressure: "
            f"{record.get('pressure', 0):.2f} "
            f"| Trust: {record.get('trust', 0):.2f}"
        )

        print(
            "   ИСХОДНЫЙ MAIN           : "
            + repr(source)
        )
        print(
            "   БЕЗ ХИРАЛЬНОСТИ MAIN    : "
            + repr(direct_main)
        )
        print(
            "   С ХИРАЛЬНОСТЬЮ MAIN     : "
            + repr(chiral_main)
        )

        print(
            "   БЕЗ ХИРАЛЬНОСТИ EURO    : "
            + repr(direct_euro)
        )
        print(
            "   С ХИРАЛЬНОСТЬЮ EURO     : "
            + repr(chiral_euro)
        )

        print(
            "   ХИРАЛЬНАЯ Δ             : +"
            + repr(
                sorted(
                    set(chiral_main)
                    - set(direct_main)
                )
            )
            + " -"
            + repr(
                sorted(
                    set(direct_main)
                    - set(chiral_main)
                )
            )
            + " | общие="
            + repr(common_main)
        )

        print(
            "   ПРЯМОЙ КОНТУР           : "
            + score_text(direct)
        )
        print(
            "   ХИРАЛЬНЫЙ КОНТУР        : "
            + score_text(chiral)
        )

        print(
            "   ОБЩИЕ EURO              : "
            + repr(common_euro)
        )

        print(" " + "─" * (WIDTH - 1))

    print_density(
        "📊 2A. ПЛОТНОСТЬ БЕЗ ХИРАЛЬНОСТИ",
        direct_support,
    )

    print_density(
        "📊 2B. ПЛОТНОСТЬ С ХИРАЛЬНОСТЬЮ",
        chiral_support,
    )

    heading(
        "🚀 3. ИТОГОВЫЙ РАСЧЁТ "
        "СОСТОЯНИЯ №83"
    )

    print()
    print(" БЕЗ ХИРАЛЬНОСТИ")
    print(" MAIN :", final_direct)
    print(" EURO :", final_direct_euro)

    print()
    print(" С ХИРАЛЬНОСТЬЮ")
    print(" MAIN :", final_chiral)
    print(" EURO :", final_chiral_euro)

    print()
    print(" ХИРАЛЬНАЯ Δ")
    print(
        " Добавлены :",
        sorted(
            set(final_chiral)
            - set(final_direct)
        ),
    )
    print(
        " Удалены   :",
        sorted(
            set(final_direct)
            - set(final_chiral)
        ),
    )
    print(
        " Общие     :",
        sorted(
            set(final_direct)
            & set(final_chiral)
        ),
    )

    heading(
        "🧭 НАВИГАЦИОННАЯ КАРТА "
        "МАЛЫША №83"
    )

    direct_wing, direct_wing_count, direct_rudder, direct_rudder_count = (
        wing_rudder(direct_support)
    )

    chiral_wing, chiral_wing_count, chiral_rudder, chiral_rudder_count = (
        wing_rudder(chiral_support)
    )

    print()
    print(" 🔵 БЕЗ ХИРАЛЬНОСТИ")
    print(
        f" ✈️ КРЫЛО : {direct_wing} "
        f"| {direct_wing_count}/18"
    )
    print(
        f" 🛞 РУЛЬ  : {direct_rudder} "
        f"| {direct_rudder_count}/18"
    )
    print(" 🧲 АТТРАКТОРЫ:")
    print_attractors(direct_support)

    print()
    print(" 🟣 С ХИРАЛЬНОСТЬЮ")
    print(
        f" ✈️ КРЫЛО : {chiral_wing} "
        f"| {chiral_wing_count}/18"
    )
    print(
        f" 🛞 РУЛЬ  : {chiral_rudder} "
        f"| {chiral_rudder_count}/18"
    )
    print(" 🧲 АТТРАКТОРЫ:")
    print_attractors(chiral_support)

    heading("🤝 ОБЩЕЕ ПОЛЕ ДВУХ ВЕТВЕЙ")

    common_nodes = sorted(
        set(direct_support)
        & set(chiral_support)
    )

    common_euro_nodes = sorted(
        set(direct_euro_support)
        & set(chiral_euro_support)
    )

    print(" ОБЩИЕ УЗЛЫ MAIN :", common_nodes)
    print(
        " ОБЩИЕ УЗЛЫ EURO :",
        common_euro_nodes,
    )

    print()
    print(" 🧲 ОБЩИЕ АТТРАКТОРЫ:")

    common_counter = {
        number: (
            direct_support[number]
            + chiral_support[number]
        )
        for number in common_nodes
    }

    for number in sorted(
        common_counter,
        key=lambda value: (
            -common_counter[value],
            value,
        ),
    ):
        direct_count = direct_support[number]
        chiral_count = chiral_support[number]
        total = common_counter[number]

        print(
            f" • {number:2d} : "
            f"БЕЗ={direct_count:2d} | "
            f"С={chiral_count:2d} | "
            f"Σ={total:2d} | "
            f"{'█' * total}"
        )

    heading(
        "🚀 ЧЕЛОВЕЧЕСКИЙ ИТОГ "
        "МАЛЫША №83"
    )

    print()
    print(" 🔵 БЕЗ ХИРАЛЬНОСТИ")
    print(" MAIN :", final_direct)
    print(" EURO :", final_direct_euro)
    print(" ✈️ КРЫЛО :", direct_wing)
    print(" 🛞 РУЛЬ  :", direct_rudder)

    print()
    print(" 🟣 С ХИРАЛЬНОСТЬЮ")
    print(" MAIN :", final_chiral)
    print(" EURO :", final_chiral_euro)
    print(" ✈️ КРЫЛО :", chiral_wing)
    print(" 🛞 РУЛЬ  :", chiral_rudder)

    print()
    print(" 🤝 ОБЩЕЕ")
    print(
        " MAIN ФИНАЛ :",
        sorted(
            set(final_direct)
            & set(final_chiral)
        ),
    )
    print(
        " EURO ФИНАЛ :",
        sorted(
            set(final_direct_euro)
            & set(final_chiral_euro)
        ),
    )
    print(" MAIN ПОЛЕ  :", common_nodes)
    print(
        " EURO ПОЛЕ  :",
        common_euro_nodes,
    )

    print()
    print(" 🪞 ХИРАЛЬНАЯ Δ")
    print(
        " + ВОШЛИ :",
        sorted(
            set(final_chiral)
            - set(final_direct)
        ),
    )
    print(
        " - ВЫШЛИ :",
        sorted(
            set(final_direct)
            - set(final_chiral)
        ),
    )
    print(
        " = ОБЩИЕ :",
        sorted(
            set(final_direct)
            & set(final_chiral)
        ),
    )

    heading(
        "🧭 ЗОНАЛЬНАЯ КАРТА "
        "ROOT / JILS / TAIL №83"
    )

    source_zones = zone_counter(
        records,
        "source",
    )

    direct_zones = zone_counter(
        records,
        direct_name,
    )

    chiral_zones = zone_counter(
        records,
        chiral_name,
    )

    print_zone_block(
        "⚪ ИСХОДНЫЕ ЭКСПЕРТНЫЕ ВЕКТОРЫ",
        source_zones,
    )

    print_zone_block(
        "🔵 БЕЗ ХИРАЛЬНОСТИ",
        direct_zones,
    )

    print_zone_block(
        "🟣 С ХИРАЛЬНОСТЬЮ",
        chiral_zones,
    )

    heading("🤝 ОБЩИЕ ЗОНАЛЬНЫЕ АТТРАКТОРЫ")

    for zone in ("ROOT", "JILS", "TAIL"):
        common = sorted(
            set(direct_zones[zone])
            & set(chiral_zones[zone])
        )

        combined = {
            number: (
                direct_zones[zone][number]
                + chiral_zones[zone][number]
            )
            for number in common
        }

        ordered = sorted(
            combined,
            key=lambda number: (
                -combined[number],
                number,
            ),
        )

        print()
        print(
            f" {zone} ОБЩИЕ УЗЛЫ : "
            f"{common}"
        )

        for number in ordered:
            print(
                f"   {number:2d}: "
                f"БЕЗ={direct_zones2d} | "
                f"С={chiral_zones2d} | "
                f"Σ={combined2d} | "
                f"{'█' * combined[number]}"
            )

    heading(
        "🚀 ЗОНЫ ФИНАЛЬНЫХ "
        "ВЕКТОРОВ №83"
    )

    print()
    print(" 🔵 БЕЗ ХИРАЛЬНОСТИ")
    print(" ROOT :", final_direct[:2])
    print(" JILS :", final_direct[2:4])
    print(" TAIL :", final_direct[4:])
    print(" EURO :", final_direct_euro)

    print()
    print(" 🟣 С ХИРАЛЬНОСТЬЮ")
    print(" ROOT :", final_chiral[:2])
    print(" JILS :", final_chiral[2:4])
    print(" TAIL :", final_chiral[4:])
    print(" EURO :", final_chiral_euro)

    print()
    print(" 🤝 ОБЩИЕ ФИНАЛЬНЫЕ ЗОНЫ")
    print(
        " ROOT :",
        sorted(
            set(final_direct[:2])
            & set(final_chiral[:2])
        ),
    )
    print(
        " JILS :",
        sorted(
            set(final_direct[2:4])
            & set(final_chiral[2:4])
        ),
    )
    print(
        " TAIL :",
        sorted(
            set(final_direct[4:])
            & set(final_chiral[4:])
        ),
    )
    print(
        " EURO :",
        sorted(
            set(final_direct_euro)
            & set(final_chiral_euro)
        ),
    )

    separator()

    print(
        " [✓] Реальный JSON: "
        + JSON_FILE.name
    )


def main():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    import run_chiral_v12_full_master as master

    runtime_draws, history = (
        prepare_runtime_history(master)
    )

    # Архивный engine импортирует RAW_DRAWS
    # из уже загруженного master-модуля.
    master.RAW_DRAWS = runtime_draws

    engine_output = run_real_engine(master)

    report, records = load_report()

    render(
        report,
        records,
        history,
    )

    print()
    print(
        "[INFO] Внутренний вывод реального engine "
        "сохранён в журнале запуска."
    )


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print(
            "\n[STOP] Остановлено пользователем",
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
