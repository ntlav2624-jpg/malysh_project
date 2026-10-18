from __future__ import annotations

from pathlib import Path
from typing import Any

from malysh_system.passport_memory import (
    DEFAULT_VAULT,
    analyze_vault,
)


def analyze_deep_history(
    vault_dir: Path = DEFAULT_VAULT,
) -> dict[str, Any]:
    """
    Пассивный внутренний источник памяти Малыша.
    """
    return analyze_vault(vault_dir)


def print_analysis(
    analysis: dict[str, Any],
) -> None:
    print(
        "=== ГЛУБОКИЙ АНАЛИЗ "
        "ПАСПОРТНОЙ ПАМЯТИ ==="
    )
    print(
        "Паспортов:",
        analysis["passport_count"],
    )
    print(
        "Ошибок чтения:",
        len(analysis["read_errors"]),
    )

    print()
    print("Классы сигналов:")

    for signal_class, stats in (
        analysis[
            "class_statistics"
        ].items()
    ):
        print(
            " ",
            signal_class,
            "count=",
            stats["count"],
            "avg_J=",
            round(
                stats[
                    "average_penalty"
                ],
                4,
            ),
            "avg_C=",
            round(
                stats[
                    "average_confidence"
                ],
                4,
            ),
        )

    print()
    print(
        "Режимы:",
        analysis["modes"],
    )
    print(
        "Резонансные поколения:",
        analysis["resonance_points"],
    )
    print(
        "Турбулентные поколения:",
        analysis["turbulence_points"],
    )

    print()
    print("STATE_WRITE : False")
    print("STATE_COMMIT: False")


def main() -> None:
    print_analysis(
        analyze_deep_history()
    )


if __name__ == "__main__":
    main()
