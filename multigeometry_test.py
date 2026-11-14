#!/usr/bin/env python3

import contextlib
import io
import json
import math
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


COORDS = model["COORDS"].astype(float)
NODE_COUNT = model["NODE_COUNT"]

POINTS = model["POINTS"]

FULL = model["FULL"]
FRACTURED = model["FRACTURED"]

COORD_TO_NODE = model["COORD_TO_NODE"]

transfer_step = model["transfer_step"]


# ============================================================
# PARAMETERS
# ============================================================

STEPS = 40

SNAPSHOTS = {
    0,
    1,
    2,
    5,
    10,
    20,
    40,
}

ACTIVE_EPS = 1e-15

# Core-radius threshold relative to
# weighted RMS projected radius.
CORE_RADIUS_FACTOR = 0.35

OUT = Path(
    "experiments/multigeometry"
)


# ============================================================
# NUMERIC UTILITIES
# ============================================================

def safe_ratio(numerator, denominator):
    if abs(denominator) < 1e-30:
        return 0.0

    return float(
        numerator / denominator
    )


def normalize_weights(rho):
    total = float(
        rho.sum()
    )

    if total <= 0:
        raise ValueError(
            "Non-positive total state"
        )

    return rho / total


def weighted_mean(points, weights):
    return np.sum(
        points * weights[:, None],
        axis=0,
    )


def weighted_covariance(
    points,
    weights,
    center=None,
):
    if center is None:
        center = weighted_mean(
            points,
            weights,
        )

    centered = points - center

    return (
        centered.T
        @ (
            centered
            * weights[:, None]
        )
    )


def weighted_quantile(
    values,
    weights,
    quantile,
):
    order = np.argsort(values)

    sorted_values = values[order]
    sorted_weights = weights[order]

    cumulative = np.cumsum(
        sorted_weights
    )

    target = (
        quantile
        * cumulative[-1]
    )

    index = int(
        np.searchsorted(
            cumulative,
            target,
            side="left",
        )
    )

    index = min(
        index,
        len(sorted_values) - 1,
    )

    return float(
        sorted_values[index]
    )


# ============================================================
# OBSERVER 1:
# GLOBAL DIMENSIONAL GEOMETRY
# ============================================================

def dimensional_observer(rho):
    weights = normalize_weights(rho)

    center = weighted_mean(
        COORDS,
        weights,
    )

    covariance = weighted_covariance(
        COORDS,
        weights,
        center,
    )

    eigenvalues, eigenvectors = (
        np.linalg.eigh(
            covariance
        )
    )

    order = np.argsort(
        eigenvalues
    )[::-1]

    eigenvalues = np.maximum(
        eigenvalues[order],
        0.0,
    )

    eigenvectors = (
        eigenvectors[:, order]
    )

    total = float(
        eigenvalues.sum()
    )

    if total > 0:
        fractions = (
            eigenvalues / total
        )
    else:
        fractions = np.zeros(3)

    denominator = float(
        eigenvalues
        @ eigenvalues
    )

    if denominator > 0:
        effective_dimension = float(
            total * total
            / denominator
        )
    else:
        effective_dimension = 0.0

    # Soft simultaneous scores.
    e1, e2, e3 = eigenvalues

    line_score = (
        1.0
        - safe_ratio(
            e2 + e3,
            2.0 * e1,
        )
        if e1 > 0
        else 0.0
    )

    line_score = float(
        np.clip(
            line_score,
            0.0,
            1.0,
        )
    )

    sheet_score = (
        1.0
        - safe_ratio(
            e3,
            0.5 * (e1 + e2),
        )
        if (e1 + e2) > 0
        else 0.0
    )

    # A line is also planar, so remove the
    # strongly line-like part from sheet score.
    sheet_score *= (
        1.0
        - line_score
    )

    sheet_score = float(
        np.clip(
            sheet_score,
            0.0,
            1.0,
        )
    )

    volume_score = float(
        np.clip(
            3.0 * safe_ratio(
                e3,
                total,
            ),
            0.0,
            1.0,
        )
    )

    if total < 1e-30:
        geometry_class = "point"

    elif effective_dimension < 1.45:
        geometry_class = "filament"

    elif effective_dimension < 2.45:
        geometry_class = "sheet-like"

    elif (
        max(fractions)
        - min(fractions)
        < 0.08
    ):
        geometry_class = (
            "isotropic-volume"
        )

    else:
        geometry_class = (
            "anisotropic-volume"
        )

    return {
        "center": [
            float(value)
            for value in center
        ],

        "eigenvalues": [
            float(value)
            for value in eigenvalues
        ],

        "variance_fractions": [
            float(value)
            for value in fractions
        ],

        "effective_dimension": (
            effective_dimension
        ),

        "line_score": line_score,

        "sheet_score": sheet_score,

        "volume_score": volume_score,

        "geometry_class": (
            geometry_class
        ),

        "_eigenvectors": eigenvectors,
        "_center": center,
    }


