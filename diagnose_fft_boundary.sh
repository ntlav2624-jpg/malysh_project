#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/malysh_project"

OUT="experiments/fft_boundary_diagnostic"
mkdir -p "$OUT"

python - "$OUT" <<'PY'
import json
import sys
from pathlib import Path

import numpy as np

outdir = Path(sys.argv[1])

results = []


def triad_count_from_bins(bins):
    """
    Exact ordered triad count for the Cartesian cube generated
    by a symmetric 1D bin set A, excluding the zero vector.

    A triad satisfies:
        p + q = k

    First count 1D pairs (a,b) for which a+b remains in A.
    3D count is the cube of that number.

    Then remove triads involving the zero vector.
    """

    values = set(float(x) for x in bins)

    one_dim = 0

    for a in values:
        for b in values:
            c = a + b

            if c in values:
                one_dim += 1

    side = len(values)
    full_nodes = side ** 3

    triads_with_zero_removed = (
        one_dim ** 3
        - (3 * full_nodes - 2)
    )

    return int(triads_with_zero_removed)


for N in range(8, 31):

    cutoff = (N - 1) // 3

    freq = np.fft.fftfreq(N) * N

    actual_mask = np.abs(freq) <= cutoff
    actual_bins = freq[actual_mask]

    expected_bins = np.arange(
        -cutoff,
        cutoff + 1,
        dtype=int,
    )

    expected_side = len(expected_bins)
    actual_side = len(actual_bins)

    expected_modes = expected_side ** 3 - 1
    actual_modes = actual_side ** 3 - 1

    bre_modes = expected_modes - actual_modes

    expected_abs = set(
        int(abs(x))
        for x in expected_bins
    )

    actual_abs = set()

    for x in actual_bins:
        nearest = int(round(float(x)))

        if abs(float(x)) <= cutoff:
            actual_abs.add(abs(nearest))

    missing_abs = sorted(
        expected_abs - actual_abs
    )

    boundary_details = []

    for x in freq:
        nearest = int(round(float(x)))

        if abs(nearest) == cutoff:
            boundary_details.append({
                "raw": repr(float(x)),
                "nearest_integer": nearest,
                "delta": float(x) - nearest,
                "passes": bool(abs(float(x)) <= cutoff),
            })

    expected_float_bins = np.array(
        expected_bins,
        dtype=float,
    )

    expected_triads = triad_count_from_bins(
        expected_float_bins
    )

    actual_triads = triad_count_from_bins(
        actual_bins
    )

    lost_triads = (
        expected_triads
        - actual_triads
    )

    result = {
        "N": N,
        "cutoff": cutoff,

        "expected_side": expected_side,
        "actual_side": actual_side,

        "expected_modes": expected_modes,
        "actual_modes": actual_modes,
        "BRE_modes": bre_modes,

        "expected_triads": expected_triads,
        "actual_triads": actual_triads,
        "lost_triads": lost_triads,

        "missing_abs_bins": missing_abs,
        "boundary": boundary_details,

        "raw_freq": [
            repr(float(x))
            for x in freq
        ],
    }

    results.append(result)


report = {
    "experiment": "FFT boundary representation diagnostic",
    "range_N": [8, 30],
    "modifies_solver": False,
    "description": (
        "Observes how floating-point fftfreq values interact "
        "with the strict cutoff comparison without altering "
        "the Navier-Stokes solver."
    ),
    "results": results,
}

json_path = outdir / "boundary_report.json"

json_path.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)


print()
print("=" * 118)
print("FFT BOUNDARY REPRESENTATION DIAGNOSTIC")
print("=" * 118)

print(
    "%-4s %-4s %-6s %-6s %-10s %-10s "
    "%-10s %-12s %-12s %-12s"
    % (
        "N",
        "cut",
        "sideE",
        "sideA",
        "modesE",
        "modesA",
        "BRE",
        "triadsE",
        "triadsA",
        "lostTriads",
    )
)

print("-" * 118)

for r in results:

    print(
        "%-4d %-4d %-6d %-6d %-10d %-10d "
        "%-10d %-12d %-12d %-12d"
        % (
            r["N"],
            r["cutoff"],
            r["expected_side"],
            r["actual_side"],
            r["expected_modes"],
            r["actual_modes"],
            r["BRE_modes"],
            r["expected_triads"],
            r["actual_triads"],
            r["lost_triads"],
        )
    )


print()
print("=" * 118)
print("ONLY CASES WITH BOUNDARY EFFECT")
print("=" * 118)

affected = [
    r
    for r in results
    if r["BRE_modes"] != 0
]

if not affected:
    print("No boundary effects detected.")
else:
    for r in affected:

        print()
        print(
            "N=%d cutoff=%d"
            % (
                r["N"],
                r["cutoff"],
            )
        )

        print(
            "  modes expected/actual : %d / %d"
            % (
                r["expected_modes"],
                r["actual_modes"],
            )
        )

        print(
            "  BRE modes             : %d"
            % r["BRE_modes"]
        )

        print(
            "  triads expected       : %d"
            % r["expected_triads"]
        )

        print(
            "  triads actual         : %d"
            % r["actual_triads"]
        )

        print(
            "  lost triads           : %d"
            % r["lost_triads"]
        )

        print(
            "  missing |k| bins      : %s"
            % r["missing_abs_bins"]
        )

        print("  boundary representation:")

        for b in r["boundary"]:
            print(
                "    raw=%-22s nearest=%3d "
                "delta=%+.18e pass=%s"
                % (
                    b["raw"],
                    b["nearest_integer"],
                    b["delta"],
                    b["passes"],
                )
            )


print()
print("=" * 118)
print("AMPLIFICATION")
print("=" * 118)

for r in affected:

    mode_loss = r["BRE_modes"]
    triad_loss = r["lost_triads"]

    if mode_loss:
        amplification = triad_loss / mode_loss
    else:
        amplification = 0.0

    print(
        "N=%d : lost modes=%d  lost triads=%d  "
        "triads-per-lost-mode=%.3f"
        % (
            r["N"],
            mode_loss,
            triad_loss,
            amplification,
        )
    )


print()
print("Saved:", json_path)
PY

echo
echo "=== JSON CHECK ==="

python -m json.tool \
  "$OUT/boundary_report.json" \
  >/dev/null

echo "JSON OK"

echo
echo "=== DONE ==="
