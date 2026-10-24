#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter
from contextlib import redirect_stdout
from io import StringIO
import json

from run_pipeline import (
    MalyshResonanceEngine as DirectEngine,
    MalyshDataPipeline as DirectPipeline,
)

from run_reflected_pipeline import (
    MalyshResonanceEngine as ChiralEngine,
    MalyshDataPipeline as ChiralPipeline,
)

from run_chiral_v12_full_master import (
    RAW_DRAWS,
    parse_draw,
    expert_v1, expert_v2, expert_v3,
    expert_v4, expert_v5, expert_v6,
    expert_v7, expert_v8, expert_v9,
    expert_v10, expert_v11, expert_v12,
    expert_v13, expert_v14, expert_v15,
    expert_v16, expert_v17, expert_v18,
)

WIDTH = 110

EXPERTS = [
    ("V1  EWMA Frequency", expert_v1),
    ("V2  Кластерный резонанс", expert_v2),
    ("V3  Модульная гармоника", expert_v3),
    ("V4  Interval Acceleration", expert_v4),
    ("V5  Markov Transitions", expert_v5),
    ("V6  Пространственная матрица", expert_v6),
    ("V7  Кватернарная логика", expert_v7),
    ("V8  Простые числа", expert_v8),
    ("V9  Series Momentum", expert_v9),
    ("V10 Anti-Cause", expert_v10),
    ("V11 Геометрия трубы", expert_v11),
    ("V12 Similarity Matching", expert_v12),
    ("V13 Causal Recovery", expert_v13),
    ("V14 Энтропийный хаос", expert_v14),
    ("V15 Historical Accuracy", expert_v15),
    ("V16 Node Survival Index", expert_v16),
    ("V17 Full Tube Drift", expert_v17),
    ("V18 Camp Accuracy", expert_v18),
]


def build_direct_pipeline():
    engine = DirectEngine(
        R6=12.0,
        R5=4.5,
        theta_0=0.5,
        a=0.05,
        k=0.08,
    )

    geometry = engine.compute_n7_nodes(
        phi_0=0.0,
        d_phi=0.05,
        n_max=400,
    )

    return DirectPipeline(
        n7_nodes=geometry["n7_indices"],
        valid_trajectory=geometry["valid_trajectory"],
    )


def build_chiral_pipeline():
    engine = ChiralEngine(
        R6=12.0,
        R5=4.5,
        theta_0=0.5,
        a=0.08,
        k=0.06,
    )

    geometry = engine.generate_bounded_trajectory(
        phi_0=0.0,
        d_phi=0.05,
        n_max=350,
    )

    return ChiralPipeline(
        n7_nodes=geometry["n7_indices"],
        trajectory=geometry["trajectory"],
    )


def execute_quietly(pipeline, initial_state):
    buffer = StringIO()

    with redirect_stdout(buffer):
        log = pipeline.execute_stream(
            initial_state=float(initial_state)
        )

    if not log:
        raise RuntimeError("Контур вернул пустой журнал")

    return log[-1]


def project_number(state, original, limit):
    """
    Детерминированная проекция непрерывного состояния Малыша
    обратно в дискретное поле 1..limit.
    """

    residue = int(
        abs(state) * 1_000_003
        + original * 97
    )

    return 1 + residue % limit


def unique_field(values, limit, count):
    result = []
    used = set()

    for value in values:
        candidate = int(value)

        while candidate in used:
            candidate += 1

            if candidate > limit:
                candidate = 1

        used.add(candidate)
        result.append(candidate)

        if len(result) == count:
            break

    return sorted(result)


def transform_vector(vector, pipeline, limit):
    transformed = []
    diagnostics = []

    for number in vector:
        last = execute_quietly(
            pipeline,
            initial_state=number,
        )

        projected = project_number(
            state=last["state"],
            original=number,
            limit=limit,
        )

        transformed.append(projected)

        diagnostics.append({
            "input": number,
            "output": projected,
            "final_state": last["state"],
            "mode": last["mode"],
            "step": last["step"],
            "point": last["point"],
        })

    return (
        unique_field(
            transformed,
            limit=limit,
            count=len(vector),
        ),
        diagnostics,
    )


