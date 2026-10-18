from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable


EngineFactory = Callable[[], Any]


@dataclass
class DiagnosticResult:
    diagnostic_id: str
    subject: str
    family: str
    status: str
    checks: list[dict[str, Any]]
    conclusion: str
    influence_on_answer: bool
    decision_authority: bool
    automatic_execution: bool
    state_write: bool
    state_commit: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_result(
    diagnostic_id: str,
    family: str,
    checks: list[dict[str, Any]],
    conclusion: str,
) -> DiagnosticResult:
    return DiagnosticResult(
        diagnostic_id=diagnostic_id,
        subject="Malysh",
        family=family,
        status="observed",
        checks=checks,
        conclusion=conclusion,
        influence_on_answer=False,
        decision_authority=False,
        automatic_execution=False,
        state_write=False,
        state_commit=False,
    )


def default_engine_factory() -> Any:
    from malysh_engine import MalyshEngine

    return MalyshEngine()
