#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter, defaultdict
import json
import math

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

WIDTH = 92

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

TRUST = [
    0.88, 0.91, 0.94, 0.97, 0.85, 0.88,
    0.91, 0.94, 0.97, 0.85, 0.88, 0.91,
    0.94, 0.97, 0.85, 0.88, 0.91, 0.94,
]

ZONE_POSITIONS = {
    "ROOT": (0, 1),
    "JILS": (2, 3),
    "TAIL": (4,),
}

ZONE_INDEX = {
    0: "ROOT",
    1: "ROOT",
    2: "JILS",
    3: "JILS",
    4: "TAIL",
}

ZONE_RADIUS = {
    "ROOT": 0.72,
    "JILS": 1.00,
    "TAIL": 1.28,
}


def load_history():
    history = []

    runtime_draws = list(RAW_DRAWS)

    fact_82_raw = "5.16.32.34.38.8.9"
    fact_82 = list(parse_draw(fact_82_raw))

    expected_fact = [5, 16, 32, 34, 38, 8, 9]

    if fact_82 != expected_fact:
        raise RuntimeError(
            "parse_draw неверно обработал факт №82: "
            + repr(fact_82)
        )

    fact_exists = any(
        list(parse_draw(raw)) == fact_82
        for raw in runtime_draws
    )

    if not fact_exists:
        runtime_draws.append(fact_82_raw)

    for raw in runtime_draws:
        parsed = list(parse_draw(raw))

        if len(parsed) != 7:
            raise ValueError(
                f"Ожидалось 7 значений, получено "
                f"{len(parsed)}: {parsed}"
            )

        main = parsed[:5]
        euro = parsed[5:7]
        history.append(
            (
                list(main),
                list(euro),
            )
        )

    if len(history) != 82:
        raise RuntimeError(
            f"Ожидалось 82 состояния, получено {len(history)}"
        )

    return history


def build_history_stats(history):
    main_frequency = Counter()
    euro_frequency = Counter()

    main_last = {
        number: -1
        for number in range(1, 51)
    }

    euro_last = {
        number: -1
        for number in range(1, 13)
    }

    main_euro_coupling = defaultdict(Counter)

    for index, (main, euro) in enumerate(history):
        main_frequency.update(main)
        euro_frequency.update(euro)

        for number in main:
            main_last[number] = index

            for euro_number in euro:
                main_euro_coupling[number][euro_number] += 1

        for euro_number in euro:
            euro_last[euro_number] = index

    return {
        "main_frequency": main_frequency,
        "euro_frequency": euro_frequency,
        "main_last": main_last,
        "euro_last": euro_last,
        "coupling": main_euro_coupling,
        "history_size": len(history),
    }


def toroidal_point(
    number,
    limit,
    zone,
    reflected=False,
):
    """
    Ограниченная тороидальная труба.

    Хиральная ветвь меняет ориентацию phi,
    но не создаёт числового взрыва и не использует
    искусственное ограничение state=1000.
    """

    phi = (
        2.0
        * math.pi
        * (number - 1)
        / limit
    )

    if reflected:
        phi = -phi

    zone_order = {
        "ROOT": 0,
        "JILS": 1,
        "TAIL": 2,
    }

    theta = (
        2.0
        * math.pi
        * (zone_order[zone] + 0.5)
        / 3.0
    )

    major_radius = 2.0
    minor_radius = ZONE_RADIUS[zone]

    return (
        (
            major_radius
            + minor_radius * math.cos(theta)
        )
        * math.cos(phi),

        (
            major_radius
            + minor_radius * math.cos(theta)
        )
        * math.sin(phi),

        minor_radius * math.sin(theta),
    )


def distance(point_a, point_b):
    return math.sqrt(
        sum(
            (a - b) ** 2
            for a, b in zip(
                point_a,
                point_b,
            )
        )
    )


