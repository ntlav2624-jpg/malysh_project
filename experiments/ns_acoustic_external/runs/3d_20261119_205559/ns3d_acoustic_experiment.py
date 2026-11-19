import json
import math
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parent

# ============================================================
# 3D TAYLOR-GREEN: БЕЗОПАСНЫЙ ПЕРВЫЙ ЗАПУСК
# ============================================================

N = 32
L = 2.0 * np.pi

RE = 200.0
NU = 1.0 / RE

DT = 0.002
STEPS = 500
REPORT_EVERY = 25
SNAPSHOT_EVERY = 50

# Акустическая база используется только для отображения
# арифметики индексов спектральных мод.
ACOUSTIC_F0 = 330.0

# ============================================================
# СЕТКА
# ============================================================

x = np.linspace(0.0, L, N, endpoint=False)
X, Y, Z = np.meshgrid(x, x, x, indexing="ij")

dx = L / N

k = np.fft.fftfreq(N, d=dx) * 2.0 * np.pi

KX, KY, KZ = np.meshgrid(
    k,
    k,
    k,
    indexing="ij",
)

K2 = KX**2 + KY**2 + KZ**2

K2_SAFE = K2.copy()
K2_SAFE[0, 0, 0] = 1.0

# ============================================================
# ФИЛЬТР 2/3
# ============================================================

cutoff = N // 3

DEALIAS = (
    (np.abs(KX) <= cutoff)
    & (np.abs(KY) <= cutoff)
    & (np.abs(KZ) <= cutoff)
)

# ============================================================
# НАЧАЛЬНОЕ УСЛОВИЕ ТЕЙЛОРА-ГРИНА
# ============================================================

u = (
    np.sin(X)
    * np.cos(Y)
    * np.cos(Z)
)

v = (
    -np.cos(X)
    * np.sin(Y)
    * np.cos(Z)
)

w = np.zeros_like(u)

# ============================================================
# ОСНОВНЫЕ ОПЕРАТОРЫ
# ============================================================

def project(U, V, W):
    """
    Проекция на бездивергентное пространство:

        u_perp = u - k (k dot u) / |k|^2
    """

    k_dot_u = (
        KX * U
        + KY * V
        + KZ * W
    )

    U2 = U - KX * k_dot_u / K2_SAFE
    V2 = V - KY * k_dot_u / K2_SAFE
    W2 = W - KZ * k_dot_u / K2_SAFE

    U2[0, 0, 0] = 0.0
    V2[0, 0, 0] = 0.0
    W2[0, 0, 0] = 0.0

    return U2, V2, W2


def diagnostics(U, V, W):
    """
    Энергия, энстрофия, дивергенция и максимум скорости.
    """

    u_local = np.fft.ifftn(U).real
    v_local = np.fft.ifftn(V).real
    w_local = np.fft.ifftn(W).real

    div_hat = 1j * (
        KX * U
        + KY * V
        + KZ * W
    )

    divergence = np.fft.ifftn(div_hat).real

    omega_x_hat = 1j * (
        KY * W
        - KZ * V
    )

    omega_y_hat = 1j * (
        KZ * U
        - KX * W
    )

    omega_z_hat = 1j * (
        KX * V
        - KY * U
    )

    omega_x = np.fft.ifftn(omega_x_hat).real
    omega_y = np.fft.ifftn(omega_y_hat).real
    omega_z = np.fft.ifftn(omega_z_hat).real

    velocity_squared = (
        u_local**2
        + v_local**2
        + w_local**2
    )

    vorticity_squared = (
        omega_x**2
        + omega_y**2
        + omega_z**2
    )

    energy = 0.5 * np.mean(velocity_squared)
    enstrophy = 0.5 * np.mean(vorticity_squared)

    speed_max = np.sqrt(velocity_squared).max()

    divergence_inf = np.max(
        np.abs(divergence)
    )

    dissipation = 2.0 * NU * enstrophy
    cfl = speed_max * DT / dx

    return {
        "energy": float(energy),
        "enstrophy": float(enstrophy),
        "dissipation": float(dissipation),
        "div_inf": float(divergence_inf),
        "speed_max": float(speed_max),
        "cfl": float(cfl),
    }


