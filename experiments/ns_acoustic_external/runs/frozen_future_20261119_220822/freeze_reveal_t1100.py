import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path.home() / "malysh_project"
EXP = ROOT / "experiments/ns_acoustic_external"
RUN = Path(__file__).resolve().parent

SOURCE_RUN = sorted(
    EXP.glob("runs/flux_time_*")
)[-1]

SOURCE_JSON = SOURCE_RUN / "ns3d_flux_time.json"
SOURCE_FIELDS = SOURCE_RUN / "ns3d_flux_time_fields.npz"

FREEZE_FILE = RUN / "prediction_t1100_frozen.json"
HASH_FILE = RUN / "prediction_t1100_frozen.sha256"
REVEAL_FILE = RUN / "reveal_t1100.json"
FUTURE_FIELDS = RUN / "fields_t1100.npz"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(value):
    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return text.encode("utf-8")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def relative_error(predicted, actual):
    p = np.asarray(predicted, dtype=float)
    a = np.asarray(actual, dtype=float)

    return float(
        np.linalg.norm(p - a)
        / (np.linalg.norm(a) + 1e-30)
    )


def linear(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)

    return 2.0 * b - a


def damped(a, b, coefficient=0.75):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)

    return b + coefficient * (b - a)


def quadratic(a, b, c):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    c = np.asarray(c, dtype=float)

    return 3.0 * c - 3.0 * b + a


def candidate_from_history(method, s1, s2, s3):
    if method == "C1_LINEAR":
        flux = linear(
            s2["cumulative_flux"],
            s3["cumulative_flux"],
        )

        energy = linear(
            s2["energy_spectrum"],
            s3["energy_spectrum"],
        )

    elif method == "C2_DAMPED":
        flux = damped(
            s2["cumulative_flux"],
            s3["cumulative_flux"],
            0.75,
        )

        energy = damped(
            s2["energy_spectrum"],
            s3["energy_spectrum"],
            0.75,
        )

    elif method == "C3_QUADRATIC":
        flux = quadratic(
            s1["cumulative_flux"],
            s2["cumulative_flux"],
            s3["cumulative_flux"],
        )

        energy = quadratic(
            s1["energy_spectrum"],
            s2["energy_spectrum"],
            s3["energy_spectrum"],
        )

    else:
        raise ValueError(method)

    energy = np.maximum(0.0, energy)

    flux_peak_shell = int(
        np.argmax(np.abs(flux))
    )

    weighted = (
        np.arange(len(energy), dtype=float) ** 4
    ) * energy

    k4_peak_shell = int(
        np.argmax(weighted)
    )

    return {
        "method": method,

        "cumulative_flux":
            flux.tolist(),

        "energy_spectrum":
            energy.tolist(),

        "flux_peak_shell":
            flux_peak_shell,

        "flux_peak_value":
            float(flux[flux_peak_shell]),

        "k4_weighted_peak_shell":
            k4_peak_shell,
    }


def backtest_methods(snapshots):
    methods = [
        "C1_LINEAR",
        "C2_DAMPED",
        "C3_QUADRATIC",
    ]

    results = {
        method: []
        for method in methods
    }

    # Для каждого уже известного target используются
    # исключительно три более ранних снимка.
    for target_index in range(3, len(snapshots)):
        s1 = snapshots[target_index - 3]
        s2 = snapshots[target_index - 2]
        s3 = snapshots[target_index - 1]
        actual = snapshots[target_index]

        for method in methods:
            predicted = candidate_from_history(
                method,
                s1,
                s2,
                s3,
            )

            results[method].append({
                "target_step":
                    int(actual["step"]),

                "flux_relative_error":
                    relative_error(
                        predicted["cumulative_flux"],
                        actual["cumulative_flux"],
                    ),

                "energy_relative_error":
                    relative_error(
                        predicted["energy_spectrum"],
                        actual["energy_spectrum"],
                    ),

                "peak_shell_error":
                    abs(
                        predicted["flux_peak_shell"]
                        - int(
                            actual["flux_peak_shell"]
                        )
                    ),
            })

    summary = {}

    for method, records in results.items():
        summary[method] = {
            "test_count": len(records),

            "mean_flux_error":
                float(np.mean([
                    item["flux_relative_error"]
                    for item in records
                ])),

            "mean_energy_error":
                float(np.mean([
                    item["energy_relative_error"]
                    for item in records
                ])),

            "mean_peak_shell_error":
                float(np.mean([
                    item["peak_shell_error"]
                    for item in records
                ])),

            "records": records,
        }

    selected = min(
        methods,
        key=lambda name: (
            summary[name]["mean_flux_error"],
            summary[name]["mean_energy_error"],
            summary[name]["mean_peak_shell_error"],
        ),
    )

    return selected, summary


