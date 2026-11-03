from research_read_windows import (
    run_long_experiment,
)


def test_long_read_window_contract():
    result = run_long_experiment(
        data=[1, 2, 3, 4, 5],
        cycles=80,
        max_lag=40,
    )

    assert (
        result["schema"]
        == "malysh.read-windows.v1"
    )

    assert result["model"]["samples"] == 81
    assert result["model"]["decoder_changed"] is False
    assert result["model"]["dynamics_changed"] is False

    assert (
        result["model"][
            "new_physical_entity_added"
        ]
        is False
    )

    assert (
        result["invariants"]["phase_conserved"]
        is True
    )

    assert (
        result["invariants"][
            "phase_max_deviation"
        ]
        < 1e-12
    )

    assert (
        result["read_windows"]["count"]
        > 0
    )

    assert (
        result["diagnosis"][
            "information_destroyed"
        ]
        is False
    )

    assert (
        result["malysh_debate"]["winner"]
        is None
    )


def test_trace_recalculates_channels():
    result = run_long_experiment(
        data=[1, 2, 3, 4, 5],
        cycles=40,
        max_lag=20,
    )

    trace = result["trace"]

    assert len(trace) == 41

    assert all(
        row["D_phase_rms"] > 0
        for row in trace
    )

    assert any(
        row["read_separated"]
        for row in trace
    )

    assert all(
        row["D_frequency_mean"] < 1e-12
        for row in trace
    )


if __name__ == "__main__":
    test_long_read_window_contract()
    test_trace_recalculates_channels()

    print("[PASS] long read-window contract")
    print("[PASS] phase distinguishability conserved")
    print("[PASS] at least one read window found")