# ============================================================
# OBSERVER 2:
# RADIAL SHELL GEOMETRY
# ============================================================

def radial_observer(rho, center):
    weights = normalize_weights(rho)

    centered = (
        COORDS - center
    )

    radii = np.linalg.norm(
        centered,
        axis=1,
    )

    mean_radius = float(
        np.sum(
            weights * radii
        )
    )

    radius_variance = float(
        np.sum(
            weights
            * (
                radii
                - mean_radius
            )**2
        )
    )

    radius_std = math.sqrt(
        max(
            radius_variance,
            0.0,
        )
    )

    radial_cv = safe_ratio(
        radius_std,
        mean_radius,
    )

    # Narrow radial spread means shell-like.
    shell_score = float(
        np.exp(
            -4.0 * radial_cv
        )
        if mean_radius > 0
        else 0.0
    )

    q10 = weighted_quantile(
        radii,
        weights,
        0.10,
    )

    q50 = weighted_quantile(
        radii,
        weights,
        0.50,
    )

    q90 = weighted_quantile(
        radii,
        weights,
        0.90,
    )

    return {
        "mean_radius": mean_radius,
        "radius_std": radius_std,
        "radial_cv": radial_cv,
        "shell_score": shell_score,
        "radius_q10": q10,
        "radius_q50": q50,
        "radius_q90": q90,
    }


# ============================================================
# OBSERVER 3:
# RING / ANNULUS IN PRINCIPAL PLANE
# ============================================================

def ring_observer(
    rho,
    center,
    eigenvectors,
    sheet_score,
):
    weights = normalize_weights(rho)

    centered = (
        COORDS - center
    )

    # Principal plane.
    u = eigenvectors[:, 0]
    v = eigenvectors[:, 1]
    normal = eigenvectors[:, 2]

    x = centered @ u
    y = centered @ v
    z = centered @ normal

    planar_radius = np.sqrt(
        x*x + y*y
    )

    rms_radius = math.sqrt(
        float(
            np.sum(
                weights
                * planar_radius**2
            )
        )
    )

    core_limit = (
        CORE_RADIUS_FACTOR
        * rms_radius
    )

    if rms_radius > 0:
        core_mass = float(
            np.sum(
                weights[
                    planar_radius
                    <= core_limit
                ]
            )
        )
    else:
        core_mass = 1.0

    annular_mass = float(
        1.0 - core_mass
    )

    mean_planar_radius = float(
        np.sum(
            weights
            * planar_radius
        )
    )

    planar_std = math.sqrt(
        max(
            float(
                np.sum(
                    weights
                    * (
                        planar_radius
                        - mean_planar_radius
                    )**2
                )
            ),
            0.0,
        )
    )

    planar_cv = safe_ratio(
        planar_std,
        mean_planar_radius,
    )

    narrow_ring_score = float(
        np.exp(
            -4.0 * planar_cv
        )
        if mean_planar_radius > 0
        else 0.0
    )

    # Ring needs:
    # 1. a plane,
    # 2. low central mass,
    # 3. concentration at a radius.
    ring_score = float(
        np.clip(
            sheet_score
            * annular_mass
            * narrow_ring_score,
            0.0,
            1.0,
        )
    )

    thickness_rms = math.sqrt(
        max(
            float(
                np.sum(
                    weights * z*z
                )
            ),
            0.0,
        )
    )

    thickness_ratio = safe_ratio(
        thickness_rms,
        rms_radius,
    )

    # Angular moments.
    angles = np.arctan2(
        y,
        x,
    )

    angular_moments = {}

    for harmonic in range(1, 9):
        moment = np.sum(
            weights
            * np.exp(
                1j
                * harmonic
                * angles
            )
        )

        angular_moments[
            str(harmonic)
        ] = float(
            abs(moment)
        )

    angular_uniformity = float(
        1.0
        - max(
            angular_moments.values()
        )
    )

    angular_uniformity = float(
        np.clip(
            angular_uniformity,
            0.0,
            1.0,
        )
    )

    ring_uniform_score = float(
        ring_score
        * angular_uniformity
    )

    return {
        "mean_planar_radius": (
            mean_planar_radius
        ),

        "planar_radius_std": (
            planar_std
        ),

        "planar_radial_cv": (
            planar_cv
        ),

        "core_mass": core_mass,

        "annular_mass": annular_mass,

        "thickness_rms": (
            thickness_rms
        ),

        "thickness_ratio": (
            thickness_ratio
        ),

        "ring_score": ring_score,

        "angular_uniformity": (
            angular_uniformity
        ),

        "ring_uniform_score": (
            ring_uniform_score
        ),

        "angular_moments": (
            angular_moments
        ),

        "_basis_u": u,
        "_basis_v": v,
        "_basis_n": normal,
    }