def euro_for_expert(index):
    return [
        (index % 12) + 1,
        ((index + 2) % 12) + 1,
    ]


def ranked(counter):
    return [
        number
        for number, count
        in counter.most_common()
    ]


def final_main(counter):
    ordered = ranked(counter)
    return unique_field(
        ordered,
        limit=50,
        count=5,
    )


def final_euro(counter):
    ordered = ranked(counter)
    return unique_field(
        ordered,
        limit=12,
        count=2,
    )


def print_density(title, counter):
    print()
    print("=" * WIDTH)
    print(" " + title)
    print("=" * WIDTH)

    groups = {}

    for number, count in counter.items():
        groups.setdefault(
            count,
            []
        ).append(number)

    for count in sorted(
        groups,
        reverse=True
    ):
        numbers = sorted(groups[count])

        print(
            f" • Поддержка {count:2d} векторов : "
            f"{numbers} | {'█' * count}"
        )


def main():
    history = [
        parse_draw(line)
        for line in RAW_DRAWS
    ]

    if len(history) != 82:
        raise RuntimeError(
            f"Ожидалось 82 состояния, "
            f"получено {len(history)}"
        )

    direct_pipeline = build_direct_pipeline()
    chiral_pipeline = build_chiral_pipeline()

    direct_main_support = Counter()
    chiral_main_support = Counter()

    direct_euro_support = Counter()
    chiral_euro_support = Counter()

    records = []

    print("=" * WIDTH)
    print(
        " МАЛЫШ v12 "
        "[РАСЧЁТ №82: БЕЗ ХИРАЛЬНОСТИ / С ХИРАЛЬНОСТЬЮ]"
    )
    print("=" * WIDTH)

    print(
        f" [✓] Исторических состояний : {len(history)}"
    )

    print(
        f" [✓] Всего входных значений : "
        f"{len(history) * 7}"
    )

    print(
        " [✓] Прямая ветвь           : run_pipeline.py"
    )

    print(
        " [✓] Хиральная ветвь         : "
        "run_reflected_pipeline.py"
    )

    print()
    print(
        " 🔬 1. ДЕТАЛЬНЫЙ ВЫВОД "
        "ПО 18 ЭКСПЕРТНЫМ ВЕКТОРАМ"
    )
    print("=" * WIDTH)

    for index, (name, expert) in enumerate(
        EXPERTS,
        start=1
    ):
        source_main = list(
            expert(history)
        )

        source_euro = euro_for_expert(index)

        direct_main, direct_diag = transform_vector(
            source_main,
            direct_pipeline,
            limit=50,
        )

        chiral_main, chiral_diag = transform_vector(
            source_main,
            chiral_pipeline,
            limit=50,
        )

        direct_euro, direct_euro_diag = transform_vector(
            source_euro,
            direct_pipeline,
            limit=12,
        )

        chiral_euro, chiral_euro_diag = transform_vector(
            source_euro,
            chiral_pipeline,
            limit=12,
        )

        direct_main_support.update(
            direct_main
        )

        chiral_main_support.update(
            chiral_main
        )

        direct_euro_support.update(
            direct_euro
        )

        chiral_euro_support.update(
            chiral_euro
        )

        added = sorted(
            set(chiral_main)
            - set(direct_main)
        )

        removed = sorted(
            set(direct_main)
            - set(chiral_main)
        )

        common = sorted(
            set(direct_main)
            & set(chiral_main)
        )

        weight = round(
            95.0 + (index % 6) * 1.5,
            1,
        )

        pressure = round(
            0.10 + (index % 4) * 0.04,
            2,
        )

        trust = round(
            0.85 + (index % 5) * 0.03,
            2,
        )

        print(
            f" [{name:<31}] "
            f"| Вес: {weight:<5.1f} "
            f"| Pressure: {pressure:.2f} "
            f"| Trust: {trust:.2f}"
        )

        print(
            f"   ИСХОДНЫЙ MAIN           : "
            f"{source_main}"
        )

        print(
            f"   БЕЗ ХИРАЛЬНОСТИ MAIN    : "
            f"{direct_main}"
        )

        print(
            f"   С ХИРАЛЬНОСТЬЮ MAIN     : "
            f"{chiral_main}"
        )

        print(
            f"   ИСХОДНЫЙ EURO           : "
            f"{source_euro}"
        )

        print(
            f"   БЕЗ ХИРАЛЬНОСТИ EURO    : "
            f"{direct_euro}"
        )

        print(
            f"   С ХИРАЛЬНОСТЬЮ EURO     : "
            f"{chiral_euro}"
        )

        print(
            f"   ХИРАЛЬНАЯ Δ             : "
            f"+{added} -{removed} "
            f"| общие={common}"
        )

        print(
            "   ПРЯМОЙ КОНТУР           : "
            f"mode={direct_diag[-1]['mode']} "
            f"| step={direct_diag[-1]['step']} "
            f"| state={direct_diag[-1]['final_state']:.6f}"
        )

        print(
            "   ХИРАЛЬНЫЙ КОНТУР        : "
            f"mode={chiral_diag[-1]['mode']} "
            f"| step={chiral_diag[-1]['step']} "
            f"| state={chiral_diag[-1]['final_state']:.6f}"
        )

        print(
            " " + "─" * (WIDTH - 2)
        )

        records.append({
            "id": index,
            "name": name,
            "source": {
                "main": source_main,
                "euro": source_euro,
            },
            "without_chirality": {
                "main": direct_main,
                "euro": direct_euro,
                "main_diagnostics": direct_diag,
                "euro_diagnostics": direct_euro_diag,
            },
            "with_chirality": {
                "main": chiral_main,
                "euro": chiral_euro,
                "main_diagnostics": chiral_diag,
                "euro_diagnostics": chiral_euro_diag,
            },
            "delta": {
                "added": added,
                "removed": removed,
                "common": common,
            },
        })

    print_density(
        "📊 2A. ПЛОТНОСТЬ БЕЗ ХИРАЛЬНОСТИ",
        direct_main_support,
    )

    print_density(
        "📊 2B. ПЛОТНОСТЬ С ХИРАЛЬНОСТЬЮ",
        chiral_main_support,
    )

    final_direct_main = final_main(
        direct_main_support
    )

    final_chiral_main = final_main(
        chiral_main_support
    )

    final_direct_euro = final_euro(
        direct_euro_support
    )

    final_chiral_euro = final_euro(
        chiral_euro_support
    )

    delta_added = sorted(
        set(final_chiral_main)
        - set(final_direct_main)
    )

    delta_removed = sorted(
        set(final_direct_main)
        - set(final_chiral_main)
    )

    delta_common = sorted(
        set(final_direct_main)
        & set(final_chiral_main)
    )

    print()
    print("=" * WIDTH)
    print(" 🚀 3. ИТОГОВЫЙ РАСЧЁТ СОСТОЯНИЯ №82")
    print("=" * WIDTH)

    print()
    print(" БЕЗ ХИРАЛЬНОСТИ")
    print(
        f" MAIN : {final_direct_main}"
    )
    print(
        f" EURO : {final_direct_euro}"
    )

    print()
    print(" С ХИРАЛЬНОСТЬЮ")
    print(
        f" MAIN : {final_chiral_main}"
    )
    print(
        f" EURO : {final_chiral_euro}"
    )

    print()
    print(" ХИРАЛЬНАЯ Δ")
    print(
        f" Добавлены : {delta_added}"
    )
    print(
        f" Удалены   : {delta_removed}"
    )
    print(
        f" Общие     : {delta_common}"
    )

    print("=" * WIDTH)


    # ============================================================
    # ЧЕЛОВЕЧЕСКАЯ НАВИГАЦИОННАЯ ПАНЕЛЬ
    # ============================================================

    def support_layers(counter):
        levels = sorted(
            set(counter.values()),
            reverse=True
        )

        wing_level = levels[0] if levels else 0
        rudder_level = levels[1] if len(levels) > 1 else 0

        wing = sorted(
            n for n, c in counter.items()
            if c == wing_level
        )

        rudder = sorted(
            n for n, c in counter.items()
            if c == rudder_level
        )

        return wing, wing_level, rudder, rudder_level

    direct_wing, direct_wing_level, direct_rudder, direct_rudder_level = (
        support_layers(direct_main_support)
    )

    chiral_wing, chiral_wing_level, chiral_rudder, chiral_rudder_level = (
        support_layers(chiral_main_support)
    )

    direct_attractors = sorted(
        direct_main_support,
        key=lambda n: (
            -direct_main_support[n],
            n
        )
    )

    chiral_attractors = sorted(
        chiral_main_support,
        key=lambda n: (
            -chiral_main_support[n],
            n
        )
    )

    common_nodes = sorted(
        set(direct_main_support)
        & set(chiral_main_support)
    )

    common_strength = {
        n: (
            direct_main_support[n]
            + chiral_main_support[n]
        )
        for n in common_nodes
    }

    common_attractors = sorted(
        common_nodes,
        key=lambda n: (
            -common_strength[n],
            n
        )
    )

    common_final_main = sorted(
        set(final_direct_main)
        & set(final_chiral_main)
    )

    common_final_euro = sorted(
        set(final_direct_euro)
        & set(final_chiral_euro)
    )

    common_euro_field = sorted(
        set(direct_euro_support)
        & set(chiral_euro_support)
    )

    print()
    print("=" * WIDTH)
    print(" 🧭 НАВИГАЦИОННАЯ КАРТА МАЛЫША №82")
    print("=" * WIDTH)

    print()
    print(" 🔵 БЕЗ ХИРАЛЬНОСТИ")
    print(
        f" ✈️ КРЫЛО : {direct_wing} "
        f"| {direct_wing_level}/18"
    )
    print(
        f" 🛞 РУЛЬ  : {direct_rudder} "
        f"| {direct_rudder_level}/18"
    )

    print(" 🧲 АТТРАКТОРЫ:")
    print(
        "   "
        + " > ".join(
            f"{n}({direct_main_support[n]})"
            for n in direct_attractors
        )
    )

    print()
    print(" 🟣 С ХИРАЛЬНОСТЬЮ")
    print(
        f" ✈️ КРЫЛО : {chiral_wing} "
        f"| {chiral_wing_level}/18"
    )
    print(
        f" 🛞 РУЛЬ  : {chiral_rudder} "
        f"| {chiral_rudder_level}/18"
    )

    print(" 🧲 АТТРАКТОРЫ:")
    print(
        "   "
        + " > ".join(
            f"{n}({chiral_main_support[n]})"
            for n in chiral_attractors
        )
    )

    print()
    print("=" * WIDTH)
    print(" 🤝 ОБЩЕЕ ПОЛЕ ДВУХ ВЕТВЕЙ")
    print("=" * WIDTH)

    print(
        f" ОБЩИЕ УЗЛЫ MAIN : {common_nodes}"
    )

    print(
        f" ОБЩИЕ УЗЛЫ EURO : {common_euro_field}"
    )

    print()
    print(" 🧲 ОБЩИЕ АТТРАКТОРЫ:")

    for n in common_attractors:
        direct = direct_main_support[n]
        chiral = chiral_main_support[n]
        total = common_strength[n]

        print(
            f" • {n:2d} : "
            f"БЕЗ={direct:2d} | "
            f"С={chiral:2d} | "
            f"Σ={total:2d} | "
            f"{'█' * total}"
        )

    print()
    print("=" * WIDTH)
    print(" 🚀 ЧЕЛОВЕЧЕСКИЙ ИТОГ МАЛЫША №82")
    print("=" * WIDTH)

    print()
    print(" 🔵 БЕЗ ХИРАЛЬНОСТИ")
    print(f" MAIN : {final_direct_main}")
    print(f" EURO : {final_direct_euro}")
    print(f" ✈️ КРЫЛО : {direct_wing}")
    print(f" 🛞 РУЛЬ  : {direct_rudder}")

    print()
    print(" 🟣 С ХИРАЛЬНОСТЬЮ")
    print(f" MAIN : {final_chiral_main}")
    print(f" EURO : {final_chiral_euro}")
    print(f" ✈️ КРЫЛО : {chiral_wing}")
    print(f" 🛞 РУЛЬ  : {chiral_rudder}")

    print()
    print(" 🤝 ОБЩЕЕ")
    print(f" MAIN ФИНАЛ : {common_final_main}")
    print(f" EURO ФИНАЛ : {common_final_euro}")
    print(f" MAIN ПОЛЕ  : {common_nodes}")
    print(f" EURO ПОЛЕ  : {common_euro_field}")

    print()
    print(" 🪞 ХИРАЛЬНАЯ Δ")
    print(f" + ВОШЛИ : {delta_added}")
    print(f" - ВЫШЛИ : {delta_removed}")
    print(f" = ОБЩИЕ : {delta_common}")

    print("=" * WIDTH)



    # ============================================================
    # ЗОНАЛЬНАЯ КАРТА ROOT / JILS / TAIL №82
    # ============================================================

    def build_zone_support(vector_records, branch):
        root_support = Counter()
        jils_support = Counter()
        tail_support = Counter()

        for item in vector_records:
            if branch == "source":
                vector = item["source"]["main"]
            else:
                vector = item[branch]["main"]

            if len(vector) != 5:
                continue

            root_support.update(vector[:2])
            jils_support.update(vector[2:4])
            tail_support.update(vector[4:5])

        return {
            "root": root_support,
            "jils": jils_support,
            "tail": tail_support,
        }


    def zone_ranking(counter):
        return sorted(
            counter,
            key=lambda number: (
                -counter[number],
                number,
            ),
        )


    def zone_groups(counter):
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


    def zone_line(counter):
        parts = []

        for count, numbers in zone_groups(counter):
            joined = ",".join(
                str(number)
                for number in numbers
            )

            parts.append(
                f"[{joined}]({count})"
            )

        return " > ".join(parts)


    def zone_leaders(counter):
        if not counter:
            return [], 0

        maximum = max(counter.values())

        leaders = sorted(
            number
            for number, count in counter.items()
            if count == maximum
        )

        return leaders, maximum


    def combined_zone(
        direct_counter,
        chiral_counter,
    ):
        common_numbers = sorted(
            set(direct_counter)
            & set(chiral_counter)
        )

        combined = Counter()

        for number in common_numbers:
            combined[number] = (
                direct_counter[number]
                + chiral_counter[number]
            )

        return combined


    source_zones = build_zone_support(
        records,
        "source",
    )

    direct_zones = build_zone_support(
        records,
        "without_chirality",
    )

    chiral_zones = build_zone_support(
        records,
        "with_chirality",
    )

    common_zones = {
        zone: combined_zone(
            direct_zones[zone],
            chiral_zones[zone],
        )
        for zone in (
            "root",
            "jils",
            "tail",
        )
    }

    zone_labels = {
        "root": "ROOT",
        "jils": "JILS",
        "tail": "TAIL",
    }

    print()
    print("=" * WIDTH)
    print(
        " 🧭 ЗОНАЛЬНАЯ КАРТА "
        "ROOT / JILS / TAIL №82"
    )
    print("=" * WIDTH)

    print()
    print(" ⚪ ИСХОДНЫЕ ЭКСПЕРТНЫЕ ВЕКТОРЫ")

    for zone in (
        "root",
        "jils",
        "tail",
    ):
        leaders, strength = zone_leaders(
            source_zones[zone]
        )

        print(
            f" {zone_labels[zone]:4} КРЫЛО : "
            f"{leaders} | {strength}/18"
        )

        print(
            f" {zone_labels[zone]:4} ПОЛЕ  : "
            f"{zone_line(source_zones[zone])}"
        )

    print()
    print("-" * WIDTH)
    print(" 🔵 БЕЗ ХИРАЛЬНОСТИ")

    for zone in (
        "root",
        "jils",
        "tail",
    ):
        leaders, strength = zone_leaders(
            direct_zones[zone]
        )

        print(
            f" {zone_labels[zone]:4} КРЫЛО : "
            f"{leaders} | {strength}/18"
        )

        print(
            f" {zone_labels[zone]:4} ПОЛЕ  : "
            f"{zone_line(direct_zones[zone])}"
        )

    print()
    print("-" * WIDTH)
    print(" 🟣 С ХИРАЛЬНОСТЬЮ")

    for zone in (
        "root",
        "jils",
        "tail",
    ):
        leaders, strength = zone_leaders(
            chiral_zones[zone]
        )

        print(
            f" {zone_labels[zone]:4} КРЫЛО : "
            f"{leaders} | {strength}/18"
        )

        print(
            f" {zone_labels[zone]:4} ПОЛЕ  : "
            f"{zone_line(chiral_zones[zone])}"
        )

    print()
    print("=" * WIDTH)
    print(
        " 🤝 ОБЩАЯ ЗОНАЛЬНАЯ КАРТА "
        "БЕЗ + С ХИРАЛЬНОСТЬЮ"
    )
    print("=" * WIDTH)

    for zone in (
        "root",
        "jils",
        "tail",
    ):
        common_counter = common_zones[zone]

        leaders, strength = zone_leaders(
            common_counter
        )

        common_numbers = sorted(
            common_counter
        )

        print()
        print(
            f" {zone_labels[zone]} "
            f"ОБЩИЕ УЗЛЫ : {common_numbers}"
        )

        print(
            f" {zone_labels[zone]} "
            f"ОБЩЕЕ КРЫЛО : "
            f"{leaders} | Σ={strength}"
        )

        print(
            f" {zone_labels[zone]} "
            f"ОБЩЕЕ ПОЛЕ  : "
            f"{zone_line(common_counter)}"
        )

        print(
            f" {zone_labels[zone]} "
            "ДЕТАЛЬНО:"
        )

        for number in zone_ranking(
            common_counter
        ):
            direct_count = (
                direct_zones[zone][number]
            )

            chiral_count = (
                chiral_zones[zone][number]
            )

            total = (
                direct_count
                + chiral_count
            )

            print(
                f"   • {number:2d} : "
                f"БЕЗ={direct_count:2d} | "
                f"С={chiral_count:2d} | "
                f"Σ={total:2d} | "
                f"{'█' * total}"
            )

    print()
    print("=" * WIDTH)
    print(" 🚀 ЗОНЫ ФИНАЛЬНЫХ ВЕКТОРОВ №82")
    print("=" * WIDTH)

    print()
    print(" 🔵 БЕЗ ХИРАЛЬНОСТИ")
    print(
        f" ROOT : {final_direct_main[:2]}"
    )
    print(
        f" JILS : {final_direct_main[2:4]}"
    )
    print(
        f" TAIL : {final_direct_main[4:5]}"
    )
    print(
        f" EURO : {final_direct_euro}"
    )

    print()
    print(" 🟣 С ХИРАЛЬНОСТЬЮ")
    print(
        f" ROOT : {final_chiral_main[:2]}"
    )
    print(
        f" JILS : {final_chiral_main[2:4]}"
    )
    print(
        f" TAIL : {final_chiral_main[4:5]}"
    )
    print(
        f" EURO : {final_chiral_euro}"
    )

    print()
    print(" 🤝 ОБЩИЕ ФИНАЛЬНЫЕ ЗОНЫ")

    direct_final_zones = {
        "root": set(final_direct_main[:2]),
        "jils": set(final_direct_main[2:4]),
        "tail": set(final_direct_main[4:5]),
    }

    chiral_final_zones = {
        "root": set(final_chiral_main[:2]),
        "jils": set(final_chiral_main[2:4]),
        "tail": set(final_chiral_main[4:5]),
    }

    common_final_zones = {}

    for zone in (
        "root",
        "jils",
        "tail",
    ):
        common_final_zones[zone] = sorted(
            direct_final_zones[zone]
            & chiral_final_zones[zone]
        )

        print(
            f" {zone_labels[zone]:4} : "
            f"{common_final_zones[zone]}"
        )

    print(
        " EURO : "
        f"{sorted(set(final_direct_euro) & set(final_chiral_euro))}"
    )

    print("=" * WIDTH)



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


    report = {
        "target_state": 82,
        "historical_states": len(history),
        "total_values": len(history) * 7,
        "vectors": records,
        "final": {
            "without_chirality": {
                "main": final_direct_main,
                "euro": final_direct_euro,
            },
            "with_chirality": {
                "main": final_chiral_main,
                "euro": final_chiral_euro,
            },
            "delta": {
                "added": delta_added,
                "removed": delta_removed,
                "common": delta_common,
            },
        },
    }

    with open(
        "malysh_v12_chirality_result_82.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        " [✓] Полный JSON: "
        "malysh_v12_chirality_result_82.json"
    )


if __name__ == "__main__":
    main()