def rhs(U, V, W):
    """
    Псевдоспектральная правая часть:

        du/dt = -P[(u dot grad)u] + nu Laplacian(u)
    """

    u_local = np.fft.ifftn(U).real
    v_local = np.fft.ifftn(V).real
    w_local = np.fft.ifftn(W).real

    du_dx = np.fft.ifftn(
        1j * KX * U
    ).real

    du_dy = np.fft.ifftn(
        1j * KY * U
    ).real

    du_dz = np.fft.ifftn(
        1j * KZ * U
    ).real

    dv_dx = np.fft.ifftn(
        1j * KX * V
    ).real

    dv_dy = np.fft.ifftn(
        1j * KY * V
    ).real

    dv_dz = np.fft.ifftn(
        1j * KZ * V
    ).real

    dw_dx = np.fft.ifftn(
        1j * KX * W
    ).real

    dw_dy = np.fft.ifftn(
        1j * KY * W
    ).real

    dw_dz = np.fft.ifftn(
        1j * KZ * W
    ).real

    conv_u = (
        u_local * du_dx
        + v_local * du_dy
        + w_local * du_dz
    )

    conv_v = (
        u_local * dv_dx
        + v_local * dv_dy
        + w_local * dv_dz
    )

    conv_w = (
        u_local * dw_dx
        + v_local * dw_dy
        + w_local * dw_dz
    )

    CU = np.fft.fftn(conv_u)
    CV = np.fft.fftn(conv_v)
    CW = np.fft.fftn(conv_w)

    CU *= DEALIAS
    CV *= DEALIAS
    CW *= DEALIAS

    CU, CV, CW = project(
        CU,
        CV,
        CW,
    )

    dU = -CU - NU * K2 * U
    dV = -CV - NU * K2 * V
    dW = -CW - NU * K2 * W

    return dU, dV, dW


def rk2_step(U, V, W):
    """
    Метод средней точки второго порядка.
    """

    k1u, k1v, k1w = rhs(U, V, W)

    Um = U + 0.5 * DT * k1u
    Vm = V + 0.5 * DT * k1v
    Wm = W + 0.5 * DT * k1w

    Um, Vm, Wm = project(
        Um,
        Vm,
        Wm,
    )

    k2u, k2v, k2w = rhs(
        Um,
        Vm,
        Wm,
    )

    U2 = U + DT * k2u
    V2 = V + DT * k2v
    W2 = W + DT * k2w

    U2 *= DEALIAS
    V2 *= DEALIAS
    W2 *= DEALIAS

    return project(U2, V2, W2)


# ============================================================
# СПЕКТР И СИЛЬНЕЙШИЕ МОДЫ
# ============================================================

def signed_mode(value):
    return int(round(float(value)))


def modal_energy(U, V, W):
    return (
        np.abs(U)**2
        + np.abs(V)**2
        + np.abs(W)**2
    ) / (2.0 * N**6)


def strongest_modes(U, V, W, count=48):
    spectrum = modal_energy(U, V, W)

    order = np.argsort(
        spectrum.ravel()
    )[::-1]

    modes = []

    for index in order:
        i, j, l = np.unravel_index(
            index,
            spectrum.shape,
        )

        mode = (
            signed_mode(KX[i, j, l]),
            signed_mode(KY[i, j, l]),
            signed_mode(KZ[i, j, l]),
        )

        if mode == (0, 0, 0):
            continue

        modes.append({
            "k": list(mode),
            "energy": float(
                spectrum[i, j, l]
            ),
            "acoustic_hz": [
                mode[0] * ACOUSTIC_F0,
                mode[1] * ACOUSTIC_F0,
                mode[2] * ACOUSTIC_F0,
            ],
        })

        if len(modes) >= count:
            break

    return modes


def mode_energy_map(modes):
    return {
        tuple(item["k"]): item["energy"]
        for item in modes
    }


# ============================================================
# ТРИАДЫ И НАБЛЮДАЕМЫЙ ЭНЕРГЕТИЧЕСКИЙ ОТКЛИК
# ============================================================

