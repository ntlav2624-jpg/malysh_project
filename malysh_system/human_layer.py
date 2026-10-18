from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Hypothesis:
    hypothesis: str
    certainty: float
    evidence: list[str]
    source: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HumanThought:
    logical: Hypothesis
    possible: list[Hypothesis]
    decision: str
    decision_is_truth: bool
    reconsideration_possible: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "logical": self.logical.to_dict(),
            "possible": [
                item.to_dict()
                for item in self.possible
            ],
            "decision": self.decision,
            "decision_is_truth": self.decision_is_truth,
            "reconsideration_possible": (
                self.reconsideration_possible
            ),
        }


def clamp(value: float) -> float:
    return max(
        0.0,
        min(1.0, float(value)),
    )


def text_matches(
    text: str,
    fragments: tuple[str, ...],
) -> bool:
    lowered = text.lower()

    return any(
        fragment in lowered
        for fragment in fragments
    )


def relevant_observer_evidence(
    text: str,
    conscious: dict[str, Any],
    observations: list[dict[str, Any]],
) -> list:
    """
    Возвращает только наблюдения,
    семантически связанные с текущей задачей.
    """
    selected = set(
        conscious.get("selected", [])
    )

    phase_relevant = (
        "phase_coupling" in selected
        or text_matches(
            text,
            (
                "фаз",
                "phase",
                "сопряж",
                "резонанс",
            ),
        )
    )

    vortex_relevant = text_matches(
        text,
        (
            "вихр",
            "vortex",
            "завихр",
            "clebsch",
        ),
    )

    vault_relevant = (
        "native_malysh_engine" in selected
        or text_matches(
            text,
            (
                "памят",
                "истори",
                "паспорт",
                "поколен",
                "прежний малыш",
                "старый малыш",
            ),
        )
    )

    evidence: list[str] = []

    for item in observations:
        observer = item.get(
            "observer",
            "unknown_observer",
        )

        if (
            observer == "phase_observer"
            and phase_relevant
        ):
            initial = item.get(
                "initial_mean_phase_diff"
            )

            final = item.get(
                "final_mean_phase_diff"
            )

            if (
                isinstance(initial, (int, float))
                and isinstance(final, (int, float))
            ):
                direction = (
                    "снизилась"
                    if final < initial
                    else "выросла"
                )

                evidence.append(
                    "phase_observer: "
                    "средняя разность фаз "
                    f"{direction}"
                )

        elif (
            observer == "vortex_observer"
            and vortex_relevant
        ):
            maximum = item.get(
                "max_vorticity"
            )

            if isinstance(
                maximum,
                (int, float),
            ):
                evidence.append(
                    "vortex_observer: "
                    "обнаружено вихревое поле"
                )

        elif (
            observer == "vault_observer"
            and vault_relevant
        ):
            count = int(
                item.get(
                    "passport_count",
                    0,
                )
                or 0
            )

            evidence.append(
                "vault_observer: "
                f"доступно исторических "
                f"паспортов {count}"
            )

    return evidence


def generate_unknown_hypothesis(
    title: str,
    kind: str,
    text: str,
    conscious: dict[str, Any],
) -> Hypothesis:
    """
    Строит собственное предположение Малыша.

    Это не восстановленная память и не факт.
    Гипотеза создаётся только для анализа,
    может быть изменена или полностью отброшена.
    """
    selected = list(
        conscious.get(
            "selected",
            [],
        )
    )

    kind_templates = {
        "collective_logic": (
            "Возможно, «{title}» обозначала "
            "коллективную координацию нескольких "
            "частей Малыша или распределённый "
            "поиск вариантов"
        ),
        "legacy_logic": (
            "Возможно, «{title}» была прежним "
            "способом объединения нескольких "
            "логических контуров в общий вывод"
        ),
        "computational_logic": (
            "Возможно, «{title}» была отдельным "
            "вычислительным правилом или режимом "
            "преобразования состояния"
        ),
        "geometric_logic": (
            "Возможно, «{title}» описывала "
            "геометрическое ограничение, переход "
            "или топологический маршрут"
        ),
        "memory_logic": (
            "Возможно, «{title}» обозначала "
            "способ связывания текущей задачи "
            "с прежним опытом"
        ),
        "cognitive_logic": (
            "Возможно, «{title}» была отдельным "
            "контуром рассуждения или согласования"
        ),
    }

    template = kind_templates.get(
        kind,
        (
            "Возможно, «{title}» была отдельной "
            "логикой Малыша, связанной с текущим "
            "запросом, но её первоначальное "
            "назначение пока не восстановлено"
        ),
    )

    hypothesis = template.format(
        title=title
    )

    evidence = [
        (
            "Основание гипотезы: тип памяти "
            f"{kind}"
        ),
        (
            "Контекст запроса: "
            + text[:160]
        ),
        (
            "Это новая интерпретация, "
            "а не восстановленный факт"
        ),
    ]

    if selected:
        evidence.append(
            "Сознательно выбранные контуры: "
            + ", ".join(selected[:6])
        )

    return Hypothesis(
        hypothesis=hypothesis,
        certainty=0.18,
        evidence=evidence,
        source="generated_hypothesis",
        status="possible",
    )


