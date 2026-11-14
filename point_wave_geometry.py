#!/usr/bin/env python3

import contextlib
import io
import json
import runpy
from pathlib import Path

import numpy as np


# ============================================================
# LOAD THE VERIFIED POINT-GENESIS MODEL
# ============================================================

BASE = Path("point_genesis_test.py")

if not BASE.exists():
    raise SystemExit(
        "STOP: point_genesis_test.py not found"
    )

silent_output = io.StringIO()

with contextlib.redirect_stdout(silent_output):
    model = runpy.run_path(str(BASE))


COORDS = model["COORDS"]
NODE_COUNT = model["NODE_COUNT"]

POINTS = model["POINTS"]
SNAPSHOTS = model["SNAPSHOTS"]
STEPS = model["STEPS"]

FULL = model["FULL"]
FRACTURED = model["FRACTURED"]

COORD_TO_NODE = model["COORD_TO_NODE"]

transfer_step = model["transfer_step"]
geometry_metrics = model["geometry_metrics"]
divergence_metrics = model["divergence_metrics"]


# ============================================================
# OUTPUT AND WAVE GRID
# ============================================================

OUT = Path(
    "experiments/point_wave_geometry"
)

OUT.mkdir(
    parents=True,
    exist_ok=True,
)

WAVE_GRID = 16

coordinate_axis = np.linspace(
    -np.pi,
    np.pi,
    WAVE_GRID,
    endpoint=False,
)

xx, yy, zz = np.meshgrid(
    coordinate_axis,
    coordinate_axis,
    coordinate_axis,
    indexing="ij",
)

REAL_POINTS = np.column_stack([
    xx.ravel(),
    yy.ravel(),
    zz.ravel(),
])


# ============================================================
# RELATIONAL VALUES OF EACH POINT
# ============================================================

def node_degree(network):
    return np.bincount(
        np.concatenate([
            network["p"],
            network["q"],
            network["k"],
        ]),
        minlength=NODE_COUNT,
    )


FULL_DEGREE = node_degree(FULL)
FRACTURED_DEGREE = node_degree(FRACTURED)


# ============================================================
# X0: SPATIAL VALUE
# ============================================================

def spatial_value(coordinate):
    vector = np.array(
        coordinate,
        dtype=float,
    )

    radius = float(
        np.linalg.norm(vector)
    )

    nonzero_components = int(
        np.sum(vector != 0)
    )

    boundary_components = int(
        np.sum(np.abs(vector) == 5)
    )

    if nonzero_components == 1:
        position_class = "axis"

    elif nonzero_components == 2:
        position_class = "plane-diagonal"

    else:
        position_class = "space-diagonal"

    if boundary_components == 3:
        boundary_class = "corner"

    elif boundary_components > 0:
        boundary_class = "boundary"

    else:
        boundary_class = "interior"

    if radius > 0:
        direction = (
            vector / radius
        ).tolist()
    else:
        direction = [0.0, 0.0, 0.0]

    return {
        "coordinate": [
            int(value)
            for value in coordinate
        ],
        "radius": radius,
        "direction": [
            float(value)
            for value in direction
        ],
        "nonzero_components": (
            nonzero_components
        ),
        "boundary_components": (
            boundary_components
        ),
        "position_class": position_class,
        "boundary_class": boundary_class,
    }


# ============================================================
# X1: RELATIONAL VALUE
# ============================================================

def relational_value(node):
    full_degree = int(
        FULL_DEGREE[node]
    )

    fractured_degree = int(
        FRACTURED_DEGREE[node]
    )

    if full_degree > 0:
        local_loss = (
            1.0
            - fractured_degree
            / full_degree
        )
    else:
        local_loss = 0.0

    return {
        "full_degree": full_degree,
        "fractured_degree": (
            fractured_degree
        ),
        "lost_degree": (
            full_degree
            - fractured_degree
        ),
        "local_relation_loss": float(
            local_loss
        ),
    }


