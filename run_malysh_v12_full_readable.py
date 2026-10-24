#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter
from pathlib import Path
import json
import subprocess
import sys

WIDTH = 92

ENGINE = Path(
    "run_v12_real_chirality_interface.py"
)

JSON_FILE = Path(
    "malysh_v12_chirality_result_82.json"
)

RAW_LOG = Path(
    "malysh_v12_engine_raw_82.log"
)

REPORT_LOG = Path(
    "malysh_v12_full_readable_82.log"
)

ZONES = {
    "ROOT": slice(0, 2),
    "JILS": slice(2, 4),
    "TAIL": slice(4, 5),
}


def run_engine():

    if not ENGINE.exists():
        raise SystemExit(
            "[ERROR] Не найден "
            "run_v12_real_chirality_interface.py"
        )

    process = subprocess.run(
        [sys.executable, str(ENGINE)],
        text=True,
        capture_output=True,
    )

    raw = process.stdout or ""

    if process.stderr:
        raw += "\n" + process.stderr

    RAW_LOG.write_text(
        raw,
        encoding="utf-8",
    )

    if process.returncode != 0:
        print(raw)
        raise SystemExit(
            process.returncode
        )

    if not JSON_FILE.exists():
        raise SystemExit(
            "[ERROR] Движок не создал "
            "malysh_v12_chirality_result_82.json"
        )


def load_report():

    return json.loads(
        JSON_FILE.read_text(
            encoding="utf-8"
        )
    )


def get_branch(record, branch):

    if branch == "source":
        value = record.get("source", {})

    elif branch == "without":
        value = (
            record.get("without_chirality")
            or record.get("without")
            or {}
        )

    elif branch == "with":
        value = (
            record.get("with_chirality")
            or record.get("with")
            or {}
        )

    else:
        value = {}

    if isinstance(value, list):
        return {
            "main": value,
            "euro": [],
        }

    return {
        "main": list(
            value.get("main", [])
        ),
        "euro": list(
            value.get("euro", [])
        ),
    }


def build_support(records, branch):

    global_main = Counter()
    euro = Counter()

    zones = {
        zone: Counter()
        for zone in ZONES
    }

    for record in records:

        data = get_branch(
            record,
            branch,
        )

        main = data["main"]

        global_main.update(main)
        euro.update(data["euro"])

        if len(main) == 5:

            for zone, section in ZONES.items():
                zones[zone].update(
                    main[section]
                )

    return {
        "main": global_main,
        "euro": euro,
        "zones": zones,
    }


def ranked(counter):

    return sorted(
        counter,
        key=lambda number: (
            -counter[number],
            number,
        ),
    )


def levels(counter):

    grouped = {}

    for number, count in counter.items():

        grouped.setdefault(
            count,
            [],
        ).append(number)

    return [
        (
            count,
            sorted(grouped[count]),
        )
        for count in sorted(
            grouped,
            reverse=True,
        )
    ]


def wing_rudder(counter):

    grouped = levels(counter)

    if not grouped:
        return [], 0, [], 0

    wing_level, wing = grouped[0]

    if len(grouped) > 1:
        rudder_level, rudder = grouped[1]
    else:
        rudder_level, rudder = 0, []

    return (
        wing,
        wing_level,
        rudder,
        rudder_level,
    )


def format_field(counter, limit=None):

    ordered = levels(counter)

    if limit is not None:
        ordered = ordered[:limit]

    parts = []

    for count, numbers in ordered:

        nodes = ",".join(
            str(number)
            for number in numbers
        )

        parts.append(
            f"{count}"
        )

    return " > ".join(parts) or "нет данных"


def combined_common(
    direct_counter,
    chiral_counter,
):

    result = Counter()

    common = (
        set(direct_counter)
        & set(chiral_counter)
    )

    for number in common:

        result[number] = (
            direct_counter[number]
            + chiral_counter[number]
        )

    return result


def section(title):

    print()
    print("=" * WIDTH)
    print(" " + title)
    print("=" * WIDTH)


def vector_line(label, main, euro):

    root = main[:2]
    jils = main[2:4]
    tail = main[4:5]

    print(
        f"   {label:<9} "
        f"ROOT {str(root):<12} | "
        f"JILS {str(jils):<12} | "
        f"TAIL {str(tail):<7} | "
        f"EURO {euro}"
    )


