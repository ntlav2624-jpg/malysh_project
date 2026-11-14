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
FRACTURED = model["FRACTURED"]

COORD_TO_NODE = model["COORD_TO_NODE"]
transfer_step = model["transfer_step"]
geometry_metrics = model["geometry_metrics"]


# ============================================================
# PARAMETERS
# ============================================================

STEPS = 40

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
    "experiments/trajectory_time"
)

OUT.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# BASIC METRICS
# ============================================================

def energy_center(rho):
    return np.sum(
        COORDS.astype(float)
        * rho[:, None],
        axis=0,
    )


def peak_coordinate(rho):
    index = int(
        np.argmax(rho)
    )

    return (
        COORDS[index]
        .astype(int)
        .tolist()
    )


def peak_energy(rho):
    return float(
        np.max(rho)
    )


def support_size(rho, threshold=1e-12):
    return int(
        np.sum(rho > threshold)
    )


def entropy_normalized(rho):
    positive = rho[rho > 0]

    return float(
        -np.sum(
            positive
            * np.log(positive)
        )
        / np.log(NODE_COUNT)
    )


# ============================================================
# CURVE UTILITIES
# ============================================================

def successive_distances(points):
    points = np.asarray(
        points,
        dtype=float,
    )

    if len(points) < 2:
        return np.array(
            [],
            dtype=float,
        )

    return np.linalg.norm(
        np.diff(points, axis=0),
        axis=1,
    )


def cumulative_length(points):
    distances = successive_distances(
        points
    )

    return np.concatenate([
        np.array([0.0]),
        np.cumsum(distances),
    ])


def correlation(first, second):
    first = np.asarray(
        first,
        dtype=float,
    )

    second = np.asarray(
        second,
        dtype=float,
    )

    if (
        np.std(first) == 0
        or np.std(second) == 0
    ):
        return 0.0

    return float(
        np.corrcoef(
            first,
            second,
        )[0, 1]
    )


def straightness(points):
    points = np.asarray(
        points,
        dtype=float,
    )

    if len(points) < 2:
        return 0.0

    direct = float(
        np.linalg.norm(
            points[-1]
            - points[0]
        )
    )

    length = float(
        successive_distances(
            points
        ).sum()
    )

    if length == 0:
        return 0.0

    return direct / length


def curve_effective_dimension(points):
    points = np.asarray(
        points,
        dtype=float,
    )

    if len(points) < 2:
        return {
            "eigenvalues": [],
            "effective_dimension": 0.0,
        }

    centered = (
        points
        - points.mean(axis=0)
    )

    covariance = (
        centered.T
        @ centered
        / len(points)
    )

    eigenvalues = np.linalg.eigvalsh(
        covariance
    )[::-1]

    eigenvalues = np.maximum(
        eigenvalues,
        0.0,
    )

    denominator = float(
        eigenvalues @ eigenvalues
    )

    if denominator > 0:
        effective_dimension = float(
            eigenvalues.sum()**2
            / denominator
        )
    else:
        effective_dimension = 0.0

    return {
        "eigenvalues": [
            float(value)
            for value in eigenvalues
        ],
        "effective_dimension": (
            effective_dimension
        ),
    }


# ============================================================
# REPEATED SPATIAL POSITIONS
# ============================================================

def repeated_events(
    spatial_positions,
    times,
):
    occurrences = {}

    for position, time_value in zip(
        spatial_positions,
        times,
    ):
        key = tuple(
            float(value)
            for value in position
        )

        occurrences.setdefault(
            key,
            [],
        ).append(
            int(time_value)
        )

    repeated = []

    for position, event_times in (
        occurrences.items()
    ):
        if len(event_times) > 1:
            repeated.append({
                "spatial_position": (
                    list(position)
                ),
                "times": event_times,
                "event_count": len(
                    event_times
                ),
            })

    repeated.sort(
        key=lambda item: (
            -item["event_count"],
            item["spatial_position"],
        )
    )

    return repeated


# ============================================================
# EVOLVE ONE BRANCH
# ============================================================

