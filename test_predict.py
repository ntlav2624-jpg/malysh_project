from __future__ import annotations

from typing import Any

from malysh_system.diagnostic_contract import (
    DiagnosticResult,
    EngineFactory,
    build_result,
    default_engine_factory,
)


def run_prediction_diagnostic(
    engine_factory: EngineFactory = default_engine_factory,
) -> DiagnosticResult:
    engine = engine_factory()

    first = engine.process_array(
        [10, 12, 14, 16, 18],
        source_name="Predict_Test_1",
    )

    second = engine.process_array(
        [18, 20, 22, 24, 26],
        source_name="Predict_Test_2",
    )

    checks: list[dict[str, Any]] = []

    for step, result in enumerate(
        (first, second),
        start=1,
    ):
        checks.append(
            {
                "step": step,
                "predicted_strategy": result[
                    "predicted_strategy"
                ],
                "applied_strategy": result[
                    "applied_strategy"
                ],
                "signal_class": result[
                    "signal_class"
                ],
                "agreement": (
                    result["predicted_strategy"]
                    == result["applied_strategy"]
                ),
            }
        )

    return build_result(
        diagnostic_id="test_predict.py",
        family="prediction",
        checks=checks,
        conclusion=(
            "Сопоставлены предсказанная и "
            "фактически применённая стратегии"
        ),
    )


def main() -> None:
    result = run_prediction_diagnostic()

    print(
        "=== ДИАГНОСТИКА ПРЕДИКТИВНОГО "
        "КОНТУРА ==="
    )

    for check in result.checks:
        print()
        print("step      :", check["step"])
        print(
            "predicted :",
            check["predicted_strategy"],
        )
        print(
            "applied   :",
            check["applied_strategy"],
        )
        print(
            "agreement :",
            check["agreement"],
        )

    print()
    print(result.conclusion)


if __name__ == "__main__":
    main()
