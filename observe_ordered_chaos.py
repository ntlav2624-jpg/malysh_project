#!/usr/bin/env python3

import json
from collections import defaultdict
from pathlib import Path

import numpy as np


OUT = Path("experiments/ordered_chaos")
OUT.mkdir(parents=True, exist_ok=True)


def float_bins(N):
    return np.fft.fftfreq(N) * N


def integer_labels(values):
    return np.rint(values).astype(int)


def analyze_tce(N):
    cutoff = (N - 1) // 3

    raw = float_bins(N)
    mask = np.abs(raw) <= cutoff

    active_raw = raw[mask]
    active_int = integer_labels(active_raw)

    raw_by_int = {}

    for raw_value, integer_value in zip(
        active_raw,
        active_int,
    ):
        raw_by_int[int(integer_value)] = float(raw_value)

    labels = sorted(raw_by_int)
    label_set = set(labels)
    raw_set = set(raw_by_int.values())

    integer_triads = 0
    float_triads = 0

    missing_examples = []
    error_histogram = defaultdict(int)

    max_defect = 0.0

    for p in labels:
        p_raw = raw_by_int[p]

        for q in labels:
            q_raw = raw_by_int[q]

            k = p + q

            if k not in label_set:
                continue

            integer_triads += 1

            k_raw = raw_by_int[k]
            candidate = p_raw + q_raw
            defect = candidate - k_raw

            max_defect = max(
                max_defect,
                abs(defect),
            )

            if candidate in raw_set:
                float_triads += 1
            else:
                exponent_key = (
                    "zero"
                    if defect == 0.0
                    else "%+.0e" % defect
                )

                error_histogram[exponent_key] += 1

                if len(missing_examples) < 40:
                    missing_examples.append({
                        "p_int": p,
                        "q_int": q,
                        "k_int": k,
                        "p_raw": repr(p_raw),
                        "q_raw": repr(q_raw),
                        "k_raw": repr(k_raw),
                        "sum_raw": repr(candidate),
                        "defect": defect,
                    })

    one_dim_missing = integer_triads - float_triads

    expected_3d = integer_triads ** 3
    observed_3d = float_triads ** 3

    return {
        "N": N,
        "cutoff": cutoff,
        "raw_bins": [
            repr(float(x))
            for x in active_raw
        ],
        "integer_labels": labels,
        "one_dim_integer_triads": integer_triads,
        "one_dim_float_triads": float_triads,
        "one_dim_missing": one_dim_missing,
        "three_dim_integer_closure": expected_3d,
        "three_dim_float_closure": observed_3d,
        "three_dim_difference": (
            expected_3d - observed_3d
        ),
        "max_abs_defect": max_defect,
        "defect_histogram": dict(
            sorted(error_histogram.items())
        ),
        "missing_examples": missing_examples,
    }


def make_cloud(N=12, seed=7):
    rng = np.random.default_rng(seed)

    freq = np.fft.fftfreq(N) * N

    kx, ky, kz = np.meshgrid(
        freq,
        freq,
        freq,
        indexing="ij",
    )

    k2 = kx*kx + ky*ky + kz*kz
    kmag = np.sqrt(k2)
    nonzero = k2 > 0

    cutoff = (N - 1) // 3

    active = (
        (np.abs(kx) <= cutoff)
        & (np.abs(ky) <= cutoff)
        & (np.abs(kz) <= cutoff)
        & nonzero
    )

    physical = rng.normal(
        size=(3, N, N, N)
    )

    uh = np.fft.fftn(
        physical,
        axes=(1, 2, 3),
    ) / N**3

    envelope = np.exp(
        -((kmag - 2.8) / 1.15)**2
    )

    uh *= envelope

    divergence = (
        kx*uh[0]
        + ky*uh[1]
        + kz*uh[2]
    )

    for component, kval in enumerate(
        (kx, ky, kz)
    ):
        uh[component, nonzero] -= (
            kval[nonzero]
            * divergence[nonzero]
            / k2[nonzero]
        )

        uh[component, ~nonzero] = 0

    uh *= active

    energy = (
        0.5
        * np.sum(np.abs(uh)**2)
    )

    uh /= np.sqrt(energy)

    geometry = {
        "N": N,
        "kx": kx,
        "ky": ky,
        "kz": kz,
        "k2": k2,
        "kmag": kmag,
        "active": active,
        "nonzero": nonzero,
    }

    return uh, geometry


