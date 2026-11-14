#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/malysh_project"
cd "$ROOT"

MODULE="malysh_system/cognitive_flow.py"
INTEGRATION="malysh_system/cognitive_flow_integration.py"
TEST="tests/test_cognitive_flow.py"
CONFIG="config/cognitive_flow.json"

echo "============================================================"
echo "MALYSH: INSTALL COGNITIVE FLOW CONTROLLER"
echo "============================================================"

# ------------------------------------------------------------
# 1. PREFLIGHT
# ------------------------------------------------------------

git rev-parse --is-inside-work-tree >/dev/null

if [ -n "$(git diff --cached --name-only)" ]; then
    echo "STOP: Git index already contains staged files."
    echo "Nothing changed."
    git diff --cached --name-only
    exit 1
fi

for f in "$MODULE" "$INTEGRATION" "$TEST" "$CONFIG"; do
    if [ -e "$f" ]; then
        echo "STOP: target already exists: $f"
        echo "Nothing overwritten."
        exit 1
    fi
done

mkdir -p malysh_system tests config runtime/cognitive_flow

BEFORE="$(git rev-parse HEAD)"
BRANCH="$(git branch --show-current)"
STAMP="$(date +%Y%m%d_%H%M%S)"
TAG="pre-cognitive-flow-$STAMP"

git tag "$TAG" "$BEFORE"

echo "[PASS] repo   : $ROOT"
echo "[PASS] branch : $BRANCH"
echo "[PASS] before : $BEFORE"
echo "[PASS] tag    : $TAG"

# ------------------------------------------------------------
# 2. CORE
# ------------------------------------------------------------

cat > "$MODULE" <<'PY'
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from threading import RLock
from time import time
from typing import Any, Callable, Iterable, Mapping
from uuid import uuid4


class CognitiveFlowError(RuntimeError):
    pass


class InvariantViolation(CognitiveFlowError):
    pass


class UnknownState(CognitiveFlowError):
    pass


class ThoughtKind(str, Enum):
    FACT = "fact"
    OBSERVATION = "observation"
    MEMORY = "memory"
    HYPOTHESIS = "hypothesis"
    POSSIBLE = "possible"
    NEGATIVE_RESULT = "negative_result"
    UNRESOLVED = "unresolved"
    INVARIANT = "invariant"
    PROPOSAL = "proposal"
    DECISION = "decision"
    ACTION = "action"
    FEEDBACK = "feedback"


class BranchKind(str, Enum):
    PRIMARY = "primary"
    POSSIBLE = "possible"
    NEGATIVE = "negative"
    UNRESOLVED = "unresolved"