def find_latest_malysh_status():
    files = sorted(
        EXP.glob(
            "sync_reports/*/malysh_semantic_forecast.json"
        )
    )

    if not files:
        return {
            "available": False,
            "status": None,
            "selection": None,
            "decision_authority": False,
        }

    path = files[-1]
    content = load_json(path)

    return {
        "available": True,
        "source": str(path),
        "status":
            content.get("malysh_status"),

        "selection":
            content.get("explicit_selection"),

        "selection_status":
            content.get("selection_status"),

        "decision_authority":
            False,

        "interpretation": (
            "Malysh observation is preserved, "
            "but the external gate does not attribute "
            "its own method selection to Malysh."
        ),
    }


def freeze():
    if FREEZE_FILE.exists() or HASH_FILE.exists():
        raise SystemExit(
            "[FAIL] Frozen prediction already exists"
        )

    packet = load_json(SOURCE_JSON)

    snapshots = packet["spectral_snapshots"]

    if len(snapshots) < 4:
        raise SystemExit(
            "[FAIL] Insufficient spectral history"
        )

    last = snapshots[-1]

    if int(last["step"]) != 500:
        raise SystemExit(
            "[FAIL] Expected source step 500"
        )

    selected, backtest = backtest_methods(
        snapshots
    )

    s1 = snapshots[-3]
    s2 = snapshots[-2]
    s3 = snapshots[-1]

    candidates = {}

    for method in [
        "C1_LINEAR",
        "C2_DAMPED",
        "C3_QUADRATIC",
    ]:
        candidates[method] = candidate_from_history(
            method,
            s1,
            s2,
            s3,
        )

    selected_prediction = candidates[selected]

    freeze_packet = {
        "schema":
            "malysh.ns3d-frozen-future.v1",

        "phase":
            "FROZEN_BEFORE_FUTURE_CALCULATION",

        "source": {
            "run": str(SOURCE_RUN),
            "json": str(SOURCE_JSON),
            "fields": str(SOURCE_FIELDS),
            "source_step": 500,
            "source_time": 1.0,
        },

        "target": {
            "step": 550,
            "time": 1.1,
        },

        "malysh_observation":
            find_latest_malysh_status(),

        "external_prediction_gate": {
            "role": (
                "External scientific recommendation only. "
                "Not an organ and not a decision by Malysh."
            ),

            "selection_rule": (
                "Lowest mean historical flux error; "
                "energy and peak-shell errors are tie-breakers."
            ),

            "selected_method":
                selected,

            "backtest":
                backtest,
        },

        "all_candidates":
            candidates,

        "frozen_selected_prediction":
            selected_prediction,

        "invariants": {
            "future_step_not_computed":
                True,

            "hidden_future_not_in_input":
                True,

            "malysh_source_unchanged":
                True,

            "gate_external_to_malysh":
                True,

            "selection_not_attributed_to_malysh":
                True,
        },
    }

    data = canonical_bytes(freeze_packet)
    digest = sha256_bytes(data)

    FREEZE_FILE.write_bytes(data)
    HASH_FILE.write_text(
        digest + "  " + FREEZE_FILE.name + "\n",
        encoding="utf-8",
    )

    print("============================================================")
    print(" PREDICTION FROZEN")
    print("============================================================")
    print("Selected method:", selected)

    for method, result in backtest.items():
        print(
            method,
            "mean_flux_error=",
            f'{result["mean_flux_error"]:.12e}',
            "mean_energy_error=",
            f'{result["mean_energy_error"]:.12e}',
        )

    print()
    print("Target step: 550")
    print("Target time: 1.1")
    print("SHA256:", digest)
    print("Frozen file:", FREEZE_FILE)
    print()

    print(
        "[PASS] Prediction fixed before future calculation"
    )


