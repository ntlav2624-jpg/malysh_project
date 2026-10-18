from __future__ import annotations

from typing import Any

from malysh_system.diagnostic_contract import (
    DiagnosticResult,
    EngineFactory,
    build_result,
    default_engine_factory,
)


def run_meta_diagnostic(
    engine_factory: EngineFactory = default_engine_factory,
) -> DiagnosticResult:
    engine = engine_factory()

    first = engine.process_array(
        [50, 51, 52, 53, 54],
        source_name="Meta_Smooth",
    )

    second = engine.process_array(
        [54, 55, 56, 57, 58],
        source_name="Meta_Smooth_2",
    )

    checks: list[dict[str, Any]] = [
        {
            "step": 1,
            "strategy": first["strategy"],
            "meta_metric_M": first[
                "meta_metric_M"
            ],
            "mode": first["mode"],
        },
        {
            "step": 2,
            "strategy": second["strategy"],
            "meta_metric_M": second[
                "meta_metric_M"
            ],
            "mode": second["mode"],
        },
    ]

    return build_result(
        diagnostic_id="test_meta.py",
        family="meta_strategy",
        checks=checks,
        conclusion=(
            "Сопоставлена мета-метрика M "
            "на последовательных гладких потоках"
        ),
    )


def main() -> None:
    result = run_meta_diagnostic()

    print(
        "=== ДИАГНОСТИКА МЕТА-СТРАТЕГИИ ==="
    )

    for check in result.checks:
        print()

        for key, value in check.items():
            print(f"{key:<14}:", value)

    print()
    print(result.conclusion)


if __name__ == "__main__":
    main()
