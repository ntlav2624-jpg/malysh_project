#!/usr/bin/env python3

import json
from pathlib import Path

import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

K = 5
NFFT = 17

STEPS = 40
ALPHA = 0.20

SNAPSHOT_STEPS = {
    0,
    10,
    20,
    40,
}

GEOMETRIES = (
    "shell",
    "filament",
    "sheet",
    "ring",
    "volume",
    "double_helix",
)

OUT = Path(
    "experiments/structural_amplification_geometry"
)

OUT.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# STATE SPACE
# ============================================================

VALUES = np.arange(
    -K,
    K + 1,
    dtype=int,
)

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


def flat_index(x, y, z):
    return (
        (
            (x + K) * SIDE
            + (y + K)
        )
        * SIDE
        + (z + K)
    )


FLAT_TO_NODE = np.full(
    SIDE ** 3,
    -1,
    dtype=np.int32,
)

for node, coordinate in enumerate(COORDS):
    x, y, z = coordinate

    FLAT_TO_NODE[
        flat_index(
            int(x),
            int(y),
            int(z),
        )
    ] = node


ZERO_FLAT = flat_index(0, 0, 0)


# ============================================================
# ONE-DIMENSIONAL RELATION ALGEBRAS
# ============================================================

def build_one_dimensional_relations(observer):
    raw = (
        np.fft.fftfreq(NFFT)
        * NFFT
    )

    mask = np.abs(raw) <= K
    active_raw = raw[mask]

    raw_by_integer = {
        int(round(float(value))): float(value)
        for value in active_raw
    }

    raw_set = set(
        raw_by_integer.values()
    )

    relations = []
    missing = []

    for p in VALUES:
        for q in VALUES:
            target = int(p + q)

            if target < -K or target > K:
                continue

            mathematical_relation = (
                int(p),
                int(q),
                target,
            )

            if observer == "integer":
                relations.append(
                    mathematical_relation
                )
                continue

            p_raw = raw_by_integer[int(p)]
            q_raw = raw_by_integer[int(q)]
            k_raw = raw_by_integer[target]

            candidate = p_raw + q_raw
            defect = candidate - k_raw

            if candidate in raw_set:
                relations.append(
                    mathematical_relation
                )
            else:
                missing.append({
                    "p": int(p),
                    "q": int(q),
                    "k": target,
                    "p_raw": repr(p_raw),
                    "q_raw": repr(q_raw),
                    "sum_raw": repr(candidate),
                    "k_raw": repr(k_raw),
                    "defect": float(defect),
                })

    return (
        np.array(
            relations,
            dtype=np.int16,
        ),
        missing,
    )


# ============================================================
# THREE-DIMENSIONAL TRIAD NETWORK
# ============================================================

def build_three_dimensional_triads(observer):
    one_dimensional, missing = (
        build_one_dimensional_relations(
            observer
        )
    )

    relation_count = len(
        one_dimensional
    )

    first = np.repeat(
        np.arange(relation_count),
        relation_count ** 2,
    )

    second = np.tile(
        np.repeat(
            np.arange(relation_count),
            relation_count,
        ),
        relation_count,
    )

    third = np.tile(
        np.arange(relation_count),
        relation_count ** 2,
    )

    p_coordinates = np.column_stack([
        one_dimensional[first, 0],
        one_dimensional[second, 0],
        one_dimensional[third, 0],
    ])

    q_coordinates = np.column_stack([
        one_dimensional[first, 1],
        one_dimensional[second, 1],
        one_dimensional[third, 1],
    ])

    k_coordinates = np.column_stack([
        one_dimensional[first, 2],
        one_dimensional[second, 2],
        one_dimensional[third, 2],
    ])

    p_flat = (
        (
            (p_coordinates[:, 0] + K)
            * SIDE
            + (p_coordinates[:, 1] + K)
        )
        * SIDE
        + (p_coordinates[:, 2] + K)
    )

    q_flat = (
        (
            (q_coordinates[:, 0] + K)
            * SIDE
            + (q_coordinates[:, 1] + K)
        )
        * SIDE
        + (q_coordinates[:, 2] + K)
    )

    k_flat = (
        (
            (k_coordinates[:, 0] + K)
            * SIDE
            + (k_coordinates[:, 1] + K)
        )
        * SIDE
        + (k_coordinates[:, 2] + K)
    )

    keep = (
        (p_flat != ZERO_FLAT)
        & (q_flat != ZERO_FLAT)
        & (k_flat != ZERO_FLAT)
    )

    p_nodes = FLAT_TO_NODE[
        p_flat[keep]
    ]

    q_nodes = FLAT_TO_NODE[
        q_flat[keep]
    ]

    k_nodes = FLAT_TO_NODE[
        k_flat[keep]
    ]

    if (
        np.any(p_nodes < 0)
        or np.any(q_nodes < 0)
        or np.any(k_nodes < 0)
    ):
        raise RuntimeError(
            "Invalid node mapping detected"
        )

    return {
        "observer": observer,
        "one_dimensional_relations": (
            relation_count
        ),
        "missing_one_dimensional": missing,
        "p": p_nodes,
        "q": q_nodes,
        "k": k_nodes,
        "triad_count": len(p_nodes),
    }


