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

if not BASE.exists():
    raise SystemExit(
        "STOP: point_genesis_test.py not found"
    )

with contextlib.redirect_stdout(io.StringIO()):
    model = runpy.run_path(str(BASE))


COORDS = model["COORDS"]
NODE_COUNT = model["NODE_COUNT"]
POINTS = model["POINTS"]

FULL = model["FULL"]
COORD_TO_NODE = model["COORD_TO_NODE"]

geometry_metrics = model["geometry_metrics"]


# ============================================================
# CONFIG
# ============================================================

STEPS = 40
ALPHA = 0.10

REPORT_STEPS = {
    0,
    1,
    2,
    5,
    10,
    20,
    40,
}

OUT = Path(
    "experiments/opposite_flow"
)


# ============================================================
# NETWORK SCALE
# ============================================================

degree = np.bincount(
    np.concatenate([
        FULL["p"],
        FULL["q"],
        FULL["k"],
    ]),
    minlength=NODE_COUNT,
)

MAX_DEGREE = int(
    degree.max()
)

DT = ALPHA / MAX_DEGREE


# ============================================================
# CONSERVATIVE FLOW GENERATOR
# ============================================================

def flow_vector(rho):
    """
    Conservative diagnostic triad flow.

    For every triad we compute a local mean.
    FLOW+ points toward triad equalization.

    FLOW- will use exactly -flow_vector(rho).

    Important:
    this is a diagnostic signed-flow experiment,
    not Navier-Stokes time reversal.
    """

    p = FULL["p"]
    q = FULL["q"]
    k = FULL["k"]

    triad_mean = (
        rho[p]
        + rho[q]
        + rho[k]
    ) / 3.0

    delta = (
        np.bincount(
            p,
            weights=(
                triad_mean - rho[p]
            ),
            minlength=NODE_COUNT,
        )
        + np.bincount(
            q,
            weights=(
                triad_mean - rho[q]
            ),
            minlength=NODE_COUNT,
        )
        + np.bincount(
            k,
            weights=(
                triad_mean - rho[k]
            ),
            minlength=NODE_COUNT,
        )
    )

    return delta


# ============================================================
# SAFE SIGNED STEP
# ============================================================

def signed_step(rho, sign):
    delta = flow_vector(rho)

    requested_dt = DT

    if sign < 0:
        direction = -delta
    else:
        direction = delta

    negative_direction = (
        direction < 0
    )

    safe_dt = requested_dt

    if np.any(negative_direction):
        limits = (
            rho[negative_direction]
            / (
                -direction[
                    negative_direction
                ]
            )
        )

        positive_limits = limits[
            limits > 0
        ]

        if len(positive_limits):
            safe_dt = min(
                requested_dt,
                0.95
                * float(
                    positive_limits.min()
                ),
            )

    result = (
        rho
        + safe_dt * direction
    )

    result[np.abs(result) < 1e-18] = 0.0

    if result.min() < -1e-12:
        raise RuntimeError(
            "Positivity failure: %.18e"
            % float(result.min())
        )

    result = np.maximum(
        result,
        0.0,
    )

    before = float(
        rho.sum()
    )

    after = float(
        result.sum()
    )

    mass_error = after - before

    if abs(mass_error) > 1e-10:
        raise RuntimeError(
            "Mass invariant broken: %.18e"
            % mass_error
        )

    result /= result.sum()

    return (
        result,
        float(safe_dt),
        delta,
    )


# ============================================================
# INITIAL CLOUD
# ============================================================

def initial_cloud(coordinate):
    """
    Start from a point, but make five ordinary FULL
    evolution steps first.

    The resulting rho* is the SAME cloud supplied
    to both FLOW+ and FLOW- experiments.
    """

    rho = np.zeros(
        NODE_COUNT,
        dtype=float,
    )

    rho[
        COORD_TO_NODE[
            coordinate
        ]
    ] = 1.0

    for _ in range(5):
        rho, _, _ = signed_step(
            rho,
            +1,
        )

    return rho


# ============================================================
# COMPARISON METRICS
# ============================================================

def distribution_metrics(
    positive,
    negative,
):
    difference = (
        positive - negative
    )

    return {
        "L1": float(
            np.sum(
                np.abs(difference)
            )
        ),

        "L2": float(
            np.linalg.norm(
                difference
            )
        ),

        "cosine": float(
            np.dot(
                positive,
                negative,
            )
            / (
                np.linalg.norm(positive)
                * np.linalg.norm(negative)
            )
        ),

        "exact_equal": int(
            np.sum(
                positive == negative
            )
        ),

        "minimum_difference": float(
            np.min(
                np.abs(difference)
            )
        ),
    }


