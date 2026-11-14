from research_information_trace import (
    run_experiment,
)


def test_information_trace_contract():
    result = run_experiment(
        data=[1, 2, 3, 4, 5],
        cycles=10,
    )

    assert (
        result["schema"]
        == "malysh.information-trace.v1"
    )

    assert len(result["trace"]) == 11

    assert (
        result[
            "malysh_reflection"
        ][
            "voice_a"
        ][
            "rights"
        ]
        == "equal"
    )

    assert (
        result[
            "malysh_reflection"
        ][
            "voice_b"
        ][
            "rights"
        ]
        == "equal"
    )

    assert (
        result[
            "malysh_reflection"
        ][
            "debate"
        ][
            "winner"
        ]
        is None
    )

    assert (
        result[
            "claims"
        ][
            "physical_proof"
        ]
        is False
    )

    assert (
        result[
            "claims"
        ][
            "computational_experiment"
        ]
        is True
    )


def test_written_phase_distinction_exists():
    result = run_experiment(
        data=[1, 2, 3, 4, 5],
        cycles=10,
    )

    trace = result["trace"]

    assert trace[0]["D_phase_rms"] > 0.0

    assert all(
        item["D_phase_rms"] > 0.0
        for item in trace
    )


if __name__ == "__main__":
    test_information_trace_contract()
    test_written_phase_distinction_exists()

    print(
        "[PASS] information trace contract"
    )

    print(
        "[PASS] written phase distinction survives"
    )
