#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

cd "$HOME/malysh_project"

SCRIPT="point_wave_geometry.py"
OUTDIR="experiments/point_wave_geometry"
RESULT="$OUTDIR/point_wave_geometry.json"
LOG="$OUTDIR/run.log"

echo "============================================================"
echo "МАЛЫШ: ТОЧКА -> ГЕОМЕТРИЯ -> ВОЛНА"
echo "============================================================"

if [ ! -f "$SCRIPT" ]; then
    echo "STOP: $SCRIPT не найден"
    exit 1
fi

mkdir -p "$OUTDIR"

echo
echo "=== 1. PYTHON SYNTAX ==="

python -m py_compile "$SCRIPT"

echo "SYNTAX OK"

echo
echo "=== 2. RUN ==="

python "$SCRIPT" 2>&1 | tee "$LOG"

echo
echo "=== 3. RESULT CHECK ==="

if [ ! -s "$RESULT" ]; then
    echo "STOP: результат не создан"
    exit 1
fi

python -m json.tool "$RESULT" >/dev/null

echo "JSON OK"

echo
echo "=== 4. AUTOMATIC SUMMARY ==="

python - "$RESULT" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])

data = json.loads(
    path.read_text(encoding="utf-8")
)

results = data["results"]

print()
print("=" * 100)
print("ТОЧКА -> K-ГЕОМЕТРИЯ -> ВОЛНОВАЯ ГЕОМЕТРИЯ")
print("=" * 100)

for item in results:
    name = item["name"]
    coordinate = item["initial_coordinate"]

    print()
    print("-" * 100)
    print(
        "%s  coordinate=%s"
        % (
            name,
            coordinate,
        )
    )
    print("-" * 100)

    x1 = item["X1_relational"]

    print(
        "degree full/fractured : %d -> %d"
        % (
            x1["full_degree"],
            x1["fractured_degree"],
        )
    )

    print(
        "local relation loss   : %.6f"
        % x1["local_relation_loss"]
    )

    print()
    print(
        "%-5s %-22s %-22s %-28s %-28s %-10s %-10s"
        % (
            "t",
            "K full",
            "K fractured",
            "Wave full",
            "Wave fractured",
            "L1-k",
            "L1-wave",
        )
    )

    for snapshot in item["snapshots"]:
        step = snapshot["step"]

        kg_full = (
            snapshot[
                "X2_full_genesis"
            ]["geometry_class"]
        )

        kg_fractured = (
            snapshot[
                "X2_fractured_genesis"
            ]["geometry_class"]
        )

        wave_full = (
            snapshot[
                "XW_full_wave"
            ]["wave_class"]
        )

        wave_fractured = (
            snapshot[
                "XW_fractured_wave"
            ]["wave_class"]
        )

        l1_k = (
            snapshot[
                "X3_observer_difference"
            ]["L1"]
        )

        l1_wave = (
            snapshot[
                "XW_wave_difference"
            ]["wave_L1"]
        )

        print(
            "%-5d %-22s %-22s %-28s %-28s %-10.5f %-10.5f"
            % (
                step,
                kg_full,
                kg_fractured,
                wave_full,
                wave_fractured,
                l1_k,
                l1_wave,
            )
        )


print()
print("=" * 100)
print("FINAL SENSITIVITY")
print("=" * 100)

ranking = []

for item in results:
    final = item["snapshots"][-1]

    l1_k = (
        final[
            "X3_observer_difference"
        ]["L1"]
    )

    l1_wave = (
        final[
            "XW_wave_difference"
        ]["wave_L1"]
    )

    ranking.append(
        (
            l1_wave,
            l1_k,
            item["name"],
            item["initial_coordinate"],
        )
    )

ranking.sort(reverse=True)

for rank, entry in enumerate(
    ranking,
    start=1,
):
    l1_wave, l1_k, name, coordinate = entry

    print(
        "%d. %-16s k=%s  L1-k=%.6f  L1-wave=%.6f"
        % (
            rank,
            name,
            coordinate,
            l1_k,
            l1_wave,
        )
    )


print()
print("=" * 100)
print("GEOMETRY TRANSITIONS")
print("=" * 100)

for item in results:
    print()
    print(
        item["name"],
        item["initial_coordinate"],
    )

    full_path = []
    fractured_path = []

    full_wave_path = []
    fractured_wave_path = []

    for snapshot in item["snapshots"]:
        full_path.append(
            snapshot[
                "X2_full_genesis"
            ]["geometry_class"]
        )

        fractured_path.append(
            snapshot[
                "X2_fractured_genesis"
            ]["geometry_class"]
        )

        full_wave_path.append(
            snapshot[
                "XW_full_wave"
            ]["wave_class"]
        )

        fractured_wave_path.append(
            snapshot[
                "XW_fractured_wave"
            ]["wave_class"]
        )

    def compress(sequence):
        result = []

        for value in sequence:
            if (
                not result
                or value != result[-1]
            ):
                result.append(value)

        return result

    print(
        "  K full :",
        " -> ".join(
            compress(full_path)
        ),
    )

    print(
        "  K frac :",
        " -> ".join(
            compress(fractured_path)
        ),
    )

    print(
        "  W full :",
        " -> ".join(
            compress(full_wave_path)
        ),
    )

    print(
        "  W frac :",
        " -> ".join(
            compress(fractured_wave_path)
        ),
    )


print()
print("=" * 100)
print("КОНТРОЛЬ МАССЫ")
print("=" * 100)

max_mass_error = 0.0

for item in results:
    for snapshot in item["snapshots"]:
        error_full = abs(
            snapshot["mass_full"] - 1.0
        )

        error_fractured = abs(
            snapshot["mass_fractured"] - 1.0
        )

        max_mass_error = max(
            max_mass_error,
            error_full,
            error_fractured,
        )

print(
    "max |mass - 1| = %.18e"
    % max_mass_error
)

if max_mass_error < 1e-12:
    print("MASS INVARIANT: PASS")
else:
    print("MASS INVARIANT: FAIL")
PY

echo
echo "============================================================"
echo "ГОТОВО"
echo "Result : $RESULT"
echo "Log    : $LOG"
echo "============================================================"
