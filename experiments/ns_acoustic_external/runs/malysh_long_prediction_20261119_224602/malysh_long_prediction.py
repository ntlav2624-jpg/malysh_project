from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path.home() / "malysh_project"
EXP = ROOT / "experiments/ns_acoustic_external"
RUN = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ============================================================
# SOURCE ARTIFACTS
# ============================================================

FLUX_RUNS = sorted(
    EXP.glob("runs/flux_time_*")
)

FUTURE_1100_RUNS = sorted(
    EXP.glob("runs/frozen_future_*")
)

BLIND_1200_RUNS = sorted(
    EXP.glob("runs/malysh_alphabet_blind_*")
)

if not FLUX_RUNS:
    raise SystemExit("[FAIL] flux_time_* not found")

if not FUTURE_1100_RUNS:
    raise SystemExit("[FAIL] frozen_future_* not found")

if not BLIND_1200_RUNS:
    raise SystemExit("[FAIL] malysh_alphabet_blind_* not found")


FLUX_RUN = FLUX_RUNS[-1]
FUTURE_1100_RUN = FUTURE_1100_RUNS[-1]
BLIND_1200_RUN = BLIND_1200_RUNS[-1]

FLUX_JSON = FLUX_RUN / "ns3d_flux_time.json"

REVEAL_1100 = (
    FUTURE_1100_RUN
    / "reveal_t1100.json"
)

FIELDS_1200 = (
    BLIND_1200_RUN
    / "fields_t1200.npz"
)

REVEAL_1200 = (
    BLIND_1200_RUN
    / "malysh_prediction_t1200_reveal.json"
)

for required in (
    FLUX_JSON,
    REVEAL_1100,
    FIELDS_1200,
    REVEAL_1200,
):
    if not required.is_file():
        raise SystemExit(
            f"[FAIL] missing source: {required}"
        )


RESULT_FILE = RUN / "long_prediction_result.json"
SUMMARY_FILE = RUN / "long_prediction_summary.txt"
FINAL_FIELDS = RUN / "fields_t2000.npz"


# ============================================================
# COMMON UTILITIES
# ============================================================

def read_json(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    ).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def relative_error(
    predicted: Any,
    actual: Any,
) -> float:
    p = np.asarray(predicted, dtype=float)
    a = np.asarray(actual, dtype=float)

    return float(
        np.linalg.norm(p - a)
        / (np.linalg.norm(a) + 1e-30)
    )


def snapshot_1100() -> dict[str, Any]:
    packet = read_json(REVEAL_1100)
    value = dict(packet["actual_future"])

    value["step"] = 550
    value["time"] = 1.1

    return value


def snapshot_1200() -> dict[str, Any]:
    packet = read_json(REVEAL_1200)
    value = dict(packet["actual_future"])

    value["step"] = 600
    value["time"] = 1.2

    return value


# ============================================================
# INITIAL HISTORY
# ============================================================

flux_packet = read_json(FLUX_JSON)

history: list[dict[str, Any]] = list(
    flux_packet["spectral_snapshots"]
)

if int(history[-1]["step"]) != 500:
    raise SystemExit(
        "[FAIL] base history must end at step 500"
    )

history.append(snapshot_1100())
history.append(snapshot_1200())

if [
    int(value["step"])
    for value in history[-3:]
] != [500, 550, 600]:
    raise SystemExit(
        "[FAIL] unexpected temporal history"
    )


# ============================================================
# SOLVER INITIALIZATION FROM t=1.2
# ============================================================

parameters = flux_packet["parameters"]

N = int(parameters["N"])
L = float(parameters["L"])
NU = float(parameters["nu"])
DT = float(parameters["dt"])

fields = np.load(FIELDS_1200)

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

if not (
    U.shape
    == V.shape
    == W.shape
    == (N, N, N)
):
    raise SystemExit(
        "[FAIL] invalid source field shape"
    )


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