# ============================================================
# OBSERVER 4:
# MULTI-SCALE CONNECTIVITY / HOLE PROXY
# ============================================================

def topology_proxy(
    rho,
    center,
    eigenvectors,
):
    """
    Dependency-free topology proxy.

    This is NOT persistent homology.

    It measures central deficit and radial
    mass concentration at multiple thresholds.
    Persistence homology can be added later
    as an independent exact observer.
    """

    weights = normalize_weights(rho)

    centered = (
        COORDS - center
    )

    u = eigenvectors[:, 0]
    v = eigenvectors[:, 1]

    x = centered @ u
    y = centered @ v

    planar_radius = np.sqrt(
        x*x + y*y
    )

    rms = math.sqrt(
        float(
            np.sum(
                weights
                * planar_radius**2
            )
        )
    )

    scales = (
        0.15,
        0.25,
        0.35,
        0.45,
        0.55,
    )

    central_masses = {}

    for scale in scales:
        if rms > 0:
            mass = float(
                np.sum(
                    weights[
                        planar_radius
                        <= scale * rms
                    ]
                )
            )
        else:
            mass = 1.0

        central_masses[
            "%.2f" % scale
        ] = mass

    deficits = [
        1.0
        - central_masses[
            "%.2f" % scale
        ]
        for scale in scales
    ]

    hole_proxy = float(
        np.mean(deficits)
    )

    return {
        "central_masses": (
            central_masses
        ),

        "hole_proxy": hole_proxy,

        "warning": (
            "Central-deficit proxy only; "
            "not a homology computation."
        ),
    }


# ============================================================
# OBSERVER 5:
# TEMPORAL TRAJECTORY GEOMETRY
# ============================================================

