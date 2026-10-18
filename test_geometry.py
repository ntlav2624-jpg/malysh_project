from __future__ import annotations

from typing import Any

from malysh_system.diagnostic_contract import (
    DiagnosticResult,
    EngineFactory,
    build_result,
    default_engine_factory,
)


def run_geometry_diagnostic(
    engine_factory: EngineFactory = default_engine_factory,
) -> DiagnosticResult:
    engine = engine_factory()

    smooth = engine.process_array(
        [10, 15, 20, 25, 30],
        source_name="Geo_Smooth",
    )

    chaotic = engine.process_array(
        [30, 80, 10, 95, 20],
        source_name="Geo_Chaotic",
    )

    checks: list[dict[str, Any]] = [
        {
            "case": "smooth",
            "signal_class": smooth["signal_class"],
            "K_metric": smooth["K_metric"],
            "r7_val": smooth["r7_val"],
        },
        {
            "case": "chaotic",
            "signal_class": chaotic["signal_class"],
            "K_metric": chaotic["K_metric"],
            "r7_val": chaotic["r7_val"],
        },
    ]

    return build_result(
        diagnostic_id="test_geometry.py",
        family="geometry",
        checks=checks,
        conclusion=(
            "Сравнены геометрические реакции R7 "
            "на плавный и резкий потоки"
        ),
    )


def main() -> None:
    result = run_geometry_diagnostic()

    print(
        "=== ДИАГНОСТИКА ДИНАМИЧЕСКОЙ "
        "ГЕОМЕТРИИ R7 ==="
    )

    for check in result.checks:
        print()
        print("case        :", check["case"])
        print(
            "signal_class:",
            check["signal_class"],
        )
        print(
            "K_metric    :",
            check["K_metric"],
        )
        print(
            "r7_val      :",
            check["r7_val"],
        )

    print()
    print(result.conclusion)


if __name__ == "__main__":
    main()
