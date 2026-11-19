import json
import math
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parent

# ============================================================
# PARAMETERS
# ============================================================

N = 32
L = 2.0 * np.pi
RE = 200.0
NU = 1.0 / RE

DT = 0.002
STEPS = 500
REPORT_EVERY = 25
SNAPSHOT_EVERY = 50

ACOUSTIC_F0 = 330.0

# ============================================================
# GRID
# ============================================================

x = np.linspace(0.0, L, N, endpoint=False)
X, Y, Z = np.meshgrid(x, x, x, indexing="ij")

dx = L / N

k_axis = np.fft.fftfreq(N, d=dx) * 2.0 * np.pi

KX, KY, KZ = np.meshgrid(
    k_axis,
    k_axis,
    k_axis,
    indexing="ij",
)

KMAG = np.sqrt(KX**2 + KY**2 + KZ**2)
K2 = KMAG**2

K2_SAFE = K2.copy()
K2_SAFE[0, 0, 0] = 1.0

cutoff = N // 3

DEALIAS = (
    (np.abs(KX) <= cutoff)
    & (np.abs(KY) <= cutoff)
    & (np.abs(KZ) <= cutoff)
)

MAX_SHELL = int(np.floor(np.max(KMAG[DEALIAS])))

# ============================================================
# INITIAL 3D TAYLOR-GREEN FIELD
# ============================================================

u = np.sin(X) * np.cos(Y) * np.cos(Z)
v = -np.cos(X) * np.sin(Y) * np.cos(Z)
w = np.zeros_like(u)

# ============================================================
# SPECTRAL OPERATORS
# ============================================================

def project(U, V, W):
    k_dot_u = KX * U + KY * V + KZ * W

    U2 = U - KX * k_dot_u / K2_SAFE
    V2 = V - KY * k_dot_u / K2_SAFE
    W2 = W - KZ * k_dot_u / K2_SAFE

    U2[0, 0, 0] = 0.0
    V2[0, 0, 0] = 0.0
    W2[0, 0, 0] = 0.0

    return U2, V2, W2


def nonlinear_term(U, V, W):
    """
    Returns the projected nonlinear RHS:

        N = -P[(u dot grad)u]
    """

    u0 = np.fft.ifftn(U).real
    v0 = np.fft.ifftn(V).real
    w0 = np.fft.ifftn(W).real

    du_dx = np.fft.ifftn(1j * KX * U).real
    du_dy = np.fft.ifftn(1j * KY * U).real
    du_dz = np.fft.ifftn(1j * KZ * U).real

    dv_dx = np.fft.ifftn(1j * KX * V).real
    dv_dy = np.fft.ifftn(1j * KY * V).real
    dv_dz = np.fft.ifftn(1j * KZ * V).real

    dw_dx = np.fft.ifftn(1j * KX * W).real
    dw_dy = np.fft.ifftn(1j * KY * W).real
    dw_dz = np.fft.ifftn(1j * KZ * W).real

    conv_u = u0 * du_dx + v0 * du_dy + w0 * du_dz
    conv_v = u0 * dv_dx + v0 * dv_dy + w0 * dv_dz
    conv_w = u0 * dw_dx + v0 * dw_dy + w0 * dw_dz

    CU = np.fft.fftn(conv_u) * DEALIAS
    CV = np.fft.fftn(conv_v) * DEALIAS
    CW = np.fft.fftn(conv_w) * DEALIAS

    CU, CV, CW = project(CU, CV, CW)

    return -CU, -CV, -CW


def rhs(U, V, W):
    NU0, NV0, NW0 = nonlinear_term(U, V, W)

    dU = NU0 - NU * K2 * U
    dV = NV0 - NU * K2 * V
    dW = NW0 - NU * K2 * W

    return dU, dV, dW


def rk2_step(U, V, W):
    k1u, k1v, k1w = rhs(U, V, W)

    Um = U + 0.5 * DT * k1u
    Vm = V + 0.5 * DT * k1v
    Wm = W + 0.5 * DT * k1w

    Um, Vm, Wm = project(Um, Vm, Wm)

    k2u, k2v, k2w = rhs(Um, Vm, Wm)

    U2 = (U + DT * k2u) * DEALIAS
    V2 = (V + DT * k2v) * DEALIAS
    W2 = (W + DT * k2w) * DEALIAS

    return project(U2, V2, W2)


# ============================================================
# DIAGNOSTICS
# ============================================================

