#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

TARGET = Path("run_v12_real_chirality_interface.py")
BACKUP = Path("run_v12_real_chirality_interface.py.backup_before_zones")

INSTALL_MARKER = "# ROOT_JILS_TAIL_PANEL_V1"
INSERT_MARKER = "    report = {"


def main():
    if not TARGET.exists():
        raise SystemExit(
            "[ERROR] Не найден файл: "
            "run_v12_real_chirality_interface.py"
        )

    source = TARGET.read_text(
        encoding="utf-8"
    )

    if INSTALL_MARKER in source:
        print(
            "[OK] ROOT / JILS / TAIL "
            "уже установлены"
        )
        return

    if INSERT_MARKER not in source:
        raise SystemExit(
            "[ERROR] Не найден блок report = {"
        )

    BACKUP.write_text(
        source,
        encoding="utf-8"
    )

    panel = r'''
    # ROOT_JILS_TAIL_PANEL_V1
    # ============================================================
    # ROOT / JILS / TAIL для всех ветвей
    # ============================================================

    def build_zone_counters(
        vector_records,
        branch_name,
    ):
        zones = {
            "ROOT": Counter(),
            "JILS": Counter(),
            "TAIL": Counter(),
        }

        for record in vector_records:
            if branch_name == "source":
                vector = record["source"]["main"]
            else:
                vector = record[branch_name]["main"]

            if len(vector) != 5:
                continue

            zones["ROOT"].update(
                vector[:2]
            )

            zones["JILS"].update(
                vector[2:4]
            )

            zones["TAIL"].update(
                vector[4:5]
            )

        return zones


    def ordered_nodes(counter):
        return sorted(
            counter,
            key=lambda number: (
                -counter[number],
                number,
            ),
        )


    def zone_levels(counter):
        groups = {}

        for number, count in counter.items():
            groups.setdefault(
                count,
                [],
            ).append(number)

        return [
            (
                count,
                sorted(groups[count]),
            )
            for count in sorted(
                groups,
                reverse=True,
            )
        ]


    def format_zone(counter):
        parts = []

        for count, numbers in zone_levels(
            counter
        ):
            node_text = ",".join(
                str(number)
                for number in numbers
            )

            parts.append(
                f"{count}"
            )

        return " > ".join(parts)


    def wing_and_rudder(counter):
        levels = sorted(
            set(counter.values()),
            reverse=True,
        )

        wing_level = (
            levels[0]
            if levels
            else 0
        )

        rudder_level = (
            levels[1]
            if len(levels) > 1
            else 0
        )

        wing = sorted(
            number
            for number, count
            in counter.items()
            if count == wing_level
        )

        rudder = sorted(
            number
            for number, count
            in counter.items()
            if count == rudder_level
        )

        return (
            wing,
            wing_level,
            rudder,
            rudder_level,
        )


    def common_zone_counter(
        direct_counter,
        chiral_counter,
    ):
        result = Counter()

        common_numbers = (
            set(direct_counter)
            & set(chiral_counter)
        )

        for number in common_numbers:
            result[number] = (
                direct_counter[number]
                + chiral_counter[number]
            )

        return result


    def show_zone_branch(
        title,
        zones,
    ):
        print()
        print(title)

        for zone_name in (
            "ROOT",
            "JILS",
            "TAIL",
        ):
            counter = zones[zone_name]

            (
                wing,
                wing_level,
                rudder,
                rudder_level,
            ) = wing_and_rudder(counter)

            print()
            print(
                f" {zone_name} КРЫЛО : "
                f"{wing} | {wing_level}/18"
            )

            print(
                f" {zone_name} РУЛЬ  : "
                f"{rudder} | {rudder_level}/18"
            )

            print(
                f" {zone_name} ПОЛЕ  : "
                f"{format_zone(counter)}"
            )


    source_zone_counters = (
        build_zone_counters(
            records,
            "source",
        )
    )

    direct_zone_counters = (
        build_zone_counters(
            records,
            "without_chirality",
        )
    )

    chiral_zone_counters = (
        build_zone_counters(
            records,
            "with_chirality",
        )
    )

    common_zone_counters = {
        zone_name: common_zone_counter(
            direct_zone_counters[
                zone_name
            ],
            chiral_zone_counters[
                zone_name
            ],
        )
        for zone_name in (
            "ROOT",
            "JILS",
            "TAIL",
        )
    }

    print()
    print("=" * WIDTH)

    print(
        " 🧭 ЗОНАЛЬНАЯ КАРТА "
        "ROOT / JILS / TAIL №82"
    )

    print("=" * WIDTH)

    show_zone_branch(
        " ⚪ ИСХОДНЫЕ ЭКСПЕРТНЫЕ ВЕКТОРЫ",
        source_zone_counters,
    )

    print()
    print("-" * WIDTH)

    show_zone_branch(
        " 🔵 БЕЗ ХИРАЛЬНОСТИ",
        direct_zone_counters,
    )

    print()
    print("-" * WIDTH)

    show_zone_branch(
        " 🟣 С ХИРАЛЬНОСТЬЮ",
        chiral_zone_counters,
    )

    print()
    print("=" * WIDTH)

    print(
        " 🤝 ОБЩИЕ ЗОНАЛЬНЫЕ "
        "АТТРАКТОРЫ"
    )

    print("=" * WIDTH)

    for zone_name in (
        "ROOT",
        "JILS",
        "TAIL",
    ):
        common_counter = (
            common_zone_counters[
                zone_name
            ]
        )

        (
            common_wing,
            common_wing_level,
            common_rudder,
            common_rudder_level,
        ) = wing_and_rudder(
            common_counter
        )

        print()
        print(
            f" {zone_name} ОБЩЕЕ КРЫЛО : "
            f"{common_wing} | "
            f"Σ={common_wing_level}"
        )

        print(
            f" {zone_name} ОБЩИЙ РУЛЬ  : "
            f"{common_rudder} | "
            f"Σ={common_rudder_level}"
        )

        print(
            f" {zone_name} ОБЩЕЕ ПОЛЕ  : "
            f"{format_zone(common_counter)}"
        )

        print(
            f" {zone_name} ДЕТАЛЬНО:"
        )

        for number in ordered_nodes(
            common_counter
        ):
            direct_count = (
                direct_zone_counters[
                    zone_name
                ][number]
            )

            chiral_count = (
                chiral_zone_counters[
                    zone_name
                ][number]
            )

            total = (
                direct_count
                + chiral_count
            )

            print(
                f"   {number:2d}: "
                f"БЕЗ={direct_count:2d} | "
                f"С={chiral_count:2d} | "
                f"Σ={total:2d} | "
                f"{'█' * total}"
            )

    print()
    print("=" * WIDTH)

    print(
        " 🚀 ЗОНЫ ФИНАЛЬНЫХ "
        "ВЕКТОРОВ №82"
    )

    print("=" * WIDTH)

    final_direct_zones = {
        "ROOT": final_direct_main[:2],
        "JILS": final_direct_main[2:4],
        "TAIL": final_direct_main[4:5],
    }

    final_chiral_zones = {
        "ROOT": final_chiral_main[:2],
        "JILS": final_chiral_main[2:4],
        "TAIL": final_chiral_main[4:5],
    }

    print()
    print(" 🔵 БЕЗ ХИРАЛЬНОСТИ")

    print(
        " ROOT :",
        final_direct_zones["ROOT"]
    )

    print(
        " JILS :",
        final_direct_zones["JILS"]
    )

    print(
        " TAIL :",
        final_direct_zones["TAIL"]
    )

    print(
        " EURO :",
        final_direct_euro
    )

    print()
    print(" 🟣 С ХИРАЛЬНОСТЬЮ")

    print(
        " ROOT :",
        final_chiral_zones["ROOT"]
    )

    print(
        " JILS :",
        final_chiral_zones["JILS"]
    )

    print(
        " TAIL :",
        final_chiral_zones["TAIL"]
    )

    print(
        " EURO :",
        final_chiral_euro
    )

    print()
    print(" 🤝 ОБЩИЕ ФИНАЛЬНЫЕ ЗОНЫ")

    common_final_zones = {}

    for zone_name in (
        "ROOT",
        "JILS",
        "TAIL",
    ):
        common_final_zones[
            zone_name
        ] = sorted(
            set(
                final_direct_zones[
                    zone_name
                ]
            )
            & set(
                final_chiral_zones[
                    zone_name
                ]
            )
        )

        print(
            f" {zone_name} : "
            f"{common_final_zones[zone_name]}"
        )

    common_final_zone_euro = sorted(
        set(final_direct_euro)
        & set(final_chiral_euro)
    )

    print(
        " EURO :",
        common_final_zone_euro
    )

    print("=" * WIDTH)

'''

    updated = source.replace(
        INSERT_MARKER,
        panel + "\n" + INSERT_MARKER,
        1,
    )

    TARGET.write_text(
        updated,
        encoding="utf-8"
    )

    print(
        "[OK] Добавлены ROOT / JILS / TAIL"
    )

    print(
        "[OK] Сохранено всё существующее"
    )

    print(
        "[OK] Резервная копия:",
        BACKUP
    )


if __name__ == "__main__":
    main()
