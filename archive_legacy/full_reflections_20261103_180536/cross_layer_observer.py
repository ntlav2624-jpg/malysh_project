from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any


LAYER_ORDER = (
    "consciousness",
    "subconscious",
    "joint",
    "experience",
    "human",
    "observations",
)


@dataclass
class Pattern:
    pattern_id: str
    kind: str
    participants: list[str]
    statement: str
    confidence: float
    evidence: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LayerReport:
    observer_layer: str
    observed_layers: list[str]
    patterns: list[str]
    agreements: list[str]
    divergences: list[str]
    anomalies: list[str]
    conclusion: str
    influence_on_answer: bool
    decision_authority: bool
    state_write: bool
    state_commit: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CrossLayerAnalysis:
    subject: str
    mode: str
    input_digest: str
    patterns: list[Pattern]
    layer_reports: list[LayerReport]
    meta_conclusion: str
    influence_on_answer: bool
    decision_authority: bool
    automatic_execution: bool
    state_write: bool
    state_commit: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "mode": self.mode,
            "input_digest": self.input_digest,
            "patterns": [
                item.to_dict()
                for item in self.patterns
            ],
            "layer_reports": [
                item.to_dict()
                for item in self.layer_reports
            ],
            "meta_conclusion": (
                self.meta_conclusion
            ),
            "influence_on_answer": (
                self.influence_on_answer
            ),
            "decision_authority": (
                self.decision_authority
            ),
            "automatic_execution": (
                self.automatic_execution
            ),
            "state_write": self.state_write,
            "state_commit": self.state_commit,
        }


def stable_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def digest_layers(
    layers: dict[str, Any],
) -> str:
    return hashlib.sha256(
        stable_json(layers).encode("utf-8")
    ).hexdigest()


def unique(values: list[str]) -> list:
    return list(
        dict.fromkeys(
            value
            for value in values
            if value
        )
    )


def selected_set(
    layer: dict[str, Any],
) -> set:
    return {
        str(item)
        for item in layer.get(
            "selected",
            [],
        )
    }


def workflow_sources(
    experience: dict[str, Any],
) -> list:
    return [
        str(item.get("source_id"))
        for item in experience.get(
            "signals",
            [],
        )
        if item.get("status")
        == "recalled_skill"
    ]


def memory_sources(
    experience: dict[str, Any],
) -> list:
    memory_statuses = {
        "recovered",
        "historical",
        "named_unresolved",
    }

    return [
        str(item.get("source_id"))
        for item in experience.get(
            "signals",
            [],
        )
        if item.get("status")
        in memory_statuses
    ]


def human_sources(
    human: dict[str, Any],
) -> list:
    return [
        str(item.get("source"))
        for item in human.get(
            "possible",
            [],
        )
    ]


