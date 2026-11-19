import json
import math
from pathlib import Path

import numpy as np

ROOT = Path.home() / "malysh_project"
RUN = Path(__file__).resolve().parent

# ============================================================
# ПАРАМЕТРЫ ЭКСПЕРИМЕНТА
# ============================================================

N = 64
L = 2.0 * np.pi
NU = 0.01
DT = 0.002
STEPS = 500
REPORT_EVERY = 50

# Акустическая база. Она используется только как наблюдатель
# арифметики спектральных индексов, а не как замена решателя.
ACOUSTIC_F0 = 330.0

# ============================================================
# СЕТКА И ВОЛНОВЫЕ ЧИСЛА
# ============================================================

x = np.linspace(0.0, L, N, endpoint=False)
X, Y = np.meshgrid(x, x, indexing="ij")

dx = L / N

kx = np.fft.fftfreq(N, d=dx) * 2.0 * np.pi
ky = np.fft.fftfreq(N, d=dx) * 2.0 * np.pi

KX, KY = np.meshgrid(kx, ky, indexing="ij")
K2 = KX**2 + KY**2

K2_SAFE = K2.copy()
K2_SAFE[0, 0] = 1.0

# Фильтр 2/3 для нелинейного члена.
cutoff = N // 3
DEALIAS = (
    (np.abs(KX) <= cutoff)
    & (np.abs(KY) <= cutoff)
)

# ============================================================
# НАЧАЛЬНОЕ УСЛОВИЕ: ВИХРЬ ТЕЙЛОРА–ГРИНА
# ============================================================

u = np.sin(X) * np.cos(Y)
v = -np.cos(X) * np.sin(Y)

def project(U, V):
    """
    Спектральная проекция скорости на бездивергентное поле:

        u_perp = u - k (k·u) / |k|²
    """
    k_dot_u = KX * U + KY * V

    U2 = U - KX * k_dot_u / K2_SAFE
    V2 = V - KY * k_dot_u / K2_SAFE

    U2[0, 0] = 0.0
    V2[0, 0] = 0.0

    return U2, V2


def diagnostics(U, V):
    u_local = np.fft.ifft2(U).real
    v_local = np.fft.ifft2(V).real

    div_hat = 1j * (KX * U + KY * V)
    div = np.fft.ifft2(div_hat).real

    omega_hat = 1j * KX * V - 1j * KY * U
    omega = np.fft.ifft2(omega_hat).real

    energy = 0.5 * np.mean(u_local**2 + v_local**2)
    enstrophy = 0.5 * np.mean(omega**2)
    div_inf = np.max(np.abs(div))

    return {
        "energy": float(energy),
        "enstrophy": float(enstrophy),
        "div_inf": float(div_inf),
    }


def rhs(U, V):
    """
    Правая часть 2D несжимаемых уравнений Навье–Стокса:

        du/dt + P[(u·grad)u] = nu Laplacian(u)

    Давление устраняется спектральной проекцией P.
    """
    u_local = np.fft.ifft2(U).real
    v_local = np.fft.ifft2(V).real

    du_dx = np.fft.ifft2(1j * KX * U).real
    du_dy = np.fft.ifft2(1j * KY * U).real

    dv_dx = np.fft.ifft2(1j * KX * V).real
    dv_dy = np.fft.ifft2(1j * KY * V).real

    conv_u = u_local * du_dx + v_local * du_dy
    conv_v = u_local * dv_dx + v_local * dv_dy

    CU = np.fft.fft2(conv_u)
    CV = np.fft.fft2(conv_v)

    CU *= DEALIAS
    CV *= DEALIAS

    CU, CV = project(CU, CV)

    dU = -CU - NU * K2 * U
    dV = -CV - NU * K2 * V

    return dU, dV


def rk4_step(U, V):
    k1u, k1v = rhs(U, V)
    k2u, k2v = rhs(
        U + 0.5 * DT * k1u,
        V + 0.5 * DT * k1v,
    )
    k3u, k3v = rhs(
        U + 0.5 * DT * k2u,
        V + 0.5 * DT * k2v,
    )
    k4u, k4v = rhs(
        U + DT * k3u,
        V + DT * k3v,
    )

    U_new = U + DT * (
        k1u + 2.0 * k2u + 2.0 * k3u + k4u
    ) / 6.0

    V_new = V + DT * (
        k1v + 2.0 * k2v + 2.0 * k3v + k4v
    ) / 6.0

    U_new *= DEALIAS
    V_new *= DEALIAS

    return project(U_new, V_new)


def strongest_modes(U, V, count=32):
    """
    Возвращает сильнейшие спектральные моды.
    """
    modal_energy = (
        np.abs(U)**2 + np.abs(V)**2
    ) / (2.0 * N**4)

    flat = np.argsort(modal_energy.ravel())[::-1]
    modes = []

    for index in flat:
        i, j = np.unravel_index(index, modal_energy.shape)

        k = (
            int(round(KX[i, j])),
            int(round(KY[i, j])),
        )

        if k == (0, 0):
            continue

        modes.append({
            "k": list(k),
            "energy": float(modal_energy[i, j]),
            "acoustic_coordinates_hz": [
                float(k[0] * ACOUSTIC_F0),
                float(k[1] * ACOUSTIC_F0),
            ],
        })

        if len(modes) >= count:
            break

    return modes


