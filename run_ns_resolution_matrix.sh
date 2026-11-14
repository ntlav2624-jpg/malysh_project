#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

cd "$HOME/malysh_project"

STAMP="$(date +%Y%m%d_%H%M%S)"
ROOT="experiments/navier_resolution/$STAMP"

mkdir -p "$ROOT"

echo "============================================================"
echo "MALYSH NAVIER RESOLUTION MATRIX"
echo "ID: $STAMP"
echo "============================================================"

for N in 10 12 15 18
do
    DIR="$ROOT/N${N}"
    mkdir -p "$DIR"

    echo
    echo "============================================================"
    echo "N=$N"
    echo "strict cutoff = $(( (N - 1) / 3 ))"
    echo "============================================================"

    python malysh_ns_cloud.py \
      --N "$N" \
      --seed 7 \
      --nu 0.03 \
      --dt 0.002 \
      --steps 10 \
      --diag-every 10 \
      --output "$DIR/result.json" \
      2>&1 | tee "$DIR/stdout.log"
done

python - "$ROOT" <<'PY'
import json
import math
import sys
from pathlib import Path

root = Path(sys.argv[1])

summary = []

for result_file in sorted(root.glob("N*/result.json")):

    N = int(result_file.parent.name[1:])

    data = json.loads(
        result_file.read_text(encoding="utf-8")
    )

    snapshots = data["snapshots"]

    first = snapshots[0]
    last = snapshots[-1]

    nonlinear_max = max(
        abs(snapshot["nonlinear_energy_sum"])
        for snapshot in snapshots
    )

    active = data["active_modes"]

    scc0 = first["network"]["largest_scc"]
    scc1 = last["network"]["largest_scc"]

    row = {
        "N": N,
        "cutoff": (N - 1) // 3,
        "active_modes": active,

        "nonlinear_max_abs": nonlinear_max,

        "energy_initial": first["energy"],
        "energy_final": last["energy"],

        "center_initial": first["spectral_center"],
        "center_final": last["spectral_center"],

        "width_initial": first["spectral_width"],
        "width_final": last["spectral_width"],

        "scc_initial": scc0,
        "scc_final": scc1,

        "scc_fraction_initial": (
            scc0 / active if active else 0.0
        ),

        "scc_fraction_final": (
            scc1 / active if active else 0.0
        ),

        "tails_initial": first["tails"],
        "tails_final": last["tails"],
    }

    summary.append(row)

output = {
    "experiment": "navier_resolution_matrix",
    "important_note": (
        "Different N currently generate different random "
        "initial fields. This tests numerical invariants and "
        "qualitative robustness, not strict solution convergence."
    ),
    "runs": summary,
}

out = root / "summary.json"

out.write_text(
    json.dumps(
        output,
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)

header = (
    "N   cut   modes    max|sumT|       "
    "SCC0      SCC1      Kc0       Kc1       "
    "sig0      sig1"
)

print(header)

for r in summary:

    print(
        f"{r['N'\]:<3} "
        f"{r['cutoff'\]:<5} "
        f"{r['active_modes'\]:<8} "
        f"{r['nonlinear_max_abs'\]:<15.5e} "
        f"{r['scc_fraction_initial'\]:<9.5f} "
        f"{r['scc_fraction_final'\]:<9.5f} "
        f"{r['center_initial'\]:<9.5f} "
        f"{r['center_final'\]:<9.5f} "
        f"{r['width_initial'\]:<9.5f} "
        f"{r['width_final'\]:<9.5f}"
    )

print()
print("Summary:", out)
PY

echo
echo "============================================================"
echo "FINISHED"
echo "Directory: $ROOT"
echo "============================================================"