def discrete_curve_metrics(points):
    points = np.asarray(
        points,
        dtype=float,
    )

    count = len(points)

    if count < 3:
        return {
            "path_length": 0.0,
            "direct_distance": 0.0,
            "straightness": 0.0,
            "mean_curvature": 0.0,
            "max_curvature": 0.0,
            "mean_abs_torsion": 0.0,
            "max_abs_torsion": 0.0,
            "nonplanarity": 0.0,
            "helix_score": 0.0,
        }

    edges = np.diff(
        points,
        axis=0,
    )

    edge_lengths = np.linalg.norm(
        edges,
        axis=1,
    )

    path_length = float(
        edge_lengths.sum()
    )

    direct_distance = float(
        np.linalg.norm(
            points[-1]
            - points[0]
        )
    )

    straightness = safe_ratio(
        direct_distance,
        path_length,
    )

    curvatures = []

    for i in range(
        1,
        count - 1,
    ):
        a = (
            points[i]
            - points[i - 1]
        )

        b = (
            points[i + 1]
            - points[i]
        )

        la = float(
            np.linalg.norm(a)
        )

        lb = float(
            np.linalg.norm(b)
        )

        if (
            la < 1e-15
            or lb < 1e-15
        ):
            continue

        cosine = float(
            np.dot(a, b)
            / (la * lb)
        )

        cosine = float(
            np.clip(
                cosine,
                -1.0,
                1.0,
            )
        )

        angle = math.acos(
            cosine
        )

        scale = 0.5 * (
            la + lb
        )

        curvatures.append(
            angle / scale
        )

    torsions = []

    if count >= 4:
        for i in range(
            count - 3
        ):
            p0 = points[i]
            p1 = points[i + 1]
            p2 = points[i + 2]
            p3 = points[i + 3]

            e1 = p1 - p0
            e2 = p2 - p1
            e3 = p3 - p2

            normal_1 = np.cross(
                e1,
                e2,
            )

            normal_2 = np.cross(
                e2,
                e3,
            )

            n1 = float(
                np.linalg.norm(
                    normal_1
                )
            )

            n2 = float(
                np.linalg.norm(
                    normal_2
                )
            )

            e2_length = float(
                np.linalg.norm(e2)
            )

            if (
                n1 < 1e-15
                or n2 < 1e-15
                or e2_length < 1e-15
            ):
                continue

            cosine = float(
                np.dot(
                    normal_1,
                    normal_2,
                )
                / (n1 * n2)
            )

            cosine = float(
                np.clip(
                    cosine,
                    -1.0,
                    1.0,
                )
            )

            angle = math.acos(
                cosine
            )

            orientation = float(
                np.sign(
                    np.dot(
                        np.cross(
                            normal_1,
                            normal_2,
                        ),
                        e2,
                    )
                )
            )

            torsions.append(
                orientation
                * angle
                / e2_length
            )

    centered = (
        points
        - points.mean(axis=0)
    )

    covariance = (
        centered.T
        @ centered
        / count
    )

    eigenvalues = np.linalg.eigvalsh(
        covariance
    )[::-1]

    eigenvalues = np.maximum(
        eigenvalues,
        0.0,
    )

    total_variance = float(
        eigenvalues.sum()
    )

    nonplanarity = (
        safe_ratio(
            eigenvalues[2],
            total_variance,
        )
        if len(eigenvalues) >= 3
        else 0.0
    )

    mean_curvature = float(
        np.mean(curvatures)
        if curvatures
        else 0.0
    )

    max_curvature = float(
        np.max(curvatures)
        if curvatures
        else 0.0
    )

    abs_torsions = np.abs(
        torsions
    )

    mean_abs_torsion = float(
        np.mean(abs_torsions)
        if len(abs_torsions)
        else 0.0
    )

    max_abs_torsion = float(
        np.max(abs_torsions)
        if len(abs_torsions)
        else 0.0
    )

    torsion_consistency = 0.0

    if len(torsions) >= 2:
        nonzero = [
            value
            for value in torsions
            if abs(value) > 1e-12
        ]

        if nonzero:
            signs = np.sign(
                nonzero
            )

            torsion_consistency = float(
                abs(
                    np.mean(signs)
                )
            )

    curvature_presence = float(
        1.0
        - np.exp(
            -mean_curvature
        )
    )

    torsion_presence = float(
        1.0
        - np.exp(
            -mean_abs_torsion
        )
    )

    # Helix candidate requires bending,
    # leaving a plane and consistent twist.
    helix_score = float(
        np.clip(
            curvature_presence
            * torsion_presence
            * torsion_consistency
            * min(
                1.0,
                12.0 * nonplanarity,
            ),
            0.0,
            1.0,
        )
    )

    return {
        "path_length": path_length,
        "direct_distance": direct_distance,
        "straightness": straightness,

        "mean_curvature": (
            mean_curvature
        ),

        "max_curvature": (
            max_curvature
        ),

        "mean_abs_torsion": (
            mean_abs_torsion
        ),

        "max_abs_torsion": (
            max_abs_torsion
        ),

        "torsion_sign_consistency": (
            torsion_consistency
        ),

        "trajectory_eigenvalues": [
            float(value)
            for value in eigenvalues
        ],

        "nonplanarity": (
            nonplanarity
        ),

        "helix_score": (
            helix_score
        ),
    }


# ============================================================
# SNAPSHOT OBSERVATION
# ============================================================