def main_field(
    vector,
    zone,
    stats,
    reflected=False,
):
    frequency = stats["main_frequency"]
    maximum_frequency = max(
        frequency.values()
    )

    anchors = []

    for position, number in enumerate(vector):
        anchor_zone = ZONE_INDEX[position]

        anchors.append(
            (
                toroidal_point(
                    number,
                    50,
                    anchor_zone,
                    reflected=reflected,
                ),
                anchor_zone,
            )
        )

    scores = {}

    for candidate in range(1, 51):
        candidate_point = toroidal_point(
            candidate,
            50,
            zone,
            reflected=False,
        )

        geometry_score = 0.0

        for anchor_point, anchor_zone in anchors:
            zone_factor = (
                1.0
                if anchor_zone == zone
                else 0.38
            )

            geometry_score += (
                zone_factor
                * math.exp(
                    -distance(
                        candidate_point,
                        anchor_point,
                    )
                    / 1.10
                )
            )

        frequency_score = (
            frequency[candidate]
            / maximum_frequency
        )

        gap_score = (
            stats["history_size"]
            - 1
            - stats["main_last"][candidate]
        ) / stats["history_size"]

        scores[candidate] = (
            0.68 * geometry_score
            + 0.20 * frequency_score
            + 0.12 * gap_score
        )

    return scores


def select_unique(
    scores,
    count,
    used,
):
    selected = []

    order = sorted(
        scores,
        key=lambda number: (
            -scores[number],
            number,
        ),
    )

    for number in order:
        if number in used:
            continue

        selected.append(number)
        used.add(number)

        if len(selected) == count:
            break

    return selected


def calculate_main(
    source,
    stats,
    reflected=False,
):
    used = set()

    root = select_unique(
        main_field(
            source,
            "ROOT",
            stats,
            reflected,
        ),
        2,
        used,
    )

    jils = select_unique(
        main_field(
            source,
            "JILS",
            stats,
            reflected,
        ),
        2,
        used,
    )

    tail = select_unique(
        main_field(
            source,
            "TAIL",
            stats,
            reflected,
        ),
        1,
        used,
    )

    return root + jils + tail


def euro_field(
    main_vector,
    stats,
    expert_index,
    reflected=False,
):
    frequency = stats["euro_frequency"]
    maximum_frequency = max(
        frequency.values()
    )

    maximum_coupling = max(
        1,
        max(
            sum(
                stats["coupling"][main_number][euro]
                for main_number in main_vector
            )
            for euro in range(1, 13)
        ),
    )

    scores = {}

    for euro in range(1, 13):
        frequency_score = (
            frequency[euro]
            / maximum_frequency
        )

        gap_score = (
            stats["history_size"]
            - 1
            - stats["euro_last"][euro]
        ) / stats["history_size"]

        coupling_score = (
            sum(
                stats["coupling"][main_number][euro]
                for main_number in main_vector
            )
            / maximum_coupling
        )

        phase = (
            2.0
            * math.pi
            * (euro - 1)
            / 12.0
        )

        expert_phase = (
            expert_index
            * math.pi
            / 9.0
        )

        if reflected:
            orientation = math.cos(
                -phase + expert_phase
            )
        else:
            orientation = math.cos(
                phase + expert_phase
            )

        orientation_score = (
            orientation + 1.0
        ) / 2.0

        scores[euro] = (
            0.38 * frequency_score
            + 0.36 * coupling_score
            + 0.16 * gap_score
            + 0.10 * orientation_score
        )

    return scores


def calculate_euro(
    main_vector,
    stats,
    expert_index,
    reflected=False,
):
    scores = euro_field(
        main_vector,
        stats,
        expert_index,
        reflected,
    )

    selected = sorted(
        scores,
        key=lambda number: (
            -scores[number],
            number,
        ),
    )[:2]

    return sorted(selected), scores


def average_selected_score(
    scores,
    numbers,
):
    if not numbers:
        return 0.0

    return sum(
        scores[number]
        for number in numbers
    ) / len(numbers)


def update_zones(
    storage,
    vector,
    weight=1.0,
):
    for zone, positions in ZONE_POSITIONS.items():
        for position in positions:
            storage[zone][vector[position]] += weight


def ranked(counter):
    return sorted(
        counter,
        key=lambda number: (
            -counter[number],
            number,
        ),
    )


def grouped(counter):
    groups = {}

    for number, value in counter.items():
        groups.setdefault(
            value,
            [],
        ).append(number)

    return [
        (
            value,
            sorted(groups[value]),
        )
        for value in sorted(
            groups,
            reverse=True,
        )
    ]


