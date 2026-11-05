# Malysh experimental/O345

Status:

    experimental
    non-authoritative
    legacy-preserving

Canonical state:

    X = (a3, b4, c5)
    X in Z3 x Z4 x Z5

Number of canonical states:

    3 * 4 * 5 = 60

CRT reconstruction:

    n = (40*a3 + 45*b4 + 36*c5) mod 60

Observers:

    O3 = 3 x 20
    O4 = 4 x 15
    O5 = 5 x 12

Core rule:

    canonical state != projection

A discontinuity or ambiguity in one observer is not automatically
treated as an anomaly of the canonical state.

The meta-observer preserves O3/O4/O5 separately. It does not use
majority voting.

Human Layer:

    main:
        canonical invariant result

    possible:
        projection-dependent alternative interpretation

This branch does not replace:

    B^3 + 8inf + 0circle^(8)
    Base-4
    logic 567
    KMBP
    Swarm
    Omni
    historical implementations

Integration requires functional tests:

    real input
      -> real computation
      -> verifiable output
      -> invariant
      -> integration test