class RelationKind(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DERIVED_FROM = "derived_from"
    REFINES = "refines"
    OBSERVED_BY = "observed_by"
    TESTED_BY = "tested_by"
    INVALIDATES = "invalidates"
    REQUIRES = "requires"
    SUGGESTS = "suggests"
    BLOCKS_EXECUTION = "blocks_execution"


@dataclass(frozen=True)
class ThoughtState:
    state_id: str
    content: Any
    kind: ThoughtKind
    source: str
    confidence: float
    created_at: float = field(default_factory=time)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.state_id:
            raise InvariantViolation("state_id required")
        if not self.source:
            raise InvariantViolation("source required")
        if not 0.0 <= self.confidence <= 1.0:
            raise InvariantViolation(
                "confidence must be in [0,1]"
            )


@dataclass(frozen=True)
class WeightedRelation:
    relation_id: str
    sources: tuple[str, ...]
    target: str
    kind: RelationKind
    sign: int
    confidence: float
    evidence: float
    priority: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.sources:
            raise InvariantViolation(
                "relation requires source"
            )

        if self.sign not in (-1, 0, 1):
            raise InvariantViolation(
                "sign must be -1, 0 or 1"
            )

        for value in (
            self.confidence,
            self.evidence,
            self.priority,
        ):
            if not 0.0 <= value <= 1.0:
                raise InvariantViolation(
                    "relation weights must be in [0,1]"
                )

    @property
    def effective_weight(self):
        return (
            self.sign
            * self.confidence
            * self.evidence
            * self.priority
        )


@dataclass(frozen=True)
class ObserverReport:
    observer: str
    findings: Any
    confidence: float
    state_ids: tuple[str, ...] = ()
    created_at: float = field(default_factory=time)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise InvariantViolation(
                "observer confidence must be in [0,1]"
            )


@dataclass(frozen=True)
class ThoughtFlow:
    flow_id: str
    cycle: int
    relation_id: str
    amount: float
    created_at: float = field(default_factory=time)


@dataclass(frozen=True)
class BranchState:
    kind: BranchKind
    candidate_ids: tuple[str, ...]
    selected_id: str | None
    score: float


@dataclass(frozen=True)
class CycleResult:
    cycle: int
    primary: BranchState
    possible: BranchState
    negative: BranchState
    unresolved: BranchState
    active_state_ids: tuple[str, ...]
    frontier_state_ids: tuple[str, ...]
    attention: Mapping[str, float]
    observer_reports: tuple[ObserverReport, ...]
    execution_allowed: bool
    selected_action_id: str | None
    invariant_failures: tuple[str, ...]


@dataclass(frozen=True)
class WALEntry:
    sequence: int
    event_type: str
    payload: Mapping[str, Any]
    created_at: float = field(default_factory=time)


Observer = Callable[
    [
        Mapping[str, ThoughtState],
        tuple[WeightedRelation, ...],
        Mapping[str, float],
    ],
    ObserverReport | None,
]

InvariantCheck = Callable[
    [
        Mapping[str, ThoughtState],
        Mapping[str, float],
        tuple[WeightedRelation, ...],
    ],
    tuple[bool, str],
]


class CognitiveFlowController:

    def __init__(self):
        self._lock = RLock()

        self._states = {}
        self._relations = {}
        self._attention = {}
        self._active = set()

        self._observers = {}
        self._invariants = {}

        self._flows = []
        self._reports = []
        self._wal = []

        self._cycle = 0

    @property
    def states(self):
        return dict(self._states)

    @property
    def relations(self):
        return tuple(self._relations.values())

    @property
    def attention(self):
        return dict(self._attention)

    @property
    def wal(self):
        return tuple(self._wal)

    @property
    def flows(self):
        return tuple(self._flows)

    @property
    def cycle(self):
        return self._cycle

    def _wal_append(self, event_type, payload):
        self._wal.append(
            WALEntry(
                sequence=len(self._wal) + 1,
                event_type=event_type,
                payload=dict(payload),
            )
        )

    def _normalize_attention(self):
        if not self._attention:
            return

        for key, value in self._attention.items():
            if not isfinite(value) or value < 0.0:
                raise InvariantViolation(
                    "invalid attention "
                    f"{key}={value}"
                )

        total = sum(self._attention.values())

        if total <= 0.0:
            value = 1.0 / len(self._attention)

            for key in self._attention:
                self._attention[key] = value

            return

        for key in self._attention:
            self._attention[key] /= total

    def add_state(
        self,
        *,
        content,
        kind,
        source,
        confidence,
        state_id=None,
        metadata=None,
        initial_attention=0.0,
        active=False,
    ):
        with self._lock:
            item = ThoughtState(
                state_id=state_id or str(uuid4()),
                content=content,
                kind=kind,
                source=source,
                confidence=confidence,
                metadata=dict(metadata or {}),
            )

            if item.state_id in self._states:
                raise InvariantViolation(
                    f"duplicate state {item.state_id}"
                )

            if initial_attention < 0.0:
                raise InvariantViolation(
                    "negative initial attention"
                )

            self._states[item.state_id] = item
            self._attention[item.state_id] = float(
                initial_attention
            )

            if active:
                self._active.add(item.state_id)

            self._normalize_attention()

            self._wal_append(
                "state_added",
                {
                    "state_id": item.state_id,
                    "kind": item.kind.value,
                    "source": item.source,
                },
            )

            return item

    def add_relation(
        self,
        *,
        sources,
        target,
        kind,
        sign,
        confidence,
        evidence,
        priority,
        relation_id=None,
        metadata=None,
    ):
        with self._lock:
            sources = tuple(sources)

            missing = [
                state_id
                for state_id in (*sources, target)
                if state_id not in self._states
            ]

            if missing:
                raise UnknownState(
                    f"unknown states: {missing}"
                )

            relation = WeightedRelation(
                relation_id=(
                    relation_id or str(uuid4())
                ),
                sources=sources,
                target=target,
                kind=kind,
                sign=sign,
                confidence=confidence,
                evidence=evidence,
                priority=priority,
                metadata=dict(metadata or {}),
            )

            if relation.relation_id in self._relations:
                raise InvariantViolation(
                    "duplicate relation"
                )

            self._relations[
                relation.relation_id
            ] = relation

            self._wal_append(
                "relation_added",
                {
                    "relation_id": relation.relation_id,
                    "kind": relation.kind.value,
                    "sign": relation.sign,
                    "sources": relation.sources,
                    "target": relation.target,
                },
            )

            return relation

    def activate(self, state_ids):
        with self._lock:
            state_ids = tuple(state_ids)

            missing = [
                state_id
                for state_id in state_ids
                if state_id not in self._states
            ]

            if missing:
                raise UnknownState(
                    f"unknown states: {missing}"
                )

            self._active.update(state_ids)

            self._wal_append(
                "states_activated",
                {"state_ids": state_ids},
            )

    def register_observer(
        self,
        name,
        observer,
    ):
        with self._lock:
            self._observers[name] = observer

            self._wal_append(
                "observer_registered",
                {"name": name},
            )

    def register_invariant(
        self,
        name,
        check,
    ):
        with self._lock:
            self._invariants[name] = check

            self._wal_append(
                "invariant_registered",
                {"name": name},
            )

    def _frontier(self) -> setfrontier: set[str] = set()

        for relation in self._relations.values():
            if set(
                relation.sources
            ).issubset(self._active):
                frontier.add(
                    relation.target
                )

        return frontier

    def _propagate_attention(
        self,
        frontier,
    ):
        next_attention = {
            state_id: 0.92 * value
            for state_id, value
            in self._attention.items()
        }

        for relation in self._relations.values():
            if not set(
                relation.sources
            ).issubset(self._active):
                continue

            source_attention = sum(
                self._attention[source]
                for source in relation.sources
            ) / len(relation.sources)

            amount = (
                source_attention
                * abs(
                    relation.effective_weight
                )
            )

            signed_amount = (
                amount
                if relation.sign >= 0
                else -amount
            )

            self._flows.append(
                ThoughtFlow(
                    flow_id=str(uuid4()),
                    cycle=self._cycle,
                    relation_id=(
                        relation.relation_id
                    ),
                    amount=signed_amount,
                )
            )

            if relation.sign > 0:
                next_attention[
                    relation.target
                ] += amount

            elif relation.sign < 0:
                # Negative result is preserved and
                # receives attention as a boundary.
                next_attention[
                    relation.target
                ] += 0.75 * amount

            else:
                next_attention[
                    relation.target
                ] += 0.10 * source_attention

        for state_id in frontier:
            next_attention[
                state_id
            ] += (
                0.05
                * self._states[
                    state_id
                ].confidence
            )

        self._attention = next_attention
        self._normalize_attention()

    def _run_observers(self):
        reports = []

        relations = tuple(
            self._relations.values()
        )

        for name, observer in (
            self._observers.items()
        ):
            report = observer(
                dict(self._states),
                relations,
                dict(self._attention),
            )

            if report is None:
                continue

            if report.observer != name:
                raise InvariantViolation(
                    "observer name mismatch"
                )

            reports.append(report)
            self._reports.append(report)

        return tuple(reports)

    def _score(self, state_id):
        state = self._states[state_id]

        positive = 0.0
        negative = 0.0

        for relation in (
            self._relations.values()
        ):
            if relation.target != state_id:
                continue

            amount = abs(
                relation.effective_weight
            )

            if relation.sign > 0:
                positive += amount

            elif relation.sign < 0:
                negative += amount

        return (
            self._attention.get(
                state_id,
                0.0,
            )
            + state.confidence
            + positive
            - negative
        )

    def _branch(
        self,
        branch_kind,
        candidate_ids,
    ):
        candidate_ids = tuple(
            sorted(
                set(candidate_ids)
            )
        )

        if not candidate_ids:
            return BranchState(
                kind=branch_kind,
                candidate_ids=(),
                selected_id=None,
                score=0.0,
            )

        ranked = sorted(
            (
                (
                    self._score(state_id),
                    state_id,
                )
                for state_id in candidate_ids
            ),
            reverse=True,
        )

        score, selected = ranked[0]

        return BranchState(
            kind=branch_kind,
            candidate_ids=candidate_ids,
            selected_id=selected,
            score=float(score),
        )

    def _branches(self, frontier):
        primary = []
        possible = []
        negative = []
        unresolved = []

        for state_id in (
            frontier | self._active
        ):
            kind = self._states[
                state_id
            ].kind

            if kind in (
                ThoughtKind.FACT,
                ThoughtKind.OBSERVATION,
                ThoughtKind.PROPOSAL,
                ThoughtKind.DECISION,
                ThoughtKind.ACTION,
            ):
                primary.append(state_id)

            elif kind in (
                ThoughtKind.HYPOTHESIS,
                ThoughtKind.POSSIBLE,
            ):
                possible.append(state_id)

            elif (
                kind
                == ThoughtKind.NEGATIVE_RESULT
            ):
                negative.append(state_id)

            elif (
                kind
                == ThoughtKind.UNRESOLVED
            ):
                unresolved.append(state_id)

        return (
            self._branch(
                BranchKind.PRIMARY,
                primary,
            ),
            self._branch(
                BranchKind.POSSIBLE,
                possible,
            ),
            self._branch(
                BranchKind.NEGATIVE,
                negative,
            ),
            self._branch(
                BranchKind.UNRESOLVED,
                unresolved,
            ),
        )

    def _check_invariants(self):
        failures = []

        relations = tuple(
            self._relations.values()
        )

        for name, check in (
            self._invariants.items()
        ):
            passed, detail = check(
                dict(self._states),
                dict(self._attention),
                relations,
            )

            if not passed:
                failures.append(
                    f"{name}: {detail}"
                )

        if self._attention:
            total = sum(
                self._attention.values()
            )

            if abs(total - 1.0) > 1e-12:
                failures.append(
                    f"attention mass={total}"
                )

            if any(
                value < 0.0
                for value
                in self._attention.values()
            ):
                failures.append(
                    "negative attention"
                )

        return tuple(failures)

    def cycle_once(
        self,
        *,
        allow_action=False,
    ):
        with self._lock:
            self._cycle += 1

            frontier = self._frontier()

            self._propagate_attention(
                frontier
            )

            reports = (
                self._run_observers()
            )

            (
                primary,
                possible,
                negative,
                unresolved,
            ) = self._branches(
                frontier
            )

            failures = (
                self._check_invariants()
            )

            selected_action = None

            if (
                allow_action
                and not failures
                and primary.selected_id
                is not None
                and self._states[
                    primary.selected_id
                ].kind
                == ThoughtKind.ACTION
            ):
                selected_action = (
                    primary.selected_id
                )

            execution_allowed = bool(
                selected_action
                and not failures
            )

            self._active.update(
                frontier
            )

            result = CycleResult(
                cycle=self._cycle,
                primary=primary,
                possible=possible,
                negative=negative,
                unresolved=unresolved,
                active_state_ids=tuple(
                    sorted(self._active)
                ),
                frontier_state_ids=tuple(
                    sorted(frontier)
                ),
                attention=dict(
                    self._attention
                ),
                observer_reports=reports,
                execution_allowed=(
                    execution_allowed
                ),
                selected_action_id=(
                    selected_action
                ),
                invariant_failures=failures,
            )

            self._wal_append(
                "cycle_committed",
                {
                    "cycle": self._cycle,
                    "primary": (
                        primary.selected_id
                    ),
                    "possible": (
                        possible.selected_id
                    ),
                    "negative": (
                        negative.selected_id
                    ),
                    "unresolved": (
                        unresolved.selected_id
                    ),
                    "frontier": (
                        result.frontier_state_ids
                    ),
                    "execution_allowed": (
                        execution_allowed
                    ),
                },
            )

            return result

    def export_snapshot(self):
        return {
            "cycle": self._cycle,
            "state_count": len(
                self._states
            ),
            "relation_count": len(
                self._relations
            ),
            "attention": dict(
                self._attention
            ),
            "active": sorted(
                self._active
            ),
            "flow_count": len(
                self._flows
            ),
            "observer_report_count": len(
                self._reports
            ),
            "wal_length": len(
                self._wal
            ),
        }


def attention_invariant(
    states,
    attention,
    relations,
):
    del relations

    if set(states) != set(attention):
        return (
            False,
            "state/attention key mismatch",
        )

    if any(
        not isfinite(value)
        or value < 0.0
        for value in attention.values()
    ):
        return (
            False,
            "invalid attention",
        )

    if attention:
        total = sum(
            attention.values()
        )

        if abs(total - 1.0) > 1e-12:
            return (
                False,
                f"sum={total}",
            )

    return True, "ok"


def relation_reference_invariant(
    states,
    attention,
    relations,
):
    del attention

    ids = set(states)

    for relation in relations:
        if relation.target not in ids:
            return (
                False,
                "unknown target",
            )

        if any(
            source not in ids
            for source in relation.sources
        ):
            return (
                False,
                "unknown source",
            )

    return True, "ok"


def create_default_controller():
    controller = (
        CognitiveFlowController()
    )

    controller.register_invariant(
        "attention",
        attention_invariant,
    )

    controller.register_invariant(
        "relation_references",
        relation_reference_invariant,
    )

    return controller
PY

# ------------------------------------------------------------
# 3. INTEGRATION ADAPTER
# ------------------------------------------------------------

cat > "$INTEGRATION" <<'PY'
from __future__ import annotations

from typing import Any

from malysh_system.cognitive_flow import (
    CognitiveFlowController,
    create_default_controller,
)


ATTRIBUTE = "cognitive_flow"


def attach_cognitive_flow(
    mind: Any,
    *,
    controller=None,
    replace=False,
):
    existing = getattr(
        mind,
        ATTRIBUTE,
        None,
    )

    if existing is not None and not replace:
        if not isinstance(
            existing,
            CognitiveFlowController,
        ):
            raise TypeError(
                "Existing cognitive_flow "
                "has incompatible type"
            )

        return existing

    controller = (
        controller
        if controller is not None
        else create_default_controller()
    )

    setattr(
        mind,
        ATTRIBUTE,
        controller,
    )

    organs = getattr(
        mind,
        "internal_organs",
        None,
    )

    if isinstance(organs, dict):
        organs.setdefault(
            ATTRIBUTE,
            controller,
        )

    registry = getattr(
        mind,
        "organ_registry",
        None,
    )

    if isinstance(registry, dict):
        registry.setdefault(
            ATTRIBUTE,
            {
                "instance": controller,
                "role": (
                    "thought-flow coordination"
                ),
                "subject_count": 1,
            },
        )

    return controller


def get_cognitive_flow(
    mind: Any,
):
    value = getattr(
        mind,
        ATTRIBUTE,
        None,
    )

    if not isinstance(
        value,
        CognitiveFlowController,
    ):
        raise RuntimeError(
            "cognitive flow not attached"
        )

    return value
PY

# ------------------------------------------------------------
# 4. CONFIG
# ------------------------------------------------------------

cat > "$CONFIG" <<'JSON'
{
  "schema": "malysh.cognitive_flow.v1",
  "enabled": true,
  "subject_count": 1,
  "model": {
    "K": "typed thought states",
    "R": "typed relations",
    "W": "sign confidence evidence priority",
    "J": "realized thought flow",
    "A": "active states",
    "rho": "normalized measured attention",
    "Phi": "append-only history",
    "O": "independent observers"
  },
  "branches": [
    "primary",
    "possible",
    "negative",
    "unresolved"
  ],
  "organs": [
    "O3",
    "O4",
    "O5",
    "O345",
    "HumanLayer",
    "Swarm",
    "Omni",
    "567",
    "KMBP",
    "Base4",
    "Legacy",
    "Executor"
  ],
  "hard_invariants": [
    "one unified Malysh",
    "attention nonnegative",
    "attention normalized",
    "relations reference existing states",
    "negative results preserved",
    "observer cannot directly execute",
    "execution requires invariant gate",
    "append-only thought history",
    "legacy never deleted"
  ]
}
JSON

# ------------------------------------------------------------
# 5. UNIT TESTS, STANDARD LIBRARY ONLY
# ------------------------------------------------------------

cat > "$TEST" <<'PY'
from dataclasses import dataclass, field
import unittest

from malysh_system.cognitive_flow import (
    BranchKind,
    ObserverReport,
    RelationKind,
    ThoughtKind,
    create_default_controller,
)

from malysh_system.cognitive_flow_integration import (
    attach_cognitive_flow,
    get_cognitive_flow,
)


def build():
    c = create_default_controller()

    c.add_state(
        state_id="obs",
        content="observation",
        kind=ThoughtKind.OBSERVATION,
        source="O3",
        confidence=0.95,
        initial_attention=1.0,
        active=True,
    )

    for state_id, kind, confidence in (
        (
            "primary",
            ThoughtKind.PROPOSAL,
            0.85,
        ),
        (
            "possible",
            ThoughtKind.POSSIBLE,
            0.65,
        ),
        (
            "negative",
            ThoughtKind.NEGATIVE_RESULT,
            0.90,
        ),
        (
            "unresolved",
            ThoughtKind.UNRESOLVED,
            0.50,
        ),
    ):
        c.add_state(
            state_id=state_id,
            content=state_id,
            kind=kind,
            source="test",
            confidence=confidence,
        )

    for (
        relation_id,
        target,
        relation_kind,
        sign,
    ) in (
        (
            "rp",
            "primary",
            RelationKind.SUPPORTS,
            1,
        ),
        (
            "rposs",
            "possible",
            RelationKind.SUGGESTS,
            1,
        ),
        (
            "rneg",
            "negative",
            RelationKind.CONTRADICTS,
            -1,
        ),
        (
            "runres",
            "unresolved",
            RelationKind.REQUIRES,
            0,
        ),
    ):
        c.add_relation(
            relation_id=relation_id,
            sources=["obs"],
            target=target,
            kind=relation_kind,
            sign=sign,
            confidence=1.0,
            evidence=1.0,
            priority=1.0,
        )

    return c


class FlowTests(unittest.TestCase):

    def test_four_branches(self):
        c = build()
        r = c.cycle_once()

        self.assertEqual(
            r.primary.selected_id,
            "primary",
        )

        self.assertEqual(
            r.possible.selected_id,
            "possible",
        )

        self.assertEqual(
            r.negative.selected_id,
            "negative",
        )

        self.assertEqual(
            r.unresolved.selected_id,
            "unresolved",
        )

        self.assertFalse(
            r.execution_allowed
        )

        self.assertEqual(
            r.invariant_failures,
            (),
        )

    def test_negative_preserved(self):
        c = build()
        c.cycle_once()

        self.assertIn(
            "negative",
            c.states,
        )

        negative_relations = [
            r
            for r in c.relations
            if r.sign < 0
        ]

        self.assertEqual(
            len(negative_relations),
            1,
        )

    def test_attention(self):
        c = build()

        for _ in range(5):
            result = c.cycle_once()

            self.assertAlmostEqual(
                sum(
                    result.attention.values()
                ),
                1.0,
                places=12,
            )

            self.assertTrue(
                all(
                    value >= 0.0
                    for value
                    in result.attention.values()
                )
            )

    def test_observer(self):
        c = build()

        def observer(
            states,
            relations,
            attention,
        ):
            self.assertTrue(states)
            self.assertTrue(relations)
            self.assertTrue(attention)

            return ObserverReport(
                observer="O3",
                findings="ok",
                confidence=1.0,
            )

        c.register_observer(
            "O3",
            observer,
        )

        result = c.cycle_once()

        self.assertEqual(
            len(
                result.observer_reports
            ),
            1,
        )

        self.assertFalse(
            result.execution_allowed
        )

    def test_wal_append_only(self):
        c = build()

        before = c.wal

        c.cycle_once()
        c.cycle_once()

        after = c.wal

        self.assertEqual(
            after[:len(before)],
            before,
        )

        self.assertEqual(
            [
                entry.sequence
                for entry in after
            ],
            list(
                range(
                    1,
                    len(after) + 1,
                )
            ),
        )


@dataclass
class DummyMind:
    internal_organs: dict = field(
        default_factory=dict
    )
    organ_registry: dict = field(
        default_factory=dict
    )


class IntegrationTests(unittest.TestCase):

    def test_one_organism(self):
        mind = DummyMind()

        controller = (
            attach_cognitive_flow(
                mind
            )
        )

        self.assertIs(
            get_cognitive_flow(mind),
            controller,
        )

        self.assertIs(
            mind.internal_organs[
                "cognitive_flow"
            ],
            controller,
        )

        self.assertEqual(
            mind.organ_registry[
                "cognitive_flow"
            ]["subject_count"],
            1,
        )

        self.assertIs(
            attach_cognitive_flow(mind),
            controller,
        )

    def test_legacy_preserved(self):
        legacy = object()

        mind = DummyMind(
            internal_organs={
                "legacy": legacy
            }
        )

        attach_cognitive_flow(
            mind
        )

        self.assertIs(
            mind.internal_organs[
                "legacy"
            ],
            legacy,
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
PY

# ------------------------------------------------------------
# 6. VALIDATE BEFORE GIT
# ------------------------------------------------------------

python -m py_compile \
    "$MODULE" \
    "$INTEGRATION" \
    "$TEST"

echo "[PASS] Python syntax"

python -m json.tool "$CONFIG" >/dev/null

echo "[PASS] JSON"

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python "$TEST"

echo "[PASS] functional tests"

# ------------------------------------------------------------
# 7. DIRECT REAL FLOW SMOKE TEST
# ------------------------------------------------------------

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python - <<'PY'
from malysh_system.cognitive_flow import (
    RelationKind,
    ThoughtKind,
    create_default_controller,
)

c = create_default_controller()

c.add_state(
    state_id="input",
    content="real input",
    kind=ThoughtKind.OBSERVATION,
    source="perception",
    confidence=1.0,
    initial_attention=1.0,
    active=True,
)

for sid, kind in (
    (
        "main",
        ThoughtKind.PROPOSAL,
    ),
    (
        "maybe",
        ThoughtKind.POSSIBLE,
    ),
    (
        "counter",
        ThoughtKind.NEGATIVE_RESULT,
    ),
    (
        "unknown",
        ThoughtKind.UNRESOLVED,
    ),
):
    c.add_state(
        state_id=sid,
        content=sid,
        kind=kind,
        source="smoke",
        confidence=0.8,
    )

for rid, target, kind, sign in (
    (
        "a",
        "main",
        RelationKind.SUPPORTS,
        1,
    ),
    (
        "b",
        "maybe",
        RelationKind.SUGGESTS,
        1,
    ),
    (
        "c",
        "counter",
        RelationKind.CONTRADICTS,
        -1,
    ),
    (
        "d",
        "unknown",
        RelationKind.REQUIRES,
        0,
    ),
):
    c.add_relation(
        relation_id=rid,
        sources=["input"],
        target=target,
        kind=kind,
        sign=sign,
        confidence=1.0,
        evidence=1.0,
        priority=1.0,
    )

r = c.cycle_once()

assert r.primary.selected_id == "main"
assert r.possible.selected_id == "maybe"
assert r.negative.selected_id == "counter"
assert r.unresolved.selected_id == "unknown"
assert r.invariant_failures == ()
assert abs(
    sum(r.attention.values()) - 1.0
) < 1e-12

print(
    "[PASS] input -> relations -> flow -> "
    "primary/possible/negative/unresolved"
)

print(
    "[PASS] attention sum =",
    sum(r.attention.values()),
)

print(
    "[PASS] WAL entries =",
    len(c.wal),
)
PY

# ------------------------------------------------------------
# 8. GIT, ONLY THESE FILES
# ------------------------------------------------------------

git add -- \
    "$MODULE" \
    "$INTEGRATION" \
    "$TEST" \
    "$CONFIG"

EXPECTED="$(
    printf '%s\n' \
        "$CONFIG" \
        "$MODULE" \
        "$INTEGRATION" \
        "$TEST" \
    | sort
)"

ACTUAL="$(
    git diff --cached \
        --name-only \
    | sort
)"