def observe_state(rho):
    dimensional = (
        dimensional_observer(rho)
    )

    center = dimensional.pop(
        "_center"
    )

    eigenvectors = dimensional.pop(
        "_eigenvectors"
    )

    radial = radial_observer(
        rho,
        center,
    )

    ring = ring_observer(
        rho,
        center,
        eigenvectors,
        dimensional[
            "sheet_score"
        ],
    )

    ring.pop("_basis_u")
    ring.pop("_basis_v")
    ring.pop("_basis_n")

    topology = topology_proxy(
        rho,
        center,
        eigenvectors,
    )

    active = int(
        np.sum(
            rho > ACTIVE_EPS
        )
    )

    positive = rho[
        rho > 0
    ]

    entropy = float(
        -np.sum(
            positive
            * np.log(positive)
        )
        / np.log(NODE_COUNT)
    )

    participation = float(
        (
            1.0
            / np.sum(rho*rho)
        )
        / NODE_COUNT
    )

    return {
        "active_support": active,
        "entropy": entropy,
        "participation": (
            participation
        ),
        "dimension": dimensional,
        "radial": radial,
        "ring": ring,
        "topology_proxy": (
            topology
        ),
    }


# ============================================================
# EVOLUTION
# ============================================================

def evolve_point(
    point_name,
    coordinate,
    network_name,
    network,
):
    rho = np.zeros(
        NODE_COUNT,
        dtype=float,
    )

    rho[
        COORD_TO_NODE[
            coordinate
        ]
    ] = 1.0

    centers = []
    snapshots = []

    geometry_path = []
    dominant_path = []

    for step in range(
        STEPS + 1
    ):
        observation = observe_state(
            rho
        )

        center = observation[
            "dimension"
        ]["center"]

        centers.append(center)

        scores = {
            "line": observation[
                "dimension"
            ]["line_score"],

            "sheet": observation[
                "dimension"
            ]["sheet_score"],

            "volume": observation[
                "dimension"
            ]["volume_score"],

            "shell": observation[
                "radial"
            ]["shell_score"],

            "ring": observation[
                "ring"
            ]["ring_score"],

            "ring_uniform": observation[
                "ring"
            ]["ring_uniform_score"],

            "hole_proxy": observation[
                "topology_proxy"
            ]["hole_proxy"],
        }

        dominant = max(
            scores,
            key=scores.get,
        )

        geometry_path.append(
            observation[
                "dimension"
            ]["geometry_class"]
        )

        dominant_path.append(
            dominant
        )

        if step in SNAPSHOTS:
            snapshots.append({
                "step": step,
                "observation": (
                    observation
                ),
                "simultaneous_scores": (
                    scores
                ),
                "dominant_observer": (
                    dominant
                ),
                "mass": float(
                    rho.sum()
                ),
            })

        if step < STEPS:
            rho = transfer_step(
                rho,
                network,
            )

    trajectory = discrete_curve_metrics(
        centers
    )

    def compress(sequence):
        result = []

        for value in sequence:
            if (
                not result
                or value != result[-1]
            ):
                result.append(value)

        return result

    return {
        "point": point_name,

        "coordinate": [
            int(value)
            for value in coordinate
        ],

        "network": network_name,

        "snapshots": snapshots,

        "geometry_path": (
            compress(geometry_path)
        ),

        "dominant_observer_path": (
            compress(dominant_path)
        ),

        "center_trajectory": (
            trajectory
        ),
    }


# ============================================================
# MAIN
# ============================================================

print("=" * 100)
print("MULTI-GEOMETRY OBSERVER")
print("=" * 100)

print(
    "One rho is observed simultaneously as:"
)

print(
    "dimension + shell + ring + "
    "hole proxy + temporal curve"
)

print()

results = []


