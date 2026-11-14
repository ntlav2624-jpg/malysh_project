#!/usr/bin/env python3

import json
from pathlib import Path

import numpy as np


# ============================================================
# PARAMETERS
# ============================================================

K = 5
NFFT = 17
STEPS = 40
ALPHA = 0.20

SNAPSHOTS = {0, 1, 2, 5, 10, 20, 40}

POINTS = {
    "axis_inner": (1, 0, 0),
    "axis_outer": (5, 0, 0),
    "plane_diagonal": (3, 3, 0),
    "space_diagonal": (3, 3, 3),
    "corner": (5, 5, 5),
}

OUT = Path("experiments/point_genesis")
OUT.mkdir(parents=True, exist_ok=True)


# ============================================================
# STATE SPACE
# ============================================================

VALUES = np.arange(-K, K + 1, dtype=int)
SIDE = len(VALUES)

COORDS = np.array(
    [
        (x, y, z)
        for x in VALUES
        for y in VALUES
        for z in VALUES
        if (x, y, z) != (0, 0, 0)
    ],
    dtype=np.int16,
)

NODE_COUNT = len(COORDS)


def flat_index(coordinate):
    x, y, z = coordinate

    return (
        ((x + K) * SIDE + (y + K))
        * SIDE
        + (z + K)
    )


FLAT_TO_NODE = np.full(
    SIDE**3,
    -1,
    dtype=np.int32,
)

for node, coordinate in enumerate(COORDS):
    FLAT_TO_NODE[
        flat_index(coordinate)
    ] = node


ZERO_FLAT = flat_index((0, 0, 0))

COORD_TO_NODE = {
    tuple(int(value) for value in coordinate): node
    for node, coordinate in enumerate(COORDS)
}


# ============================================================
# ONE-DIMENSIONAL RELATIONS
# ============================================================

def one_dimensional_relations(observer):
    raw = np.fft.fftfreq(NFFT) * NFFT
    active = raw[np.abs(raw) <= K]

    raw_by_integer = {
        int(round(float(value))): float(value)
        for value in active
    }

    raw_set = set(raw_by_integer.values())

    relations = []
    missing = []

    for p in VALUES:
        for q in VALUES:
            target = int(p + q)

            if target < -K or target > K:
                continue

            relation = (
                int(p),
                int(q),
                target,
            )

            if observer == "integer":
                relations.append(relation)
                continue

            p_raw = raw_by_integer[int(p)]
            q_raw = raw_by_integer[int(q)]
            k_raw = raw_by_integer[target]

            candidate = p_raw + q_raw
            defect = candidate - k_raw

            if candidate in raw_set:
                relations.append(relation)
            else:
                missing.append({
                    "p": int(p),
                    "q": int(q),
                    "k": target,
                    "defect": float(defect),
                })

    return (
        np.array(relations, dtype=np.int16),
        missing,
    )


# ============================================================
# THREE-DIMENSIONAL TRIADS
# ============================================================

def build_network(observer):
    relations, missing = (
        one_dimensional_relations(observer)
    )

    count = len(relations)

    first = np.repeat(
        np.arange(count),
        count * count,
    )

    second = np.tile(
        np.repeat(np.arange(count), count),
        count,
    )

    third = np.tile(
        np.arange(count),
        count * count,
    )

    p_coord = np.column_stack([
        relations[first, 0],
        relations[second, 0],
        relations[third, 0],
    ])

    q_coord = np.column_stack([
        relations[first, 1],
        relations[second, 1],
        relations[third, 1],
    ])

    k_coord = np.column_stack([
        relations[first, 2],
        relations[second, 2],
        relations[third, 2],
    ])

    def flat_array(array):
        return (
            (
                (array[:, 0] + K) * SIDE
                + (array[:, 1] + K)
            )
            * SIDE
            + (array[:, 2] + K)
        )

    p_flat = flat_array(p_coord)
    q_flat = flat_array(q_coord)
    k_flat = flat_array(k_coord)

    keep = (
        (p_flat != ZERO_FLAT)
        & (q_flat != ZERO_FLAT)
        & (k_flat != ZERO_FLAT)
    )

    return {
        "observer": observer,
        "relations_1D": count,
        "missing_1D": missing,
        "p": FLAT_TO_NODE[p_flat[keep]],
        "q": FLAT_TO_NODE[q_flat[keep]],
        "k": FLAT_TO_NODE[k_flat[keep]],
        "triads": int(np.sum(keep)),
    }


