from malysh_system.thought_cycle import (
    build_thought_cycle,
    thought_snapshot,
)


def build():
    return build_thought_cycle(
        n=17,

        text=(
            "Исследуй единое состояние Малыша"
        ),

        consciousness={
            "selected": [
                "native_malysh_engine",
            ],

            "mode":
                "analysis",
        },

        subconscious={
            "selected": [],
            "categories": [],
            "broad_fallback": False,
        },

        joint={
            "selected": [
                "native_malysh_engine",
            ],
        },

        experience={
            "signals": [],
            "unresolved": [],
        },

        observations=[],
    )


def test_one_subject():
    mind = build()

    assert mind.subject == "Malysh"

    assert mind.invariant()


def test_o345_inside_same_mind():
    mind = build()

    assert set(
        mind.observations
    ) == {
        "O3",
        "O4",
        "O5",
    }

    assert mind.canonical == {
        "a3": 2,
        "b4": 1,
        "c5": 2,
    }


def test_passive_authority():
    mind = build()

    assert (
        mind.reflections[
            "O345"
        ][
            "decision_authority"
        ]
        is False
    )

    cross = mind.reflections[
        "cross_layer"
    ]

    assert (
        cross[
            "decision_authority"
        ]
        is False
    )

    assert (
        cross[
            "automatic_execution"
        ]
        is False
    )

    assert (
        cross[
            "state_write"
        ]
        is False
    )

    assert (
        cross[
            "state_commit"
        ]
        is False
    )


def test_human_same_context():
    mind = build()

    assert mind.main is not None

    assert isinstance(
        mind.possible,
        list,
    )

    assert (
        mind.human[
            "decision_is_truth"
        ]
        is False
    )

    assert (
        mind.human[
            "reconsideration_possible"
        ]
        is True
    )


def test_no_executor():
    architecture = thought_snapshot(
        build()
    )[
        "architecture"
    ]

    assert (
        architecture[
            "subject_count"
        ]
        == 1
    )

    assert (
        architecture[
            "executor_called"
        ]
        is False
    )

    assert (
        architecture[
            "transaction_committed"
        ]
        is False
    )