def cloud_geometry(uh, g):
    rho = (
        0.5
        * np.sum(np.abs(uh)**2, axis=0)
    )

    selector = g["active"]

    weights = rho[selector]

    points = np.column_stack([
        g["kx"][selector],
        g["ky"][selector],
        g["kz"][selector],
    ])

    total = float(np.sum(weights))

    probability = weights / total

    center_vector = np.sum(
        points * probability[:, None],
        axis=0,
    )

    centered = points - center_vector

    covariance = (
        centered.T
        @ (
            centered
            * probability[:, None]
        )
    )

    eigenvalues = np.linalg.eigvalsh(
        covariance
    )[::-1]

    eigenvalues = np.maximum(
        eigenvalues,
        0.0,
    )

    trace = float(
        np.sum(eigenvalues)
    )

    if trace > 0:
        shape_fractions = (
            eigenvalues / trace
        )
    else:
        shape_fractions = np.zeros(3)

    participation = float(
        1.0 / np.sum(probability**2)
    )

    nonzero_probability = probability[
        probability > 0
    ]

    entropy = float(
        -np.sum(
            nonzero_probability
            * np.log(nonzero_probability)
        )
    )

    entropy_normalized = float(
        entropy / np.log(len(probability))
    )

    radial_center = float(
        np.sum(
            g["kmag"][selector]
            * probability
        )
    )

    radial_width = float(
        np.sqrt(
            np.sum(
                (
                    g["kmag"][selector]
                    - radial_center
                )**2
                * probability
            )
        )
    )

    shell_index = np.floor(
        g["kmag"][selector]
    ).astype(int)

    shell_energy = defaultdict(float)

    for shell, value in zip(
        shell_index,
        probability,
    ):
        shell_energy[int(shell)] += float(value)

    anisotropy = 0.0

    if eigenvalues[0] > 0:
        anisotropy = float(
            1.0
            - eigenvalues[-1]
            / eigenvalues[0]
        )

    if shape_fractions[1] < 0.12:
        geometry_name = "filament-like"
    elif shape_fractions[2] < 0.12:
        geometry_name = "sheet-like"
    elif anisotropy < 0.15:
        geometry_name = "nearly isotropic volume"
    else:
        geometry_name = "anisotropic volume"

    return {
        "states": int(len(weights)),
        "total_energy": total,
        "center_vector": [
            float(x)
            for x in center_vector
        ],
        "radial_center": radial_center,
        "radial_width": radial_width,
        "covariance_eigenvalues": [
            float(x)
            for x in eigenvalues
        ],
        "shape_fractions": [
            float(x)
            for x in shape_fractions
        ],
        "anisotropy": anisotropy,
        "geometry_class": geometry_name,
        "participation_number": participation,
        "participation_fraction": (
            participation / len(weights)
        ),
        "entropy": entropy,
        "entropy_normalized": (
            entropy_normalized
        ),
        "shell_energy_fraction": {
            str(k): v
            for k, v in sorted(
                shell_energy.items()
            )
        },
    }


def print_tce(result):
    print()
    print("=" * 72)
    print(
        "TCE N=%d cutoff=%d"
        % (
            result["N"],
            result["cutoff"],
        )
    )
    print("=" * 72)

    print(
        "1D integer closure :",
        result["one_dim_integer_triads"],
    )

    print(
        "1D float closure   :",
        result["one_dim_float_triads"],
    )

    print(
        "1D missing         :",
        result["one_dim_missing"],
    )

    print(
        "3D closure loss    :",
        result["three_dim_difference"],
    )

    print(
        "max abs defect     : %.18e"
        % result["max_abs_defect"]
    )

    print(
        "defect histogram   :",
        result["defect_histogram"],
    )

    if result["missing_examples"]:
        print("examples:")

        for example in (
            result["missing_examples"][:8]
        ):
            print(
                "  %d + %d = %d | "
                "%s + %s -> %s | "
                "target=%s | defect=%+.18e"
                % (
                    example["p_int"],
                    example["q_int"],
                    example["k_int"],
                    example["p_raw"],
                    example["q_raw"],
                    example["sum_raw"],
                    example["k_raw"],
                    example["defect"],
                )
            )


def print_cloud(result):
    print()
    print("=" * 72)
    print("CLOUD AS ORDERED CHAOS")
    print("=" * 72)

    print(
        "states                 :",
        result["states"],
    )

    print(
        "geometry class         :",
        result["geometry_class"],
    )

    print(
        "center vector          :",
        result["center_vector"],
    )

    print(
        "radial center          : %.8f"
        % result["radial_center"]
    )

    print(
        "radial width           : %.8f"
        % result["radial_width"]
    )

    print(
        "covariance eigenvalues :",
        result[
            "covariance_eigenvalues"
        ],
    )

    print(
        "shape fractions        :",
        result["shape_fractions"],
    )

    print(
        "anisotropy             : %.8f"
        % result["anisotropy"]
    )

    print(
        "participation fraction : %.8f"
        % result[
            "participation_fraction"
        ]
    )

    print(
        "normalized entropy     : %.8f"
        % result["entropy_normalized"]
    )

    print(
        "shell energy           :",
        result["shell_energy_fraction"],
    )


def main():
    tce_results = [
        analyze_tce(N)
        for N in (17, 24, 27, 30)
    ]

    uh, geometry = make_cloud(
        N=12,
        seed=7,
    )

    cloud_result = cloud_geometry(
        uh,
        geometry,
    )

    report = {
        "experiment": (
            "TCE anatomy and ordered-chaos "
            "cloud geometry"
        ),
        "solver_modified": False,
        "tce": tce_results,
        "cloud": cloud_result,
        "interpretation_guard": (
            "Geometry labels are classifications "
            "of covariance eigenvalue ratios, "
            "not assumed physical objects."
        ),
    }

    output = OUT / "ordered_chaos.json"

    output.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    for result in tce_results:
        print_tce(result)

    print_cloud(cloud_result)

    print()
    print("Saved:", output)


if __name__ == "__main__":
    main()