def evolve(initial, network):
    rho = initial.copy()

    distributions = []
    centers = []
    peaks = []
    peak_energies = []
    supports = []
    entropies = []
    classes = []

    for step_number in range(
        STEPS + 1
    ):
        distributions.append(
            rho.copy()
        )

        centers.append(
            energy_center(rho)
        )

        peaks.append(
            peak_coordinate(rho)
        )

        peak_energies.append(
            peak_energy(rho)
        )

        supports.append(
            support_size(rho)
        )

        entropies.append(
            entropy_normalized(rho)
        )

        classes.append(
            geometry_metrics(
                rho
            )["geometry_class"]
        )

        if step_number < STEPS:
            rho = transfer_step(
                rho,
                network,
            )

    return {
        "distributions": np.array(
            distributions
        ),
        "centers": np.array(
            centers
        ),
        "peaks": np.array(
            peaks,
            dtype=float,
        ),
        "peak_energies": np.array(
            peak_energies
        ),
        "supports": np.array(
            supports
        ),
        "entropies": np.array(
            entropies
        ),
        "classes": classes,
    }


# ============================================================
# ANALYZE TRAJECTORIES
# ============================================================

def analyze_branch(branch):
    times = np.arange(
        STEPS + 1,
        dtype=float,
    )

    distributions = branch[
        "distributions"
    ]

    centers = branch["centers"]
    peaks = branch["peaks"]

    # High-dimensional trajectory in state space.
    state_step_distances = (
        np.linalg.norm(
            np.diff(
                distributions,
                axis=0,
            ),
            axis=1,
        )
    )

    state_clock = np.concatenate([
        np.array([0.0]),
        np.cumsum(
            state_step_distances
        ),
    ])

    center_clock = cumulative_length(
        centers
    )

    peak_clock = cumulative_length(
        peaks
    )

    # Spacetime event curves.
    center_worldline = np.column_stack([
        centers,
        times,
    ])

    peak_worldline = np.column_stack([
        peaks,
        times,
    ])

    # Four-dimensional Euclidean diagnostic lengths.
    # This is not a Minkowski metric.
    center_4d_clock = cumulative_length(
        center_worldline
    )

    peak_4d_clock = cumulative_length(
        peak_worldline
    )

    repeated_peaks = repeated_events(
        peaks,
        times,
    )

    repeated_centers = (
        repeated_events(
            np.round(
                centers,
                decimals=12,
            ),
            times,
        )
    )

    # Fixed Fourier coordinates with the most
    # strongly changing energy history.
    temporal_variance = np.var(
        distributions,
        axis=0,
    )

    variable_indices = np.argsort(
        temporal_variance
    )[::-1][:12]

    strongest_fixed_points = []

    for index in variable_indices:
        strongest_fixed_points.append({
            "coordinate": (
                COORDS[index]
                .astype(int)
                .tolist()
            ),
            "variance": float(
                temporal_variance[index]
            ),
            "initial_energy": float(
                distributions[0, index]
            ),
            "final_energy": float(
                distributions[-1, index]
            ),
            "maximum_energy": float(
                distributions[:, index].max()
            ),
            "maximum_time": int(
                np.argmax(
                    distributions[:, index]
                )
            ),
        })

    report_rows = []

    for step_number in sorted(
        REPORT_STEPS
    ):
        report_rows.append({
            "time": step_number,
            "center": [
                float(value)
                for value in centers[
                    step_number
                ]
            ],
            "peak_coordinate": [
                int(value)
                for value in peaks[
                    step_number
                ]
            ],
            "peak_energy": float(
                branch[
                    "peak_energies"
                ][step_number]
            ),
            "support": int(
                branch[
                    "supports"
                ][step_number]
            ),
            "entropy": float(
                branch[
                    "entropies"
                ][step_number]
            ),
            "geometry_class": (
                branch["classes"][
                    step_number
                ]
            ),
            "state_internal_time": float(
                state_clock[
                    step_number
                ]
            ),
            "center_path_time": float(
                center_clock[
                    step_number
                ]
            ),
            "peak_path_time": float(
                peak_clock[
                    step_number
                ]
            ),
        })

    return {
        "time_is_strictly_ordered": bool(
            np.all(
                np.diff(times) > 0
            )
        ),

        "state_path_length": float(
            state_clock[-1]
        ),

        "center_spatial_length": float(
            center_clock[-1]
        ),

        "peak_spatial_length": float(
            peak_clock[-1]
        ),

        "center_4d_length": float(
            center_4d_clock[-1]
        ),

        "peak_4d_length": float(
            peak_4d_clock[-1]
        ),

        "time_vs_state_clock": (
            correlation(
                times,
                state_clock,
            )
        ),

        "time_vs_center_clock": (
            correlation(
                times,
                center_clock,
            )
        ),

        "time_vs_peak_clock": (
            correlation(
                times,
                peak_clock,
            )
        ),

        "center_straightness": (
            straightness(centers)
        ),

        "peak_straightness": (
            straightness(peaks)
        ),

        "center_curve_geometry": (
            curve_effective_dimension(
                centers
            )
        ),

        "peak_curve_geometry": (
            curve_effective_dimension(
                peaks
            )
        ),

        "center_worldline_geometry": (
            curve_effective_dimension(
                center_worldline
            )
        ),

        "peak_worldline_geometry": (
            curve_effective_dimension(
                peak_worldline
            )
        ),

        "unique_peak_positions": int(
            len({
                tuple(
                    int(value)
                    for value in position
                )
                for position in peaks
            })
        ),

        "repeated_peak_events": (
            repeated_peaks
        ),

        "repeated_center_events": (
            repeated_centers
        ),

        "strongest_fixed_point_histories": (
            strongest_fixed_points
        ),

        "reported_events": report_rows,

        "_state_clock": state_clock,

        "_center_clock": center_clock,

        "_peak_clock": peak_clock,
    }


