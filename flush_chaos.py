from __future__ import annotations

from typing import Any, Iterable

from malysh_engine import MalyshEngine


DEFAULT_SMOOTH_STREAMS = (
    (50, 52, 54, 56, 58, 60),
    (60, 62, 64, 66, 68, 70),
    (70, 72, 74, 76, 78, 80),
)


def analyze_smooth_streams(
    streams: Iterable[Iterable[float]] = (
        DEFAULT_SMOOTH_STREAMS
    ),
) -> list[dict[str, Any]]:
    """
    Старый опыт вытеснения хаотического режима
    гладкими потоками.

    Функция ничего не запускает при импорте.
    Выполнение происходит только при явном вызове.
    """
    results: list[dict[str, Any]] = []

    for index, stream in enumerate(
        streams,
        start=1,
    ):
        values = list(stream)

        engine = MalyshEngine()

        result = engine.process_array(
            values,
            source_name=(
                f"Smooth_Wave_{index}"
            ),
        )

        results.append(
            {
                "source": (
                    f"Smooth_Wave_{index}"
                ),
                "input": values,
                "result": result,
            }
        )

    return results


def main() -> None:
    print(
        "=== ОПЕРАЦИЯ: ВЫТЕСНЕНИЕ ХАОСА "
        "ПЛАВНЫМИ СИГНАЛАМИ ==="
    )

    results = analyze_smooth_streams()

    for index, item in enumerate(
        results,
        start=1,
    ):
        result = item["result"]

        print()
        print(f"[Шаг {index}]")
        print(
            "  Источник:",
            item["source"],
        )
        print(
            "  Класс сигнала:",
            result["signal_class"],
        )
        print(
            "  Стратегия:",
            result["strategy"],
        )
        print(
            "  Режим:",
            result["mode"],
        )
        print(
            "  Метрика K:",
            result["K_metric"],
        )
        print(
            "  Уверенность C:",
            result["confidence"],
        )
        print(
            "  Параметр R7:",
            result["r7_val"],
        )

    print()
    print(
        "обработка гладких "
        "потоков завершена."
    )


if __name__ == "__main__":
    main()