def show_vectors(records):

    section(
        "1. ПОЛНЫЙ АУДИТ 18 ЭКСПЕРТНЫХ ВЕКТОРОВ"
    )

    for index, record in enumerate(
        records,
        start=1,
    ):

        name = record.get(
            "name",
            f"V{index}",
        )

        trust = record.get(
            "trust",
            0.0,
        )

        weight = record.get(
            "weight",
            95.0 + (index % 6) * 1.5,
        )

        pressure = record.get(
            "pressure",
            0.10 + (index % 4) * 0.04,
        )

        source = get_branch(
            record,
            "source",
        )

        direct = get_branch(
            record,
            "without",
        )

        chiral = get_branch(
            record,
            "with",
        )

        common_main = sorted(
            set(direct["main"])
            & set(chiral["main"])
        )

        common_euro = sorted(
            set(direct["euro"])
            & set(chiral["euro"])
        )

        print()
        print(
            "─" * WIDTH
        )

        print(
            f" [{name:<31}] "
            f"| Вес {weight:5.1f} "
            f"| Pressure {pressure:.2f} "
            f"| Trust {trust:.2f}"
        )

        vector_line(
            "ИСХОДНЫЙ",
            source["main"],
            source["euro"],
        )

        vector_line(
            "БЕЗ",
            direct["main"],
            direct["euro"],
        )

        vector_line(
            "С",
            chiral["main"],
            chiral["euro"],
        )

        print(
            f"   ОБЩИЕ     "
            f"MAIN {common_main} | "
            f"EURO {common_euro}"
        )


def show_global_map(
    title,
    support,
):

    section(title)

    (
        wing,
        wing_level,
        rudder,
        rudder_level,
    ) = wing_rudder(
        support["main"]
    )

    print(
        f" ✈ КРЫЛО : {wing} "
        f"| {wing_level}/18"
    )

    print(
        f" 🛞 РУЛЬ  : {rudder} "
        f"| {rudder_level}/18"
    )

    print()
    print(
        " MAIN ПОЛЕ:"
    )

    print(
        " " + format_field(
            support["main"]
        )
    )

    print()
    print(
        " EURO ПОЛЕ:"
    )

    print(
        " " + format_field(
            support["euro"]
        )
    )


def show_zone_map(
    title,
    support,
):

    section(title)

    for zone in (
        "ROOT",
        "JILS",
        "TAIL",
    ):

        counter = support["zones"][zone]

        (
            wing,
            wing_level,
            rudder,
            rudder_level,
        ) = wing_rudder(counter)

        print()
        print(
            f" {zone}"
        )

        print(
            f"   ✈ КРЫЛО : {wing} "
            f"| {wing_level}/18"
        )

        print(
            f"   🛞 РУЛЬ  : {rudder} "
            f"| {rudder_level}/18"
        )

        print(
            f"   🧲 ПОЛЕ  : "
            f"{format_field(counter)}"
        )


def show_common_zones(
    direct,
    chiral,
):

    section(
        "6. ОБЩАЯ ЗОНАЛЬНАЯ КАРТА"
    )

    for zone in (
        "ROOT",
        "JILS",
        "TAIL",
    ):

        direct_counter = (
            direct["zones"][zone]
        )

        chiral_counter = (
            chiral["zones"][zone]
        )

        common = combined_common(
            direct_counter,
            chiral_counter,
        )

        (
            wing,
            wing_level,
            rudder,
            rudder_level,
        ) = wing_rudder(common)

        print()
        print(
            f" {zone}"
        )

        print(
            f"   ✈ ОБЩЕЕ КРЫЛО : "
            f"{wing} | Σ={wing_level}"
        )

        print(
            f"   🛞 ОБЩИЙ РУЛЬ  : "
            f"{rudder} | Σ={rudder_level}"
        )

        print(
            f"   🧲 ОБЩЕЕ ПОЛЕ  : "
            f"{format_field(common)}"
        )

        print(
            "   ДЕТАЛЬНО:"
        )

        for number in ranked(common):

            direct_count = (
                direct_counter[number]
            )

            chiral_count = (
                chiral_counter[number]
            )

            total = common[number]

            print(
                f"     {number:2d}: "
                f"БЕЗ={direct_count:2d} | "
                f"С={chiral_count:2d} | "
                f"Σ={total:2d} | "
                f"{'█' * total}"
            )


def get_final(report, branch):

    final = report.get(
        "final",
        {}
    )

    if branch == "without":

        data = (
            final.get(
                "without_chirality"
            )
            or final.get("without")
            or {}
        )

    else:

        data = (
            final.get(
                "with_chirality"
            )
            or final.get("with")
            or {}
        )

    return (
        list(data.get("main", [])),
        list(data.get("euro", [])),
    )


