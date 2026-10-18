from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent

REGISTRY_PATH = (
    ROOT
    / "malysh_system"
    / "workflow_experience_registry.json"
)


WORKFLOW_PROFILES = {
    "run_pipeline.py": {
        "title": "Базовый резонансный pipeline",
        "aliases": (
            "базовый резонанс",
            "резонансный pipeline",
            "резонансный контур",
            "spiral trajectory",
            "спиральная траектория",
            "operator 7",
            "o7",
            "n7",
        ),
        "capability": (
            "базовая геометрия N7 и "
            "резонансный оператор O7"
        ),
    },
    "run_reflected_pipeline.py": {
        "title": "Отражённый резонансный pipeline",
        "aliases": (
            "отражённая траектория",
            "отраженная траектория",
            "отражённую траекторию",
            "отраженную траекторию",
            "отражённой траектории",
            "отраженной траектории",
            "движение с отражением",
            "траектория с отражением",
            "контур с отражением",
            "геометрия с отражением",
            "построй отражённую траекторию",
            "построй отраженную траекторию",
            "замкнутый контур",
            "ограниченная траектория",
            "ограниченную траекторию",
            "стенка шестиугольника",
        ),
        "capability": (
            "ограниченная траектория с отражением "
            "и насыщенным резонансным режимом"
        ),
    },
    "run_adaptive_pipeline.py": {
        "title": "Адаптивный резонансный pipeline",
        "aliases": (
            "адаптивный o7",
            "адаптивный резонанс",
            "фазовый детектор",
            "частотная модуляция",
            "phase detector",
            "adaptive",
        ),
        "capability": (
            "фазовый детектор и адаптивный "
            "коэффициент усиления O7"
        ),
    },
    "run_processor.py": {
        "title": "Резонансный процессор потока",
        "aliases": (
            "обработай поток",
            "обработка потока",
            "поток данных",
            "числовой поток",
            "символьный поток",
            "process stream",
            "processor",
            "преобразуй данные",
        ),
        "capability": (
            "обработка числовых и символьных "
            "данных через N7-резонансную сеть"
        ),
    },
    "run_malysh.py": {
        "title": "Первичная геометрия Малыша",
        "aliases": (
            "первичная геометрия",
            "первичную геометрию",
            "первичной геометрии",
            "исследуй первичную геометрию малыша",
            "узлы n7",
            "node 7",
            "геометрия n7",
            "геометрию n7",
            "спираль",
            "пятиугольник",
            "шестиугольник",
        ),
        "capability": (
            "поиск узлов N7 внутри геометрии "
            "пятиугольника и шестиугольника"
        ),
    },
    "run_origin_of_life.py": {
        "title": "Опыт биогенеза",
        "aliases": (
            "биогенез",
            "зарождение жизни",
            "возникновение жизни",
            "возникновение порядка",
            "эволюционный синтез",
            "каталитический резонанс",
            "параметр порядка",
            "prebiotic",
        ),
        "capability": (
            "моделирование перехода от хаоса "
            "к порядку через каталитические N7-узлы"
        ),
    },
    "run_maglev_flywheel.py": {
        "title": "Опыт энергетической динамики",
        "aliases": (
            "затухание энергии",
            "потери энергии",
            "маховик",
            "маглев",
            "левитация",
            "пружина",
            "энергетическая динамика",
            "damping",
            "flywheel",
        ),
        "capability": (
            "моделирование затухания и "
            "перераспределения энергии"
        ),
    },
    "run_full_translation.py": {
        "title": "Опыт клинописного перевода",
        "aliases": (
            "клинопись",
            "клинописный",
            "клинописная",
            "клинописную",
            "клинописной",
            "клинописные",
            "перевод таблички",
            "переведи табличку",
            "древняя табличка",
            "древнюю табличку",
            "клинописная табличка",
            "клинописную табличку",
            "переведи древнюю клинописную табличку",
            "переведи текст",
            "translation",
            "tablet",
            "cuneiform",
        ),
        "capability": (
            "загрузка корпуса, перевод и анализ "
            "клинописного текста"
        ),
    },
}


STOPWORDS = {
    "и",
    "в",
    "на",
    "для",
    "через",
    "про",
    "это",
    "этот",
    "эту",
    "исследуй",
    "рассмотри",
    "проанализируй",
    "используй",
    "вспомни",
    "малыш",
}


def normalize(text: str) -> str:
    return " ".join(
        re.findall(
            r"[0-9a-zа-яё_-]+",
            text.lower(),
        )
    )


def tokens(text: str) -> set:
    return {
        token
        for token in normalize(text).split()
        if len(token) >= 3
        and token not in STOPWORDS
    }


def load_registry() -> dict[str, Any]:
    return json.loads(
        REGISTRY_PATH.read_text(
            encoding="utf-8"
        )
    )


def score_workflow(
    text: str,
    workflow: dict[str, Any],
) -> tuple[float, list[str]]:
    profile = WORKFLOW_PROFILES[
        workflow["id"]
    ]

    lowered = normalize(text)
    query_tokens = tokens(text)

    reasons = []
    score = 0.0

    for alias in profile["aliases"]:
        normalized_alias = normalize(alias)

        if normalized_alias in lowered:
            score += 12.0

            reasons.append(
                f"точное смысловое совпадение: {alias}"
            )

    searchable = " ".join(
        [
            workflow["id"],
            workflow["experience_family"],
            workflow["category"],
            *workflow["classes"],
            *workflow["functions"],
            *workflow["strings"],
            profile["title"],
            profile["capability"],
            *profile["aliases"],
        ]
    )

    searchable_tokens = tokens(searchable)

    overlap = sorted(
        query_tokens
        & searchable_tokens
    )

    if overlap:
        score += 2.0 * len(overlap)

        reasons.append(
            "совпавшие понятия: "
            + ", ".join(overlap)
        )

    if workflow["uses_randomness"]:
        reasons.append(
            "опыт использует стохастический компонент"
        )

    return score, reasons


def recall_workflows(
    text: str,
    limit: int = 4,
) -> dict[str, Any]:
    registry = load_registry()
    ranked = []

    for workflow in registry["workflows"]:
        score, reasons = score_workflow(
            text,
            workflow,
        )

        if score < 4.0:
            continue

        profile = WORKFLOW_PROFILES[
            workflow["id"]
        ]

        strength = min(
            0.56,
            0.20 + score / 100.0,
        )

        ranked.append(
            {
                "source_id": (
                    "workflow:"
                    + workflow["id"]
                ),
                "workflow_id": workflow["id"],
                "title": profile["title"],
                "family": workflow[
                    "experience_family"
                ],
                "status": "recalled_skill",
                "strength": strength,
                "score": score,
                "capability": profile[
                    "capability"
                ],
                "evidence": [
                    *reasons,
                    (
                        "source="
                        + workflow["path"]
                    ),
                    (
                        "registry_sha256="
                        + workflow["sha256"]
                    ),
                ],
                "uses_randomness": workflow[
                    "uses_randomness"
                ],
                "automatic_execution": False,
                "decision_authority": False,
                "state_write": False,
                "state_commit": False,
            }
        )

    ranked.sort(
        key=lambda item: (
            -item["score"],
            item["workflow_id"],
        )
    )

    return {
        "query": text,
        "subject": "Malysh",
        "mode": "semantic_experience_recall",
        "recalled": ranked[:limit],
        "automatic_execution": False,
        "decision_authority": False,
        "state_write": False,
        "state_commit": False,
    }
