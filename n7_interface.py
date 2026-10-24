#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math


def point_segment_distance(point, start, end):
    """Минимальное расстояние от точки до отрезка."""
    px, py = point
    ax, ay = start
    bx, by = end

    dx = bx - ax
    dy = by - ay
    length_squared = dx * dx + dy * dy

    if length_squared == 0.0:
        return math.hypot(px - ax, py - ay)

    projection = (
        (px - ax) * dx + (py - ay) * dy
    ) / length_squared

    projection = max(0.0, min(1.0, projection))

    nearest_x = ax + projection * dx
    nearest_y = ay + projection * dy

    return math.hypot(
        px - nearest_x,
        py - nearest_y,
    )


def boundary_distance(point, vertices):
    """Расстояние от точки до границы многоугольника."""
    if len(vertices) < 2:
        raise ValueError(
            "Polygon requires at least two vertices"
        )

    return min(
        point_segment_distance(
            point,
            vertices[index],
            vertices[(index + 1) % len(vertices)],
        )
        for index in range(len(vertices))
    )


def classify_n7_interface(
    trajectory,
    vertices_5,
    vertices_6,
    tolerance=None,
):
    """
    Выделяет N7 как интерфейс перехода R5 <-> R6.

    Основной режим:
        d(point, boundary(R5)) <= epsilon
        and
        d(point, boundary(R6)) <= epsilon

    Если границы не имеют общей интерфейсной полосы,
    выбирается дискретный минимум совместной невязки.
    """
    trajectory = list(trajectory)
    vertices_5 = list(vertices_5)
    vertices_6 = list(vertices_6)

    if not trajectory:
        return {
            "indices": [],
            "nodes": [],
            "mode": "empty",
            "tolerance": 0.0,
            "minimum_score": None,
            "forward": "R5->N7->R6",
            "reverse": "R6->N7->R5",
        }

    scale = max(
        math.hypot(x, y)
        for x, y in vertices_5 + vertices_6
    )

    sample_step = 0.0

    for (_, previous), (_, current) in zip(
        trajectory,
        trajectory[1:],
    ):
        sample_step = max(
            sample_step,
            math.dist(previous, current),
        )

    epsilon = (
        float(tolerance)
        if tolerance is not None
        else max(
            sample_step * 1.5,
            scale * 1.0e-3,
            1.0e-9,
        )
    )

    diagnostics = []
    interface_nodes = []

    for index, point in trajectory:
        distance_5 = boundary_distance(
            point,
            vertices_5,
        )
        distance_6 = boundary_distance(
            point,
            vertices_6,
        )

        node = {
            "index": index,
            "point": point,
            "distance_r5": distance_5,
            "distance_r6": distance_6,
            "score": max(distance_5, distance_6),
            "forward": "R5->N7->R6",
            "reverse": "R6->N7->R5",
        }

        diagnostics.append(node)

        if (
            distance_5 <= epsilon
            and distance_6 <= epsilon
        ):
            interface_nodes.append(node)

    if interface_nodes:
        mode = "boundary_intersection"
        minimum_score = min(
            node["score"]
            for node in interface_nodes
        )
    else:
        mode = "nearest_boundary_fallback"

        minimum_score = min(
            node["score"]
            for node in diagnostics
        )

        numerical_band = max(
            epsilon * 0.05,
            minimum_score * 1.0e-9,
            1.0e-12,
        )

        interface_nodes = [
            node
            for node in diagnostics
            if node["score"]
            <= minimum_score + numerical_band
        ]

    return {
        "indices": [
            node["index"]
            for node in interface_nodes
        ],
        "nodes": interface_nodes,
        "mode": mode,
        "tolerance": epsilon,
        "minimum_score": minimum_score,
        "forward": "R5->N7->R6",
        "reverse": "R6->N7->R5",
    }