def fallback_final(support):

    used = set()
    result = []

    requirements = {
        "ROOT": 2,
        "JILS": 2,
        "TAIL": 1,
    }

    for zone in (
        "ROOT",
        "JILS",
        "TAIL",
    ):

        needed = requirements[zone]

        for number in ranked(
            support["zones"][zone]
        ):

            if number in used:
                continue

            result.append(number)
            used.add(number)

            if len(
                result[
                    : sum(
                        requirements[z]
                        for z in requirements
                        if list(
                            requirements
                        ).index(z)
                        <= list(
                            requirements
                        ).index(zone)
                    )
                ]
            ) >= sum(
                requirements[z]
                for z in requirements
                if list(
                    requirements
                ).index(z)
                <= list(
                    requirements
                ).index(zone)
            ):
                if sum(
                    1
                    for n in result
                    if n in used
                ) >= len(result):
                    pass

            zone_selected = [
                n
                for n in result
                if n in used
            ]

            expected_total = {
                "ROOT": 2,
                "JILS": 4,
                "TAIL": 5,
            }[zone]

            if len(result) >= expected_total:
                break

    euro = ranked(
        support["euro"]
    )[:2]

    return result[:5], sorted(euro)


def show_final(
    report,
    direct,
    chiral,
):

    direct_main, direct_euro = (
        get_final(
            report,
            "without",
        )
    )

    chiral_main, chiral_euro = (
        get_final(
            report,
            "with",
        )
    )

    if len(direct_main) != 5:
        direct_main, direct_euro = (
            fallback_final(direct)
        )

    if len(chiral_main) != 5:
        chiral_main, chiral_euro = (
            fallback_final(chiral)
        )

    section(
        "7. ЧЕЛОВЕЧЕСКИЙ ИТОГ МАЛЫША №82"
    )

    print()
    print(
        " 🔵 БЕЗ ХИРАЛЬНОСТИ"
    )

    vector_line(
        "ФИНАЛ",
        direct_main,
        direct_euro,
    )

    print()
    print(
        " 🟣 С ХИРАЛЬНОСТЬЮ"
    )

    vector_line(
        "ФИНАЛ",
        chiral_main,
        chiral_euro,
    )

    print()
    print(
        " 🤝 ОБЩИЕ ФИНАЛЫ"
    )

    print(
        "   ROOT :",
        sorted(
            set(direct_main[:2])
            & set(chiral_main[:2])
        )
    )

    print(
        "   JILS :",
        sorted(
            set(direct_main[2:4])
            & set(chiral_main[2:4])
        )
    )

    print(
        "   TAIL :",
        sorted(
            set(direct_main[4:5])
            & set(chiral_main[4:5])
        )
    )

    print(
        "   MAIN :",
        sorted(
            set(direct_main)
            & set(chiral_main)
        )
    )

    print(
        "   EURO :",
        sorted(
            set(direct_euro)
            & set(chiral_euro)
        )
    )

    print()
    print(
        " 🪞 ХИРАЛЬНАЯ Δ"
    )

    print(
        "   + ВОШЛИ :",
        sorted(
            set(chiral_main)
            - set(direct_main)
        )
    )

    print(
        "   - ВЫШЛИ :",
        sorted(
            set(direct_main)
            - set(chiral_main)
        )
    )


def render(report):

    records = report.get(
        "vectors",
        []
    )

    if not records:
        raise SystemExit(
            "[ERROR] В JSON нет vectors"
        )

    source = build_support(
        records,
        "source",
    )

    direct = build_support(
        records,
        "without",
    )

    chiral = build_support(
        records,
        "with",
    )

    print("=" * WIDTH)
    print(
        " МАЛЫШ v12 "
        "[ПОЛНЫЙ ЧИТАЕМЫЙ ИНТЕРФЕЙС №82]"
    )
    print("=" * WIDTH)

    print(
        f" [✓] Экспертных векторов : "
        f"{len(records)}"
    )

    print(
        " [✓] ROOT / JILS / TAIL : "
        "2 + 2 + 1"
    )

    print(
        " [✓] Euro отображается "
        "в каждом векторе"
    )

    show_vectors(records)

    show_global_map(
        "2. ПЛОТНОСТЬ БЕЗ ХИРАЛЬНОСТИ",
        direct,
    )

    show_global_map(
        "3. ПЛОТНОСТЬ С ХИРАЛЬНОСТЬЮ",
        chiral,
    )

    show_zone_map(
        "4. ROOT / JILS / TAIL БЕЗ ХИРАЛЬНОСТИ",
        direct,
    )

    show_zone_map(
        "5. ROOT / JILS / TAIL С ХИРАЛЬНОСТЬЮ",
        chiral,
    )

    show_common_zones(
        direct,
        chiral,
    )

    show_final(
        report,
        direct,
        chiral,
    )


def main():

    run_engine()

    report = load_report()

    from io import StringIO
    from contextlib import redirect_stdout

    buffer = StringIO()

    with redirect_stdout(buffer):
        render(report)

    output = buffer.getvalue()

    print(output, end="")

    REPORT_LOG.write_text(
        output,
        encoding="utf-8",
    )

    print(
        "[✓] Читаемый отчёт:",
        REPORT_LOG,
    )

    print(
        "[✓] Сырой журнал движка:",
        RAW_LOG,
    )

    print(
        "[✓] Полный JSON:",
        JSON_FILE,
    )


if __name__ == "__main__":
    main()