def setup_solver():
    source = load_json(SOURCE_JSON)
    parameters = source["parameters"]

    fields = np.load(SOURCE_FIELDS)

    U = np.asarray(
        fields["U"],
        dtype=np.complex128,
    )

    V = np.asarray(
        fields["V"],
        dtype=np.complex128,
    )

    W = np.asarray(
        fields["W"],
        dtype=np.complex128,
    )

    N = int(parameters["N"])
    L = float(parameters["L"])
    NU = float(parameters["nu"])
    DT = float(parameters["dt"])

    dx = L / N

    k_axis = (
        np.fft.fftfreq(N, d=dx)
        * 2.0
        * np.pi
    )

    KX, KY, KZ = np.meshgrid(
        k_axis,
        k_axis,
        k_axis,
        indexing="ij",
    )

    K2 = KX**2 + KY**2 + KZ**2
    KMAG = np.sqrt(K2)

    K2_SAFE = K2.copy()
    K2_SAFE[0, 0, 0] = 1.0

    cutoff = N // 3

    DEALIAS = (
        (np.abs(KX) <= cutoff)
        & (np.abs(KY) <= cutoff)
        & (np.abs(KZ) <= cutoff)
    )

    MAX_SHELL = int(
        np.floor(
            np.max(KMAG[DEALIAS])
        )
    )

    def project(A, B, C):
        dot = KX * A + KY * B + KZ * C

        A2 = A - KX * dot / K2_SAFE
        B2 = B - KY * dot / K2_SAFE
        C2 = C - KZ * dot / K2_SAFE

        A2[0, 0, 0] = 0.0
        B2[0, 0, 0] = 0.0
        C2[0, 0, 0] = 0.0

        return A2, B2, C2

    def nonlinear(A, B, C):
        u = np.fft.ifftn(A).real
        v = np.fft.ifftn(B).real
        w = np.fft.ifftn(C).real

        du_dx = np.fft.ifftn(
            1j * KX * A
        ).real

        du_dy = np.fft.ifftn(
            1j * KY * A
        ).real

        du_dz = np.fft.ifftn(
            1j * KZ * A
        ).real

        dv_dx = np.fft.ifftn(
            1j * KX * B
        ).real

        dv_dy = np.fft.ifftn(
            1j * KY * B
        ).real

        dv_dz = np.fft.ifftn(
            1j * KZ * B
        ).real

        dw_dx = np.fft.ifftn(
            1j * KX * C
        ).real

        dw_dy = np.fft.ifftn(
            1j * KY * C
        ).real

        dw_dz = np.fft.ifftn(
            1j * KZ * C
        ).real

        cu = (
            u * du_dx
            + v * du_dy
            + w * du_dz
        )

        cv = (
            u * dv_dx
            + v * dv_dy
            + w * dv_dz
        )

        cw = (
            u * dw_dx
            + v * dw_dy
            + w * dw_dz
        )

        CA = np.fft.fftn(cu) * DEALIAS
        CB = np.fft.fftn(cv) * DEALIAS
        CC = np.fft.fftn(cw) * DEALIAS

        CA, CB, CC = project(
            CA,
            CB,
            CC,
        )

        return -CA, -CB, -CC

    def rhs(A, B, C):
        NA, NB, NC = nonlinear(A, B, C)

        return (
            NA - NU * K2 * A,
            NB - NU * K2 * B,
            NC - NU * K2 * C,
        )

    def rk2(A, B, C):
        k1a, k1b, k1c = rhs(A, B, C)

        Am = A + 0.5 * DT * k1a
        Bm = B + 0.5 * DT * k1b
        Cm = C + 0.5 * DT * k1c

        Am, Bm, Cm = project(
            Am,
            Bm,
            Cm,
        )

        k2a, k2b, k2c = rhs(
            Am,
            Bm,
            Cm,
        )

        A2 = (A + DT * k2a) * DEALIAS
        B2 = (B + DT * k2b) * DEALIAS
        C2 = (C + DT * k2c) * DEALIAS

        return project(A2, B2, C2)

    def shell_sum(field):
        result = np.zeros(
            MAX_SHELL + 1,
            dtype=float,
        )

        for shell in range(
            MAX_SHELL + 1
        ):
            mask = (
                (KMAG >= shell)
                & (KMAG < shell + 1)
                & DEALIAS
            )

            result[shell] = float(
                np.sum(field[mask])
            )

        return result

    def snapshot(A, B, C):
        NA, NB, NC = nonlinear(A, B, C)

        normalization = float(N**6)

        energy_mode = (
            np.abs(A)**2
            + np.abs(B)**2
            + np.abs(C)**2
        ) / (2.0 * normalization)

        transfer_mode = np.real(
            np.conj(A) * NA
            + np.conj(B) * NB
            + np.conj(C) * NC
        ) / normalization

        energy = shell_sum(energy_mode)
        transfer = shell_sum(
            transfer_mode
        )

        flux = -np.cumsum(transfer)

        flux_peak_shell = int(
            np.argmax(np.abs(flux))
        )

        weighted = (
            np.arange(
                len(energy),
                dtype=float,
            ) ** 4
        ) * energy

        return {
            "step": 550,
            "time": 1.1,

            "energy_spectrum":
                energy.tolist(),

            "nonlinear_transfer":
                transfer.tolist(),

            "cumulative_flux":
                flux.tolist(),

            "flux_peak_shell":
                flux_peak_shell,

            "flux_peak_value":
                float(
                    flux[flux_peak_shell]
                ),

            "k4_weighted_peak_shell":
                int(np.argmax(weighted)),

            "nonlinear_global_sum":
                float(np.sum(transfer)),
        }

    return (
        U,
        V,
        W,
        DT,
        rk2,
        snapshot,
    )