def wing_rudder(counter):
    levels = grouped(counter)

    if not levels:
        return [], 0, [], 0

    wing_value, wing = levels[0]

    if len(levels) > 1:
        rudder_value, rudder = levels[1]
    else:
        rudder_value, rudder = 0, []

    return (
        wing,
        wing_value,
        rudder,
        rudder_value,
    )


def format_field(counter):
    parts = []

    for value, numbers in grouped(counter):
        node_text = ",".join(
            str(number)
            for number in numbers
        )

        parts.append(
            f"{value:.2f}"
        )

    return " > ".join(parts) or "нет данных"


def choose_final(zone_scores):
    used = set()

    root = select_unique(
        zone_scores["ROOT"],
        2,
        used,
    )

    jils = select_unique(
        zone_scores["JILS"],
        2,
        used,
    )

    tail = select_unique(
        zone_scores["TAIL"],
        1,
        used,
    )

    return root + jils + tail


def show_zone_map(
    title,
    zones,
):
    print()
    print("=" * WIDTH)
    print(" " + title)
    print("=" * WIDTH)

    for zone in (
        "ROOT",
        "JILS",
        "TAIL",
    ):
        wing, wing_value, rudder, rudder_value = (
            wing_rudder(
                zones[zone]
            )
        )

        print()
        print(
            f" {zone} КРЫЛО : "
            f"{wing} | {wing_value:.2f}"
        )

        print(
            f" {zone} РУЛЬ  : "
            f"{rudder} | {rudder_value:.2f}"
        )

        print(
            f" {zone} ПОЛЕ  : "
            f"{format_field(zones[zone])}"
        )


