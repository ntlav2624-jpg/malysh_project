#!/usr/bin/env python3

"""
Malysh experimental O345 observer.

Canonical state:
    X = (a3, b4, c5) in Z3 x Z4 x Z5

CRT:
    n = (40*a3 + 45*b4 + 36*c5) mod 60

Observers:
    O3 = (n mod 3, n mod 20)
    O4 = (n mod 4, n mod 15)
    O5 = (n mod 5, n mod 12)

Important architectural invariant:

    canonical state != geometric observation

O3/O4/O5 are independent views of the same canonical state.
Disagreement between observers is information, not automatically
an error.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Tuple


PERIOD = 60


@dataclass(frozen=True)
class Canonical345:
    a3: int
    b4: int
    c5: int

    def __post_init__(self):
        if not 0 <= self.a3 < 3:
            raise ValueError("a3 must be in Z3")
        if not 0 <= self.b4 < 4:
            raise ValueError("b4 must be in Z4")
        if not 0 <= self.c5 < 5:
            raise ValueError("c5 must be in Z5")

    @classmethod
    def from_n(cls, n: int) -> "Canonical345":
        n %= PERIOD
        return cls(
            a3=n % 3,
            b4=n % 4,
            c5=n % 5,
        )

    def to_n(self) -> int:
        # Chinese Remainder Theorem reconstruction.
        return (
            40 * self.a3
            + 45 * self.b4
            + 36 * self.c5
        ) % PERIOD

    def step(self, k: int = 1) -> "Canonical345":
        return Canonical345(
            (self.a3 + k) % 3,
            (self.b4 + k) % 4,
            (self.c5 + k) % 5,
        )


@dataclass(frozen=True)
class ObserverResult:
    name: str
    outer: int
    inner: int
    outer_period: int
    inner_period: int
    canonical_n: int


def observer_o3(x: Canonical345) -> ObserverResult:
    n = x.to_n()
    return ObserverResult(
        name="O3",
        outer=n % 3,
        inner=n % 20,
        outer_period=3,
        inner_period=20,
        canonical_n=n,
    )


def observer_o4(x: Canonical345) -> ObserverResult:
    n = x.to_n()
    return ObserverResult(
        name="O4",
        outer=n % 4,
        inner=n % 15,
        outer_period=4,
        inner_period=15,
        canonical_n=n,
    )


def observer_o5(x: Canonical345) -> ObserverResult:
    n = x.to_n()
    return ObserverResult(
        name="O5",
        outer=n % 5,
        inner=n % 12,
        outer_period=5,
        inner_period=12,
        canonical_n=n,
    )


def observe(x: Canonical345) -> Dict[str, ObserverResult]:
    """
    Independent observers.

    There is deliberately no majority vote here.
    """
    return {
        "O3": observer_o3(x),
        "O4": observer_o4(x),
        "O5": observer_o5(x),
    }


def meta_observe(x: Canonical345) -> dict:
    """
    M345 meta-observer.

    It keeps observer outputs separate and verifies only the
    hard invariant that all observations refer back to one
    canonical state.
    """

    observations = observe(x)
    n = x.to_n()

    invariant_ok = all(
        result.canonical_n == n
        for result in observations.values()
    )

    return {
        "canonical": asdict(x),
        "n": n,
        "observers": {
            key: asdict(value)
            for key, value in observations.items()
        },
        "invariant_ok": invariant_ok,

        # Human Layer:
        # no forced conclusion from projection disagreement.
        "main": (
            "canonical_consistent"
            if invariant_ok
            else "canonical_invariant_failure"
        ),
        "possible": (
            "observer divergence may encode projection-dependent information"
        ),
    }


def phase_state(n: int) -> Tuple[int, int, int]:
    x = Canonical345.from_n(n)
    return x.a3, x.b4, x.c5
