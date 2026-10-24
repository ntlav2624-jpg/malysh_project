#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import unittest

from n7_interface import (
    boundary_distance,
    classify_n7_interface,
)


class TestN7Interface(unittest.TestCase):
    def test_boundary_distance(self):
        square = [
            (-1.0, -1.0),
            (1.0, -1.0),
            (1.0, 1.0),
            (-1.0, 1.0),
        ]

        self.assertAlmostEqual(
            boundary_distance(
                (0.0, 0.0),
                square,
            ),
            1.0,
        )

        self.assertAlmostEqual(
            boundary_distance(
                (1.0, 0.0),
                square,
            ),
            0.0,
        )

    def test_boundary_intersection_mode(self):
        polygon = [
            (-1.0, -1.0),
            (1.0, -1.0),
            (1.0, 1.0),
            (-1.0, 1.0),
        ]

        trajectory = [
            (0, (0.0, 0.0)),
            (1, (1.0, 0.0)),
        ]

        result = classify_n7_interface(
            trajectory=trajectory,
            vertices_5=polygon,
            vertices_6=polygon,
            tolerance=1.0e-6,
        )

        self.assertEqual(
            result["indices"],
            [1],
        )

        self.assertEqual(
            result["mode"],
            "boundary_intersection",
        )

    def test_nearest_boundary_fallback(self):
        inner = [
            (
                math.cos(index * math.pi / 2.0),
                math.sin(index * math.pi / 2.0),
            )
            for index in range(4)
        ]

        outer = [
            (
                3.0 * math.cos(
                    index * math.pi / 2.0
                ),
                3.0 * math.sin(
                    index * math.pi / 2.0
                ),
            )
            for index in range(4)
        ]

        trajectory = [
            (0, (0.0, 0.0)),
            (1, (2.0, 0.0)),
            (2, (4.0, 0.0)),
        ]

        result = classify_n7_interface(
            trajectory=trajectory,
            vertices_5=inner,
            vertices_6=outer,
            tolerance=1.0e-9,
        )

        self.assertEqual(
            result["mode"],
            "nearest_boundary_fallback",
        )

        self.assertEqual(
            result["indices"],
            [1],
        )

    def test_directional_contract(self):
        triangle_5 = [
            (1.0, 0.0),
            (0.0, 1.0),
            (-1.0, 0.0),
        ]

        triangle_6 = [
            (1.0, 0.0),
            (0.0, -1.0),
            (-1.0, 0.0),
        ]

        result = classify_n7_interface(
            trajectory=[(0, (1.0, 0.0))],
            vertices_5=triangle_5,
            vertices_6=triangle_6,
            tolerance=1.0e-6,
        )

        self.assertEqual(
            result["forward"],
            "R5->N7->R6",
        )

        self.assertEqual(
            result["reverse"],
            "R6->N7->R5",
        )


if __name__ == "__main__":
    unittest.main()
