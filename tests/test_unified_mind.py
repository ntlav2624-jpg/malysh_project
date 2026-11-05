from malysh_system.unified_mind import (
    MindState,
    merge_o345,
)


def o345_sample():
    return {
        "canonical": {
            "a3": 2,
            "b4": 1,
            "c5": 2,
        },

        "invariant_ok": True,

        "main":
            "canonical_consistent",

        "possible":
            "projection divergence may contain information",

        "observers": {
            "O3": {
                "outer": 2,
                "inner": 17,
            },

            "O4": {
                "outer": 1,
                "inner": 2,
            },

            "O5": {
                "outer": 2,
                "inner": 5,
            },
        },
    }


def test_exactly_one_subject():

    mind = MindState()

    assert mind.subject == "Malysh"

    assert mind.invariant()


def test_o345_observers_are_not_subjects():

    mind = merge_o345(
        MindState(),
        o345_sample(),
    )

    assert mind.subject == "Malysh"

    assert set(
        mind.observations
    ) == {
        "O3",
        "O4",
        "O5",
    }

    assert (
        mind.reflections[
            "O345"
        ][
            "decision_authority"
        ]
        is False
    )

    assert (
        mind.reflections[
            "O345"
        ][
            "state_write"
        ]
        is False
    )

    assert (
        mind.reflections[
            "O345"
        ][
            "state_commit"
        ]
        is False
    )


def test_one_canonical_state():

    mind = merge_o345(
        MindState(),
        o345_sample(),
    )

    assert mind.canonical == {
        "a3": 2,
        "b4": 1,
        "c5": 2,
    }


def test_snapshot_is_isolated():

    mind = merge_o345(
        MindState(),
        o345_sample(),
    )

    snapshot = mind.snapshot()

    snapshot[
        "observations"
    ][
        "O3"
    ][
        "outer"
    ] = 99

    assert (
        mind.observations[
            "O3"
        ][
            "outer"
        ]
        == 2
    )


def test_human_layer_one_context():

    mind = MindState()

    mind.set_human(
        {
            "logical": {
                "hypothesis":
                    "primary",
            },

            "possible": [
                {
                    "hypothesis":
                        "alternative",
                }
            ],
        }
    )

    assert (
        mind.main
        == "primary"
    )

    assert (
        mind.possible[
            0
        ][
            "hypothesis"
        ]
        == "alternative"
    )

    assert mind.subject == "Malysh"

    assert mind.invariant()


def test_legacy_is_experience():

    mind = MindState()

    mind.remember(
        "logic567",
        {
            "status":
                "historical_experience",
        },
    )

    assert (
        mind.experience[
            "logic567"
        ][
            "status"
        ]
        == "historical_experience"
    )

    assert mind.subject == "Malysh"


def test_conflicting_canonical_state_is_rejected():

    mind = merge_o345(
        MindState(),
        o345_sample(),
    )

    conflicting = o345_sample()

    conflicting[
        "canonical"
    ] = {
        "a3": 0,
        "b4": 0,
        "c5": 0,
    }

    try:

        merge_o345(
            mind,
            conflicting,
        )

    except ValueError:
        return

    raise AssertionError(
        "canonical conflict accepted"
    )
