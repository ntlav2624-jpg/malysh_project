import pytest

from malysh_system.legacy_567_adapter import (
    observe_567,
)

from malysh_system.thought_cycle import (
    build_thought_cycle,
)


def test_complete_argmin_is_preserved():

    result = observe_567(
        [
            "dingir",
            "[x]",
            "ki",
        ]
    )

    output = result[
        "output"
    ]

    assert (
        output[
            "restored_sign"
        ]
        == "an-unna"
    )

    assert (
        output[
            "topological_tension"
        ]
        == pytest.approx(
            2.0 / 3.0
        )
    )

    assert (
        output[
            "minimum_tension"
        ]
        == pytest.approx(
            2.0 / 3.0
        )
    )

    assert (
        output[
            "equal_minima"
        ]
        == [
            "an-unna",
            "unug",
        ]
    )

    assert (
        output[
            "alternatives"
        ]
        == [
            "unug",
        ]
    )


def test_historical_main_is_not_replaced():

    result = observe_567(
        [
            "dingir",
            "[x]",
            "ki",
        ]
    )

    assert (
        result[
            "output"
        ][
            "restored_sign"
        ]
        == "an-unna"
    )

    assert (
        "unug"
        in result[
            "output"
        ][
            "alternatives"
        ]
    )


def test_equal_minimum_enters_human_possible():

    mind = build_thought_cycle(
        n=17,

        text=(
            "Единый Малыш исследует "
            "неоднозначность 567"
        ),

        legacy_567_input=[
            "dingir",
            "[x]",
            "ki",
        ],
    )

    possible = mind.possible

    generated = [
        item
        for item in possible
        if item.get(
            "source"
        )
        == "legacy_567_equal_minimum"
    ]

    assert len(
        generated
    ) == 1

    assert (
        "unug"
        in generated[
            0
        ][
            "hypothesis"
        ]
    )

    assert (
        mind.main
        != generated[
            0
        ][
            "hypothesis"
        ]
    )

    assert (
        mind.subject
        == "Malysh"
    )


def test_567_stays_passive():

    mind = build_thought_cycle(
        n=17,

        legacy_567_input=[
            "dingir",
            "[x]",
            "ki",
        ],
    )

    reflection = (
        mind.reflections[
            "567"
        ]
    )

    assert (
        reflection[
            "decision_authority"
        ]
        is False
    )

    assert (
        reflection[
            "automatic_execution"
        ]
        is False
    )

    assert (
        reflection[
            "state_write"
        ]
        is False
    )

    assert (
        reflection[
            "state_commit"
        ]
        is False
    )
