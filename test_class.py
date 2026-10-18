from __future__ import annotations

from typing import Any

from malysh_system.diagnostic_contract import (
    DiagnosticResult,
    EngineFactory,
    build_result,
    default_engine_factory,
)


DEFAULT_CLASSIFICATION_STREAMS = {
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


def run_classification_diagnostic(
    engine_factory: EngineFactory = default_engine_factory,
) -> DiagnosticResult:
    checks: list[dict[str, Any]] = []

    for name, data in (
        DEFAULT_CLASSIFICATION_STREAMS.items()
    ):
        engine = engine_factory()

        result = engine.process_array(
            list(data),
            source_name=name,
        )

        checks.append(
            {
                "source": name,
                "signal_class": result[
                    "signal_class"
                ],
                "mode": result["mode"],
                "K_metric": result["K_metric"],
                "confidence": result["confidence"],
                "penalty_total": result["J"]["total"],
            }
        )

    return build_result(
        diagnostic_id="test_class.py",
        family="classification",
        checks=checks,
        conclusion=(
            "Сопоставлена классификация "
            "трёх типов потоков"
        ),
    )


def main() -> None:
    result = run_classification_diagnostic()

    print(
        "=== ДИАГНОСТИКА КЛАССИФИКАТОРА ==="
    )

    for check in result.checks:
        print()

        for key, value in check.items():
            print(f"{key:<14}:", value)

    print()
    print(result.conclusion)


if __name__ == "__main__":
    main()