def main():
    history = load_history()
    stats = build_history_stats(history)

    global_direct = Counter()
    global_chiral = Counter()

    euro_direct = Counter()
    euro_chiral = Counter()

    zones_direct = {
        zone: Counter()
        for zone in ZONE_POSITIONS
    }

    zones_chiral = {
        zone: Counter()
        for zone in ZONE_POSITIONS
    }

    weighted_direct = {
        zone: Counter()
        for zone in ZONE_POSITIONS
    }

    weighted_chiral = {
        zone: Counter()
        for zone in ZONE_POSITIONS
    }

    records = []

    print("=" * WIDTH)
    print(
        " МАЛЫШ v12 "
        "[ПОЛНЫЙ ПЕРЕСЧЁТ №83: "
        "ТРУБА + ХИРАЛЬНОСТЬ + EURO]"
    )
    print("=" * WIDTH)

    print(
        " [✓] 82 исторических состояния"
    )

    print(
        " [✓] 574 входных значения"
    )

    print(
        " [✓] Геометрия: bounded toroidal"
    )

    print(
        " [✓] ROOT=2 / JILS=2 / TAIL=1"
    )

    for index, (name, expert) in enumerate(
        EXPERTS,
        start=1,
    ):
        source = list(
            expert(history)
        )

        direct = calculate_main(
            source,
            stats,
            reflected=False,
        )

        chiral = calculate_main(
            source,
            stats,
            reflected=True,
        )

        direct_euro, direct_euro_scores = (
            calculate_euro(
                direct,
                stats,
                index,
                reflected=False,
            )
        )

        chiral_euro, chiral_euro_scores = (
            calculate_euro(
                chiral,
                stats,
                index,
                reflected=True,
            )
        )

        trust = TRUST[index - 1]

        weight = round(
            95.0
            + (index % 6) * 1.5,
            1,
        )

        pressure = round(
            0.10
            + (index % 4) * 0.04,
            2,
        )

        direct_tube_scores = {}
        chiral_tube_scores = {}

        for zone, positions in ZONE_POSITIONS.items():
            direct_scores = main_field(
                source,
                zone,
                stats,
                reflected=False,
            )

            chiral_scores = main_field(
                source,
                zone,
                stats,
                reflected=True,
            )

            direct_numbers = [
                direct[position]
                for position in positions
            ]

            chiral_numbers = [
                chiral[position]
                for position in positions
            ]

            direct_tube_scores[zone] = (
                average_selected_score(
                    direct_scores,
                    direct_numbers,
                )
            )

            chiral_tube_scores[zone] = (
                average_selected_score(
                    chiral_scores,
                    chiral_numbers,
                )
            )

        direct_euro_score = (
            average_selected_score(
                direct_euro_scores,
                direct_euro,
            )
        )

        chiral_euro_score = (
            average_selected_score(
                chiral_euro_scores,
                chiral_euro,
            )
        )

        global_direct.update(direct)
        global_chiral.update(chiral)

        euro_direct.update(direct_euro)
        euro_chiral.update(chiral_euro)

        update_zones(
            zones_direct,
            direct,
        )

        update_zones(
            zones_chiral,
            chiral,
        )

        update_zones(
            weighted_direct,
            direct,
            trust,
        )

        update_zones(
            weighted_chiral,
            chiral,
            trust,
        )

        common_main = sorted(
            set(direct)
            & set(chiral)
        )

        common_euro = sorted(
            set(direct_euro)
            & set(chiral_euro)
        )

        print()
        print("─" * WIDTH)

        print(
            f" [{name:<31}] "
            f"| Вес {weight:<5.1f} "
            f"| Pressure {pressure:.2f} "
            f"| Trust {trust:.2f}"
        )

        print(
            f"   ИСХОДНЫЙ : "
            f"ROOT {source[:2]} | "
            f"JILS {source[2:4]} | "
            f"TAIL {source[4:]}"
        )

        print()
        print("   🔵 БЕЗ ХИРАЛЬНОСТИ")

        print(
            f"      ROOT {direct[:2]} "
            f"| TubeScore "
            f"{direct_tube_scores['ROOT']:.6f}"
        )

        print(
            f"      JILS {direct[2:4]} "
            f"| TubeScore "
            f"{direct_tube_scores['JILS']:.6f}"
        )

        print(
            f"      TAIL {direct[4:]} "
            f"| TubeScore "
            f"{direct_tube_scores['TAIL']:.6f}"
        )

        print(
            f"      EURO {direct_euro} "
            f"| EuroScore "
            f"{direct_euro_score:.6f}"
        )

        print()
        print("   🟣 С ХИРАЛЬНОСТЬЮ")

        print(
            f"      ROOT {chiral[:2]} "
            f"| TubeScore "
            f"{chiral_tube_scores['ROOT']:.6f}"
        )

        print(
            f"      JILS {chiral[2:4]} "
            f"| TubeScore "
            f"{chiral_tube_scores['JILS']:.6f}"
        )

        print(
            f"      TAIL {chiral[4:]} "
            f"| TubeScore "
            f"{chiral_tube_scores['TAIL']:.6f}"
        )

        print(
            f"      EURO {chiral_euro} "
            f"| EuroScore "
            f"{chiral_euro_score:.6f}"
        )

        print()
        print(
            f"   🤝 ОБЩИЕ MAIN : "
            f"{common_main}"
        )

        print(
            f"   🤝 ОБЩИЕ EURO : "
            f"{common_euro}"
        )

        print(
            f"   🪞 MAIN +ВОШЛИ : "
            f"{sorted(set(chiral) - set(direct))}"
        )

        print(
            f"   🪞 MAIN -ВЫШЛИ : "
            f"{sorted(set(direct) - set(chiral))}"
        )

        records.append({
            "id": index,
            "name": name,
            "weight": weight,
            "pressure": pressure,
            "trust": trust,

            "source": {
                "main": source,
                "root": source[:2],
                "jils": source[2:4],
                "tail": source[4:],
            },

            "without_chirality": {
                "main": direct,
                "root": direct[:2],
                "jils": direct[2:4],
                "tail": direct[4:],
                "euro": direct_euro,
                "tube_scores": direct_tube_scores,
                "euro_score": direct_euro_score,
            },

            "with_chirality": {
                "main": chiral,
                "root": chiral[:2],
                "jils": chiral[2:4],
                "tail": chiral[4:],
                "euro": chiral_euro,
                "tube_scores": chiral_tube_scores,
                "euro_score": chiral_euro_score,
            },

            "common": {
                "main": common_main,
                "euro": common_euro,
            },
        })

    show_zone_map(
        "🔵 ЗОНАЛЬНАЯ КАРТА БЕЗ ХИРАЛЬНОСТИ",
        zones_direct,
    )

    show_zone_map(
        "🟣 ЗОНАЛЬНАЯ КАРТА С ХИРАЛЬНОСТЬЮ",
        zones_chiral,
    )

    common_zones = {
        zone: Counter()
        for zone in ZONE_POSITIONS
    }

    for zone in ZONE_POSITIONS:
        common_numbers = (
            set(zones_direct[zone])
            & set(zones_chiral[zone])
        )

        for number in common_numbers:
            common_zones[zone][number] = (
                zones_direct[zone][number]
                + zones_chiral[zone][number]
            )

    show_zone_map(
        "🤝 ОБЩАЯ ЗОНАЛЬНАЯ КАРТА",
        common_zones,
    )

    final_direct = choose_final(
        weighted_direct
    )

    final_chiral = choose_final(
        weighted_chiral
    )

    final_direct_euro = sorted(
        ranked(euro_direct)[:2]
    )

    final_chiral_euro = sorted(
        ranked(euro_chiral)[:2]
    )

    direct_wing = wing_rudder(
        global_direct
    )

    chiral_wing = wing_rudder(
        global_chiral
    )

    print()
    print("=" * WIDTH)
    print(
        " 🧭 ЧЕЛОВЕЧЕСКИЙ ИТОГ "
        "МАЛЫША №82"
    )
    print("=" * WIDTH)

    print()
    print(" 🔵 БЕЗ ХИРАЛЬНОСТИ")

    print(
        f" ROOT : {final_direct[:2]}"
    )

    print(
        f" JILS : {final_direct[2:4]}"
    )

    print(
        f" TAIL : {final_direct[4:]}"
    )

    print(
        f" EURO : {final_direct_euro}"
    )

    print(
        f" ✈ КРЫЛО : "
        f"{direct_wing[0]} "
        f"| {direct_wing[1]}/18"
    )

    print(
        f" 🛞 РУЛЬ  : "
        f"{direct_wing[2]} "
        f"| {direct_wing[3]}/18"
    )

    print()
    print(" 🟣 С ХИРАЛЬНОСТЬЮ")

    print(
        f" ROOT : {final_chiral[:2]}"
    )

    print(
        f" JILS : {final_chiral[2:4]}"
    )

    print(
        f" TAIL : {final_chiral[4:]}"
    )

    print(
        f" EURO : {final_chiral_euro}"
    )

    print(
        f" ✈ КРЫЛО : "
        f"{chiral_wing[0]} "
        f"| {chiral_wing[1]}/18"
    )

    print(
        f" 🛞 РУЛЬ  : "
        f"{chiral_wing[2]} "
        f"| {chiral_wing[3]}/18"
    )

    print()
    print(" 🤝 ОБЩИЕ")

    print(
        " MAIN :",
        sorted(
            set(final_direct)
            & set(final_chiral)
        )
    )

    print(
        " EURO :",
        sorted(
            set(final_direct_euro)
            & set(final_chiral_euro)
        )
    )

    print()
    print(" 🪞 ХИРАЛЬНАЯ Δ")

    print(
        " + ВОШЛИ :",
        sorted(
            set(final_chiral)
            - set(final_direct)
        )
    )

    print(
        " - ВЫШЛИ :",
        sorted(
            set(final_direct)
            - set(final_chiral)
        )
    )

    print("=" * WIDTH)

    report = {
        "target": 83,
        "history": 82,
        "total_values": 574,
        "actual_state_82": {
            "main": [5, 16, 32, 34, 38],
            "euro": [8, 9],
            "raw": "5.16.32.34.38.8.9",
        },
        "calculation_mode": (
            "fixed_legacy_probes_"
            "history_dependent_bounded_toroidal"
        ),
        "geometry": "bounded_toroidal",
        "vectors": records,

        "final": {
            "without_chirality": {
                "main": final_direct,
                "root": final_direct[:2],
                "jils": final_direct[2:4],
                "tail": final_direct[4:],
                "euro": final_direct_euro,
            },

            "with_chirality": {
                "main": final_chiral,
                "root": final_chiral[:2],
                "jils": final_chiral[2:4],
                "tail": final_chiral[4:],
                "euro": final_chiral_euro,
            },
        },
    }

    with open(
        "malysh_v12_recalculated_83.json",
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
        " [✓] JSON: "
        "malysh_v12_recalculated_83.json"
    )


if __name__ == "__main__":
    main()