def center(rho):
    return np.sum(
        COORDS.astype(float)
        * rho[:, None],
        axis=0,
    )


def entropy(rho):
    positive = rho[
        rho > 0
    ]

    return float(
        -np.sum(
            positive
            * np.log(positive)
        )
        / np.log(NODE_COUNT)
    )


def participation(rho):
    return float(
        (
            1.0
            / np.sum(rho*rho)
        )
        / NODE_COUNT
    )


def state_summary(rho):
    geometry = geometry_metrics(
        rho
    )

    peak = int(
        np.argmax(rho)
    )

    return {
        "geometry_class": (
            geometry[
                "geometry_class"
            ]
        ),

        "center": [
            float(value)
            for value in center(rho)
        ],

        "peak_coordinate": (
            COORDS[peak]
            .astype(int)
            .tolist()
        ),

        "peak_energy": float(
            rho[peak]
        ),

        "entropy": entropy(rho),

        "participation": (
            participation(rho)
        ),

        "support": int(
            np.sum(
                rho > 1e-12
            )
        ),
    }


# ============================================================
# FLOW ALIGNMENT
# ============================================================

def flow_alignment(rho):
    j = flow_vector(rho)

    jp = j
    jm = -j

    denominator = (
        np.linalg.norm(jp)
        * np.linalg.norm(jm)
    )

    if denominator == 0:
        cosine = 0.0
    else:
        cosine = float(
            np.dot(jp, jm)
            / denominator
        )

    return {
        "norm_J": float(
            np.linalg.norm(j)
        ),

        "sum_J": float(
            np.sum(j)
        ),

        "opposite_flow_cosine": (
            cosine
        ),
    }


# ============================================================
# EXPERIMENT
# ============================================================

print("=" * 92)
print(
    "ОДИНАКОВОЕ ОБЛАКО -> "
    "ПРОТИВОПОЛОЖНЫЕ ПОТОКИ"
)
print("=" * 92)

print(
    "states       :",
    NODE_COUNT,
)

print(
    "triads       :",
    FULL["triads"],
)

print(
    "base dt      : %.12e"
    % DT
)

print(
    "initial prep : 5 FLOW+ steps"
)

results = []


for name, coordinate in (
    POINTS.items()
):
    rho_star = initial_cloud(
        coordinate
    )

    positive = rho_star.copy()
    negative = rho_star.copy()

    initial_positive = (
        positive.copy()
    )

    initial_negative = (
        negative.copy()
    )

    exact_initial_L1 = float(
        np.sum(
            np.abs(
                initial_positive
                - initial_negative
            )
        )
    )

    flow0 = flow_alignment(
        rho_star
    )

    print()
    print("-" * 92)

    print(
        name,
        coordinate,
    )

    print(
        "initial L1          : %.18e"
        % exact_initial_L1
    )

    print(
        "sum J              : %+.18e"
        % flow0["sum_J"]
    )

    print(
        "J+ vs J- cosine    : %.12f"
        % flow0[
            "opposite_flow_cosine"
        ]
    )

    print("-" * 92)

    snapshots = []

    cumulative_positive_time = 0.0
    cumulative_negative_time = 0.0

    for step_number in range(
        STEPS + 1
    ):
        if step_number in REPORT_STEPS:
            positive_summary = (
                state_summary(
                    positive
                )
            )

            negative_summary = (
                state_summary(
                    negative
                )
            )

            difference = (
                distribution_metrics(
                    positive,
                    negative,
                )
            )

            center_distance = float(
                np.linalg.norm(
                    center(positive)
                    - center(negative)
                )
            )

            snapshot = {
                "step": step_number,

                "positive": (
                    positive_summary
                ),

                "negative": (
                    negative_summary
                ),

                "difference": difference,

                "center_distance": (
                    center_distance
                ),

                "positive_elapsed": (
                    cumulative_positive_time
                ),

                "negative_elapsed": (
                    cumulative_negative_time
                ),

                "mass_positive": float(
                    positive.sum()
                ),

                "mass_negative": float(
                    negative.sum()
                ),
            }

            snapshots.append(
                snapshot
            )

            print(
                "n=%2d | "
                "J+:%-20s "
                "J-:%-20s "
                "| L1=%.6f "
                "center=%.6f "
                "H+=%.4f H-=%.4f"
                % (
                    step_number,

                    positive_summary[
                        "geometry_class"
                    ],

                    negative_summary[
                        "geometry_class"
                    ],

                    difference["L1"],

                    center_distance,

                    positive_summary[
                        "entropy"
                    ],

                    negative_summary[
                        "entropy"
                    ],
                )
            )

        if step_number == STEPS:
            break

        (
            positive,
            positive_dt,
            _,
        ) = signed_step(
            positive,
            +1,
        )

        (
            negative,
            negative_dt,
            _,
        ) = signed_step(
            negative,
            -1,
        )

        cumulative_positive_time += (
            positive_dt
        )

        cumulative_negative_time += (
            negative_dt
        )

    results.append({
        "name": name,

        "seed_coordinate": [
            int(value)
            for value in coordinate
        ],

        "initial_cloud": (
            state_summary(
                rho_star
            )
        ),

        "initial_L1": (
            exact_initial_L1
        ),

        "initial_flow": flow0,

        "snapshots": snapshots,
    })


