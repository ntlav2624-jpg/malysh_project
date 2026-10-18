from __future__ import annotations

import re
import tempfile
import time
from pathlib import Path
from typing import Any

from malysh_engine import MalyshEngine
from malysh_system.protocols import Command, OrganResult


NUMBER_PATTERN = re.compile(
    r"[-+]?(?:\d+(?:[.,]\d*)?|[.,]\d+)"
)


def extract_series(text: str) -> list:
    """
    Извлекает числовую последовательность из запроса.
    """
    values: list[float] = []

    for match in NUMBER_PATTERN.findall(text):
        normalized = match.replace(",", ".")

        try:
            values.append(float(normalized))
        except ValueError:
            continue

    return values


def context_series(
    context: dict[str, Any],
) -> list:
    """
    Создаёт минимальный ряд из текущего состояния.

    Используется только тогда, когда навык уже был
    семантически вызван, но ряд не указан явно.
    """
    generation = float(
        context.get("generation", 0) or 0
    )

    virtual_time = float(
        context.get("virtual_time", 0) or 0
    )

    metrics = context.get("metrics", {})

    numeric_metrics = [
        float(value)
        for value in metrics.values()
        if isinstance(value, (int, float))
    ]

    values = [
        generation,
        virtual_time,
        *numeric_metrics[:6],
    ]

    if len(values) < 3:
        base = generation + virtual_time

        values.extend(
            [
                base + 1.0,
                base + 2.0,
                base + 3.0,
            ]
        )

    return values


class RecalledMalyshEngineSkill:
    """
    Вспоминаемый навык старого Malysh Engine.

    Это не глобальный управляющий центр.

    Навык вызывается Semantic Router только для задач,
    связанных с числовыми рядами, прогнозом потока,
    выбором стратегии и прежними расчётными моделями.
    """

    organ_id = "native_malysh_engine"
    category = "memory.sequence_skill"
    role = "recalled_skill"

    def validate(self) -> list:
        problems: list[str] = []

        required_methods = (
            "_load_state",
            "predict_next_strategy",
            "process_array",
        )

        for method in required_methods:
            if not callable(
                getattr(MalyshEngine, method, None)
            ):
                problems.append(
                    f"Метод отсутствует: {method}"
                )

        return problems

    def invoke(
        self,
        command: Command,
        context: dict[str, Any],
        dry_run: bool = True,
    ) -> OrganResult:
        problems = self.validate()

        if problems:
            return OrganResult(
                organ=self.organ_id,
                status="adapter_invalid",
                data={
                    "category": self.category,
                    "role": self.role,
                    "validation_errors": problems,
                },
                error="; ".join(problems),
            )

        explicit = extract_series(command.text)

        data = (
            explicit
            if explicit
            else context_series(context)
        )

        source = (
            "command"
            if explicit
            else "shared_context"
        )

        if not data:
            return OrganResult(
                organ=self.organ_id,
                status="invalid_input",
                data={
                    "category": self.category,
                    "role": self.role,
                    "input_size": 0,
                },
                error="Числовой поток отсутствует",
            )

        if dry_run:
            return OrganResult(
                organ=self.organ_id,
                status="skill_recalled",
                data={
                    "category": self.category,
                    "role": self.role,
                    "input_size": len(data),
                    "input_source": source,
                    "capabilities": [
                        "sequence_analysis",
                        "strategy_recall",
                        "forecast_10",
                        "adaptive_signal_memory",
                    ],
                    "persistent_memory_write": False,
                },
            )

        started = time.monotonic()

        try:
            with tempfile.TemporaryDirectory(
                prefix="malysh_recalled_skill_"
            ) as temporary_directory:
                vault = (
                    Path(temporary_directory)
                    / "memory_vault"
                )

                engine = MalyshEngine(
                    vault_dir=str(vault)
                )

                remembered_strategy = (
                    engine.predict_next_strategy()
                )

                passport = engine.process_array(
                    data=data,
                    source_name=(
                        "recalled_sequence_skill"
                    ),
                )

                passports_written = len(
                    list(
                        vault.glob(
                            "passport_*.json"
                        )
                    )
                )

            if "error" in passport:
                return OrganResult(
                    organ=self.organ_id,
                    status="error",
                    data={
                        "category": self.category,
                        "role": self.role,
                        "input_size": len(data),
                        "output_tail": str(passport),
                    },
                    error=str(passport["error"]),
                )

            thought = {
                "remembered_strategy": remembered_strategy,
                "predicted_strategy": passport.get(
                    "predicted_strategy"
                ),
                "applied_strategy": passport.get(
                    "applied_strategy"
                ),
                "signal_class": passport.get(
                    "signal_class"
                ),
                "confidence": passport.get(
                    "confidence"
                ),
                "K_metric": passport.get(
                    "K_metric"
                ),
                "forecast_10": passport.get(
                    "forecast_10",
                    [],
                ),
            }

            return OrganResult(
                organ=self.organ_id,
                status="ok",
                data={
                    "category": self.category,
                    "role": self.role,
                    "duration_seconds": round(
                        time.monotonic() - started,
                        6,
                    ),
                    "input_size": len(data),
                    "input_source": source,
                    "thought": thought,
                    "passports_written": (
                        passports_written
                    ),
                    "storage": (
                        "temporary_isolated_memory"
                    ),
                    "persistent_memory_write": False,
                    "output_tail": str(thought),
                },
            )

        except Exception as error:
            return OrganResult(
                organ=self.organ_id,
                status="exception",
                data={
                    "category": self.category,
                    "role": self.role,
                    "duration_seconds": round(
                        time.monotonic() - started,
                        6,
                    ),
                    "input_size": len(data),
                    "output_tail": "",
                },
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )


def build_native_adapters() -> list[
    RecalledMalyshEngineSkill
]:
    return [
        RecalledMalyshEngineSkill(),
    ]