# ============================================================
# COMPARE FULL AND FRACTURED PATHS
# ============================================================

def compare_branches(
    full_branch,
    fractured_branch,
):
    state_distance = np.linalg.norm(
        full_branch["distributions"]
        - fractured_branch[
            "distributions"
        ],
        axis=1,
    )

    center_distance = np.linalg.norm(
        full_branch["centers"]
        - fractured_branch["centers"],
        axis=1,
    )

    peak_distance = np.linalg.norm(
        full_branch["peaks"]
        - fractured_branch["peaks"],
        axis=1,
    )

    rows = []

    for step_number in sorted(
        REPORT_STEPS
    ):
        rows.append({
            "time": step_number,
            "state_distance_L2": float(
                state_distance[
                    step_number
                ]
            ),
            "center_distance": float(
                center_distance[
                    step_number
                ]
            ),
            "peak_distance": float(
                peak_distance[
                    step_number
                ]
            ),
            "same_peak_coordinate": bool(
                peak_distance[
                    step_number
                ] == 0
            ),
        })

    return {
        "final_state_distance_L2": float(
            state_distance[-1]
        ),
        "maximum_state_distance_L2": float(
            state_distance.max()
        ),
        "time_of_maximum_state_distance": int(
            np.argmax(
                state_distance
            )
        ),
        "final_center_distance": float(
            center_distance[-1]
        ),
        "maximum_center_distance": float(
            center_distance.max()
        ),
        "final_peak_distance": float(
            peak_distance[-1]
        ),
        "maximum_peak_distance": float(
            peak_distance.max()
        ),
        "same_peak_times": [
            int(index)
            for index, value
            in enumerate(peak_distance)
            if value == 0
        ],
        "reported_comparison": rows,
    }


# ============================================================
# MAIN
# ============================================================

print("=" * 92)
print("ТРАЕКТОРИЯ КАК ВНУТРЕННЕЕ ВРЕМЯ")
print("=" * 92)

print(
    "Time parameter : t = network step"
)

print(
    "State clock    : cumulative ||rho(t+1)-rho(t)||"
)

print(
    "Center clock   : cumulative center displacement"
)

print(
    "Peak clock     : cumulative peak displacement"
)

results = []