def compare_triads(previous_modes, current_modes):
    """
    Проверяется:

        p + q = k

    и наблюдаемое изменение энергии моды k.

    Важно:
    это пока корреляционный индикатор, а не полная
    декомпозиция точного триадного переноса.
    """

    previous = mode_energy_map(previous_modes)
    current = mode_energy_map(current_modes)

    keys = list(current)
    triads = []

    for p in keys:
        for q in keys:
            k_mode = (
                p[0] + q[0],
                p[1] + q[1],
                p[2] + q[2],
            )

            if k_mode not in current:
                continue

            invariant = (
                p[0] + q[0] == k_mode[0]
                and p[1] + q[1] == k_mode[1]
                and p[2] + q[2] == k_mode[2]
            )

            e_previous = previous.get(
                k_mode,
                0.0,
            )

            e_current = current[k_mode]

            delta_e_k = (
                e_current
                - e_previous
            )

            strength = (
                current[p]
                * current[q]
                * current[k_mode]
            ) ** (1.0 / 3.0)

            triads.append({
                "p": list(p),
                "q": list(q),
                "k": list(k_mode),
                "invariant": invariant,
                "energy_p": float(current[p]),
                "energy_q": float(current[q]),
                "energy_k": float(
                    current[k_mode]
                ),
                "delta_energy_k": float(
                    delta_e_k
                ),
                "candidate_strength": float(
                    strength
                ),
                "acoustic_equation_hz": {
                    "p": [
                        p[0] * ACOUSTIC_F0,
                        p[1] * ACOUSTIC_F0,
                        p[2] * ACOUSTIC_F0,
                    ],
                    "q": [
                        q[0] * ACOUSTIC_F0,
                        q[1] * ACOUSTIC_F0,
                        q[2] * ACOUSTIC_F0,
                    ],
                    "k": [
                        k_mode[0] * ACOUSTIC_F0,
                        k_mode[1] * ACOUSTIC_F0,
                        k_mode[2] * ACOUSTIC_F0,
                    ],
                },
            })

    triads.sort(
        key=lambda item: (
            item["candidate_strength"],
            abs(item["delta_energy_k"]),
        ),
        reverse=True,
    )

    return triads[:100]


# ============================================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================================

U = np.fft.fftn(u)
V = np.fft.fftn(v)
W = np.fft.fftn(w)

U, V, W = project(U, V, W)

initial = diagnostics(U, V, W)
previous_modes = strongest_modes(U, V, W)

history = []
triad_history = []

print("============================================================")
print(" 3D TAYLOR-GREEN + ACOUSTIC TRIAD OBSERVER")
print("============================================================")
print(f"Grid          : {N}^3 = {N**3} nodes")
print(f"Re            : {RE}")
print(f"Viscosity     : {NU}")
print(f"dt            : {DT}")
print(f"Steps         : {STEPS}")
print(f"Final time    : {DT * STEPS}")
print(f"E(0)          : {initial['energy']:.12e}")
print(f"Omega(0)      : {initial['enstrophy']:.12e}")
print(f"Div(0)        : {initial['div_inf']:.3e}")
print(f"CFL(0)        : {initial['cfl']:.3e}")
print()

# ============================================================
# ОСНОВНОЙ ЦИКЛ
# ============================================================

for step in range(1, STEPS + 1):
    U, V, W = rk2_step(U, V, W)

    if (
        step == 1
        or step % REPORT_EVERY == 0
    ):
        state = diagnostics(U, V, W)
        state["step"] = step
        state["time"] = step * DT

        history.append(state)

        print(
            f"[STEP {step:04d}] "
            f"t={state['time']:.4f} | "
            f"E={state['energy']:.12e} | "
            f"Omega={state['enstrophy']:.12e} | "
            f"eps={state['dissipation']:.6e} | "
            f"Div={state['div_inf']:.3e} | "
            f"CFL={state['cfl']:.3e}"
        )

        if not all(
            math.isfinite(state[key])
            for key in (
                "energy",
                "enstrophy",
                "div_inf",
                "cfl",
            )
        ):
            raise SystemExit(
                "[FAIL] NaN or Inf detected"
            )

        if state["cfl"] >= 0.5:
            raise SystemExit(
                "[FAIL] CFL >= 0.5; "
                "reduce DT"
            )

    if step % SNAPSHOT_EVERY == 0:
        current_modes = strongest_modes(
            U,
            V,
            W,
        )

        triads = compare_triads(
            previous_modes,
            current_modes,
        )

        growing = sum(
            item["delta_energy_k"] > 0.0
            for item in triads
        )

        triad_history.append({
            "step": step,
            "time": step * DT,
            "triads": triads,
            "growing_output_modes": growing,
        })

        print(
            f"          triads={len(triads)} | "
            f"growing k-modes={growing}"
        )

        previous_modes = current_modes


# ============================================================
# ФИНАЛЬНАЯ ПРОВЕРКА
# ============================================================