def discover_patterns(
    layers: dict[str, Any],
) -> list:
    consciousness = layers["consciousness"]
    subconscious = layers["subconscious"]
    joint = layers["joint"]
    experience = layers["experience"]
    human = layers["human"]
    observations = layers["observations"]

    patterns: list[Pattern] = []

    conscious_selected = selected_set(
        consciousness
    )

    joint_selected = selected_set(
        joint
    )

    subconscious_selected = selected_set(
        subconscious
    )

    if conscious_selected == joint_selected:
        patterns.append(
            Pattern(
                pattern_id=(
                    "conscious_joint_alignment"
                ),
                kind="agreement",
                participants=[
                    "consciousness",
                    "joint",
                ],
                statement=(
                    "Совместный слой сохранил "
                    "выбор сознательного контура"
                ),
                confidence=0.85,
                evidence=[
                    (
                        "consciousness.selected="
                        + repr(
                            sorted(
                                conscious_selected
                            )
                        )
                    ),
                    (
                        "joint.selected="
                        + repr(
                            sorted(
                                joint_selected
                            )
                        )
                    ),
                ],
            )
        )

    shared_selected = sorted(
        conscious_selected
        & subconscious_selected
    )

    if shared_selected:
        patterns.append(
            Pattern(
                pattern_id=(
                    "conscious_subconscious_overlap"
                ),
                kind="agreement",
                participants=[
                    "consciousness",
                    "subconscious",
                ],
                statement=(
                    "Сознание и подсознание "
                    "выделили общие внутренние контуры"
                ),
                confidence=min(
                    0.80,
                    0.35
                    + 0.08
                    * len(shared_selected),
                ),
                evidence=[
                    (
                        "shared="
                        + ", ".join(
                            shared_selected
                        )
                    )
                ],
            )
        )

    broad_fallback = bool(
        subconscious.get(
            "broad_fallback",
            False,
        )
    )

    if broad_fallback:
        patterns.append(
            Pattern(
                pattern_id=(
                    "subconscious_broad_fallback"
                ),
                kind="divergence",
                participants=[
                    "consciousness",
                    "subconscious",
                ],
                statement=(
                    "Подсознание не нашло точную "
                    "альтернативу и подавило широкий "
                    "fallback"
                ),
                confidence=0.90,
                evidence=[
                    (
                        "subconscious."
                        "broad_fallback=True"
                    ),
                    (
                        "conscious_selected="
                        + repr(
                            sorted(
                                conscious_selected
                            )
                        )
                    ),
                ],
            )
        )

    recalled_workflows = workflow_sources(
        experience
    )

    recalled_memories = memory_sources(
        experience
    )

    if recalled_workflows:
        patterns.append(
            Pattern(
                pattern_id=(
                    "workflow_experience_recalled"
                ),
                kind="association",
                participants=[
                    "experience",
                    "human",
                ],
                statement=(
                    "Единый опыт вспомнил прежние "
                    "workflow-навыки для текущей задачи"
                ),
                confidence=min(
                    0.75,
                    0.35
                    + 0.08
                    * len(
                        recalled_workflows
                    ),
                ),
                evidence=[
                    (
                        "workflows="
                        + ", ".join(
                            recalled_workflows
                        )
                    )
                ],
            )
        )

    if (
        recalled_workflows
        and recalled_memories
    ):
        patterns.append(
            Pattern(
                pattern_id=(
                    "memory_workflow_coactivation"
                ),
                kind="cross_layer_pattern",
                participants=[
                    "subconscious",
                    "experience",
                    "human",
                ],
                statement=(
                    "Старая память и workflow-опыт "
                    "активировались в одном цикле"
                ),
                confidence=0.55,
                evidence=[
                    (
                        "memory="
                        + ", ".join(
                            recalled_memories
                        )
                    ),
                    (
                        "workflow="
                        + ", ".join(
                            recalled_workflows
                        )
                    ),
                ],
            )
        )

    unresolved = list(
        experience.get(
            "unresolved",
            [],
        )
    )

    generated_count = sum(
        1
        for source in human_sources(human)
        if source
        == "generated_hypothesis"
    )

    if unresolved:
        patterns.append(
            Pattern(
                pattern_id=(
                    "unresolved_memory_observed"
                ),
                kind="uncertainty",
                participants=[
                    "experience",
                    "human",
                ],
                statement=(
                    "Обнаружена неразрешённая память; "
                    "она сохранена отдельно от фактов"
                ),
                confidence=0.95,
                evidence=[
                    (
                        "unresolved="
                        + ", ".join(
                            map(
                                str,
                                unresolved,
                            )
                        )
                    ),
                    (
                        "generated_hypotheses="
                        + str(generated_count)
                    ),
                ],
            )
        )

    possible_count = len(
        human.get(
            "possible",
            [],
        )
    )

    if possible_count:
        patterns.append(
            Pattern(
                pattern_id=(
                    "human_alternatives_preserved"
                ),
                kind="human_pattern",
                participants=[
                    "human",
                ],
                statement=(
                    "Human Layer сохранил "
                    "альтернативные выводы отдельно "
                    "от основного решения"
                ),
                confidence=0.90,
                evidence=[
                    (
                        "possible_count="
                        + str(possible_count)
                    ),
                    (
                        "decision_is_truth="
                        + str(
                            human.get(
                                "decision_is_truth"
                            )
                        )
                    ),
                ],
            )
        )

    if observations:
        observer_names = unique(
            [
                str(
                    item.get(
                        "observer",
                        "unknown_observer",
                    )
                )
                for item in observations
            ]
        )

        patterns.append(
            Pattern(
                pattern_id=(
                    "physical_observation_available"
                ),
                kind="observation",
                participants=[
                    "observations",
                    "experience",
                ],
                statement=(
                    "Физические наблюдатели доступны "
                    "для межслойного сравнения"
                ),
                confidence=0.80,
                evidence=[
                    (
                        "observers="
                        + ", ".join(
                            observer_names
                        )
                    )
                ],
            )
        )

    return patterns