def reveal():
    if not FREEZE_FILE.exists():
        raise SystemExit(
            "[FAIL] Frozen prediction missing"
        )

    if not HASH_FILE.exists():
        raise SystemExit(
            "[FAIL] Frozen hash missing"
        )

    frozen_data = FREEZE_FILE.read_bytes()
    actual_hash = sha256_bytes(frozen_data)

    expected_hash = (
        HASH_FILE
        .read_text(encoding="utf-8")
        .split()[0]
    )

    if actual_hash != expected_hash:
        raise SystemExit(
            "[FAIL] Frozen prediction hash mismatch"
        )

    frozen = json.loads(
        frozen_data.decode("utf-8")
    )

    U, V, W, DT, rk2, snapshot = (
        setup_solver()
    )

    steps_to_advance = 50

    for local_step in range(
        1,
        steps_to_advance + 1,
    ):
        U, V, W = rk2(U, V, W)

        if local_step % 10 == 0:
            print(
                f"[FUTURE {local_step:02d}/50] "
                f"t={1.0 + local_step * DT:.3f}"
            )

    actual = snapshot(U, V, W)

    candidates = frozen["all_candidates"]

    scores = {}

    for method, prediction in candidates.items():
        scores[method] = {
            "flux_relative_error":
                relative_error(
                    prediction[
                        "cumulative_flux"
                    ],
                    actual[
                        "cumulative_flux"
                    ],
                ),

            "energy_relative_error":
                relative_error(
                    prediction[
                        "energy_spectrum"
                    ],
                    actual[
                        "energy_spectrum"
                    ],
                ),

            "peak_shell_error":
                abs(
                    int(
                        prediction[
                            "flux_peak_shell"
                        ]
                    )
                    - int(
                        actual[
                            "flux_peak_shell"
                        ]
                    )
                ),

            "k4_peak_shell_error":
                abs(
                    int(
                        prediction[
                            "k4_weighted_peak_shell"
                        ]
                    )
                    - int(
                        actual[
                            "k4_weighted_peak_shell"
                        ]
                    )
                ),
        }

    selected_method = frozen[
        "external_prediction_gate"
    ]["selected_method"]

    selected_score = scores[
        selected_method
    ]

    best_actual_method = min(
        scores,
        key=lambda name: (
            scores[name][
                "flux_relative_error"
            ],
            scores[name][
                "energy_relative_error"
            ],
        ),
    )

    reveal_packet = {
        "schema":
            "malysh.ns3d-frozen-reveal.v1",

        "frozen_prediction_sha256":
            actual_hash,

        "hash_verified":
            True,

        "source_step":
            500,

        "target_step":
            550,

        "actual_future":
            actual,

        "selected_method":
            selected_method,

        "selected_score":
            selected_score,

        "all_scores":
            scores,

        "best_actual_method":
            best_actual_method,

        "selection_was_best":
            selected_method
            == best_actual_method,

        "nonlinear_conservation_pass":
            abs(
                actual[
                    "nonlinear_global_sum"
                ]
            ) < 1e-10,

        "interpretation": (
            "The external gate selected a method "
            "using only historical backtests. "
            "This selection is not attributed to Malysh."
        ),
    }

    REVEAL_FILE.write_text(
        json.dumps(
            reveal_packet,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    np.savez_compressed(
        FUTURE_FIELDS,
        U=U,
        V=V,
        W=W,
        u=np.fft.ifftn(U).real,
        v=np.fft.ifftn(V).real,
        w=np.fft.ifftn(W).real,
    )

    print()
    print("============================================================")
    print(" FUTURE REVEALED AND SCORED")
    print("============================================================")
    print("Frozen SHA256:", actual_hash)
    print("Selected method:", selected_method)

    for method, score in scores.items():
        print(
            method,
            "flux_error=",
            f'{score["flux_relative_error"]:.12e}',
            "energy_error=",
            f'{score["energy_relative_error"]:.12e}',
            "peak_error=",
            score["peak_shell_error"],
            "k4_error=",
            score["k4_peak_shell_error"],
        )

    print()
    print(
        "Best actual method:",
        best_actual_method,
    )

    print(
        "Gate selection was best:",
        selected_method
        == best_actual_method,
    )

    print(
        "Selected flux error:",
        f'{selected_score["flux_relative_error"]:.12e}',
    )

    print(
        "Selected energy error:",
        f'{selected_score["energy_relative_error"]:.12e}',
    )

    print(
        "Actual flux peak shell:",
        actual["flux_peak_shell"],
    )

    print(
        "Actual flux peak value:",
        f'{actual["flux_peak_value"]:.12e}',
    )

    print(
        "Actual k4 peak shell:",
        actual["k4_weighted_peak_shell"],
    )

    print(
        "Nonlinear conservation:",
        abs(
            actual["nonlinear_global_sum"]
        ) < 1e-10,
    )

    print("Reveal file:", REVEAL_FILE)


def status():
    print("RUN:", RUN)
    print(
        "freeze_exists:",
        FREEZE_FILE.exists(),
    )

    print(
        "hash_exists:",
        HASH_FILE.exists(),
    )

    print(
        "reveal_exists:",
        REVEAL_FILE.exists(),
    )

    if FREEZE_FILE.exists():
        data = FREEZE_FILE.read_bytes()

        print(
            "current_freeze_sha256:",
            sha256_bytes(data),
        )


parser = argparse.ArgumentParser()

parser.add_argument(
    "mode",
    choices=[
        "freeze",
        "reveal",
        "status",
    ],
)

args = parser.parse_args()

if args.mode == "freeze":
    freeze()

elif args.mode == "reveal":
    reveal()

else:
    status()
