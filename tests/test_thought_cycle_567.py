from malysh_system.thought_cycle import (
    build_thought_cycle,
    thought_snapshot,
)


def build_with_567():

    return build_thought_cycle(
        n=17,

        text=(
            "Малыш исследует пропуск "
            "в логике 567"
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

        legacy_567_input=[
            "dingir",
            "[x]",
            "ki",
        ],
    )


def test_567_inside_one_malysh():

    mind = build_with_567()

    assert mind.subject == "Malysh"

    assert "567" in mind.reflections

    assert (
        mind.reflections[
            "567"
        ][
            "subject"
        ]
        == "Malysh"
    )

    assert (
        mind.reflections[
            "567"
        ][
            "output"
        ][
            "restored_sign"
        ]
        == "an-unna"
    )


def test_567_does_not_replace_o345():

    mind = build_with_567()

    assert set(
        mind.observations
    ) == {
        "O3",
        "O4",
        "O5",
    }

    assert "O345" in mind.reflections

    assert "567" in mind.reflections

    assert "cross_layer" in mind.reflections


def test_567_does_not_take_executor():

    mind = build_with_567()

    result = mind.reflections[
        "567"
    ]

    assert (
        result[
            "decision_authority"
        ]
        is False
    )

    assert (
        result[
            "state_commit"
        ]
        is False
    )

    snapshot = thought_snapshot(
        mind
    )

    assert (
        snapshot[
            "architecture"
        ][
            "subject_count"
        ]
        == 1
    )

    assert (
        snapshot[
            "architecture"
        ][
            "executor_called"
        ]
        is False
    )


def test_cross_layer_sees_567_observation():

    mind = build_with_567()

    cross = mind.reflections[
        "cross_layer"
    ]

    patterns = cross.get(
        "patterns",
        [],
    )

    physical = [
        pattern
        for pattern in patterns
        if pattern.get(
            "pattern_id"
        )
        == "physical_observation_available"
    ]

    assert physical

    evidence = physical[0].get(
        "evidence",
        [],
    )

    assert any(
        "567" in item
        for item in evidence
    )