FULL = build_network("integer")
FRACTURED = build_network("float")


# ============================================================
# CONSERVATIVE DYNAMICS
# ============================================================

degree = np.bincount(
    np.concatenate([
        FULL["p"],
        FULL["q"],
        FULL["k"],
    ]),
    minlength=NODE_COUNT,
)

DT = ALPHA / int(degree.max())


def transfer_step(rho, network):
    p = network["p"]
    q = network["q"]
    k = network["k"]

    triad_mean = (
        rho[p] + rho[q] + rho[k]
    ) / 3.0

    delta = (
        np.bincount(
            p,
            weights=triad_mean - rho[p],
            minlength=NODE_COUNT,
        )
        + np.bincount(
            q,
            weights=triad_mean - rho[q],
            minlength=NODE_COUNT,
        )
        + np.bincount(
            k,
            weights=triad_mean - rho[k],
            minlength=NODE_COUNT,
        )
    )

    result = rho + DT * delta

    if result.min() < -1e-12:
        raise RuntimeError(
            "Отрицательная энергия: %.18e"
            % float(result.min())
        )

    result = np.maximum(result, 0.0)
    result /= result.sum()

    return result


# ============================================================
# GEOMETRY CREATED FROM A POINT
# ============================================================

def geometry_metrics(rho):
    points = COORDS.astype(float)

    center = np.sum(
        points * rho[:, None],
        axis=0,
    )

    centered = points - center

    covariance = (
        centered.T
        @ (centered * rho[:, None])
    )

    eigenvalues = np.linalg.eigvalsh(
        covariance
    )[::-1]

    eigenvalues = np.maximum(
        eigenvalues,
        0.0,
    )

    trace = float(eigenvalues.sum())
    denominator = float(eigenvalues @ eigenvalues)

    if denominator > 0:
        effective_dimension = (
            trace * trace / denominator
        )
    else:
        effective_dimension = 0.0

    radial = np.linalg.norm(
        centered,
        axis=1,
    )

    radial_center = float(radial @ rho)

    radial_width = float(
        np.sqrt(
            ((radial - radial_center)**2)
            @ rho
        )
    )

    anisotropy = 0.0

    if eigenvalues[0] > 0:
        anisotropy = float(
            1.0
            - eigenvalues[-1]
            / eigenvalues[0]
        )

    if trace < 1e-14:
        geometry_class = "point"

    elif effective_dimension < 1.5:
        geometry_class = "filament"

    elif effective_dimension < 2.5:
        geometry_class = "sheet-or-ring"

    elif (
        radial_center > 0
        and radial_width / radial_center < 0.22
    ):
        geometry_class = "shell-like-volume"

    elif anisotropy < 0.15:
        geometry_class = "isotropic-volume"

    else:
        geometry_class = "anisotropic-volume"

    positive = rho[rho > 0]

    entropy = float(
        -np.sum(positive * np.log(positive))
        / np.log(NODE_COUNT)
    )

    participation = float(
        (1.0 / np.sum(rho*rho))
        / NODE_COUNT
    )

    peak = int(np.argmax(rho))

    return {
        "geometry_class": geometry_class,
        "effective_dimension": float(
            effective_dimension
        ),
        "center": [
            float(value)
            for value in center
        ],
        "eigenvalues": [
            float(value)
            for value in eigenvalues
        ],
        "anisotropy": anisotropy,
        "radial_center": radial_center,
        "radial_width": radial_width,
        "entropy": entropy,
        "participation": participation,
        "support_1e-12": int(
            np.sum(rho > 1e-12)
        ),
        "peak_coordinate": (
            COORDS[peak].astype(int).tolist()
        ),
        "peak_energy": float(rho[peak]),
    }


