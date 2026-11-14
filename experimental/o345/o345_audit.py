#!/usr/bin/env python3

import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

from o345 import Canonical345, observe


MODULI = {
    "O3": (3, 20),
    "O4": (4, 15),
    "O5": (5, 12),
}


def cyclic_distance(a, b, modulus):
    d = abs(a - b) % modulus
    return min(d, modulus - d)


def coords(n):
    obs = observe(Canonical345.from_n(n))
    return {
        name: (value.outer, value.inner)
        for name, value in obs.items()
    }


def distance(i, j, observer):
    a = coords(i)[observer]
    b = coords(j)[observer]

    mo, mi = MODULI[observer]

    return (
        cyclic_distance(a[0], b[0], mo),
        cyclic_distance(a[1], b[1], mi),
    )


def run_audit():
    states = [
        Canonical345.from_n(n)
        for n in range(60)
    ]

    assert len(set(states)) == 60

    for n, state in enumerate(states):
        assert state.to_n() == n

    origin = Canonical345.from_n(0)

    assert origin.step(60) == origin
    assert all(
        origin.step(k) != origin
        for k in range(1, 60)
    )

    observer_unique = {}

    for observer in MODULI:
        values = {
            coords(n)[observer]
            for n in range(60)
        }
        observer_unique[observer] = len(values)

    assert observer_unique == {
        "O3": 60,
        "O4": 60,
        "O5": 60,
    }

    pair_count = 0

    collisions = {
        "O3": [],
        "O4": [],
        "O5": [],
    }

    signatures = Counter()

    zero_candidates = defaultdict(list)

    for i, j in itertools.combinations(range(60), 2):
        pair_count += 1

        ci = coords(i)
        cj = coords(j)

        for observer in MODULI:
            if ci[observer] == cj[observer]:
                collisions[observer].append((i, j))

        components = {
            observer: distance(i, j, observer)
            for observer in MODULI
        }

        scalar = {
            observer: sum(value)
            for observer, value in components.items()
        }

        signatures[
            (
                scalar["O3"],
                scalar["O4"],
                scalar["O5"],
            )
        ] += 1

        ordered = sorted(
            scalar.items(),
            key=lambda item: item[1],
        )

        winner, d0 = ordered[0]
        d1 = ordered[1][1]
        d2 = ordered[2][1]

        if d0 + 2 <= d1 and d0 + 2 <= d2:
            zero_candidates[winner].append({
                "pair": [i, j],
                "distance": scalar,
                "components": {
                    k: list(v)
                    for k, v in components.items()
                },
            })

    assert pair_count == 1770

    assert all(
        len(value) == 0
        for value in collisions.values()
    )

    report = {
        "states": 60,
        "unordered_pairs": pair_count,
        "unique_canonical_states": 60,
        "observer_unique_addresses": observer_unique,
        "exact_projection_collisions": {
            k: len(v)
            for k, v in collisions.items()
        },
        "unique_distance_signatures": len(signatures),
        "projection_zero_candidate_counts": {
            observer: len(zero_candidates[observer])
            for observer in MODULI
        },
        "projection_zero_examples": {
            observer: zero_candidates[observer][:10]
            for observer in MODULI
        },
        "invariant_ok": True,
    }

    return report


if __name__ == "__main__":
    result = run_audit()

    out = Path("reports/o345_audit.json")

    out.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