for point_name, coordinate in (
    POINTS.items()
):
    for network_name, network in (
        ("full", FULL),
        ("fractured", FRACTURED),
    ):
        result = evolve_point(
            point_name,
            coordinate,
            network_name,
            network,
        )

        results.append(result)

        trajectory = result[
            "center_trajectory"
        ]

        print()
        print("-" * 100)

        print(
            point_name,
            coordinate,
            network_name,
        )

        print(
            "dimension path :",
            " -> ".join(
                result[
                    "geometry_path"
                ]
            ),
        )

        print(
            "observer path  :",
            " -> ".join(
                result[
                    "dominant_observer_path"
                ]
            ),
        )

        print(
            "trajectory     : "
            "curvature=%.6e "
            "torsion=%.6e "
            "nonplanarity=%.6e "
            "helix=%.6f"
            % (
                trajectory[
                    "mean_curvature"
                ],

                trajectory[
                    "mean_abs_torsion"
                ],

                trajectory[
                    "nonplanarity"
                ],

                trajectory[
                    "helix_score"
                ],
            )
        )

        print(
            "%-4s %-9s %-9s %-9s %-9s "
            "%-9s %-9s %-10s"
            % (
                "t",
                "D_eff",
                "line",
                "sheet",
                "volume",
                "shell",
                "ring",
                "holeProxy",
            )
        )

        for snapshot in result[
            "snapshots"
        ]:
            observation = snapshot[
                "observation"
            ]

            scores = snapshot[
                "simultaneous_scores"
            ]

            print(
                "%-4d %-9.4f %-9.4f %-9.4f "
                "%-9.4f %-9.4f %-9.4f %-10.4f"
                % (
                    snapshot["step"],

                    observation[
                        "dimension"
                    ][
                        "effective_dimension"
                    ],

                    scores["line"],
                    scores["sheet"],
                    scores["volume"],
                    scores["shell"],
                    scores["ring"],
                    scores["hole_proxy"],
                )
            )


# ============================================================
# CROSS OBSERVER AGREEMENT
# ============================================================

cross_analysis = []

for result in results:
    for snapshot in result[
        "snapshots"
    ]:
        scores = snapshot[
            "simultaneous_scores"
        ]

        active_scores = [
            name
            for name, value
            in scores.items()
            if value >= 0.50
        ]

        cross_analysis.append({
            "point": result["point"],
            "coordinate": (
                result["coordinate"]
            ),
            "network": (
                result["network"]
            ),
            "step": snapshot["step"],
            "active_observers_0_5": (
                active_scores
            ),
            "simultaneous_count": len(
                active_scores
            ),
            "scores": scores,
        })


multi_hits = [
    item
    for item in cross_analysis
    if item[
        "simultaneous_count"
    ] >= 2
]


print()
print("=" * 100)
print("SIMULTANEOUS GEOMETRIES")
print("=" * 100)

print(
    "records with >=2 scores above 0.5:",
    len(multi_hits),
)

for item in multi_hits[:40]:
    print(
        "%-16s %-9s t=%2d  %s"
        % (
            item["point"],
            item["network"],
            item["step"],
            ", ".join(
                item[
                    "active_observers_0_5"
                ]
            ),
        )
    )


# ============================================================
# INVARIANTS
# ============================================================

max_mass_error = 0.0

for result in results:
    for snapshot in result[
        "snapshots"
    ]:
        max_mass_error = max(
            max_mass_error,
            abs(
                snapshot["mass"]
                - 1.0
            ),
        )


print()
print("=" * 100)
print("INVARIANTS")
print("=" * 100)

print(
    "max mass error = %.18e"
    % max_mass_error
)


# ============================================================
# SAVE
# ============================================================

report = {
    "experiment": (
        "Simultaneous geometric observers"
    ),

    "solver_modified": False,

    "warning": (
        "Ring and hole values are geometric "
        "proxies, not persistent homology. "
        "Helix score is a diagnostic based on "
        "center-trajectory curvature, torsion "
        "and nonplanarity."
    ),

    "hypothesis": (
        "Cloud, dimension, sheet, shell, ring "
        "and temporal spiral may describe "
        "different projections or scales of "
        "one evolving distribution."
    ),

    "parameters": {
        "steps": STEPS,
        "snapshots": sorted(
            SNAPSHOTS
        ),
        "active_eps": (
            ACTIVE_EPS
        ),
        "core_radius_factor": (
            CORE_RADIUS_FACTOR
        ),
        "states": NODE_COUNT,
    },

    "results": results,

    "cross_analysis": cross_analysis,

    "simultaneous_geometry_records": (
        multi_hits
    ),

    "invariants": {
        "max_mass_error": (
            max_mass_error
        ),
    },
}


output = OUT / (
    "multigeometry.json"
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
