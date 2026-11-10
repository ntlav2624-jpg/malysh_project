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
