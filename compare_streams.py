from __future__ import annotations

from typing import Any, Mapping, Sequence

from malysh_engine import MalyshEngine


DEFAULT_STREAMS = {
    "1_Synthetic_Sine": (
        10.0,
        12.5,
        15.0,
        16.2,
        14.8,
        12.1,
        10.5,
        12.0,
        14.5,
    ),
    "2_Physical_Sensor": (
        22.1,
        22.3,
        22.2,
        22.8,
        23.5,
        23.1,
        23.6,
        24.0,
        23.8,
    ),
    "3_Chaotic_Stream": (
        5,
        82,
        12,
        94,
        3,
        67,
        45,
        19,
        88,
    ),
}


def compare_streams(
    streams: Mapping[
        str,
        Sequence[float],
    ] = DEFAULT_STREAMS,
) -> list[dict[str, Any]]:
    """
    Сравнивает несколько потоков через
    исторический MalyshEngine.

    Импорт модуля сам анализ не запускает.
    """
    results: list[dict[str, Any]] = []

    for name, data in streams.items():
        values = list(data)

        engine = MalyshEngine()

        result = engine.process_array(
            values,
            source_name=name,
        )

        results.append(
            {
                "source": name,
                "input": values,
                "result": result,
            }
        )

    return results


def main() -> None:
    print(
        "=== СРАВНИТЕЛЬНЫЙ АНАЛИЗ "
        "ПОТОКОВ ЧЕРЕЗ MALYSH ENGINE ==="
    )

    results = compare_streams()

    for item in results:
        result = item["result"]

        print()
        print(
            "",
            item["source"],
        )
        print(
            "  Режим:",
            result["mode"],
        )
        print(
            "  Уверенность:",
            result["confidence"],
        )
        print(
            "  Общий штраф:",
            result["J"]["total"],
        )
        print(
            "  Мета-стабильность:",
            result["S_n"],
        )
        print(
            "  Энергия системы:",
            result["energy"],
        )
        print(
            "  Прогноз (+3):",
            result["forecast_10"][:3],
        )

    print()
    print(
        "[Анализ завершён]: "
        "сравнение потоков выполнено."
    )


if __name__ == "__main__":
    main()