if [ "$ACTUAL" != "$EXPECTED" ]; then
    echo "STOP: staged files differ."
    echo
    echo "EXPECTED:"
    printf '%s\n' "$EXPECTED"
    echo
    echo "ACTUAL:"
    printf '%s\n' "$ACTUAL"
    exit 1
fi

echo "[PASS] staged exact file set"

git commit \
    -m "architecture: add cognitive flow controller"

AFTER="$(git rev-parse HEAD)"

echo "[PASS] commit: $AFTER"

# ------------------------------------------------------------
# 9. VERIFY COMMIT
# ------------------------------------------------------------

COMMITTED="$(
    git diff-tree \
        --no-commit-id \
        --name-only \
        -r \
        "$AFTER" \
    | sort
)"

if [ "$COMMITTED" != "$EXPECTED" ]; then
    echo "STOP: unexpected commit content"
    printf '%s\n' "$COMMITTED"
    exit 1
fi

echo "[PASS] exact commit content"

# ------------------------------------------------------------
# 10. POST-COMMIT TEST
# ------------------------------------------------------------

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python "$TEST"

echo "[PASS] post-commit tests"

echo
echo "============================================================"
echo "COGNITIVE FLOW INSTALLED"
echo "============================================================"
echo "Root       : $ROOT"
echo "Branch     : $BRANCH"
echo "Before     : $BEFORE"
echo "Safety tag : $TAG"
echo "Commit     : $AFTER"
echo
echo "Core:"
echo "K -> R -> W -> J -> A/rho -> Phi -> O"
echo
echo "Branches:"
echo "primary + possible + negative + unresolved"
echo
echo "Added:"
echo "$MODULE"
echo "$INTEGRATION"
echo "$TEST"
echo "$CONFIG"
echo
echo "[PASS] one Malysh"
echo "[PASS] legacy preserved"
echo "[PASS] no unrelated file staged by installer"
echo "[PASS] functional test completed"
echo "============================================================"

echo
echo "Current working tree:"
git status --short