# ============================================================
# WAVE RECONSTRUCTION
# ============================================================

def reconstruct_wave(rho):
    """
    Diagnostic coherent-phase reconstruction:

        psi(x) = sum_k sqrt(rho_k) exp(i k dot x)

    All spectral phases are initially set to zero.

    This is a wave-geometry observer, not a recovered
    physical phase field and not a dispersion model.
    """

    spectrum = np.zeros(
        (
            WAVE_GRID,
            WAVE_GRID,
            WAVE_GRID,
        ),
        dtype=complex,
    )

    amplitudes = np.sqrt(rho)

    for amplitude, coordinate in zip(
        amplitudes,
        COORDS,
    ):
        kx, ky, kz = (
            int(value)
            for value in coordinate
        )

        spectrum[
            kx % WAVE_GRID,
            ky % WAVE_GRID,
            kz % WAVE_GRID,
        ] = amplitude

    wave = (
        np.fft.ifftn(spectrum)
        * WAVE_GRID**3
    )

    intensity = np.abs(wave)**2

    intensity /= intensity.sum()

    return wave, intensity


# ============================================================
# WAVE DIRECTION GEOMETRY
# ============================================================

def wave_direction_geometry(rho):
    """
    Gradient-energy tensor:

        G_ij = sum_k rho_k k_i k_j

    It measures how many independent propagation
    directions are active.
    """

    wave_vectors = COORDS.astype(float)

    tensor = (
        wave_vectors.T
        @ (
            wave_vectors
            * rho[:, None]
        )
    )

    eigenvalues = np.linalg.eigvalsh(
        tensor
    )[::-1]

    eigenvalues = np.maximum(
        eigenvalues,
        0.0,
    )

    trace = float(
        eigenvalues.sum()
    )

    square_sum = float(
        eigenvalues @ eigenvalues
    )

    if square_sum > 0:
        effective_dimension = (
            trace * trace / square_sum
        )
    else:
        effective_dimension = 0.0

    support = int(
        np.sum(rho > 1e-12)
    )

    if support == 1:
        wave_class = "single-plane-wave"

    elif effective_dimension < 1.5:
        wave_class = (
            "quasi-collinear-wave-bundle"
        )

    elif effective_dimension < 2.5:
        wave_class = "planar-wave-fan"

    else:
        wave_class = (
            "three-dimensional-wave-cloud"
        )

    return {
        "wave_class": wave_class,
        "direction_eigenvalues": [
            float(value)
            for value in eigenvalues
        ],
        "direction_effective_dimension": (
            float(effective_dimension)
        ),
        "active_spectral_support": support,
    }


# ============================================================
# INTERFERENCE GEOMETRY IN REAL SPACE
# ============================================================