final = diagnostics(U, V, W)
final_modes = strongest_modes(U, V, W)

finite = all(
    math.isfinite(final[key])
    for key in (
        "energy",
        "enstrophy",
        "div_inf",
        "cfl",
    )
)

energy_nonincrease = (
    final["energy"]
    <= initial["energy"] + 1e-10
)

divergence_pass = (
    final["div_inf"] < 1e-8
)

cfl_pass = (
    max(item["cfl"] for item in history)
    < 0.5
)

triads_flat = [
    triad
    for snapshot in triad_history
    for triad in snapshot["triads"]
]

triad_arithmetic_pass = all(
    item["invariant"]
    for item in triads_flat
)

growing_triads = sum(
    item["delta_energy_k"] > 0.0
    for item in triads_flat
)

packet = {
    "schema":
        "malysh.ns3d-acoustic-external.v1",

    "role":
        "read-only external experiment",

    "malysh_modified":
        False,

    "interpretation": {
        "solver":
            "3D incompressible pseudospectral "
            "Taylor-Green experiment",

        "acoustic_role":
            "observer of spectral index addition",

        "important_limit":
            "delta_energy_k is an observed modal "
            "change, not yet an exact isolated "
            "triad-transfer coefficient",
    },

    "parameters": {
        "N": N,
        "nodes": N**3,
        "L": L,
        "Re": RE,
        "nu": NU,
        "dt": DT,
        "steps": STEPS,
        "final_time": DT * STEPS,
        "time_integrator": "RK2 midpoint",
        "dealiasing": "2/3",
        "acoustic_f0_hz": ACOUSTIC_F0,
    },

    "initial": initial,
    "final": final,

    "history": history,
    "final_modes": final_modes,
    "triad_history": triad_history,

    "summary": {
        "energy_delta":
            final["energy"]
            - initial["energy"],

        "enstrophy_delta":
            final["enstrophy"]
            - initial["enstrophy"],

        "triad_records":
            len(triads_flat),

        "growing_output_mode_records":
            growing_triads,
    },

    "verification": {
        "finite": finite,
        "energy_nonincrease":
            energy_nonincrease,
        "divergence_pass":
            divergence_pass,
        "cfl_pass":
            cfl_pass,
        "triad_arithmetic_pass":
            triad_arithmetic_pass,
    },

    "claims_allowed": [
        "finite-grid numerical observation",
        "3D Taylor-Green evolution",
        "verified spectral-index triads",
        "observed modal-energy changes",
    ],

    "claims_forbidden": [
        "proof of global regularity",
        "solution of the Clay Millennium Problem",
        "exact causal transfer assigned to a "
        "single triad without further decomposition",
    ],
}

packet_path = (
    RUN
    / "ns3d_acoustic_observation.json"
)

packet_path.write_text(
    json.dumps(
        packet,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

np.savez_compressed(
    RUN / "ns3d_final_fields.npz",
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
    "[PASS]" if finite else "[FAIL]",
    "finite values",
)

print(
    "[PASS]"
    if energy_nonincrease
    else "[FAIL]",
    "energy did not increase",
)

print(
    "[PASS]"
    if divergence_pass
    else "[FAIL]",
    f"divergence = {final['div_inf']:.3e}",
)

print(
    "[PASS]"
    if cfl_pass
    else "[FAIL]",
    f"max CFL = "
    f"{max(x['cfl'] for x in history):.3e}",
)

print(
    "[PASS]"
    if triad_arithmetic_pass
    else "[FAIL]",
    "all reported triads satisfy p + q = k",
)

print(
    f"[INFO] triad records: "
    f"{len(triads_flat)}"
)

print(
    f"[INFO] records where E(k) grew: "
    f"{growing_triads}"
)

print(
    f"[INFO] initial energy: "
    f"{initial['energy']:.12e}"
)

print(
    f"[INFO] final energy: "
    f"{final['energy']:.12e}"
)

print(
    f"[INFO] initial enstrophy: "
    f"{initial['enstrophy']:.12e}"
)

print(
    f"[INFO] final enstrophy: "
    f"{final['enstrophy']:.12e}"
)

print(f"[INFO] packet: {packet_path}")

print()
print(
    "[INFO] Finite-grid experiment only. "
    "This is not a proof of global regularity."
)

if not (
    finite
    and energy_nonincrease
    and divergence_pass
    and cfl_pass
    and triad_arithmetic_pass
):
    raise SystemExit(2)
