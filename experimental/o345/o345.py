#!/usr/bin/env python3

from dataclasses import dataclass, asdict


PERIOD = 60


@dataclass(frozen=True)
class Canonical345:
    a3: int
    b4: int
    c5: int

    @classmethod
    def from_n(cls, n: int):
        n %= 60
        return cls(n % 3, n % 4, n % 5)

    def to_n(self) -> int:
        return (
            40 * self.a3 +
            45 * self.b4 +
            36 * self.c5
        ) % 60

    def step(self, k: int = 1):
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
    canonical_n: int


def observer_o3(x):
    n = x.to_n()
    return ObserverResult("O3", n % 3, n % 20, n)


def observer_o4(x):
    n = x.to_n()
    return ObserverResult("O4", n % 4, n % 15, n)


def observer_o5(x):
    n = x.to_n()
    return ObserverResult("O5", n % 5, n % 12, n)


def observe(x):
    return {
        "O3": observer_o3(x),
        "O4": observer_o4(x),
        "O5": observer_o5(x),
    }


def meta_observe(x):
    obs = observe(x)
    n = x.to_n()

    invariant_ok = all(
        value.canonical_n == n
        for value in obs.values()
    )

    return {
        "canonical": asdict(x),
        "n": n,
        "observers": {
            k: asdict(v)
            for k, v in obs.items()
        },
        "invariant_ok": invariant_ok,
        "main": (
            "canonical_consistent"
            if invariant_ok
            else "canonical_failure"
        ),
        "possible":
            "projection divergence may contain information",
    }