# ============================================================
# INITIAL GEOMETRIES
# ============================================================

def symmetrize(weights):
    lookup = {
        tuple(
            int(value)
            for value in coordinate
        ): index
        for index, coordinate
        in enumerate(COORDS)
    }

    inverted = np.empty_like(
        weights
    )

    for index, coordinate in enumerate(
        COORDS
    ):
        opposite = tuple(
            int(-value)
            for value in coordinate
        )

        inverted[index] = weights[
            lookup[opposite]
        ]

    return 0.5 * (
        weights + inverted
    )


def make_initial_geometry(name):
    x = COORDS[:, 0].astype(float)
    y = COORDS[:, 1].astype(float)
    z = COORDS[:, 2].astype(float)

    radius = np.sqrt(
        x*x + y*y + z*z
    )

    cylindrical_radius = np.sqrt(
        x*x + y*y
    )

    if name == "shell":
        weights = np.exp(
            -(
                (radius - 3.5)
                / 0.65
            )**2
        )

    elif name == "filament":
        weights = (
            np.exp(
                -(y*y + z*z)
                / 1.2
            )
            * np.exp(
                -(x / 5.0)**8
            )
        )

    elif name == "sheet":
        weights = (
            np.exp(
                -(z*z)
                / 0.8
            )
            * np.exp(
                -(
                    (
                        cylindrical_radius
                        - 3.0
                    )
                    / 2.0
                )**4
            )
        )

    elif name == "ring":
        weights = np.exp(
            -(
                (
                    cylindrical_radius
                    - 3.5
                )
                / 0.55
            )**2
            - (z / 0.7)**2
        )

    elif name == "volume":
        weights = np.exp(
            -(
                x*x / 14.0
                + y*y / 10.0
                + z*z / 8.0
            )
        )

    elif name == "double_helix":
        parameter = np.linspace(
            -np.pi,
            np.pi,
            241,
        )

        curve = np.column_stack([
            3.0 * np.cos(parameter),
            3.0 * np.sin(parameter),
            1.4 * parameter,
        ])

        distance_squared = (
            (
                COORDS[:, None, :]
                - curve[None, :, :]
            )**2
        ).sum(axis=2)

        minimum_distance = (
            distance_squared.min(axis=1)
        )

        weights = np.exp(
            -minimum_distance / 0.7
        )

        weights = symmetrize(
            weights
        )

    else:
        raise ValueError(
            "Unknown geometry: %s"
            % name
        )

    weights = (
        weights.astype(float)
        + 1e-15
    )

    weights /= weights.sum()

    return weights


# ============================================================
# CONSERVATIVE TRIAD TRANSFER
# ============================================================

def node_degrees(network):
    return np.bincount(
        np.concatenate([
            network["p"],
            network["q"],
            network["k"],
        ]),
        minlength=NODE_COUNT,
    )