def scalar_diagnostics(U, V, W):
    u0 = np.fft.ifftn(U).real
    v0 = np.fft.ifftn(V).real
    w0 = np.fft.ifftn(W).real

    div_hat = 1j * (KX * U + KY * V + KZ * W)
    divergence = np.fft.ifftn(div_hat).real

    ox_hat = 1j * (KY * W - KZ * V)
    oy_hat = 1j * (KZ * U - KX * W)
    oz_hat = 1j * (KX * V - KY * U)

    ox = np.fft.ifftn(ox_hat).real
    oy = np.fft.ifftn(oy_hat).real
    oz = np.fft.ifftn(oz_hat).real

    speed2 = u0**2 + v0**2 + w0**2
    omega2 = ox**2 + oy**2 + oz**2

    energy = 0.5 * np.mean(speed2)
    enstrophy = 0.5 * np.mean(omega2)
    dissipation = 2.0 * NU * enstrophy

    speed_max = float(np.sqrt(speed2).max())
    cfl = speed_max * DT / dx

    return {
        "energy": float(energy),
        "enstrophy": float(enstrophy),
        "dissipation": float(dissipation),
        "div_inf": float(np.max(np.abs(divergence))),
        "speed_max": speed_max,
        "cfl": float(cfl),
    }


def shell_sums(field):
    result = np.zeros(MAX_SHELL + 1, dtype=np.float64)

    for shell in range(MAX_SHELL + 1):
        mask = (
            (KMAG >= shell)
            & (KMAG < shell + 1)
            & DEALIAS
        )

        result[shell] = float(np.sum(field[mask]))

    return result


def spectral_snapshot(U, V, W, step):
    """
    Builds:
      E(K): shell energy
      T(K): nonlinear shell transfer
      D(K): viscous shell transfer
      Pi(K): cumulative forward flux
    """

    NU0, NV0, NW0 = nonlinear_term(U, V, W)

    normalization = float(N**6)

    energy_mode = (
        np.abs(U)**2
        + np.abs(V)**2
        + np.abs(W)**2
    ) / (2.0 * normalization)

    transfer_mode = np.real(
        np.conj(U) * NU0
        + np.conj(V) * NV0
        + np.conj(W) * NW0
    ) / normalization

    viscous_mode = (
        -NU
        * K2
        * (
            np.abs(U)**2
            + np.abs(V)**2
            + np.abs(W)**2
        )
        / normalization
    )

    energy_shell = shell_sums(energy_mode)
    transfer_shell = shell_sums(transfer_mode)
    viscous_shell = shell_sums(viscous_mode)

    # Positive Pi(K) means net nonlinear transfer
    # from modes <= K toward modes > K.
    flux = -np.cumsum(transfer_shell)

    weighted_k4 = (
        (np.arange(MAX_SHELL + 1, dtype=float) ** 4)
        * energy_shell
    )

    if np.any(weighted_k4 > 0.0):
        k4_peak = int(np.argmax(weighted_k4))
    else:
        k4_peak = 0

    if np.any(np.abs(flux) > 0.0):
        flux_peak_shell = int(np.argmax(np.abs(flux)))
        flux_peak_value = float(flux[flux_peak_shell])
    else:
        flux_peak_shell = 0
        flux_peak_value = 0.0

    nonlinear_sum = float(np.sum(transfer_shell))
    viscous_sum = float(np.sum(viscous_shell))

    return {
        "step": int(step),
        "time": float(step * DT),
        "shells": list(range(MAX_SHELL + 1)),
        "energy_spectrum": energy_shell.tolist(),
        "nonlinear_transfer": transfer_shell.tolist(),
        "viscous_transfer": viscous_shell.tolist(),
        "cumulative_flux": flux.tolist(),
        "nonlinear_global_sum": nonlinear_sum,
        "viscous_global_sum": viscous_sum,
        "k4_weighted_peak_shell": k4_peak,
        "flux_peak_shell": flux_peak_shell,
        "flux_peak_value": flux_peak_value,
    }


# ============================================================
# SIMPLE BLIND PREDICTOR
# ============================================================

def predict_next_snapshot(previous, current):
    """
    Linear extrapolation from two already observed snapshots.
    This is a deliberately simple baseline, not Malysh.
    """

    previous_flux = np.asarray(
        previous["cumulative_flux"],
        dtype=float,
    )

    current_flux = np.asarray(
        current["cumulative_flux"],
        dtype=float,
    )

    predicted_flux = (
        current_flux
        + (current_flux - previous_flux)
    )

    previous_energy = np.asarray(
        previous["energy_spectrum"],
        dtype=float,
    )

    current_energy = np.asarray(
        current["energy_spectrum"],
        dtype=float,
    )

    predicted_energy = np.maximum(
        0.0,
        current_energy
        + (current_energy - previous_energy),
    )

    return {
        "source_steps": [
            int(previous["step"]),
            int(current["step"]),
        ],
        "target_step": int(
            current["step"] + SNAPSHOT_EVERY
        ),
        "predicted_flux": predicted_flux.tolist(),
        "predicted_energy_spectrum":
            predicted_energy.tolist(),
    }


