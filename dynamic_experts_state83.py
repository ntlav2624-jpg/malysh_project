#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Динамические эксперты состояния №83.

Каждый эксперт получает 82 исторических состояния и формирует
новый MAIN-вектор из статистики истории.

Это реконструированная реализация экспертов, а не восстановленная
из Git исходная версия старых алгоритмов.
"""

from collections import Counter, defaultdict
import math


PRIMES = {
    2, 3, 5, 7, 11, 13, 17, 19,
    23, 29, 31, 37, 41, 43, 47,
}


def normalize_history(history):
    result = []

    for state in history:
        if isinstance(state, dict):
            main = (
                state.get("main")
                or state.get("numbers")
                or state.get("primary")
            )

            euro = (
                state.get("euro")
                or state.get("stars")
                or state.get("secondary")
                or []
            )

        elif isinstance(state, (list, tuple)):
            if len(state) == 7:
                main = state[:5]
                euro = state[5:7]

            elif len(state) == 2:
                main, euro = state

            else:
                raise ValueError(
                    "Неизвестная запись истории: "
                    + repr(state)
                )

        else:
            raise TypeError(
                "Неизвестный тип записи истории: "
                + type(state).__name__
            )

        main = [int(value) for value in main]
        euro = [int(value) for value in euro]

        if len(main) != 5:
            raise ValueError(
                "MAIN должен содержать 5 значений: "
                + repr(main)
            )

        if len(euro) != 2:
            raise ValueError(
                "EURO должен содержать 2 значения: "
                + repr(euro)
            )

        result.append((main, euro))

    if not result:
        raise ValueError("История пуста")

    return result


def build_stats(history):
    states = normalize_history(history)
    total = len(states)

    frequency = Counter()
    weighted_frequency = Counter()
    position_frequency = [
        Counter()
        for _ in range(5)
    ]

    last_seen = {
        number: -1
        for number in range(1, 51)
    }

    previous_seen = {
        number: -1
        for number in range(1, 51)
    }

    transitions = defaultdict(Counter)
    cooccurrence = defaultdict(Counter)

    sums = []
    spreads = []

    for index, (main, euro) in enumerate(states):
        ordered = sorted(main)
        sums.append(sum(ordered))
        spreads.append(ordered[-1] - ordered[0])

        recency_weight = (index + 1) / total

        for position, number in enumerate(ordered):
            frequency[number] += 1
            weighted_frequency[number] += recency_weight
            position_frequency[position][number] += 1

            previous_seen[number] = last_seen[number]
            last_seen[number] = index

        for left in ordered:
            for right in ordered:
                if left != right:
                    cooccurrence[left][right] += 1

        if index > 0:
            previous_main = states[index - 1][0]

            for old_number in previous_main:
                for new_number in main:
                    transitions[old_number][new_number] += 1

    gaps = {}
    interval_acceleration = {}

    for number in range(1, 51):
        if last_seen[number] < 0:
            gap = total + 1
        else:
            gap = total - 1 - last_seen[number]

        gaps[number] = gap

        if previous_seen[number] < 0:
            previous_gap = total
        else:
            previous_gap = (
                last_seen[number]
                - previous_seen[number]
            )

        interval_acceleration[number] = (
            previous_gap - gap
        )

    recent = states[-1][0]
    recent_3 = [
        number
        for main, euro in states[-3:]
        for number in main
    ]
    recent_5 = [
        number
        for main, euro in states[-5:]
        for number in main
    ]
    recent_10 = [
        number
        for main, euro in states[-10:]
        for number in main
    ]

    return {
        "states": states,
        "total": total,
        "frequency": frequency,
        "weighted_frequency": weighted_frequency,
        "position_frequency": position_frequency,
        "last_seen": last_seen,
        "gaps": gaps,
        "interval_acceleration": interval_acceleration,
        "transitions": transitions,
        "cooccurrence": cooccurrence,
        "recent": recent,
        "recent_3": Counter(recent_3),
        "recent_5": Counter(recent_5),
        "recent_10": Counter(recent_10),
        "average_sum": sum(sums) / len(sums),
        "average_spread": sum(spreads) / len(spreads),
    }


def stable_seed(stats, expert_index):
    value = 2166136261

    for state_index, (main, euro) in enumerate(
        stats["states"],
        start=1,
    ):
        for position, number in enumerate(
            main + euro,
            start=1,
        ):
            value ^= (
                number
                + state_index * 17
                + position * 31
                + expert_index * 97
            )

            value = (
                value * 16777619
            ) & 0xFFFFFFFF

    return value


def deterministic_noise(
    number,
    seed,
    scale=1.0,
):
    value = (
        seed
        ^ (number * 2654435761)
    ) & 0xFFFFFFFF

    value ^= value >> 13
    value = (
        value * 1274126177
    ) & 0xFFFFFFFF
    value ^= value >> 16

    return (
        value / 0xFFFFFFFF
    ) * scale


def select_unique(scores, count=5):
    ordered = sorted(
        range(1, 51),
        key=lambda number: (
            scores.get(number, 0.0),
            -number,
        ),
        reverse=True,
    )

    selected = []

    for number in ordered:
        if number not in selected:
            selected.append(number)

        if len(selected) == count:
            break

    if len(selected) != count:
        raise RuntimeError(
            "Не удалось сформировать 5 уникальных чисел"
        )

    return selected


def base_scores(stats):
    scores = {}

    for number in range(1, 51):
        scores[number] = (
            stats["frequency"][number] * 1.0
            + stats["weighted_frequency"][number] * 1.5
            + stats["recent_10"][number] * 0.8
            + stats["gaps"][number] * 0.03
        )

    return scores


def expert_v1(history):
    stats = build_stats(history)
    alpha = 0.18
    ewma = {
        number: 0.0
        for number in range(1, 51)
    }

    for main, euro in stats["states"]:
        present = set(main)

        for number in range(1, 51):
            signal = 1.0 if number in present else 0.0
            ewma[number] = (
                alpha * signal
                + (1.0 - alpha) * ewma[number]
            )

    return select_unique(ewma)


def expert_v2(history):
    stats = build_stats(history)
    anchor = set(stats["recent"])
    scores = {}

    for number in range(1, 51):
        resonance = sum(
            stats["cooccurrence"][number][other]
            for other in anchor
        )

        scores[number] = (
            resonance * 1.3
            + stats["recent_10"][number]
            + stats["frequency"][number] * 0.15
        )

    return select_unique(scores)


def expert_v3(history):
    stats = build_stats(history)
    target_mod = int(stats["average_sum"]) % 7
    scores = {}

    for number in range(1, 51):
        harmonic = math.cos(
            2.0
            * math.pi
            * (number - target_mod)
            / 7.0
        )

        scores[number] = (
            stats["frequency"][number] * 0.35
            + stats["weighted_frequency"][number]
            + harmonic * 2.2
        )

    return select_unique(scores)


def expert_v4(history):
    stats = build_stats(history)

    scores = {
        number: (
            stats["interval_acceleration"][number] * 1.8
            + stats["gaps"][number] * 0.25
            + stats["recent_5"][number] * 0.7
        )
        for number in range(1, 51)
    }

    return select_unique(scores)


def expert_v5(history):
    stats = build_stats(history)
    previous = stats["recent"]
    scores = {}

    for number in range(1, 51):
        scores[number] = sum(
            stats["transitions"][old][number]
            for old in previous
        )

        scores[number] += (
            stats["weighted_frequency"][number] * 0.3
        )

    return select_unique(scores)


def expert_v6(history):
    stats = build_stats(history)
    center = stats["average_sum"] / 5.0
    spread = stats["average_spread"]
    scores = {}

    for number in range(1, 51):
        radial = abs(number - center)
        shell = abs(radial - spread / 4.0)

        scores[number] = (
            stats["frequency"][number] * 0.45
            - shell * 0.25
            + stats["recent_10"][number] * 0.8
        )

    return select_unique(scores)


def expert_v7(history):
    stats = build_stats(history)
    last_sum = sum(stats["recent"])
    state = last_sum % 4
    scores = {}

    for number in range(1, 51):
        residue = number % 4
        distance = min(
            (residue - state) % 4,
            (state - residue) % 4,
        )

        scores[number] = (
            stats["weighted_frequency"][number]
            + (3 - distance) * 1.4
            + stats["recent_5"][number] * 0.4
        )

    return select_unique(scores)


def expert_v8(history):
    stats = build_stats(history)

    scores = {
        number: (
            stats["frequency"][number] * 0.35
            + stats["weighted_frequency"][number]
            + (3.0 if number in PRIMES else 0.0)
            + stats["gaps"][number] * 0.04
        )
        for number in range(1, 51)
    }

    return select_unique(scores)


def expert_v9(history):
    stats = build_stats(history)
    scores = {}

    for number in range(1, 51):
        momentum = (
            stats["recent_3"][number] * 2.0
            + stats["recent_5"][number]
            - stats["recent_10"][number] * 0.35
        )

        scores[number] = (
            momentum
            + stats["weighted_frequency"][number] * 0.7
        )

    return select_unique(scores)


def expert_v10(history):
    stats = build_stats(history)
    recent = set(stats["recent"])
    scores = {}

    for number in range(1, 51):
        anti_recent = (
            0.0
            if number in recent
            else 2.5
        )

        scores[number] = (
            stats["gaps"][number] * 0.22
            - stats["recent_5"][number] * 1.3
            + anti_recent
            + stats["frequency"][number] * 0.08
        )

    return select_unique(scores)


def expert_v11(history):
    stats = build_stats(history)
    scores = {}

    for number in range(1, 51):
        angle = (
            2.0
            * math.pi
            * number
            / 50.0
        )

        geometry = (
            math.sin(angle * 3.0)
            + math.cos(angle * 5.0)
        )

        scores[number] = (
            geometry * 1.7
            + stats["weighted_frequency"][number]
            + stats["position_frequency"][
                (number - 1) % 5
            ][number] * 0.5
        )

    return select_unique(scores)


def expert_v12(history):
    stats = build_stats(history)
    recent_sorted = sorted(stats["recent"])
    scores = {}

    for number in range(1, 51):
        similarity = 0.0

        for main, euro in stats["states"][:-1]:
            ordered = sorted(main)
            distance = sum(
                abs(a - b)
                for a, b in zip(
                    ordered,
                    recent_sorted,
                )
            )

            weight = 1.0 / (1.0 + distance)

            if number in main:
                similarity += weight

        scores[number] = (
            similarity * 100.0
            + stats["weighted_frequency"][number] * 0.4
        )

    return select_unique(scores)


def expert_v13(history):
    stats = build_stats(history)
    transition_scores = {}

    for number in range(1, 51):
        incoming = sum(
            counter[number]
            for counter in stats["transitions"].values()
        )

        outgoing = sum(
            stats["transitions"][number].values()
        )

        transition_scores[number] = (
            incoming * 0.8
            + outgoing * 0.2
            + stats["gaps"][number] * 0.08
        )

    return select_unique(transition_scores)


def expert_v14(history):
    stats = build_stats(history)
    seed = stable_seed(stats, 14)
    scores = {}

    for number in range(1, 51):
        frequency = stats["frequency"][number]
        probability = (
            frequency
            / max(1, stats["total"] * 5)
        )

        entropy = (
            -probability * math.log(
                probability + 1e-12
            )
        )

        scores[number] = (
            entropy * 20.0
            + stats["weighted_frequency"][number]
            + deterministic_noise(
                number,
                seed,
                scale=1.5,
            )
        )

    return select_unique(scores)


def expert_v15(history):
    stats = build_stats(history)
    scores = base_scores(stats)

    for number in range(1, 51):
        positional_accuracy = sum(
            stats["position_frequency"][position][
                number
            ]
            * (1.0 + position * 0.08)
            for position in range(5)
        )

        scores[number] += (
            positional_accuracy * 0.75
        )

    return select_unique(scores)


def expert_v16(history):
    stats = build_stats(history)
    scores = {}

    for number in range(1, 51):
        survival = 0.0

        for window in (3, 5, 10):
            recent_states = stats["states"][-window:]
            appearances = sum(
                1
                for main, euro in recent_states
                if number in main
            )

            survival += appearances / window

        scores[number] = (
            survival * 4.0
            + stats["weighted_frequency"][number]
            + stats["gaps"][number] * 0.02
        )

    return select_unique(scores)


def expert_v17(history):
    stats = build_stats(history)
    scores = {}
    recent_center = (
        sum(stats["recent"])
        / 5.0
    )

    for number in range(1, 51):
        drift = number - recent_center
        phase = math.sin(
            drift / 5.0
            + stats["total"] / 7.0
        )

        scores[number] = (
            phase * 2.0
            + stats["weighted_frequency"][number]
            + stats["recent_10"][number] * 0.7
        )

    return select_unique(scores)


def expert_v18(history):
    stats = build_stats(history)
    seed = stable_seed(stats, 18)
    scores = {}

    for number in range(1, 51):
        camp_frequency = (
            stats["recent_5"][number] * 1.4
            + stats["frequency"][number] * 0.2
        )

        balance = (
            1.0
            if (number <= 25)
            == (sum(stats["recent"]) <= 125)
            else 0.0
        )

        scores[number] = (
            camp_frequency
            + stats["weighted_frequency"][number]
            + balance
            + deterministic_noise(
                number,
                seed,
                scale=0.7,
            )
        )

    return select_unique(scores)


EXPERT_FUNCTIONS = [
    expert_v1,
    expert_v2,
    expert_v3,
    expert_v4,
    expert_v5,
    expert_v6,
    expert_v7,
    expert_v8,
    expert_v9,
    expert_v10,
    expert_v11,
    expert_v12,
    expert_v13,
    expert_v14,
    expert_v15,
    expert_v16,
    expert_v17,
    expert_v18,
]


STATIC_STATE82 = [
    [17, 45, 7, 43, 30],
    [27, 23, 30, 14, 43],
    [23, 32, 5, 50, 14],
    [8, 44, 3, 1, 42],
    [43, 25, 46, 50, 17],
    [27, 30, 22, 25, 23],
    [12, 17, 11, 22, 7],
    [3, 2, 5, 7, 11],
    [12, 17, 45, 11, 18],
    [44, 8, 1, 3, 13],
    [1, 2, 3, 4, 5],
    [5, 6, 17, 34, 36],
    [1, 3, 8, 9, 13],
    [17, 28, 5, 32, 9],
    [17, 6, 25, 30, 34],
    [17, 4, 6, 35, 42],
    [25, 24, 26, 23, 27],
    [25, 24, 26, 28, 23],
]


def calculate_vectors(history):
    vectors = [
        function(history)
        for function in EXPERT_FUNCTIONS
    ]

    for index, vector in enumerate(
        vectors,
        start=1,
    ):
        if len(vector) != 5:
            raise RuntimeError(
                "V"
                + str(index)
                + " вернул не 5 чисел"
            )

        if len(set(vector)) != 5:
            raise RuntimeError(
                "V"
                + str(index)
                + " содержит дубли"
            )

        if not all(
            1 <= number <= 50
            for number in vector
        ):
            raise RuntimeError(
                "V"
                + str(index)
                + " вышел за диапазон 1..50"
            )

    return vectors


def install(expert_master, history):
    vectors = calculate_vectors(history)

    changed = sum(
        1
        for old, new in zip(
            STATIC_STATE82,
            vectors,
        )
        if old != new
    )

    if changed == 0:
        raise RuntimeError(
            "Динамические эксперты не изменили "
            "ни одного вектора"
        )

    for index, function in enumerate(
        EXPERT_FUNCTIONS,
        start=1,
    ):
        setattr(
            expert_master,
            "expert_v" + str(index),
            function,
        )

    return vectors, changed
