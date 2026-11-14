#!/usr/bin/env python3

import contextlib
import io
import json
import runpy
from pathlib import Path

import numpy as np


# ============================================================
# LOAD VERIFIED MODEL
# ============================================================

BASE = Path("point_genesis_test.py")

with contextlib.redirect_stdout(io.StringIO()):
    model = runpy.run_path(str(BASE))


COORDS = model["COORDS"]
NODE_COUNT = model["NODE_COUNT"]
POINTS = model["POINTS"]

FULL = model["FULL"]
COORD_TO_NODE = model["COORD_TO_NODE"]

transfer_step = model["transfer_step"]

OUT = Path(
    "experiments/flow_admissibility"
)


# ============================================================
# FLOW
# ============================================================

def flow_vector(rho):
    p = FULL["p"]
    q = FULL["q"]
    k = FULL["k"]

    mean = (
        rho[p] + rho[q] + rho[k]
    ) / 3.0

    return (
        np.bincount(
            p,
            weights=mean - rho[p],
            minlength=NODE_COUNT,
        )
        + np.bincount(
            q,
            weights=mean - rho[q],
            minlength=NODE_COUNT,
        )
        + np.bincount(
            k,
            weights=mean - rho[k],
            minlength=NODE_COUNT,
        )
    )


# ============================================================
# ADMISSIBILITY
# ============================================================

def analyze_direction(
    rho,
    direction,
    tolerance=1e-15,
):
    boundary = (
        rho <= tolerance
    )

    outward = (
        boundary
        & (direction < -tolerance)
    )

    inward = (
        boundary
        & (direction > tolerance)
    )

    tangent = (
        boundary
        & (
            np.abs(direction)
            <= tolerance
        )
    )

    negative = (
        direction < -tolerance
    )

    if np.any(outward):
        max_step = 0.0

    elif np.any(negative):
        limits = (
            rho[negative]
            / (-direction[negative])
        )

        max_step = float(
            limits.min()
        )

    else:
        max_step = float("inf")

    outward_indices = np.where(
        outward
    )[0]

    strongest = sorted(
        outward_indices,
        key=lambda i: direction[i],
    )[:20]

    return {
        "admissible_positive_step": bool(
            not np.any(outward)
        ),

        "max_positive_step": (
            None
            if np.isinf(max_step)
            else max_step
        ),

        "boundary_nodes": int(
            boundary.sum()
        ),

        "outward_boundary_nodes": int(
            outward.sum()
        ),

        "inward_boundary_nodes": int(
            inward.sum()
        ),

        "tangent_boundary_nodes": int(
            tangent.sum()
        ),

        "strongest_outward": [
            {
                "coordinate": (
                    COORDS[index]
                    .astype(int)
                    .tolist()
                ),

                "rho": float(
                    rho[index]
                ),

                "direction": float(
                    direction[index]
                ),
            }
            for index in strongest
        ],
    }


# ============================================================
# PREPARE SAME CLOUDS AT DIFFERENT AGES
# ============================================================

PREP_STEPS = (
    0,
    1,
    2,
    5,
    10,
    20,
    40,
)


def prepare_states(coordinate):
    rho = np.zeros(
        NODE_COUNT,
        dtype=float,
    )

    rho[
        COORD_TO_NODE[
            coordinate
        ]
    ] = 1.0

    states = {
        0: rho.copy()
    }

    for step in range(
        1,
        max(PREP_STEPS) + 1,
    ):
        rho = transfer_step(
            rho,
            FULL,
        )

        if step in PREP_STEPS:
            states[step] = (
                rho.copy()
            )

    return states


# ============================================================
# EXPERIMENT
# ============================================================

print("=" * 92)
print("FLOW ADMISSIBILITY")
print("=" * 92)

print(
    "Question: if J is admissible, "
    "is -J also admissible?"
)

results = []


for name, coordinate in POINTS.items():
    states = prepare_states(
        coordinate
    )

    point_results = []

    print()
    print("-" * 92)
    print(name, coordinate)
    print("-" * 92)

    for age in PREP_STEPS:
        rho = states[age]

        J = flow_vector(
            rho
        )

        positive = analyze_direction(
            rho,
            J,
        )

        negative = analyze_direction(
            rho,
            -J,
        )

        both = (
            positive[
                "admissible_positive_step"
            ]
            and
            negative[
                "admissible_positive_step"
            ]
        )

        support = int(
            np.sum(
                rho > 1e-15
            )
        )

        print(
            "age=%2d support=%4d "
            "J:%s out=%4d "
            "-J:%s out=%4d "
            "both=%s"
            % (
                age,
                support,

                "YES"
                if positive[
                    "admissible_positive_step"
                ]
                else "NO",

                positive[
                    "outward_boundary_nodes"
                ],

                "YES"
                if negative[
                    "admissible_positive_step"
                ]
                else "NO",

                negative[
                    "outward_boundary_nodes"
                ],

                "YES" if both else "NO",
            )
        )

        point_results.append({
            "age": age,

            "support": support,

            "sum_J": float(
                J.sum()
            ),

            "norm_J": float(
                np.linalg.norm(J)
            ),

            "J": positive,

            "minus_J": negative,

            "both_directions_admissible": (
                both
            ),
        })

    results.append({
        "name": name,

        "coordinate": [
            int(value)
            for value in coordinate
        ],

        "ages": point_results,
    })


# ============================================================
# GLOBAL SUMMARY
# ============================================================

both_cases = []

for point in results:
    for item in point["ages"]:
        if item[
            "both_directions_admissible"
        ]:
            both_cases.append({
                "name": point["name"],
                "coordinate": (
                    point["coordinate"]
                ),
                "age": item["age"],
                "support": (
                    item["support"]
                ),
            })


print()
print("=" * 92)
print("BIDIRECTIONAL CASES")
print("=" * 92)

if both_cases:
    for item in both_cases:
        print(item)
else:
    print(
        "NONE detected in tested states"
    )


# ============================================================
# SAVE
# ============================================================

report = {
    "experiment": (
        "Admissible flow cone"
    ),

    "solver_modified": False,

    "definition": (
        "At rho_i=0 an admissible direction "
        "must satisfy J_i>=0. "
        "Mass-preserving directions additionally "
        "satisfy sum(J)=0."
    ),

    "results": results,

    "bidirectional_cases": both_cases,
}


output = OUT / (
    "flow_admissibility.json"
)

output.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)

print()
print("Saved:", output)