def build_human_thought(
    text: str,
    conscious: dict[str, Any],
    subconscious: dict[str, Any],
    joint: dict[str, Any],
    observations: list[dict[str, Any]],
) -> HumanThought:
    selected = list(
        conscious.get(
            "selected",
            [],
        )
    )

    categories = list(
        subconscious.get(
            "categories",
            [],
        )
    )

    answer = conscious.get("answer")

    logical_evidence: list[str] = []

    if selected:
        logical_evidence.append(
            "semantic_router: "
            + ", ".join(selected)
        )

    if categories:
        logical_evidence.append(
            "subconscious: "
            + ", ".join(categories)
        )

    if answer is not None:
        logical_text = (
            "Основной вывод: "
            + str(answer)
        )

        logical_certainty = 0.95

    elif selected:
        logical_text = (
            "Основной путь: "
            + ", ".join(selected)
        )

        logical_certainty = min(
            0.88,
            0.55 + 0.07 * len(selected),
        )

    else:
        logical_text = (
            "Основной путь пока не определён"
        )

        logical_certainty = 0.35

    logical = Hypothesis(
        hypothesis=logical_text,
        certainty=clamp(
            logical_certainty
        ),
        evidence=logical_evidence,
        source="logical_branch",
        status="primary",
    )

    possible: list[Hypothesis] = []

    is_reflex = (
        conscious.get("mode") == "reflex"
        or answer is not None
    )

    if not is_reflex:
        observation_evidence = (
            relevant_observer_evidence(
                text=text,
                conscious=conscious,
                observations=observations,
            )
        )

        if observation_evidence:
            possible.append(
                Hypothesis(
                    hypothesis=(
                        "Релевантное наблюдение "
                        "может изменить основной вывод"
                    ),
                    certainty=clamp(
                        min(
                            0.49,
                            0.24
                            + 0.08
                            * len(
                                observation_evidence
                            ),
                        )
                    ),
                    evidence=observation_evidence,
                    source="observers",
                    status="possible",
                )
            )

        subconscious_selected = set(
            subconscious.get(
                "selected",
                [],
            )
        )

        conscious_selected = set(
            selected
        )

        alternative = sorted(
            subconscious_selected
            - conscious_selected
        )

        broad_fallback = bool(
            subconscious.get(
                "broad_fallback",
                False,
            )
        )

        if alternative and not broad_fallback:
            visible = alternative[:6]

            possible.append(
                Hypothesis(
                    hypothesis=(
                        "Подсознание предлагает "
                        "альтернативный путь: "
                        + ", ".join(visible)
                    ),
                    certainty=clamp(
                        min(
                            0.45,
                            0.22
                            + 0.04
                            * len(visible),
                        )
                    ),
                    evidence=[
                        "Избирательный независимый "
                        "подсознательный PLAN"
                    ],
                    source="subconscious",
                    status="possible",
                )
            )

    legacy_memory = subconscious.get(
        "legacy_memory",
        {},
    )

    recalled_memories = legacy_memory.get(
        "recalled",
        [],
    )

    for memory in recalled_memories[:5]:
        status = memory.get(
            "status",
            "named_unresolved",
        )

        title = memory.get(
            "title",
            memory.get(
                "id",
                "Неизвестное воспоминание",
            ),
        )

        score = float(
            memory.get(
                "score",
                0,
            )
            or 0
        )

        if status == "recovered":
            certainty = min(
                0.58,
                0.28 + score / 200.0,
            )

            hypothesis = (
                "Восстановленное знание "
                f"«{title}» может быть "
                "полезно для текущей задачи"
            )

        elif status == "historical":
            certainty = min(
                0.42,
                0.20 + score / 250.0,
            )

            hypothesis = (
                "Историческое воспоминание "
                f"«{title}» может содержать "
                "подходящий прежний опыт"
            )

        else:
            certainty = 0.12

            hypothesis = (
                "Малыш помнит название "
                f"«{title}», но исходное содержание "
                "ещё не восстановлено"
            )

        possible.append(
            Hypothesis(
                hypothesis=hypothesis,
                certainty=clamp(
                    certainty
                ),
                evidence=[
                    (
                        "Legacy Memory: "
                        f"status={status}"
                    ),
                    (
                        "Восстановленный смысл "
                        "не подменяется гипотезой"
                    ),
                ],
                source="legacy_memory",
                status="possible",
            )
        )

        if status == "named_unresolved":
            possible.append(
                generate_unknown_hypothesis(
                    title=title,
                    kind=memory.get(
                        "kind",
                        "legacy_logic",
                    ),
                    text=text,
                    conscious=conscious,
                )
            )

    uncertainty_text = (
        "Интерпретация запроса может быть пересмотрена"
        if is_reflex
        else (
            "Основное решение может оказаться "
            "неполным или ошибочным"
        )
    )

    uncertainty_value = (
        0.05
        if is_reflex
        else 0.20
    )

    possible.append(
        Hypothesis(
            hypothesis=uncertainty_text,
            certainty=uncertainty_value,
            evidence=[
                "Human Layer сохраняет "
                "право на пересмотр"
            ],
            source="human_uncertainty",
            status="possible",
        )
    )

    return HumanThought(
        logical=logical,
        possible=possible,
        decision=logical.hypothesis,
        decision_is_truth=False,
        reconsideration_possible=True,
    )


def human_summary(
    thought: HumanThought,
) -> str:
    lines = [
        "=== HUMAN LAYER ===",
        (
            "ОСНОВНОЕ : "
            + thought.logical.hypothesis
        ),
        (
            "Уверенность: "
            f"{thought.logical.certainty:.2f}"
        ),
        "Истина?   : не утверждается",
        "ВОЗМОЖНО:",
    ]

    for index, item in enumerate(
        thought.possible,
        start=1,
    ):
        lines.append(
            f"  {index}. "
            f"{item.hypothesis} "
            f"[{item.certainty:.2f}]"
        )

        for evidence in item.evidence:
            lines.append(
                "     потому что: "
                + evidence
            )

    lines.append(
        "Пересмотр решения: возможно"
    )

    return "\n".join(lines)