def transfer_step(
    rho,
    network,
    dt,
):
    p = network["p"]
    q = network["q"]
    k = network["k"]

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

    result = rho + dt * delta

    minimum = float(
        result.min()
    )

    if minimum < -1e-13:
        raise RuntimeError(
            "Positivity lost: %.18e"
            % minimum
        )

    result = np.maximum(
        result,
        0.0,
    )

    mass = float(
        result.sum()
    )

    result /= mass

    return result


# ============================================================
# GEOMETRIC AND INFORMATION METRICS
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
        @ (
            centered
            * rho[:, None]
        )
    )

    eigenvalues = np.linalg.eigvalsh(
        covariance
    )[::-1]

    eigenvalues = np.maximum(
        eigenvalues,
        0.0,
    )

    eigen_sum = float(
        eigenvalues.sum()
    )

    if eigen_sum > 0:
        shape = (
            eigenvalues / eigen_sum
        )
    else:
        shape = np.zeros(3)

    radial = np.linalg.norm(
        points,
        axis=1,
    )

    radial_center = float(
        radial @ rho
    )

    radial_width = float(
        np.sqrt(
            (
                (
                    radial
                    - radial_center
                )**2
            )
            @ rho
        )
    )

    entropy = float(
        -np.sum(
            rho * np.log(rho)
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

    anisotropy = 0.0

    if eigenvalues[0] > 0:
        anisotropy = float(
            1.0
            - eigenvalues[-1]
            / eigenvalues[0]
        )

    if shape[1] < 0.12:
        geometry_class = "filament-like"
    elif shape[2] < 0.12:
        geometry_class = "sheet-like"
    elif anisotropy < 0.15:
        geometry_class = (
            "nearly-isotropic-volume"
        )
    else:
        geometry_class = (
            "anisotropic-volume"
        )

    shell_energy = {}

    shell_labels = np.floor(
        radial
    ).astype(int)

    for shell in sorted(
        set(shell_labels.tolist())
    ):
        mask = shell_labels == shell

        shell_energy[str(shell)] = float(
            rho[mask].sum()
        )

    return {
        "center": [
            float(value)
            for value in center
        ],
        "covariance_eigenvalues": [
            float(value)
            for value in eigenvalues
        ],
        "shape_fractions": [
            float(value)
            for value in shape
        ],
        "anisotropy": anisotropy,
        "geometry_class": geometry_class,
        "radial_center": radial_center,
        "radial_width": radial_width,
        "entropy_normalized": entropy,
        "participation_fraction": (
            participation
        ),
        "shell_energy": shell_energy,
    }


def divergence_metrics(
    full,
    fractured,
):
    midpoint = 0.5 * (
        full + fractured
    )

    l1 = float(
        np.sum(
            np.abs(
                full - fractured
            )
        )
    )

    l2 = float(
        np.linalg.norm(
            full - fractured
        )
    )

    js = float(
        0.5
        * np.sum(
            full
            * np.log(
                full / midpoint
            )
        )
        + 0.5
        * np.sum(
            fractured
            * np.log(
                fractured / midpoint
            )
        )
    )

    return {
        "L1": l1,
        "L2": l2,
        "Jensen_Shannon": js,
    }


# ============================================================
# EXPERIMENT
# ============================================================

def run_geometry(
    name,
    full_network,
    fractured_network,
    dt,
):
    initial = make_initial_geometry(
        name
    )

    full = initial.copy()
    fractured = initial.copy()

    snapshots = []

    for step in range(
        STEPS + 1
    ):
        if step in SNAPSHOT_STEPS:
            snapshots.append({
                "step": step,
                "full": geometry_metrics(
                    full
                ),
                "fractured": (
                    geometry_metrics(
                        fractured
                    )
                ),
                "divergence": (
                    divergence_metrics(
                        full,
                        fractured,
                    )
                ),
                "mass_full": float(
                    full.sum()
                ),
                "mass_fractured": float(
                    fractured.sum()
                ),
            })

        if step == STEPS:
            break

        full = transfer_step(
            full,
            full_network,
            dt,
        )

        fractured = transfer_step(
            fractured,
            fractured_network,
            dt,
        )

    final = snapshots[-1]

    return {
        "geometry": name,
        "snapshots": snapshots,
        "final_L1": final[
            "divergence"
        ]["L1"],
        "final_JS": final[
            "divergence"
        ]["Jensen_Shannon"],
        "full_final_class": final[
            "full"
        ]["geometry_class"],
        "fractured_final_class": final[
            "fractured"
        ]["geometry_class"],
    }


def main():
    print("=" * 78)
    print(
        "STRUCTURAL AMPLIFICATION "
        "ACROSS GEOMETRIES"
    )
    print("=" * 78)

    full_network = (
        build_three_dimensional_triads(
            "integer"
        )
    )

    fractured_network = (
        build_three_dimensional_triads(
            "float"
        )
    )

    relation_loss = (
        1.0
        - fractured_network[
            "triad_count"
        ]
        / full_network[
            "triad_count"
        ]
    )

    full_degree = node_degrees(
        full_network
    )

    max_degree = int(
        full_degree.max()
    )

    dt = ALPHA / max_degree

    print(
        "states               :",
        NODE_COUNT,
    )

    print(
        "integer 1D relations :",
        full_network[
            "one_dimensional_relations"
        ],
    )

    print(
        "float 1D relations   :",
        fractured_network[
            "one_dimensional_relations"
        ],
    )

    print(
        "full triads          :",
        full_network["triad_count"],
    )

    print(
        "fractured triads     :",
        fractured_network[
            "triad_count"
        ],
    )

    print(
        "relation loss        : %.8f"
        % relation_loss
    )

    print(
        "max degree           :",
        max_degree,
    )

    print(
        "dt                   : %.12e"
        % dt
    )

    results = []

    for name in GEOMETRIES:
        print()
        print(
            "Running geometry:",
            name,
        )

        result = run_geometry(
            name,
            full_network,
            fractured_network,
            dt,
        )

        result[
            "amplification_L1_per_relation_loss"
        ] = (
            result["final_L1"]
            / relation_loss
        )

        results.append(result)

        print(
            "  final L1          : %.8f"
            % result["final_L1"]
        )

        print(
            "  final JS          : %.8f"
            % result["final_JS"]
        )

        print(
            "  full class        :",
            result[
                "full_final_class"
            ],
        )

        print(
            "  fractured class   :",
            result[
                "fractured_final_class"
            ],
        )

    ranking = sorted(
        results,
        key=lambda item: (
            item["final_L1"]
        ),
        reverse=True,
    )

    print()
    print("=" * 78)
    print("SENSITIVITY RANKING")
    print("=" * 78)

    for rank, result in enumerate(
        ranking,
        start=1,
    ):
        print(
            "%d. %-14s "
            "L1=%.8f JS=%.8f "
            "amplification=%.8f"
            % (
                rank,
                result["geometry"],
                result["final_L1"],
                result["final_JS"],
                result[
                    "amplification_L1_per_relation_loss"
                ],
            )
        )

    report = {
        "experiment": (
            "Structural amplification "
            "across geometric states"
        ),
        "warning": (
            "This is a conservative "
            "triad-network diagnostic model, "
            "not a Navier-Stokes proof."
        ),
        "solver_modified": False,
        "parameters": {
            "K": K,
            "NFFT": NFFT,
            "steps": STEPS,
            "alpha": ALPHA,
            "dt": dt,
            "states": NODE_COUNT,
        },
        "relations": {
            "integer_1D": full_network[
                "one_dimensional_relations"
            ],
            "float_1D": fractured_network[
                "one_dimensional_relations"
            ],
            "full_triads": full_network[
                "triad_count"
            ],
            "fractured_triads": (
                fractured_network[
                    "triad_count"
                ]
            ),
            "relation_loss_fraction": (
                relation_loss
            ),
            "missing_1D_examples": (
                fractured_network[
                    "missing_one_dimensional"
                ][:40]
            ),
        },
        "results": results,
        "ranking": [
            item["geometry"]
            for item in ranking
        ],
    }

    output = OUT / (
        "structural_amplification.json"
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


if __name__ == "__main__":
    main()
