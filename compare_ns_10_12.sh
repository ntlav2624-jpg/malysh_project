#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/malysh_project"

ROOT="experiments/navier_compare_10_12"
mkdir -p "$ROOT"

for N in 10 12
do
    echo
    echo "=========================================="
    echo "N=$N  cutoff=$(( (N - 1) / 3 ))"
    echo "=========================================="

    python malysh_ns_cloud.py \
        --N "$N" \
        --seed 7 \
        --nu 0.03 \
        --dt 0.002 \
        --steps 10 \
        --diag-every 10 \
        --output "$ROOT/N${N}.json" \
        2>&1 | tee "$ROOT/N${N}.log"
done

python - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])

def read_run(n):
    p = root / ("N%d.json" % n)
    data = json.loads(p.read_text(encoding="utf-8"))

    first = data["snapshots"][0]
    last = data["snapshots"][-1]
    active = int(data["active_modes"])

    max_sum_t = max(
        abs(float(x["nonlinear_energy_sum"]))
        for x in data["snapshots"]
    )

    return {
        "N": n,
        "active": active,
        "max_sum_t": max_sum_t,
        "E0": float(first["energy"]),
        "E1": float(last["energy"]),
        "K0": float(first["spectral_center"]),
        "K1": float(last["spectral_center"]),
        "W0": float(first["spectral_width"]),
        "W1": float(last["spectral_width"]),
        "SCC0": int(first["network"]["largest_scc"]),
        "SCC1": int(last["network"]["largest_scc"]),
        "tails": last["tails"],
    }

runs = [read_run(10), read_run(12)]

print()
print("=" * 72)
print("СРАВНЕНИЕ N=10 И N=12")
print("=" * 72)

for r in runs:
    f0 = r["SCC0"] / r["active"]
    f1 = r["SCC1"] / r["active"]

    print()
    print("N =", r["N"])
    print("active modes       =", r["active"])
    print("max |sum T|        = %.6e" % r["max_sum_t"])
    print("energy             = %.8f -> %.8f" % (r["E0"], r["E1"]))
    print("center             = %.8f -> %.8f" % (r["K0"], r["K1"]))
    print("delta center       = %+.6e" % (r["K1"] - r["K0"]))
    print("width              = %.8f -> %.8f" % (r["W0"], r["W1"]))
    print("delta width        = %+.6e" % (r["W1"] - r["W0"]))
    print("SCC                = %d -> %d" % (r["SCC0"], r["SCC1"]))
    print("SCC fraction       = %.6f -> %.6f" % (f0, f1))

    for threshold in sorted(r["tails"], key=float):
        t = r["tails"][threshold]
        ratio = t["flux_to_dissipation"]

        if ratio is None:
            ratio_text = "n/a"
        else:
            ratio_text = "%+.6f" % float(ratio)

        print(
            "k >= %s : Efrac=%.6f Phi=%+.6e D=%.6e Phi/D=%s"
            % (
                threshold,
                float(t["energy_fraction"]),
                float(t["nonlinear_flux"]),
                float(t["viscous_dissipation"]),
                ratio_text,
            )
        )

print()
print("=" * 72)
print("ИНВАРИАНТ")
print("=" * 72)

all_pass = True

for r in runs:
    passed = r["max_sum_t"] < 1e-12
    all_pass = all_pass and passed

    print(
        "N=%d : %s   max|sumT|=%.6e"
        % (
            r["N"],
            "PASS" if passed else "FAIL",
            r["max_sum_t"],
        )
    )

print()

if all_pass:
    print("RESULT: BOTH PASS")
else:
    print("RESULT: FAILURE DETECTED")

comparison = {
    "runs": runs,
    "threshold_sumT": 1e-12,
    "both_pass": all_pass,
    "note": (
        "This compares numerical invariants and qualitative network "
        "structure. Initial random fields are not yet identical."
    ),
}

out = root / "comparison.json"

out.write_text(
    json.dumps(comparison, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print("Saved:", out)
PY