def score_prediction(prediction, actual):
    predicted_flux = np.asarray(
        prediction["predicted_flux"],
        dtype=float,
    )

    actual_flux = np.asarray(
        actual["cumulative_flux"],
        dtype=float,
    )

    predicted_energy = np.asarray(
        prediction["predicted_energy_spectrum"],
        dtype=float,
    )

    actual_energy = np.asarray(
        actual["energy_spectrum"],
        dtype=float,
    )

    flux_error = float(
        np.linalg.norm(predicted_flux - actual_flux)
        / (np.linalg.norm(actual_flux) + 1e-30)
    )

    energy_error = float(
        np.linalg.norm(predicted_energy - actual_energy)
        / (np.linalg.norm(actual_energy) + 1e-30)
    )

    predicted_peak = int(
        np.argmax(np.abs(predicted_flux))
    )

    actual_peak = int(
        np.argmax(np.abs(actual_flux))
    )

    return {
        "target_step": int(actual["step"]),
        "relative_flux_error": flux_error,
        "relative_energy_error": energy_error,
        "predicted_flux_peak_shell": predicted_peak,
        "actual_flux_peak_shell": actual_peak,
        "peak_shell_error":
            abs(predicted_peak - actual_peak),
    }


# ============================================================
# INITIALIZATION
# ============================================================

U = np.fft.fftn(u)
V = np.fft.fftn(v)
W = np.fft.fftn(w)

U, V, W = project(U, V, W)

initial = scalar_diagnostics(U, V, W)

history = []
snapshots = []
predictions = []
prediction_scores = []

print("============================================================")
print(" 3D TAYLOR-GREEN TIME-RESOLVED FLUX")
print("============================================================")
print(f"Grid       : {N}^3")
print(f"Re         : {RE}")
print(f"nu         : {NU}")
print(f"dt         : {DT}")
print(f"Steps      : {STEPS}")
print(f"Final time : {STEPS * DT}")
print(f"Snapshots  : every {SNAPSHOT_EVERY} steps")
print(f"E(0)       : {initial['energy']:.12e}")
print(f"Omega(0)   : {initial['enstrophy']:.12e}")
print(f"Div(0)     : {initial['div_inf']:.3e}")
print()

snapshots.append(spectral_snapshot(U, V, W, 0))

# ============================================================
# TIME LOOP
# ============================================================

for step in range(1, STEPS + 1):
    U, V, W = rk2_step(U, V, W)

    if step == 1 or step % REPORT_EVERY == 0:
        state = scalar_diagnostics(U, V, W)
        state["step"] = int(step)
        state["time"] = float(step * DT)

        history.append(state)

        print(
            f"[STEP {step:04d}] "
            f"t={state['time']:.3f} | "
            f"E={state['energy']:.9e} | "
            f"Omega={state['enstrophy']:.9e} | "
            f"eps={state['dissipation']:.6e} | "
            f"Div={state['div_inf']:.3e} | "
            f"CFL={state['cfl']:.3e}"
        )

        if not all(
            math.isfinite(state[key])
            for key in (
                "energy",
                "enstrophy",
                "dissipation",
                "div_inf",
                "cfl",
            )
        ):
            raise SystemExit("[FAIL] NaN or Inf")

        if state["cfl"] >= 0.5:
            raise SystemExit("[FAIL] CFL >= 0.5")

    if step % SNAPSHOT_EVERY == 0:
        snapshot = spectral_snapshot(U, V, W, step)
        snapshots.append(snapshot)

        print(
            "          "
            f"Pi_peak={snapshot['flux_peak_value']:+.6e} "
            f"at K={snapshot['flux_peak_shell']} | "
            f"k4_peak={snapshot['k4_weighted_peak_shell']} | "
            f"sum(T)={snapshot['nonlinear_global_sum']:+.3e}"
        )

        if len(snapshots) >= 3:
            prediction = predict_next_snapshot(
                snapshots[-3],
                snapshots[-2],
            )

            score = score_prediction(
                prediction,
                snapshots[-1],
            )

            predictions.append(prediction)
            prediction_scores.append(score)

            print(
                "          "
                f"blind prediction for step {step}: "
                f"flux_error={score['relative_flux_error']:.3e} | "
                f"peak_error={score['peak_shell_error']}"
            )


# ============================================================
# FINAL VERIFICATION
# ============================================================

final = scalar_diagnostics(U, V, W)

finite_pass = all(
    math.isfinite(final[key])
    for key in (
        "energy",
        "enstrophy",
        "dissipation",
        "div_inf",
        "cfl",
    )
)

energy_pass = (
    final["energy"]
    <= initial["energy"] + 1e-10
)

divergence_pass = final["div_inf"] < 1e-8

cfl_pass = max(
    item["cfl"] for item in history
) < 0.5

nonlinear_conservation_error = max(
    abs(item["nonlinear_global_sum"])
    for item in snapshots
)

