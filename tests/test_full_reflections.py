
from malysh_system.full_reflections import FullReflections


def test_full_reflections(tmp_path):

    calls = []

    def legacy(data):
        calls.append(data)
        return {
            "567_called": True,
            "KMBP_called": True,
            "sum": sum(data),
        }

    mind = FullReflections(
        root=tmp_path,
        legacy_hook=legacy,
    )

    result = mind.think(
        [1, 2, 3, 4],
        {"old_engine": True},
        "возможно",
    )

    assert result["name"] == "Размышления"

    assert (
        result["as_before"]["result"]
        ==
        {"old_engine": True}
    )

    modern = result["as_now"]["result"]

    required = [
        "small_zero",
        "zero_alphabet",
        "temporal_state",
        "ball_geometry",
        "clock_code",
        "orientation_cube",
        "possibility",
        "history",
        "write_evolve_read",
        "controls",
        "possible",
        "legacy_experience",
    ]

    for key in required:
        assert key in modern

    assert (
        modern[
            "legacy_experience"
        ][
            "called"
        ]
        is True
    )

    assert calls == [
        [1, 2, 3, 4]
    ]

    assert (
        modern[
            "claims"
        ][
            "physical_proof"
        ]
        is False
    )
