#!/usr/bin/env python3

import unittest

from o345 import (
    PERIOD,
    Canonical345,
    observer_o3,
    observer_o4,
    observer_o5,
    meta_observe,
)


class TestO345(unittest.TestCase):

    def test_all_60_states_are_unique(self):
        states = {
            Canonical345.from_n(n)
            for n in range(PERIOD)
        }
        self.assertEqual(len(states), 60)

    def test_crt_roundtrip_all_states(self):
        for n in range(PERIOD):
            x = Canonical345.from_n(n)
            self.assertEqual(x.to_n(), n)

    def test_step_matches_linear_clock(self):
        for n in range(PERIOD):
            x = Canonical345.from_n(n)
            self.assertEqual(
                x.step().to_n(),
                (n + 1) % PERIOD,
            )

    def test_exact_period_is_60(self):
        x = Canonical345.from_n(0)

        self.assertEqual(x.step(60), x)

        for k in range(1, 60):
            self.assertNotEqual(x.step(k), x)

    def test_o3_unique(self):
        pairs = set()

        for n in range(PERIOD):
            o = observer_o3(Canonical345.from_n(n))
            pairs.add((o.outer, o.inner))

        self.assertEqual(len(pairs), 60)

    def test_o4_unique(self):
        pairs = set()

        for n in range(PERIOD):
            o = observer_o4(Canonical345.from_n(n))
            pairs.add((o.outer, o.inner))

        self.assertEqual(len(pairs), 60)

    def test_o5_unique(self):
        pairs = set()

        for n in range(PERIOD):
            o = observer_o5(Canonical345.from_n(n))
            pairs.add((o.outer, o.inner))

        self.assertEqual(len(pairs), 60)

    def test_observers_point_to_same_parent(self):
        for n in range(PERIOD):
            x = Canonical345.from_n(n)

            values = [
                observer_o3(x).canonical_n,
                observer_o4(x).canonical_n,
                observer_o5(x).canonical_n,
            ]

            self.assertEqual(values, [n, n, n])

    def test_meta_observer(self):
        for n in range(PERIOD):
            result = meta_observe(Canonical345.from_n(n))
            self.assertTrue(result["invariant_ok"])
            self.assertEqual(
                result["main"],
                "canonical_consistent",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
