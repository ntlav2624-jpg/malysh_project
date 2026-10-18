from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from malysh_system.workflow_recall import recall_workflows


@dataclass
class ExperienceSignal:
    source_id: str
    family: str
    status: str
    strength: float
    statement: str
    evidence: list[str]
    factual: bool
    generated: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MalyshExperience:
    """
    Единый внутренний опыт одного Малыша.

    Инструменты не принимают самостоятельных решений.
    Они дают сигналы одному мыслительному контексту.
    """

    subject: str
    signals: list[ExperienceSignal]
    contradictions: list[dict[str, Any]]
    unresolved: list[str]
    generated_hypotheses: list[str]
    decision_authority: bool
    state_write: bool
    state_commit: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "signals": [
                item.to_dict()
                for item in self.signals
            ],
            "contradictions": self.contradictions,
            "unresolved": self.unresolved,
            "generated_hypotheses": (
                self.generated_hypotheses
            ),
            "decision_authority": (
                self.decision_authority
            ),
            "state_write": self.state_write,
            "state_commit": self.state_commit,
        }


def clamp(value: float) -> float:
    return max(
        0.0,
        min(0.99, float(value)),
    )


def memory_statement(
    memory: dict[str, Any],
) -> str:
    title = memory.get(
        "title",
        memory.get(
            "id",
            "Неизвестное знание",
        ),
    )

    status = memory.get(
        "status",
        "named_unresolved",
    )

    if status == "recovered":
        return (
            f"Восстановленный инструмент «{title}» "
            "доступен единому опыту Малыша"
        )

    if status == "historical":
        return (
            f"Исторический инструмент «{title}» "
            "может дать прежний способ анализа"
        )

    return (
        f"Имя инструмента «{title}» сохранено, "
        "но исходный смысл ещё не восстановлен"
    )


def memory_strength(
    memory: dict[str, Any],
) -> float:
    status = memory.get(
        "status",
        "named_unresolved",
    )

    score = float(
        memory.get(
            "score",
            0,
        )
        or 0
    )

    if status == "recovered":
        return clamp(
            min(
                0.62,
                0.30 + score / 200.0,
            )
        )

    if status == "historical":
        return clamp(
            min(
                0.46,
                0.22 + score / 250.0,
            )
        )

    return 0.12


def observation_signal(
    observation: dict[str, Any],
) -> ExperienceSignal:
    observer = observation.get(
        "observer",
        "unknown_observer",
    )

    evidence = [
        (
            f"{key}={value}"
        )
        for key, value in observation.items()
        if key not in {
            "observer",
            "role",
            "state_write",
        }
    ]

    return ExperienceSignal(
        source_id=observer,
        family="observation",
        status="observed",
        strength=0.24,
        statement=(
            f"Наблюдение «{observer}» доступно "
            "общему контексту Малыша"
        ),
        evidence=evidence[:8],
        factual=True,
        generated=False,
    )


def memory_signal(
    memory: dict[str, Any],
) -> ExperienceSignal:
    status = memory.get(
        "status",
        "named_unresolved",
    )

    paths = list(
        memory.get(
            "paths",
            [],
        )
    )

    return ExperienceSignal(
        source_id=memory.get(
            "id",
            "unknown_memory",
        ),
        family=memory.get(
            "kind",
            "legacy_logic",
        ),
        status=status,
        strength=memory_strength(memory),
        statement=memory_statement(memory),
        evidence=[
            f"memory_status={status}",
            *[
                f"source={path}"
                for path in paths[:6]
            ],
        ],
        factual=(
            status in {
                "recovered",
                "historical",
            }
        ),
        generated=False,
    )


def workflow_signal(
    recalled: dict[str, Any],
) -> ExperienceSignal:
    return ExperienceSignal(
        source_id=recalled["source_id"],
        family=(
            "workflow_experience:"
            + recalled["family"]
        ),
        status="recalled_skill",
        strength=clamp(
            recalled["strength"]
        ),
        statement=(
            "Малыш вспоминает навык "
            f"«{recalled['title']}»: "
            + recalled["capability"]
        ),
        evidence=list(
            recalled.get(
                "evidence",
                [],
            )
        ),
        factual=False,
        generated=False,
    )


def detect_contradictions(
    signals: list[ExperienceSignal],
) -> list[dict[str, Any]]:
    """
    Пока фиксирует только структурные противоречия:
    одно имя одновременно не должно быть и фактом,
    и неразрешённой памятью.
    """
    by_source: dict[
        str,
        set[str],
    ] = {}

    for signal in signals:
        by_source.setdefault(
            signal.source_id,
            set(),
        ).add(signal.status)

    contradictions = []

    for source_id, statuses in by_source.items():
        if (
            "named_unresolved" in statuses
            and (
                "recovered" in statuses
                or "historical" in statuses
            )
        ):
            contradictions.append(
                {
                    "source_id": source_id,
                    "statuses": sorted(
                        statuses
                    ),
                    "resolution": (
                        "требуется проверка "
                        "происхождения"
                    ),
                }
            )

    return contradictions


def build_experience(
    text: str,
    conscious: dict[str, Any],
    subconscious: dict[str, Any],
    observations: list[dict[str, Any]],
) -> MalyshExperience:
    """
    Собирает все внутренние инструменты в один опыт.

    Единственный субъект:
        Malysh

    567, КМБП, N7/O7, Base-4, память,
    наблюдатели, Рой и Омни являются источниками
    сигналов, но не самостоятельными решающими
    субъектами.
    """
    signals: list[ExperienceSignal] = []

    selected = list(
        conscious.get(
            "selected",
            [],
        )
    )

    if selected:
        signals.append(
            ExperienceSignal(
                source_id="conscious_router",
                family="conscious_logic",
                status="current",
                strength=min(
                    0.88,
                    0.55
                    + 0.07 * len(selected),
                ),
                statement=(
                    "Сознательная логика выбрала: "
                    + ", ".join(selected)
                ),
                evidence=[
                    f"query={text[:180]}"
                ],
                factual=False,
                generated=False,
            )
        )

    categories = list(
        subconscious.get(
            "categories",
            [],
        )
    )

    if categories:
        signals.append(
            ExperienceSignal(
                source_id="subconscious_plan",
                family="subconscious_logic",
                status="current",
                strength=0.34,
                statement=(
                    "Подсознание распознало контуры: "
                    + ", ".join(categories)
                ),
                evidence=[
                    "Независимый PLAN"
                ],
                factual=False,
                generated=False,
            )
        )

    legacy = subconscious.get(
        "legacy_memory",
        {},
    )

    recalled = list(
        legacy.get(
            "recalled",
            [],
        )
    )

    unresolved = []

    for memory in recalled:
        signals.append(
            memory_signal(memory)
        )

        if memory.get("status") == (
            "named_unresolved"
        ):
            unresolved.append(
                memory.get(
                    "title",
                    memory.get(
                        "id",
                        "unknown",
                    ),
                )
            )

    workflow_recall = recall_workflows(
        text,
        limit=4,
    )

    for recalled_workflow in workflow_recall[
        "recalled"
    ]:
        signals.append(
            workflow_signal(
                recalled_workflow
            )
        )

    for observation in observations:
        signals.append(
            observation_signal(
                observation
            )
        )

    return MalyshExperience(
        subject="Malysh",
        signals=signals,
        contradictions=detect_contradictions(
            signals
        ),
        unresolved=unresolved,
        generated_hypotheses=[],
        decision_authority=False,
        state_write=False,
        state_commit=False,
    )
