from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VAULT = ROOT / "memory_vault"


def passport_files(
    vault_dir: Path = DEFAULT_VAULT,
) -> list:
    if not vault_dir.exists():
        return []

    return sorted(
        vault_dir.glob("passport_*.json")
    )


def load_passports(
    vault_dir: Path = DEFAULT_VAULT,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, str]],
]:
    """
    Пассивно читает паспортную память.

    Повреждённые файлы не стираются и не скрываются.
    Они возвращаются отдельным списком ошибок.
    """
    history: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for path in passport_files(vault_dir):
        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

            if not isinstance(
                payload,
                dict,
            ):
                raise TypeError(
                    "passport root must be object"
                )

        except Exception as error:
            errors.append(
                {
                    "path": str(path),
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )
            continue

        history.append(payload)

    return history, errors


def numeric(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def analyze_history(
    history: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    records = list(history)

    class_stats: dict[
        str,
        dict[str, float | int],
    ] = {}

    modes = Counter()

    resonance_points = []
    turbulence_points = []
    generations = []

    for passport in records:
        generation = passport.get(
            "generation",
            0,
        )

        generations.append(generation)

        signal_class = str(
            passport.get(
                "signal_class",
                "unknown",
            )
        )

        mode = str(
            passport.get(
                "mode",
                "N/A",
            )
        )

        penalty = numeric(
            passport.get(
                "J",
                {},
            ).get(
                "total",
                0.0,
            )
            if isinstance(
                passport.get("J", {}),
                dict,
            )
            else 0.0
        )

        confidence = numeric(
            passport.get(
                "confidence",
                0.0,
            )
        )

        energy = numeric(
            passport.get(
                "energy",
                0.0,
            )
        )

        stability = numeric(
            passport.get(
                "S_n",
                0.0,
            )
        )

        if signal_class not in class_stats:
            class_stats[signal_class] = {
                "count": 0,
                "j_sum": 0.0,
                "confidence_sum": 0.0,
            }

        stats = class_stats[signal_class]

        stats["count"] = (
            int(stats["count"])
            + 1
        )

        stats["j_sum"] = (
            float(stats["j_sum"])
            + penalty
        )

        stats["confidence_sum"] = (
            float(
                stats["confidence_sum"]
            )
            + confidence
        )

        modes[mode] += 1

        if (
            stability < 0.05
            and penalty < 1.0
        ):
            resonance_points.append(
                generation
            )

        if (
            energy > 180.0
            or penalty > 4.0
        ):
            turbulence_points.append(
                generation
            )

    normalized_classes = {}

    for signal_class, stats in (
        class_stats.items()
    ):
        count = int(stats["count"])

        normalized_classes[
            signal_class
        ] = {
            "count": count,
            "average_penalty": (
                float(stats["j_sum"])
                / count
                if count
                else 0.0
            ),
            "average_confidence": (
                float(
                    stats[
                        "confidence_sum"
                    ]
                )
                / count
                if count
                else 0.0
            ),
        }

    phase_formation = [
        generation
        for generation in generations
        if isinstance(
            generation,
            (
                int,
                float,
            ),
        )
        and generation <= 7
    ]

    phase_stress = [
        generation
        for generation in generations
        if isinstance(
            generation,
            (
                int,
                float,
            ),
        )
        and generation > 7
    ]

    return {
        "subject": "Malysh",
        "mode": "passport_memory_analysis",
        "passport_count": len(records),
        "class_statistics": (
            normalized_classes
        ),
        "modes": dict(
            sorted(modes.items())
        ),
        "sources": sorted(
            {
                str(
                    item.get(
                        "source",
                        "N/A",
                    )
                )
                for item in records
            }
        ),
        "signal_classes": sorted(
            normalized_classes
        ),
        "resonance_points": (
            resonance_points
        ),
        "turbulence_points": (
            turbulence_points
        ),
        "phases": {
            "formation": phase_formation,
            "stress_test": phase_stress,
        },
        "records": records,
        "influence_on_answer": False,
        "decision_authority": False,
        "automatic_execution": False,
        "state_write": False,
        "state_commit": False,
    }


def analyze_vault(
    vault_dir: Path = DEFAULT_VAULT,
) -> dict[str, Any]:
    history, errors = load_passports(
        vault_dir
    )

    analysis = analyze_history(
        history
    )

    analysis["vault"] = str(vault_dir)
    analysis["read_errors"] = errors

    return analysis


def passport_evidence(
    vault_dir: Path = DEFAULT_VAULT,
) -> dict[str, Any]:
    """
    Компактная форма для Legacy Memory.
    """
    analysis = analyze_vault(
        vault_dir
    )

    return {
        "passport_count": analysis[
            "passport_count"
        ],
        "modes": sorted(
            analysis["modes"]
        ),
        "sources": analysis["sources"],
        "signal_classes": analysis[
            "signal_classes"
        ],
        "read_errors": analysis[
            "read_errors"
        ],
        "state_write": False,
        "state_commit": False,
    }


def phase_range(
    generations: list[Any],
) -> str:
    if not generations:
        return "нет данных"

    return (
        f"{generations[0]}"
        f"-{generations[-1]}"
    )


def render_passport_markdown(
    analysis: dict[str, Any],
    generated_at: str | None = None,
) -> str:
    created = (
        generated_at
        or datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    lines = [
        "# Единый паспорт проекта «Малыш»",
        "",
        f"**Дата формирования:** {created}",
        "",
        (
            "**Источник:** паспортная память "
            "одного Малыша"
        ),
        "",
        "## 1. Общая сводка",
        "",
        (
            "- Паспортов: "
            + str(
                analysis[
                    "passport_count"
                ]
            )
        ),
        (
            "- Ошибок чтения: "
            + str(
                len(
                    analysis.get(
                        "read_errors",
                        [],
                    )
                )
            )
        ),
        (
            "- Влияние на текущий ответ: нет"
        ),
        (
            "- Право принятия решения: нет"
        ),
        "",
        "## 2. Поколения",
        "",
        (
            "| Gen | Источник | Режим | "
            "Класс | Conf | J | S_n | "
            "Theta | Энергия |"
        ),
        (
            "|---:|:---|:---|:---|---:|"
            "---:|---:|---:|---:|"
        ),
    ]

    for item in analysis["records"]:
        penalty = (
            item.get(
                "J",
                {},
            ).get(
                "total",
                0.0,
            )
            if isinstance(
                item.get("J", {}),
                dict,
            )
            else 0.0
        )

        lines.append(
            "| "
            + str(
                item.get(
                    "generation",
                    0,
                )
            )
            + " | "
            + str(
                item.get(
                    "source",
                    "N/A",
                )
            )[:30]
            + " | "
            + str(
                item.get(
                    "mode",
                    "N/A",
                )
            )
            + " | "
            + str(
                item.get(
                    "signal_class",
                    "unknown",
                )
            )
            + " | "
            + f"{numeric(item.get('confidence')):.4f}"
            + " | "
            + f"{numeric(penalty):.4f}"
            + " | "
            + f"{numeric(item.get('S_n')):.4f}"
            + " | "
            + f"{numeric(item.get('theta')):.4f}"
            + " | "
            + f"{numeric(item.get('energy')):.1f}"
            + " |"
        )

    lines.extend(
        [
            "",
            "## 3. Фазы истории",
            "",
            (
                "- Становление: "
                + phase_range(
                    analysis[
                        "phases"
                    ]["formation"]
                )
            ),
            (
                "- Последующая адаптация: "
                + phase_range(
                    analysis[
                        "phases"
                    ]["stress_test"]
                )
            ),
            "",
            "## 4. Режимы",
            "",
            "| Режим | Количество |",
            "|:---|---:|",
        ]
    )

    for mode, count in (
        analysis["modes"].items()
    ):
        lines.append(
            f"| {mode} | {count} |"
        )

    lines.extend(
        [
            "",
            "## 5. Классы сигналов",
            "",
        ]
    )

    for signal_class, stats in (
        analysis[
            "class_statistics"
        ].items()
    ):
        lines.append(
            "- "
            + signal_class
            + ": count="
            + str(stats["count"])
            + ", avg_J="
            + f"{stats['average_penalty']:.4f}"
            + ", avg_C="
            + f"{stats['average_confidence']:.4f}"
        )

    lines.extend(
        [
            "",
            "## 6. Наблюдаемые точки",
            "",
            (
                "- Резонансные поколения: "
                + repr(
                    analysis[
                        "resonance_points"
                    ]
                )
            ),
            (
                "- Турбулентные поколения: "
                + repr(
                    analysis[
                        "turbulence_points"
                    ]
                )
            ),
            "",
            "## 7. Архитектурный статус",
            "",
            (
                "Этот документ представляет "
                "историческую память одного Малыша. "
                "Он не является отдельным разумом "
                "и не изменяет текущий ответ."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def write_passport(
    output_path: Path,
    vault_dir: Path = DEFAULT_VAULT,
    generated_at: str | None = None,
) -> Path:
    """
    Явная операция записи.

    Импорт и анализ ничего не записывают.
    """
    analysis = analyze_vault(
        vault_dir
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        render_passport_markdown(
            analysis,
            generated_at=generated_at,
        ),
        encoding="utf-8",
    )

    return output_path