def report_for_layer(
    layer_name: str,
    patterns: list[Pattern],
) -> LayerReport:
    observed_layers = [
        name
        for name in LAYER_ORDER
        if name != layer_name
    ]

    relevant = [
        pattern
        for pattern in patterns
        if (
            layer_name
            in pattern.participants
            or any(
                name
                in pattern.participants
                for name in observed_layers
            )
        )
    ]

    agreements = unique(
        [
            item.statement
            for item in relevant
            if item.kind == "agreement"
        ]
    )

    divergences = unique(
        [
            item.statement
            for item in relevant
            if item.kind
            in {
                "divergence",
                "uncertainty",
            }
        ]
    )

    anomalies = unique(
        [
            item.statement
            for item in relevant
            if item.kind == "anomaly"
        ]
    )

    pattern_statements = unique(
        [
            item.statement
            for item in relevant
            if item.kind
            not in {
                "agreement",
                "divergence",
                "uncertainty",
                "anomaly",
            }
        ]
    )

    if relevant:
        conclusion = (
            f"Слой «{layer_name}» увидел "
            f"{len(relevant)} межслойных связей; "
            "вывод сохранён только для анализа"
        )
    else:
        conclusion = (
            f"Слой «{layer_name}» не обнаружил "
            "значимых межслойных связей"
        )

    return LayerReport(
        observer_layer=layer_name,
        observed_layers=observed_layers,
        patterns=pattern_statements,
        agreements=agreements,
        divergences=divergences,
        anomalies=anomalies,
        conclusion=conclusion,
        influence_on_answer=False,
        decision_authority=False,
        state_write=False,
        state_commit=False,
    )


def observe_cross_layers(
    consciousness: dict[str, Any],
    subconscious: dict[str, Any],
    joint: dict[str, Any],
    experience: dict[str, Any],
    human: dict[str, Any],
    observations: list[dict[str, Any]],
) -> CrossLayerAnalysis:
    """
    Пассивно анализирует уже сформированные слои.

    Функция вызывается только после Human Layer.
    Она не возвращает команды, не изменяет ответ
    и не участвует в исполнительном решении.
    """
    layers = {
        "consciousness": consciousness,
        "subconscious": subconscious,
        "joint": joint,
        "experience": experience,
        "human": human,
        "observations": observations,
    }

    before = stable_json(layers)
    input_digest = digest_layers(layers)

    patterns = discover_patterns(layers)

    reports = [
        report_for_layer(
            layer_name,
            patterns,
        )
        for layer_name in LAYER_ORDER
    ]

    after = stable_json(layers)

    if before != after:
        raise RuntimeError(
            "Cross-layer observer mutated "
            "its input layers"
        )

    if patterns:
        meta_conclusion = (
            "Перекрёстное наблюдение обнаружило "
            f"{len(patterns)} паттернов. "
            "Они не изменяют текущий ответ."
        )
    else:
        meta_conclusion = (
            "Значимые межслойные паттерны "
            "не обнаружены. Текущий ответ "
            "не изменялся."
        )

    return CrossLayerAnalysis(
        subject="Malysh",
        mode="passive_cross_layer_observation",
        input_digest=input_digest,
        patterns=patterns,
        layer_reports=reports,
        meta_conclusion=meta_conclusion,
        influence_on_answer=False,
        decision_authority=False,
        automatic_execution=False,
        state_write=False,
        state_commit=False,
    )


def cross_layer_summary(
    analysis: CrossLayerAnalysis,
) -> str:
    lines = [
        "=== ПЕРЕКРЁСТНОЕ НАБЛЮДЕНИЕ ===",
        (
            "Режим          : "
            + analysis.mode
        ),
        (
            "Паттернов      : "
            + str(len(analysis.patterns))
        ),
        "Влияние на ответ: нет",
        "Право решения   : нет",
        "Выводы слоёв:",
    ]

    for report in analysis.layer_reports:
        lines.append(
            "  "
            + report.observer_layer
            + ": "
            + report.conclusion
        )

    if analysis.patterns:
        lines.append(
            "Общие паттерны:"
        )

        for index, pattern in enumerate(
            analysis.patterns,
            start=1,
        ):
            lines.append(
                f"  {index}. "
                + pattern.statement
                + f" [{pattern.confidence:.2f}]"
            )

    lines.append(
        "Мета-вывод: "
        + analysis.meta_conclusion
    )

    return "\n".join(lines)
