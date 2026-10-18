from __future__ import annotations

from typing import Any

from malysh_system.diagnostic_contract import (
    DiagnosticResult,
    EngineFactory,
    build_result,
    default_engine_factory,
)


def run_resonance_diagnostic(
    engine_factory: EngineFactory = default_engine_factory,
) -> DiagnosticResult:
    engine = engine_factory()

    result = engine.process_array(
        [50, 52, 55, 53, 56, 58, 60],
        source_name="Smooth_Resonance_Run",
    )

    checks: list[dict[str, Any]] = [
        {
            "signal_class": result["signal_class"],
            "strategy": result["strategy"],
            "mode": result["mode"],
            "K_metric": result["K_metric"],
            "confidence": result["confidence"],
            "r7_val": result["r7_val"],
        }
    ]

    return build_result(
        diagnostic_id="test_resonance.py",
        family="resonance",
        checks=checks,
        conclusion=(
            "Проверен отклик резонансного "
            "контура на плавный поток"
        ),
    )


def main() -> None:
    result = run_resonance_diagnostic()
    check = result.checks[0]

    print(
        "=== ДИАГНОСТИКА RESONANCE_SEARCH ==="
    )

    for key, value in check.items():
        print(f"{key:<13}:", value)

    print()
    print(result.conclusion)


if __name__ == "__main__":
    main()
