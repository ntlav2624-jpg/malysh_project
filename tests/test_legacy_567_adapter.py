import pytest

from malysh_system.legacy_567_adapter import (
    observe_567,
)


def test_real_567_gap_restoration():

    result = observe_567(
        [
            "dingir",
            "[x]",
            "ki",
        ]
    )

    assert result["organ"] == "567"

    assert result["subject"] == "Malysh"

    assert (
        result[
            "output"
        ][
            "restored_sign"
        ]
        == "an-unna"
    )

    assert (
        result[
            "output"
        ][
            "restored_sequence"
        ]
        == [
            "dingir",
            "an-unna",
            "ki",
        ]
    )

    assert (
        result[
            "output"
        ][
            "topological_tension"
        ]
        == pytest.approx(
            2.0 / 3.0
        )
    )

    assert (
        result[
            "evidence"
        ][
            "engine_class"
        ]
        == "MalyshCuneiformEngine567"
    )

    assert (
        result[
            "evidence"
        ][
            "corpus_sequences"
        ]
        == 6
    )

    assert (
        result[
            "functional_invariant"
        ]
        is True
    )


def test_567_has_no_authority():

    result = observe_567(
        [
            "dingir",
            "[x]",
            "ki",
        ]
    )

    assert (
        result[
            "decision_authority"
        ]
        is False
    )

    assert (
        result[
            "automatic_execution"
        ]
        is False
    )

    assert (
        result[
            "state_write"
        ]
        is False
    )

    assert (
        result[
            "state_commit"
        ]
        is False
    )


def test_567_rejects_non_gap_input():

    with pytest.raises(
        ValueError
    ):
        observe_567(
            [
                "dingir",
                "not-a-gap",
                "ki",
            ]
        )