# ============================================================
# SPECTRAL OPERATORS
# ============================================================

def project(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    dot = KX * A + KY * B + KZ * C

    A2 = A - KX * dot / K2_SAFE
    B2 = B - KY * dot / K2_SAFE
    C2 = C - KZ * dot / K2_SAFE

    A2[0, 0, 0] = 0.0
    B2[0, 0, 0] = 0.0
    C2[0, 0, 0] = 0.0

    return A2, B2, C2


def nonlinear(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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

    conv_u = (
        u * du_dx
        + v * du_dy
        + w * du_dz
    )

    conv_v = (
        u * dv_dx
        + v * dv_dy
        + w * dv_dz
    )

    conv_w = (
        u * dw_dx
        + v * dw_dy
        + w * dw_dz
    )

    CA = np.fft.fftn(conv_u) * DEALIAS
    CB = np.fft.fftn(conv_v) * DEALIAS
    CC = np.fft.fftn(conv_w) * DEALIAS

    CA, CB, CC = project(
        CA,
        CB,
        CC,
    )

    return -CA, -CB, -CC


def rhs(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    NA, NB, NC = nonlinear(A, B, C)

    return (
        NA - NU * K2 * A,
        NB - NU * K2 * B,
        NC - NU * K2 * C,
    )


def rk2(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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


def shell_sum(
    field: np.ndarray,
) -> np.ndarray:
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


# ============================================================
# PHYSICAL AND SPECTRAL SNAPSHOT
# ============================================================

def calculate_snapshot(
    A: np.ndarray,
    B: np.ndarray,
    C: np.ndarray,
    *,
    step: int,
    time_value: float,
) -> dict[str, Any]:
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

    viscous_mode = (
        -NU
        * K2
        * (
            np.abs(A)**2
            + np.abs(B)**2
            + np.abs(C)**2
        )
        / normalization
    )

    energy_spectrum = shell_sum(
        energy_mode
    )

    transfer_spectrum = shell_sum(
        transfer_mode
    )

    viscous_spectrum = shell_sum(
        viscous_mode
    )

    flux = -np.cumsum(
        transfer_spectrum
    )

    flux_peak_shell = int(
        np.argmax(np.abs(flux))
    )

    weighted = (
        np.arange(
            len(energy_spectrum),
            dtype=float,
        ) ** 4
    ) * energy_spectrum

    k4_peak_shell = int(
        np.argmax(weighted)
    )

    u = np.fft.ifftn(A).real
    v = np.fft.ifftn(B).real
    w = np.fft.ifftn(C).real

    div_hat = 1j * (
        KX * A
        + KY * B
        + KZ * C
    )

    divergence = np.fft.ifftn(
        div_hat
    ).real

    ox_hat = 1j * (
        KY * C
        - KZ * B
    )

    oy_hat = 1j * (
        KZ * A
        - KX * C
    )

    oz_hat = 1j * (
        KX * B
        - KY * A
    )

    ox = np.fft.ifftn(
        ox_hat
    ).real

    oy = np.fft.ifftn(
        oy_hat
    ).real

    oz = np.fft.ifftn(
        oz_hat
    ).real

    speed2 = (
        u**2
        + v**2
        + w**2
    )

    omega2 = (
        ox**2
        + oy**2
        + oz**2
    )

    energy_total = float(
        0.5 * np.mean(speed2)
    )

    enstrophy = float(
        0.5 * np.mean(omega2)
    )

    speed_max = float(
        np.sqrt(speed2).max()
    )

    cfl = float(
        speed_max * DT / dx
    )

    return {
        "step": int(step),
        "time": float(time_value),

        "energy":
            energy_total,

        "enstrophy":
            enstrophy,

        "dissipation":
            float(2.0 * NU * enstrophy),

        "div_inf":
            float(
                np.max(
                    np.abs(divergence)
                )
            ),

        "cfl":
            cfl,

        "energy_spectrum":
            energy_spectrum.tolist(),

        "nonlinear_transfer":
            transfer_spectrum.tolist(),

        "viscous_transfer":
            viscous_spectrum.tolist(),

        "cumulative_flux":
            flux.tolist(),

        "flux_peak_shell":
            flux_peak_shell,

        "flux_peak_value":
            float(
                flux[flux_peak_shell]
            ),

        "k4_weighted_peak_shell":
            k4_peak_shell,

        "nonlinear_global_sum":
            float(
                np.sum(
                    transfer_spectrum
                )
            ),
    }


# ============================================================
# MALYSH PREDICTION
# ============================================================

from malysh_system.thinking_cycle import (
    run_thinking_cycle,
)


def malysh_predict(
    visible: list[dict[str, Any]],
    target_step: int,
    target_time: float,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
]:
    old_result = {
        "source":
            "malysh_long_acoustic_alphabet_prediction",

        "semantic_context": {
            "experiment":
                "3D Taylor-Green spectral flux",

            "visible_snapshots":
                visible,

            "target_step":
                int(target_step),

            "target_time":
                float(target_time),
        },
    }

    unresolved = {
        "kind":
            "long_blind_acoustic_alphabet_forecast",

        "target_step":
            int(target_step),

        "target_time":
            float(target_time),

        "instruction": (
            "Use AcousticAlphabet as an independent observer. "
            "Do not use future physical data."
        ),

        "revisable":
            True,
    }

    numeric_data: list[int] = []

    for snapshot in visible:
        numeric_data.extend([
            int(snapshot["step"]),

            int(
                round(
                    float(snapshot["time"])
                    * 1_000_000
                )
            ),

            int(
                round(
                    float(
                        snapshot[
                            "flux_peak_value"
                        ]
                    )
                    * 1_000_000_000_000
                )
            ),

            int(
                snapshot[
                    "flux_peak_shell"
                ]
            ),

            int(
                snapshot[
                    "k4_weighted_peak_shell"
                ]
            ),
        ])

    cycle_result = run_thinking_cycle(
        data=numeric_data,
        old_result=old_result,
        unresolved=unresolved,
        root=ROOT,
    )

    alphabet = cycle_result.get(
        "acoustic_alphabet"
    )

    if not isinstance(
        alphabet,
        dict,
    ):
        raise RuntimeError(
            "AcousticAlphabet result missing"
        )

    if (
        alphabet.get(
            "decision_authority"
        )
        is not False
    ):
        raise RuntimeError(
            "observer gained decision authority"
        )

    prediction = alphabet.get(
        "prediction",
        {},
    )

    if prediction.get(
        "available"
    ) is not True:
        raise RuntimeError(
            "observer prediction unavailable"
        )

    fields = prediction.get(
        "fields",
        {},
    )

    predicted_flux = [
        float(value)
        for value in fields[
            "cumulative_flux"
        ]
    ]

    predicted_energy = [
        max(0.0, float(value))
        for value in fields[
            "energy_spectrum"
        ]
    ]

    flux_peak_shell = int(
        np.argmax(
            np.abs(
                np.asarray(
                    predicted_flux,
                    dtype=float,
                )
            )
        )
    )

    weighted = (
        np.arange(
            len(predicted_energy),
            dtype=float,
        ) ** 4
    ) * np.asarray(
        predicted_energy,
        dtype=float,
    )

    prediction_packet = {
        "cumulative_flux":
            predicted_flux,

        "energy_spectrum":
            predicted_energy,

        "flux_peak_shell":
            flux_peak_shell,

        "flux_peak_value":
            float(
                predicted_flux[
                    flux_peak_shell
                ]
            ),

        "k4_weighted_peak_shell":
            int(np.argmax(weighted)),
    }

    observer_state = {
        "decision_authority":
            alphabet[
                "decision_authority"
            ],

        "main_answer_write":
            alphabet[
                "main_answer_write"
            ],

        "winner_selection":
            alphabet[
                "winner_selection"
            ],

        "kmbp_bridge_present":
            bool(
                cycle_result
                .get("mind", {})
                .get("observations", {})
                .get(
                    "KMBP_AcousticAlphabet"
                )
            ),
    }

    return (
        prediction_packet,
        observer_state,
    )


# ============================================================
# LONG ROLLING BLIND EXPERIMENT
# ============================================================

TARGET_STEPS = list(
    range(650, 1001, 50)
)

records: list[dict[str, Any]] = []

current_step = 600
current_time = 1.2

print("============================================================")
print(" MALYSH LONG ROLLING PREDICTION")
print("============================================================")
print("Grid:", f"{N}^3")
print("Re:", parameters["Re"])
print("Initial step:", current_step)
print("Initial time:", current_time)
print("Final target step:", TARGET_STEPS[-1])
print("Final target time:", 2.0)
print("Prediction windows:", len(TARGET_STEPS))
print()


for target_step in TARGET_STEPS:
    target_time = target_step * DT

    visible = history[-3:]

    expected_visible = [
        target_step - 150,
        target_step - 100,
        target_step - 50,
    ]

    actual_visible = [
        int(item["step"])
        for item in visible
    ]

    if actual_visible != expected_visible:
        raise RuntimeError(
            "history gap: "
            f"expected {expected_visible}, "
            f"got {actual_visible}"
        )

    prediction, observer = (
        malysh_predict(
            visible,
            target_step,
            target_time,
        )
    )

    freeze_packet = {
        "schema":
            "malysh.long-acoustic-alphabet-freeze.v1",

        "visible_steps":
            actual_visible,

        "target_step":
            int(target_step),

        "target_time":
            float(target_time),

        "observer":
            observer,

        "prediction":
            prediction,

        "invariants": {
            "future_not_calculated":
                True,

            "decision_authority":
                False,

            "existing_logic_preserved":
                True,
        },
    }

    freeze_data = canonical_bytes(
        freeze_packet
    )

    freeze_hash = sha256(
        freeze_data
    )

    freeze_file = (
        RUN
        / f"freeze_{target_step}.json"
    )

    hash_file = (
        RUN
        / f"freeze_{target_step}.sha256"
    )

    freeze_file.write_bytes(
        freeze_data
    )

    hash_file.write_text(
        freeze_hash
        + "  "
        + freeze_file.name
        + "\n",
        encoding="utf-8",
    )

    print(
        f"[FREEZE {target_step}] "
        f"SHA256={freeze_hash[:16]}..."
    )

    before_hash = sha256(
        freeze_file.read_bytes()
    )

    if before_hash != freeze_hash:
        raise RuntimeError(
            "freeze changed before physics"
        )

    for local_step in range(1, 51):
        U, V, W = rk2(U, V, W)

    actual = calculate_snapshot(
        U,
        V,
        W,
        step=target_step,
        time_value=target_time,
    )

    after_hash = sha256(
        freeze_file.read_bytes()
    )

    if after_hash != freeze_hash:
        raise RuntimeError(
            "freeze changed after physics"
        )

    previous = history[-1]

    linear_flux = (
        2.0
        * np.asarray(
            previous[
                "cumulative_flux"
            ],
            dtype=float,
        )
        - np.asarray(
            history[-2][
                "cumulative_flux"
            ],
            dtype=float,
        )
    )

    linear_energy = np.maximum(
        0.0,
        2.0
        * np.asarray(
            previous[
                "energy_spectrum"
            ],
            dtype=float,
        )
        - np.asarray(
            history[-2][
                "energy_spectrum"
            ],
            dtype=float,
        ),
    )

    alphabet_flux_error = relative_error(
        prediction[
            "cumulative_flux"
        ],
        actual[
            "cumulative_flux"
        ],
    )

    alphabet_energy_error = relative_error(
        prediction[
            "energy_spectrum"
        ],
        actual[
            "energy_spectrum"
        ],
    )

    linear_flux_error = relative_error(
        linear_flux,
        actual[
            "cumulative_flux"
        ],
    )

    linear_energy_error = relative_error(
        linear_energy,
        actual[
            "energy_spectrum"
        ],
    )

    record = {
        "target_step":
            int(target_step),

        "target_time":
            float(target_time),

        "freeze_sha256":
            freeze_hash,

        "visible_steps":
            actual_visible,

        "observer":
            observer,

        "prediction":
            prediction,

        "actual":
            actual,

        "alphabet": {
            "flux_error":
                alphabet_flux_error,

            "energy_error":
                alphabet_energy_error,

            "flux_peak_error":
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

            "k4_peak_error":
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
        },

        "linear": {
            "flux_error":
                linear_flux_error,

            "energy_error":
                linear_energy_error,
        },

        "beats_linear":
            bool(
                alphabet_flux_error
                < linear_flux_error
            ),

        "nonlinear_conservation":
            bool(
                abs(
                    actual[
                        "nonlinear_global_sum"
                    ]
                ) < 1e-10
            ),

        "hash_verified_before":
            before_hash == freeze_hash,

        "hash_verified_after":
            after_hash == freeze_hash,
    }

    records.append(record)
    history.append(actual)

    checkpoint = (
        RUN
        / f"checkpoint_{target_step}.npz"
    )

    np.savez_compressed(
        checkpoint,
        U=U,
        V=V,
        W=W,
    )

    improvement = (
        (
            linear_flux_error
            - alphabet_flux_error
        )
        / (
            linear_flux_error
            + 1e-30
        )
    )

    print(
        f"[REVEAL {target_step}] "
        f"t={target_time:.1f} | "
        f"A={alphabet_flux_error:.6e} | "
        f"L={linear_flux_error:.6e} | "
        f"improve={100.0 * improvement:+.3f}% | "
        f"beat={record['beats_linear']} | "
        f"K={actual['flux_peak_shell']} | "
        f"k4={actual['k4_weighted_peak_shell']}"
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

alphabet_flux_errors = [
    item["alphabet"]["flux_error"]
    for item in records
]

linear_flux_errors = [
    item["linear"]["flux_error"]
    for item in records
]

alphabet_energy_errors = [
    item["alphabet"]["energy_error"]
    for item in records
]

linear_energy_errors = [
    item["linear"]["energy_error"]
    for item in records
]

wins = sum(
    item["beats_linear"]
    for item in records
)

all_hashes_pass = all(
    item["hash_verified_before"]
    and item["hash_verified_after"]
    for item in records
)

all_conservation_pass = all(
    item["nonlinear_conservation"]
    for item in records
)

all_authority_pass = all(
    item["observer"][
        "decision_authority"
    ] is False
    for item in records
)

mean_alphabet_flux = float(
    np.mean(
        alphabet_flux_errors
    )
)

mean_linear_flux = float(
    np.mean(
        linear_flux_errors
    )
)

mean_alphabet_energy = float(
    np.mean(
        alphabet_energy_errors
    )
)

mean_linear_energy = float(
    np.mean(
        linear_energy_errors
    )
)

overall_improvement = float(
    (
        mean_linear_flux
        - mean_alphabet_flux
    )
    / (
        mean_linear_flux
        + 1e-30
    )
)

result = {
    "schema":
        "malysh.long-acoustic-alphabet-result.v1",

    "parameters": {
        "N": N,
        "Re": parameters["Re"],
        "nu": NU,
        "dt": DT,
        "start_time": 1.2,
        "end_time": 2.0,
        "window": 0.1,
        "prediction_count":
            len(records),
    },

    "records":
        records,

    "summary": {
        "prediction_count":
            len(records),

        "alphabet_wins":
            wins,

        "alphabet_win_fraction":
            float(
                wins / len(records)
            ),

        "mean_alphabet_flux_error":
            mean_alphabet_flux,

        "mean_linear_flux_error":
            mean_linear_flux,

        "mean_alphabet_energy_error":
            mean_alphabet_energy,

        "mean_linear_energy_error":
            mean_linear_energy,

        "overall_flux_improvement":
            overall_improvement,

        "max_alphabet_flux_error":
            float(
                np.max(
                    alphabet_flux_errors
                )
            ),

        "all_hashes_pass":
            all_hashes_pass,

        "all_conservation_pass":
            all_conservation_pass,

        "all_decision_authority_false":
            all_authority_pass,
    },

    "interpretation": {
        "observer":
            "Integrated AcousticAlphabet",

        "kmbp_bridge":
            "KMBP_AcousticAlphabet",

        "decision_authority":
            False,

        "existing_logic_replaced":
            False,

        "claim_limit":
            (
                "Finite-grid trajectory test only. "
                "Not a proof of global regularity."
            ),
    },
}

RESULT_FILE.write_text(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    ),
    encoding="utf-8",
)

np.savez_compressed(
    FINAL_FIELDS,
    U=U,
    V=V,
    W=W,
    u=np.fft.ifftn(U).real,
    v=np.fft.ifftn(V).real,
    w=np.fft.ifftn(W).real,
)

summary_lines = [
    "schema=malysh.long-acoustic-alphabet-summary.v1",
    "",
    f"prediction_count={len(records)}",
    f"alphabet_wins={wins}",
    f"alphabet_win_fraction={wins / len(records):.12e}",
    f"mean_alphabet_flux_error={mean_alphabet_flux:.12e}",
    f"mean_linear_flux_error={mean_linear_flux:.12e}",
    f"mean_alphabet_energy_error={mean_alphabet_energy:.12e}",
    f"mean_linear_energy_error={mean_linear_energy:.12e}",
    f"overall_flux_improvement={overall_improvement:.12e}",
    f"max_alphabet_flux_error={max(alphabet_flux_errors):.12e}",
    f"all_hashes_pass={all_hashes_pass}",
    f"all_conservation_pass={all_conservation_pass}",
    f"all_decision_authority_false={all_authority_pass}",
]

SUMMARY_FILE.write_text(
    "\n".join(summary_lines) + "\n",
    encoding="utf-8",
)


print()
print("============================================================")
print(" LONG CALCULATION COMPLETE")
print("============================================================")
print(
    "Predictions:",
    len(records),
)
print(
    "Alphabet wins:",
    wins,
    "/",
    len(records),
)
print(
    "Mean Alphabet flux error:",
    f"{mean_alphabet_flux:.12e}",
)
print(
    "Mean linear flux error:",
    f"{mean_linear_flux:.12e}",
)
print(
    "Overall flux improvement:",
    f"{100.0 * overall_improvement:.6f}%",
)
print(
    "Mean Alphabet energy error:",
    f"{mean_alphabet_energy:.12e}",
)
print(
    "Mean linear energy error:",
    f"{mean_linear_energy:.12e}",
)
print(
    "All frozen hashes verified:",
    all_hashes_pass,
)
print(
    "Nonlinear conservation:",
    all_conservation_pass,
)
print(
    "Decision authority always false:",
    all_authority_pass,
)
print(
    "Final energy:",
    f'{history[-1]["energy"]:.12e}',
)
print(
    "Final enstrophy:",
    f'{history[-1]["enstrophy"]:.12e}',
)
print(
    "Final flux peak:",
    f'{history[-1]["flux_peak_value"]:.12e}',
)
print(
    "Final flux peak shell:",
    history[-1][
        "flux_peak_shell"
    ],
)
print(
    "Final k4 peak shell:",
    history[-1][
        "k4_weighted_peak_shell"
    ],
)
print()
print("Result:", RESULT_FILE)
print("Summary:", SUMMARY_FILE)
print("Final fields:", FINAL_FIELDS)