for point_name, coordinate in (
    POINTS.items()
):
    initial = np.zeros(
        NODE_COUNT,
        dtype=float,
    )

    initial[
        COORD_TO_NODE[
            coordinate
        ]
    ] = 1.0

    full_branch = evolve(
        initial,
        FULL,
    )

    fractured_branch = evolve(
        initial,
        FRACTURED,
    )

    full_analysis = analyze_branch(
        full_branch
    )

    fractured_analysis = analyze_branch(
        fractured_branch
    )

    comparison = compare_branches(
        full_branch,
        fractured_branch,
    )

    # Remove temporary arrays before JSON.
    for analysis in (
        full_analysis,
        fractured_analysis,
    ):
        analysis.pop(
            "_state_clock"
        )

        analysis.pop(
            "_center_clock"
        )

        analysis.pop(
            "_peak_clock"
        )

    result = {
        "name": point_name,
        "initial_coordinate": [
            int(value)
            for value in coordinate
        ],
        "full": full_analysis,
        "fractured": (
            fractured_analysis
        ),
        "comparison": comparison,
    }

    results.append(result)

    print()
    print("-" * 92)

    print(
        point_name,
        coordinate,
    )

    print("-" * 92)

    print(
        "FULL : "
        "corr(t,state)=%.6f "
        "center_dim=%.4f "
        "peak_dim=%.4f "
        "unique_peaks=%d"
        % (
            full_analysis[
                "time_vs_state_clock"
            ],
            full_analysis[
                "center_curve_geometry"
            ]["effective_dimension"],
            full_analysis[
                "peak_curve_geometry"
            ]["effective_dimension"],
            full_analysis[
                "unique_peak_positions"
            ],
        )
    )

    print(
        "FRAC : "
        "corr(t,state)=%.6f "
        "center_dim=%.4f "
        "peak_dim=%.4f "
        "unique_peaks=%d"
        % (
            fractured_analysis[
                "time_vs_state_clock"
            ],
            fractured_analysis[
                "center_curve_geometry"
            ]["effective_dimension"],
            fractured_analysis[
                "peak_curve_geometry"
            ]["effective_dimension"],
            fractured_analysis[
                "unique_peak_positions"
            ],
        )
    )

    print(
        "final state distance : %.8f"
        % comparison[
            "final_state_distance_L2"
        ]
    )

    print(
        "same peak times      :",
        comparison[
            "same_peak_times"
        ],
    )

    print()
    print(
        "%-5s %-20s %-20s %-12s %-12s %-12s"
        % (
            "t",
            "full peak",
            "fractured peak",
            "state L2",
            "center d",
            "peak d",
        )
    )

    for row in comparison[
        "reported_comparison"
    ]:
        time_value = row["time"]

        full_peak = (
            full_branch["peaks"][
                time_value
            ]
            .astype(int)
            .tolist()
        )

        fractured_peak = (
            fractured_branch[
                "peaks"
            ][time_value]
            .astype(int)
            .tolist()
        )

        print(
            "%-5d %-20s %-20s %-12.6f %-12.6f %-12.6f"
            % (
                time_value,
                str(full_peak),
                str(fractured_peak),
                row[
                    "state_distance_L2"
                ],
                row[
                    "center_distance"
                ],
                row[
                    "peak_distance"
                ],
            )
        )


# ============================================================
# SAVE
# ============================================================

report = {
    "experiment": (
        "Trajectory as internal time"
    ),

    "warning": (
        "Diagnostic conservative triad-network "
        "model. Four-dimensional path lengths "
        "use a Euclidean diagnostic metric, "
        "not a relativistic Minkowski metric. "
        "Energy parcels are not individually "
        "identified; tracked objects are the "
        "energy center, maximum-energy coordinate, "
        "full state vector and fixed-node histories."
    ),

    "solver_modified": False,

    "hypothesis": (
        "Time parametrizes the trajectory; "
        "cumulative state change may act as "
        "an internal clock but is not assumed "
        "identical to coordinate time."
    ),

    "definitions": {
        "event": "(kx,ky,kz,t,state)",
        "trajectory": "t -> event",
        "state_internal_time": (
            "sum ||rho(t+1)-rho(t)||"
        ),
        "center_path_time": (
            "sum ||C(t+1)-C(t)||"
        ),
        "peak_path_time": (
            "sum ||Pmax(t+1)-Pmax(t)||"
        ),
    },

    "parameters": {
        "steps": STEPS,
        "reported_steps": sorted(
            REPORT_STEPS
        ),
        "states": NODE_COUNT,
    },

    "results": results,
}

output = OUT / (
    "trajectory_time.json"
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
print("=" * 92)
print("ГОТОВО")
print("Результат:", output)
print("=" * 92)
