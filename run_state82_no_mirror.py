#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from malysh_engine import MalyshEngine

RUN_CONTEXT = """
MALYSH EXPERIMENT: STATE 82

Использовать 81 историческое состояние.

ЛОКАЛЬНОЕ ПРАВИЛО ЭТОГО ПРОГОНА:
НЕ использовать зеркальность, mirror transformations,
reflected transformations или зеркальные соответствия
при интерпретации результата.

НЕ изменять:
- исходный код Малыша;
- память Малыша;
- архитектуру Малыша;
- R7;
- theta;
- резонансную систему.

Все остальные внутренние механизмы оставить штатными.

Разреженные независимые сигналы сохранять как наблюдения
и не отбрасывать только из-за отсутствия зонального большинства.
"""

RAW_DRAWS = [
"10.15.29.34.38.2.9",
"21.23.30.33.38.8.12",
"1.17.19.25.41.6.12",
"2.16.27.33.47.6.12",
"8.16.37.39.48.5.11",
"16.26.32.37.45.2.3",
"18.36.39.45.50.6.9",
"13.18.19.29.32.8.9",
"8.13.15.17.37.3.7",
"3.20.27.37.44.1.2",
"8.14.38.41.48.1.11",
"12.19.34.39.47.4.5",
"1.21.44.45.46.2.7",
"8.23.39.40.44.6.7",
"11.17.23.36.40.5.6",
"4.5.26.38.48.2.9",
"7.17.19.28.47.2.7",
"1.9.14.35.49.2.10",
"8.17.26.31.47.1.6",
"2.3.17.18.28.4.10",
"7.23.37.44.47.2.6",
"12.13.16.17.37.4.11",
"2.17.21.25.30.2.6",
"9.15.23.43.48.3.5",
"21.23.25.38.40.7.11",
"9.10.18.22.37.1.11",
"2.4.16.23.27.5.8",
"1.6.11.18.48.10.12",
"13.22.32.46.47.6.7",
"16.31.35.43.44.2.9",
"31.32.36.39.47.7.8",
"6.21.29.39.44.1.5",
"19.20.41.43.46.5.7",
"10.11.13.16.27.5.7",
"1.30.33.34.43.5.10",
"3.17.18.31.41.6.12",
"7.15.19.28.35.3.11",
"1.32.33.36.37.7.12",
"10.36.37.39.47.5.6",
"5.34.35.42.46.3.5",
"5.11.23.33.42.10.12",
"3.20.21.42.49.5.6",
"2.36.38.40.46.7.8",
"21.23.44.47.50.1.7",
"1.14.22.39.48.8.11",
"2.4.14.18.28.9.11",
"9.26.29.37.42.1.7",
"16.27.37.42.45.5.12",
"24.27.43.48.50.4.12",
"17.25.35.39.41.5.9",
"12.19.34.44.50.3.8",
"4.9.20.25.28.1.3",
"6.16.24.41.46.2.3",
"13.25.28.42.45.5.12",
"5.6.17.34.36.3.11",
"6.21.31.47.48.2.9",
"4.8.10.17.37.5.7",
"4.6.8.17.22.7.10",
"11.25.40.41.45.1.5",
"3.17.30.35.43.1.12",
"1.3.6.13.23.5.7",
"4.11.12.16.30.8.9",
"5.26.28.30.40.3.6",
"15.22.24.34.42.4.7",
"25.35.45.46.50.4.8",
"4.5.7.48.50.4.5",
"23.34.39.45.49.1.4",
"9.14.35.43.50.3.7",
"5.14.31.33.43.3.4",
"14.27.34.36.47.3.4",
"14.21.35.37.49.1.12",
"5.6.10.27.42.1.8",
"4.25.30.32.33.4.5",
"17.23.33.46.47.4.5",
"2.7.10.29.30.5.10",
"21.30.36.43.48.1.5",
"4.6.7.17.45.7.12",
"7.12.19.28.50.1.6",
"18.38.41.43.46.7.10",
"11.17.20.22.35.4.8",
"12.24.25.29.45.1.9"
]


def parse_draw(line):
    values = [int(x) for x in line.split(".")]
    if len(values) != 7:
        raise ValueError(
            f"Ожидалось 7 значений, получено {len(values)}: {line}"
        )
    return values


def main():

    states = [parse_draw(x) for x in RAW_DRAWS]

    assert len(states) == 81
    assert all(len(x) == 7 for x in states)

    flat_history = [
        value
        for state in states
        for value in state
    ]

    assert len(flat_history) == 567

    print("=" * 100)
    print("МАЛЫШ: ЭКСПЕРИМЕНТАЛЬНЫЙ РАСЧЕТ СОСТОЯНИЯ 82")
    print("=" * 100)

    print(RUN_CONTEXT)

    print("=" * 100)
    print("Historical states :", len(states))
    print("Values per state  : 7")
    print("Total values      :", len(flat_history))
    print("Mirror/reflected  : НЕ ИСПОЛЬЗОВАТЬ В ИНТЕРПРЕТАЦИИ")
    print("=" * 100)

    engine = MalyshEngine()

    print("\nСостояние Малыша перед расчетом:")
    print(" generation :", engine.generation)
    print(" theta      :", engine.theta)
    print(" energy     :", engine.energy)
    print(" eta        :", engine.eta)
    print(" r7_val     :", engine.r7_val)

    result = engine.process_array(
        flat_history,
        source_name="STATE_82__81_STATES__NO_MIRROR"
    )

    print("\n" + "=" * 100)
    print("РЕЗУЛЬТАТ МАЛЫША")
    print("=" * 100)

    print(json.dumps(
        result,
        indent=2,
        ensure_ascii=False
    ))

    print("\n" + "=" * 100)
    print("КОНТРОЛЬ")
    print("=" * 100)

    print("generation         :", result.get("generation"))
    print("mode               :", result.get("mode"))
    print("predicted_strategy :", result.get("predicted_strategy"))
    print("applied_strategy   :", result.get("applied_strategy"))
    print("signal_class       :", result.get("signal_class"))
    print("confidence         :", result.get("confidence"))
    print("K_metric           :", result.get("K_metric"))
    print("theta              :", result.get("theta"))
    print("r7_val             :", result.get("r7_val"))
    print("energy             :", result.get("energy"))
    print("forecast_10        :", result.get("forecast_10"))

    print("\nЭкспериментальное правило:")
    print("MIRROR/REFLECTED = EXCLUDED FROM RESULT INTERPRETATION")
    print("SOURCE CODE       = UNCHANGED")


if __name__ == "__main__":
    main()