def divergence_metrics(full, fractured):
    difference = np.abs(
        full - fractured
    )

    midpoint = 0.5 * (
        full + fractured
    )

    full_positive = full > 0
    fractured_positive = fractured > 0

    js = float(
        0.5
        * np.sum(
            full[full_positive]
            * np.log(
                full[full_positive]
                / midpoint[full_positive]
            )
        )
        + 0.5
        * np.sum(
            fractured[fractured_positive]
            * np.log(
                fractured[fractured_positive]
                / midpoint[fractured_positive]
            )
        )
    )

    closest = int(
        np.argmin(difference)
    )

    return {
        "L1": float(difference.sum()),
        "L2": float(
            np.linalg.norm(
                full - fractured
            )
        ),
        "Jensen_Shannon": js,
        "exact_equal_coordinates": int(
            np.sum(difference == 0)
        ),
        "near_equal_1e-12": int(
            np.sum(difference <= 1e-12)
        ),
        "closest_coordinate": (
            COORDS[closest]
            .astype(int)
            .tolist()
        ),
        "minimum_difference": float(
            difference[closest]
        ),
    }


# ============================================================
# POINT GENESIS EXPERIMENT
# ============================================================

print("=" * 76)
print("POINT GENESIS: ТОЧКА СОЗДАЁТ ГЕОМЕТРИЮ")
print("=" * 76)

print("states             :", NODE_COUNT)
print("relations 1D       :", FULL["relations_1D"],
      "->", FRACTURED["relations_1D"])
print("triads             :", FULL["triads"],
      "->", FRACTURED["triads"])
print("dt                 : %.12e" % DT)

results = []

for name, coordinate in POINTS.items():
    initial = np.zeros(
        NODE_COUNT,
        dtype=float,
    )

    initial[
        COORD_TO_NODE[coordinate]
    ] = 1.0

    full = initial.copy()
    fractured = initial.copy()

    snapshots = []

    print()
    print("-" * 76)
    print(name, coordinate)
    print("-" * 76)

    for step in range(STEPS + 1):
        if step in SNAPSHOTS:
            full_geometry = geometry_metrics(
                full
            )

            fractured_geometry = (
                geometry_metrics(fractured)
            )

            divergence = divergence_metrics(
                full,
                fractured,
            )

            snapshot = {
                "step": step,
                "full": full_geometry,
                "fractured": (
                    fractured_geometry
                ),
                "divergence": divergence,
                "mass_full": float(full.sum()),
                "mass_fractured": float(
                    fractured.sum()
                ),
            }

            snapshots.append(snapshot)

            print(
                "t=%2d | full=%-20s D=%.4f | "
                "fractured=%-20s D=%.4f | "
                "L1=%.6f equal=%d closest=%s"
                % (
                    step,
                    full_geometry[
                        "geometry_class"
                    ],
                    full_geometry[
                        "effective_dimension"
                    ],
                    fractured_geometry[
                        "geometry_class"
                    ],
                    fractured_geometry[
                        "effective_dimension"
                    ],
                    divergence["L1"],
                    divergence[
                        "exact_equal_coordinates"
                    ],
                    divergence[
                        "closest_coordinate"
                    ],
                )
            )

        if step == STEPS:
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
        "initial_coordinate": list(
            coordinate
        ),
        "snapshots": snapshots,
    })


report = {
    "experiment": (
        "Point genesis under full and "
        "fractured triad relations"
    ),
    "warning": (
        "Conservative triad-network diagnostic; "
        "not a Navier-Stokes proof."
    ),
    "solver_modified": False,
    "parameters": {
        "K": K,
        "NFFT": NFFT,
        "steps": STEPS,
        "dt": DT,
        "states": NODE_COUNT,
    },
    "networks": {
        "full_relations_1D": (
            FULL["relations_1D"]
        ),
        "fractured_relations_1D": (
            FRACTURED["relations_1D"]
        ),
        "full_triads": FULL["triads"],
        "fractured_triads": (
            FRACTURED["triads"]
        ),
    },
    "results": results,
}

output = OUT / "point_genesis.json"

output.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)

print()
print("=" * 76)
print("ГОТОВО")
print("Результат:", output)
print("=" * 76)