def interference_geometry(rho):
    wave, intensity = (
        reconstruct_wave(rho)
    )

    flat = intensity.ravel()

    uniform_value = (
        1.0 / flat.size
    )

    contrast = float(
        flat.std() / uniform_value
    )

    positive = flat[flat > 0]

    entropy = float(
        -np.sum(
            positive * np.log(positive)
        )
        / np.log(flat.size)
    )

    participation = float(
        (
            1.0
            / np.sum(flat*flat)
        )
        / flat.size
    )

    center = np.sum(
        REAL_POINTS
        * flat[:, None],
        axis=0,
    )

    centered = (
        REAL_POINTS - center
    )

    covariance = (
        centered.T
        @ (
            centered
            * flat[:, None]
        )
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

    mean_intensity = float(
        intensity.mean()
    )

    local_maximum = (
        (intensity >= np.roll(
            intensity, 1, axis=0
        ))
        & (intensity >= np.roll(
            intensity, -1, axis=0
        ))
        & (intensity >= np.roll(
            intensity, 1, axis=1
        ))
        & (intensity >= np.roll(
            intensity, -1, axis=1
        ))
        & (intensity >= np.roll(
            intensity, 1, axis=2
        ))
        & (intensity >= np.roll(
            intensity, -1, axis=2
        ))
        & (
            intensity
            > 2.0 * mean_intensity
        )
    )

    peaks = int(
        np.sum(local_maximum)
    )

    occupied_fraction = float(
        np.mean(
            intensity
            > 2.0 * mean_intensity
        )
    )

    peak_index = np.unravel_index(
        int(np.argmax(intensity)),
        intensity.shape,
    )

    peak_coordinate = [
        float(
            coordinate_axis[index]
        )
        for index in peak_index
    ]

    if contrast < 1e-12:
        interference_class = (
            "uniform-plane-wave-intensity"
        )

    elif peaks == 1:
        interference_class = (
            "single-interference-focus"
        )

    elif occupied_fraction < 0.03:
        interference_class = (
            "sparse-interference-lattice"
        )

    elif occupied_fraction < 0.15:
        interference_class = (
            "clustered-interference-field"
        )

    else:
        interference_class = (
            "distributed-interference-field"
        )

    return {
        "interference_class": (
            interference_class
        ),
        "intensity_contrast": contrast,
        "intensity_entropy": entropy,
        "intensity_participation": (
            participation
        ),
        "intensity_effective_dimension": (
            effective_dimension
        ),
        "intensity_eigenvalues": [
            float(value)
            for value in eigenvalues
        ],
        "local_peak_count": peaks,
        "occupied_fraction_above_2mean": (
            occupied_fraction
        ),
        "peak_coordinate": (
            peak_coordinate
        ),
        "_intensity": flat,
        "_wave_norm": float(
            np.sum(np.abs(wave)**2)
        ),
    }


def wave_metrics(rho):
    direction = wave_direction_geometry(
        rho
    )

    interference = (
        interference_geometry(rho)
    )

    intensity = interference.pop(
        "_intensity"
    )

    return (
        {
            **direction,
            **interference,
        },
        intensity,
    )


# ============================================================
# WAVE DIVERGENCE
# ============================================================

def wave_divergence(
    full_intensity,
    fractured_intensity,
):
    difference = np.abs(
        full_intensity
        - fractured_intensity
    )

    midpoint = 0.5 * (
        full_intensity
        + fractured_intensity
    )

    full_positive = (
        full_intensity > 0
    )

    fractured_positive = (
        fractured_intensity > 0
    )

    js = float(
        0.5
        * np.sum(
            full_intensity[
                full_positive
            ]
            * np.log(
                full_intensity[
                    full_positive
                ]
                / midpoint[
                    full_positive
                ]
            )
        )
        + 0.5
        * np.sum(
            fractured_intensity[
                fractured_positive
            ]
            * np.log(
                fractured_intensity[
                    fractured_positive
                ]
                / midpoint[
                    fractured_positive
                ]
            )
        )
    )

    return {
        "wave_L1": float(
            difference.sum()
        ),
        "wave_L2": float(
            np.linalg.norm(
                full_intensity
                - fractured_intensity
            )
        ),
        "wave_Jensen_Shannon": js,
        "exact_equal_samples": int(
            np.sum(difference == 0)
        ),
        "near_equal_1e-12": int(
            np.sum(
                difference <= 1e-12
            )
        ),
        "minimum_difference": float(
            difference.min()
        ),
    }


# ============================================================
# FIVE-LAYER POINT CONSTRUCTION
# ============================================================

results = []

print("=" * 78)
print("POINT -> GEOMETRY -> WAVE GEOMETRY")
print("=" * 78)

print(
    "Wave phase observer : coherent zero phase"
)

print(
    "Wave grid           :",
    WAVE_GRID,
)

print(
    "Relations           :",
    FULL["relations_1D"],
    "->",
    FRACTURED["relations_1D"],
)

print(
    "Triads              :",
    FULL["triads"],
    "->",
    FRACTURED["triads"],
)


for name, coordinate in POINTS.items():
    node = COORD_TO_NODE[
        coordinate
    ]

    initial = np.zeros(
        NODE_COUNT,
        dtype=float,
    )

    initial[node] = 1.0

    full = initial.copy()
    fractured = initial.copy()

    x0 = spatial_value(
        coordinate
    )

    x1 = relational_value(
        node
    )

    snapshots = []

    print()
    print("-" * 78)

    print(
        name,
        coordinate,
        "| degree",
        x1["full_degree"],
        "->",
        x1["fractured_degree"],
    )

    print("-" * 78)

    for step_number in range(
        STEPS + 1
    ):
        if step_number in SNAPSHOTS:
            full_geometry = (
                geometry_metrics(full)
            )

            fractured_geometry = (
                geometry_metrics(
                    fractured
                )
            )

            state_divergence = (
                divergence_metrics(
                    full,
                    fractured,
                )
            )

            full_wave, full_intensity = (
                wave_metrics(full)
            )

            (
                fractured_wave,
                fractured_intensity,
            ) = wave_metrics(fractured)

            wave_difference = (
                wave_divergence(
                    full_intensity,
                    fractured_intensity,
                )
            )

            snapshot = {
                "step": step_number,

                "X0_spatial": x0,
                "X1_relational": x1,

                "X2_full_genesis": (
                    full_geometry
                ),

                "X2_fractured_genesis": (
                    fractured_geometry
                ),

                "X3_observer_difference": (
                    state_divergence
                ),

                "XW_full_wave": full_wave,

                "XW_fractured_wave": (
                    fractured_wave
                ),

                "XW_wave_difference": (
                    wave_difference
                ),

                "mass_full": float(
                    full.sum()
                ),

                "mass_fractured": float(
                    fractured.sum()
                ),
            }

            snapshots.append(snapshot)

            print(
                "t=%2d | k:%-18s/%-18s "
                "| wave:%-30s/%-30s "
                "| L1k=%.5f L1w=%.5f"
                % (
                    step_number,

                    full_geometry[
                        "geometry_class"
                    ],

                    fractured_geometry[
                        "geometry_class"
                    ],

                    full_wave[
                        "wave_class"
                    ],

                    fractured_wave[
                        "wave_class"
                    ],

                    state_divergence[
                        "L1"
                    ],

                    wave_difference[
                        "wave_L1"
                    ],
                )
            )

        if step_number == STEPS:
            break

        full = transfer_step(
            full,
            FULL,
        )

        fractured = transfer_step(
            fractured,
            FRACTURED,
        )

    results.append({
        "name": name,
        "initial_coordinate": [
            int(value)
            for value in coordinate
        ],
        "X0_spatial": x0,
        "X1_relational": x1,
        "snapshots": snapshots,
    })


# ============================================================
# SAVE
# ============================================================

report = {
    "experiment": (
        "Five-layer point and wave geometry"
    ),

    "warning": (
        "The network dynamics is diagnostic, "
        "not a Navier-Stokes proof. "
        "The wave field uses amplitudes sqrt(rho) "
        "with all spectral phases fixed to zero. "
        "No physical dispersion law omega(k) "
        "is assumed."
    ),

    "solver_modified": False,

    "construction": {
        "X0": "spatial point geometry",
        "X1": "relational network geometry",
        "X2": "geometry generated in k-space",
        "X3": "difference between observers",
        "XW": (
            "wave-direction and interference "
            "geometry in x-space"
        ),
    },

    "parameters": {
        "wave_grid": WAVE_GRID,
        "steps": STEPS,
        "states": NODE_COUNT,
        "phase_convention": (
            "all spectral phases zero"
        ),
    },

    "results": results,
}

output = OUT / (
    "point_wave_geometry.json"
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
print("=" * 78)
print("ГОТОВО")
print("Результат:", output)
print("=" * 78)
