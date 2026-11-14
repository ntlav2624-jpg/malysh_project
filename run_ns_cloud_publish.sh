#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

cd "$HOME/malysh_project"

BRANCH="$(git branch --show-current)"
STAMP="$(date +%Y%m%d_%H%M%S)"
EXP_DIR="experiments/navier_cloud/${STAMP}"

RESULT="${EXP_DIR}/result.json"
LOG="${EXP_DIR}/stdout.log"
META="${EXP_DIR}/metadata.json"

mkdir -p "$EXP_DIR"

echo "============================================================"
echo "МАЛЫШ: ПОЛНЫЙ СЛЕПОЙ ТРИАДНЫЙ ЭКСПЕРИМЕНТ"
echo "ID:      $STAMP"
echo "Ветка:   $BRANCH"
echo "Каталог: $EXP_DIR"
echo "============================================================"

python malysh_ns_cloud.py \
  --N 12 \
  --seed 7 \
  --nu 0.03 \
  --dt 0.002 \
  --steps 500 \
  --diag-every 100 \
  --output "$RESULT" \
  2>&1 | tee "$LOG"

python - "$META" "$STAMP" "$BRANCH" <<'PY'
import json
import platform
import subprocess
import sys
from pathlib import Path

meta_path = Path(sys.argv[1])
experiment_id = sys.argv[2]
branch = sys.argv[3]


def command(*args):
    try:
        return subprocess.check_output(
            list(args),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


metadata = {
    "experiment_id": experiment_id,
    "experiment": "navier_cloud_blind",
    "description": (
        "Independent Fourier-triad state-network experiment "
        "for incompressible 3D Navier-Stokes"
    ),
    "branch": branch,
    "git_head_before_commit": command(
        "git",
        "rev-parse",
        "HEAD",
    ),
    "python_version": platform.python_version(),
    "platform": platform.platform(),
    "parameters": {
        "N": 12,
        "seed": 7,
        "nu": 0.03,
        "dt": 0.002,
        "steps": 500,
        "diag_every": 100,
    },
    "blind_assumptions": {
        "predefined_geometry": False,
        "special_role_of_7": False,
        "ring_hypothesis": False,
        "spiral_hypothesis": False,
        "plate_hypothesis": False,
        "cloud_hypothesis": False,
    },
}

meta_path.write_text(
    json.dumps(
        metadata,
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)

print("Metadata создан:", meta_path)
PY

echo
echo "=== ВАЛИДАЦИЯ РЕЗУЛЬТАТА ==="

test -s "$RESULT"
test -s "$LOG"
test -s "$META"

python -m json.tool "$RESULT" >/dev/null
python -m json.tool "$META" >/dev/null

echo "RESULT JSON: OK"
echo "METADATA:    OK"
echo "LOG:         OK"

echo
echo "=== СОЗДАННЫЕ ФАЙЛЫ ==="
ls -lh "$EXP_DIR"

echo
echo "=== ДОБАВЛЯЕМ ТОЛЬКО ЭКСПЕРИМЕНТ ==="

git add -- \
  "$RESULT" \
  "$LOG" \
  "$META"

echo
echo "=== STAGED FILES ==="
git diff --cached --name-status

EXPECTED_RESULT="$RESULT"
EXPECTED_LOG="$LOG"
EXPECTED_META="$META"

UNEXPECTED="$(
  git diff --cached --name-only |
  grep -Fvx "$EXPECTED_RESULT" |
  grep -Fvx "$EXPECTED_LOG" |
  grep -Fvx "$EXPECTED_META" ||
  true
)"

if [ -n "$UNEXPECTED" ]; then
    echo
    echo "STOP: в индексе найдены посторонние файлы:"
    printf '%s\n' "$UNEXPECTED"
    echo
    echo "Коммит и push отменены."
    exit 1
fi

git diff --cached --quiet && {
    echo "STOP: нечего коммитить."
    exit 1
}

echo
echo "=== COMMIT ==="

git commit \
  -m "experiment: Navier cloud ${STAMP}"

echo
echo "=== PUSH ==="

git push origin "$BRANCH"

echo
echo "============================================================"
echo "ОПУБЛИКОВАНО"
echo "Experiment ID: $STAMP"
echo "Branch:        $BRANCH"
echo "Result:        $RESULT"
echo "Log:           $LOG"
echo "Metadata:      $META"
echo "============================================================"