# ============================================================
# CROSS-POINT RANKING
# ============================================================

ranking = []

for item in results:
    final = item[
        "snapshots"
    ][-1]

    ranking.append({
        "name": item["name"],

        "coordinate": item[
            "seed_coordinate"
        ],

        "L1": final[
            "difference"
        ]["L1"],

        "center_distance": (
            final[
                "center_distance"
            ]
        ),

        "positive_class": (
            final[
                "positive"
            ]["geometry_class"]
        ),

        "negative_class": (
            final[
                "negative"
            ]["geometry_class"]
        ),
    })


ranking.sort(
    key=lambda item: item["L1"],
    reverse=True,
)


print()
print("=" * 92)
print("FINAL RANKING")
print("=" * 92)

for rank, item in enumerate(
    ranking,
    start=1,
):
    print(
        "%d. %-16s k=%s "
        "L1=%.6f center=%.6f "
        "J+=%s J-=%s"
        % (
            rank,

            item["name"],

            item["coordinate"],

            item["L1"],

            item[
                "center_distance"
            ],

            item[
                "positive_class"
            ],

            item[
                "negative_class"
            ],
        )
    )


# ============================================================
# INVARIANTS
# ============================================================

max_mass_error = 0.0
max_initial_error = 0.0

for item in results:
    max_initial_error = max(
        max_initial_error,
        abs(
            item[
                "initial_L1"
            ]
        ),
    )

    for snapshot in item[
        "snapshots"
    ]:
        max_mass_error = max(
            max_mass_error,

            abs(
                snapshot[
                    "mass_positive"
                ]
                - 1.0
            ),

            abs(
                snapshot[
                    "mass_negative"
                ]
                - 1.0
            ),
        )


print()
print("=" * 92)
print("INVARIANTS")
print("=" * 92)

print(
    "max initial branch difference = "
    "%.18e"
    % max_initial_error
)

print(
    "max mass error                = "
    "%.18e"
    % max_mass_error
)

if max_initial_error < 1e-15:
    print(
        "SAME INITIAL CLOUD: PASS"
    )
else:
    print(
        "SAME INITIAL CLOUD: FAIL"
    )

if max_mass_error < 1e-12:
    print(
        "MASS CONSERVATION: PASS"
    )
else:
    print(
        "MASS CONSERVATION: FAIL"
    )


# ============================================================
# SAVE
# ============================================================

report = {
    "experiment": (
        "Same cloud, opposite diagnostic flows"
    ),

    "warning": (
        "J- = -J+ is a diagnostic signed-flow "
        "construction. It is not claimed to be "
        "physical Navier-Stokes time reversal."
    ),

    "solver_modified": False,

    "hypothesis": (
        "The same instantaneous cloud can have "
        "different future geometries when the "
        "flow field acting on it differs."
    ),

    "parameters": {
        "steps": STEPS,
        "alpha": ALPHA,
        "base_dt": DT,
        "initial_preparation_steps": 5,
        "states": NODE_COUNT,
        "triads": FULL["triads"],
    },

    "invariants": {
        "same_initial_cloud_max_L1": (
            max_initial_error
        ),

        "max_mass_error": (
            max_mass_error
        ),
    },

    "results": results,

    "ranking": ranking,
}


output = OUT / (
    "opposite_flow.json"
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