# Nonlinear advection should redistribute energy among modes
# without creating net global energy in a periodic domain.
nonlinear_conservation_pass = (
    nonlinear_conservation_error < 1e-10
)

if prediction_scores:
    mean_flux_prediction_error = float(
        np.mean([
            item["relative_flux_error"]
            for item in prediction_scores
        ])
    )

    mean_energy_prediction_error = float(
        np.mean([
            item["relative_energy_error"]
            for item in prediction_scores
        ])
    )

    mean_peak_shell_error = float(
        np.mean([
            item["peak_shell_error"]
            for item in prediction_scores
        ])
    )
else:
    mean_flux_prediction_error = None
    mean_energy_prediction_error = None
    mean_peak_shell_error = None

packet = {
    "schema": "malysh.ns3d-flux-time.v1",
    "role": "external read-only experiment",
    "malysh_modified": False,

    "parameters": {
        "N": N,
        "nodes": N**3,
        "L": L,
        "Re": RE,
        "nu": NU,
        "dt": DT,
        "steps": STEPS,
        "final_time": STEPS * DT,
        "snapshot_every": SNAPSHOT_EVERY,
        "dealiasing": "2/3",
        "time_integrator": "RK2 midpoint",
        "acoustic_f0_hz": ACOUSTIC_F0,
    },

    "initial": initial,
    "final": final,
    "history": history,
    "spectral_snapshots": snapshots,
    "blind_predictions": predictions,
    "prediction_scores": prediction_scores,

    "summary": {
        "snapshot_count": len(snapshots),
        "prediction_count": len(prediction_scores),
        "energy_delta":
            final["energy"] - initial["energy"],
        "enstrophy_delta":
            final["enstrophy"] - initial["enstrophy"],
        "max_nonlinear_global_sum_abs":
            nonlinear_conservation_error,
        "mean_blind_flux_prediction_error":
            mean_flux_prediction_error,
        "mean_blind_energy_prediction_error":
            mean_energy_prediction_error,
        "mean_blind_peak_shell_error":
            mean_peak_shell_error,
    },

    "verification": {
        "finite_pass": finite_pass,
        "energy_nonincrease_pass": energy_pass,
        "divergence_pass": divergence_pass,
        "cfl_pass": cfl_pass,
        "nonlinear_conservation_pass":
            nonlinear_conservation_pass,
    },

    "claims_allowed": [
        "finite-grid temporal spectral observation",
        "shell energy spectrum",
        "nonlinear shell transfer",
        "cumulative spectral flux",
        "baseline blind prediction score",
    ],

    "claims_forbidden": [
        "global regularity proof",
        "Clay Millennium Problem solved",
        "Malysh prediction before Malysh is actually run",
    ],
}

result_path = RUN / "ns3d_flux_time.json"

result_path.write_text(
    json.dumps(
        packet,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

np.savez_compressed(
    RUN / "ns3d_flux_time_fields.npz",
    u=np.fft.ifftn(U).real,
    v=np.fft.ifftn(V).real,
    w=np.fft.ifftn(W).real,
    U=U,
    V=V,
    W=W,
)

print()
print("============================================================")
print(" VERIFICATION")
print("============================================================")

print(
    "[PASS]" if finite_pass else "[FAIL]",
    "finite values",
)

print(
    "[PASS]" if energy_pass else "[FAIL]",
    "energy did not increase",
)

print(
    "[PASS]" if divergence_pass else "[FAIL]",
    f"divergence = {final['div_inf']:.3e}",
)

print(
    "[PASS]" if cfl_pass else "[FAIL]",
    f"max CFL = {max(x['cfl'] for x in history):.3e}",
)

print(
    "[PASS]"
    if nonlinear_conservation_pass
    else "[FAIL]",
    "nonlinear transfer conserves global modal energy",
)

print(
    "[INFO] max |sum shell T| =",
    f"{nonlinear_conservation_error:.12e}",
)

print(
    "[INFO] snapshots =",
    len(snapshots),
)

print(
    "[INFO] blind predictions scored =",
    len(prediction_scores),
)

if mean_flux_prediction_error is not None:
    print(
        "[INFO] mean blind flux error =",
        f"{mean_flux_prediction_error:.6e}",
    )

    print(
        "[INFO] mean blind energy error =",
        f"{mean_energy_prediction_error:.6e}",
    )

    print(
        "[INFO] mean peak-shell error =",
        f"{mean_peak_shell_error:.6e}",
    )

print("[INFO] result:", result_path)
print()
print(
    "[INFO] This is a finite-grid experiment, "
    "not a proof of global regularity."
)

if not all([
    finite_pass,
    energy_pass,
    divergence_pass,
    cfl_pass,
    nonlinear_conservation_pass,
]):
    raise SystemExit(2)