def detect_triads(modes, limit=60):
    """
    Ищет триады:

        p + q = k

    Это двумерный аналог акустического закона:

        S_a ⊕ S_b = S_(a+b)
    """
    energy = {
        tuple(m["k"]): m["energy"]
        for m in modes
    }

    keys = list(energy)
    candidates = []

    for p in keys:
        for q in keys:
            k = (
                p[0] + q[0],
                p[1] + q[1],
            )

            if k not in energy:
                continue

            invariant = (
                p[0] + q[0] == k[0]
                and p[1] + q[1] == k[1]
            )

            score = (
                energy[p] * energy[q] * energy[k]
            ) ** (1.0 / 3.0)

            candidates.append({
                "p": list(p),
                "q": list(q),
                "k": list(k),
                "invariant": invariant,
                "score": float(score),
                "acoustic_check_hz": {
                    "p": [
                        p[0] * ACOUSTIC_F0,
                        p[1] * ACOUSTIC_F0,
                    ],
                    "q": [
                        q[0] * ACOUSTIC_F0,
                        q[1] * ACOUSTIC_F0,
                    ],
                    "k": [
                        k[0] * ACOUSTIC_F0,
                        k[1] * ACOUSTIC_F0,
                    ],
                },
            })

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return candidates[:limit]


U = np.fft.fft2(u)
V = np.fft.fft2(v)
U, V = project(U, V)

initial = diagnostics(U, V)
history = []

print("============================================================")
print(" EXTERNAL NAVIER-STOKES + ACOUSTIC TRIADS")
print("============================================================")
print(f"Grid       : {N} x {N}")
print(f"Viscosity  : {NU}")
print(f"dt         : {DT}")
print(f"Steps      : {STEPS}")
print(f"E(0)       : {initial['energy']:.12e}")
print(f"Omega(0)   : {initial['enstrophy']:.12e}")
print(f"Div(0)     : {initial['div_inf']:.12e}")
print()

for step in range(1, STEPS + 1):
    U, V = rk4_step(U, V)

    if step % REPORT_EVERY == 0 or step == 1:
        d = diagnostics(U, V)
        d["step"] = step
        d["time"] = step * DT
        history.append(d)

        print(
            f"[STEP {step:04d}] "
            f"t={step*DT:.4f} | "
            f"E={d['energy']:.12e} | "
            f"Omega={d['enstrophy']:.12e} | "
            f"Div={d['div_inf']:.3e}"
        )

final = diagnostics(U, V)
modes = strongest_modes(U, V)
triads = detect_triads(modes)

finite = all(
    math.isfinite(value)
    for value in (
        final["energy"],
        final["enstrophy"],
        final["div_inf"],
    )
)

energy_nonincrease = (
    final["energy"]
    <= initial["energy"] + 1e-10
)

divergence_pass = final["div_inf"] < 1e-8

triads_pass = all(
    item["invariant"]
    for item in triads
)

packet = {
    "schema": "malysh.ns-acoustic-external.v2",
    "role": "read-only external experiment",
    "malysh_modified": False,
    "equations": {
        "momentum":
            "du/dt + P[(u.grad)u] = nu Laplacian(u)",
        "incompressibility":
            "div(u) = 0",
        "triad":
            "p + q = k",
        "acoustic_analogue":
            "S_p plus S_q produces S_(p+q)",
    },
    "parameters": {
        "N": N,
        "L": L,
        "nu": NU,
        "dt": DT,
        "steps": STEPS,
        "dealiasing": "2/3",
        "time_integrator": "RK4",
        "acoustic_f0_hz": ACOUSTIC_F0,
    },
    "initial": initial,
    "final": final,
    "energy_delta":
        final["energy"] - initial["energy"],
    "history": history,
    "strongest_modes": modes,
    "triads": triads,
    "verification": {
        "finite": finite,
        "energy_nonincrease": energy_nonincrease,
        "divergence_pass": divergence_pass,
        "triads_pass": triads_pass,
    },
    "claims_allowed": [
        "finite-grid numerical result",
        "spectral-mode observation",
        "verified triad index arithmetic",
    ],
    "claims_forbidden": [
        "proof of global regularity",
        "solution of the Clay Millennium Problem",
    ],
}

packet_path = RUN / "ns_acoustic_observation.json"

packet_path.write_text(
    json.dumps(packet, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

np.savez_compressed(
    RUN / "ns_final_fields.npz",
    u=np.fft.ifft2(U).real,
    v=np.fft.ifft2(V).real,
    U=U,
    V=V,
)

print()
print("============================================================")
print(" VERIFICATION")
print("============================================================")
print("[PASS]" if finite else "[FAIL]", "finite values")
print(
    "[PASS]" if energy_nonincrease else "[FAIL]",
    "energy did not increase",
)
print(
    "[PASS]" if divergence_pass else "[FAIL]",
    f"divergence = {final['div_inf']:.3e}",
)
print(
    "[PASS]" if triads_pass else "[FAIL]",
    "all reported triads satisfy p + q = k",
)
print(f"[INFO] triads found: {len(triads)}")
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
    and triads_pass
):
    raise SystemExit(2)
