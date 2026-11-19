#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/malysh_project"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_ROOT="$HOME/malysh_backups"
BACKUP="$BACKUP_ROOT/malysh_before_sync_$STAMP.tar.gz"
REPORT="$ROOT/experiments/ns_acoustic_external/sync_reports/$STAMP"
TAG="pre-flux-malysh-sync-$STAMP"

cd "$ROOT"

mkdir -p "$BACKUP_ROOT"
mkdir -p "$REPORT"

echo "============================================================"
echo " MALYSH: FLUX OBSERVATION + SAFE GIT SYNCHRONIZATION"
echo "============================================================"
echo "Project : $ROOT"
echo "Report  : $REPORT"
echo "Tag     : $TAG"
echo

# ------------------------------------------------------------
# 1. Проверка Git
# ------------------------------------------------------------

git rev-parse --is-inside-work-tree >/dev/null

HEAD_BEFORE="$(git rev-parse HEAD)"
BRANCH="$(git branch --show-current)"

if [ -z "$BRANCH" ]; then
    echo "[FAIL] Detached HEAD. Синхронизация остановлена."
    exit 1
fi

printf '%s\n' "$HEAD_BEFORE" > "$REPORT/head_before.txt"
printf '%s\n' "$BRANCH" > "$REPORT/branch.txt"

git status --short > "$REPORT/status_before.txt"
git remote -v > "$REPORT/remotes_before.txt"

echo "[PASS] Current branch: $BRANCH"
echo "[PASS] Current HEAD:   $HEAD_BEFORE"

# ------------------------------------------------------------
# 2. Полный резервный архив без каталога .git
# ------------------------------------------------------------

echo
echo "=== BACKUP ==="

tar \
    --exclude='./.git' \
    -czf "$BACKUP" \
    -C "$ROOT" \
    .

test -s "$BACKUP"

echo "[PASS] Backup created:"
ls -lh "$BACKUP"

# ------------------------------------------------------------
# 3. Находим последний временной спектральный эксперимент
# ------------------------------------------------------------

FLUX_RUN="$(
    find "$ROOT/experiments/ns_acoustic_external/runs" \
        -maxdepth 1 \
        -type d \
        -name 'flux_time_*' \
        2>/dev/null \
    | sort \
    | tail -n 1
)"

if [ -z "$FLUX_RUN" ]; then
    echo "[FAIL] Не найден flux_time_* эксперимент."
    exit 1
fi

FLUX_JSON="$FLUX_RUN/ns3d_flux_time.json"

if [ ! -s "$FLUX_JSON" ]; then
    echo "[FAIL] Не найден результат:"
    echo "$FLUX_JSON"
    exit 1
fi

echo
echo "=== LATEST PHYSICS PACKET ==="
echo "$FLUX_JSON"

cp "$FLUX_JSON" "$REPORT/ns3d_flux_time.source.json"

# ------------------------------------------------------------
# 4. Создание слепого пакета для Малыша
# Последний настоящий снимок скрывается от входа.
# ------------------------------------------------------------

python - "$FLUX_JSON" "$REPORT" <<'PY'
import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
report = Path(sys.argv[2])

packet = json.loads(
    source.read_text(encoding="utf-8")
)

snapshots = packet["spectral_snapshots"]

if len(snapshots) < 3:
    raise SystemExit(
        "[FAIL] Недостаточно спектральных снимков"
    )

hidden = snapshots[-1]
visible = snapshots[:-1]

task = {
    "schema": "malysh.ns3d-blind-flux-task.v1",

    "source_schema": packet.get("schema"),

    "task": (
        "По видимым спектральным состояниям предсказать "
        "следующее состояние потока энергии."
    ),

    "rules": {
        "do_not_modify_malysh": True,
        "hidden_target_not_in_input": True,

        "predict": [
            "cumulative_flux",
            "energy_spectrum",
            "flux_peak_shell",
            "flux_peak_value",
            "k4_weighted_peak_shell",
        ],

        "physical_invariants": [
            "finite values",
            "divergence approximately zero",
            "nonlinear global energy transfer approximately zero",
        ],
    },

    "parameters": packet["parameters"],
    "initial": packet["initial"],
    "history": packet["history"],
    "visible_snapshots": visible,

    "target_step": hidden["step"],
    "target_time": hidden["time"],
}

target = {
    "schema": "malysh.ns3d-hidden-flux-target.v1",
    "hidden_snapshot": hidden,
}

(report / "blind_task.json").write_text(
    json.dumps(
        task,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

(report / "hidden_target.json").write_text(
    json.dumps(
        target,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print("[PASS] blind_task.json created")
print("[PASS] hidden_target.json created separately")
print("[INFO] target step:", hidden["step"])
print("[INFO] visible snapshots:", len(visible))
PY

# ------------------------------------------------------------
# 5. Внешний запуск существующего мышления Малыша
# Никакие файлы malysh_system не изменяются.
# ------------------------------------------------------------

echo
echo "=== MALYSH READ-ONLY OBSERVER ==="

python - "$REPORT/blind_task.json" "$REPORT" <<'PY'
import inspect
import json
import sys
import traceback
from pathlib import Path

task_path = Path(sys.argv[1])
report = Path(sys.argv[2])

task = json.loads(
    task_path.read_text(encoding="utf-8")
)

visible = task["visible_snapshots"]

# Компактный числовой поток для существующего интерфейса.
# Используются только видимые снимки.
data = []

for snapshot in visible:
    data.extend([
        int(snapshot["step"]),
        int(round(snapshot["time"] * 1_000_000)),
        int(round(snapshot["flux_peak_value"] * 1_000_000_000)),
        int(snapshot["flux_peak_shell"]),
        int(snapshot["k4_weighted_peak_shell"]),
    ])

    flux = snapshot["cumulative_flux"]
    energy = snapshot["energy_spectrum"]

    data.extend(
        int(round(value * 1_000_000_000))
        for value in flux[:12]
    )

    data.extend(
        int(round(value * 1_000_000_000))
        for value in energy[:12]
    )

unresolved = {
    "kind": "blind_ns3d_flux_forecast",

    "instruction": (
        "Сформировать основной прогноз следующего спектрального "
        "состояния и параллельную ветвь возможно. "
        "Не считать скрытый результат известным. "
        "Не заявлять доказательство глобальной регулярности."
    ),

    "target_step": task["target_step"],
    "target_time": task["target_time"],

    "required_outputs": [
        "predicted_flux_direction",
        "predicted_flux_peak_shell",
        "predicted_k4_peak_shell",
        "confidence_or_uncertainty",
        "primary_reasoning",
        "possible_alternative",
        "negative_case",
    ],
}

result = {
    "status": "not_run",
    "error": None,
    "thinking_signature": None,
    "output": None,
}

try:
    from malysh_system.thinking_cycle import (
        run_thinking_cycle,
    )

    result["thinking_signature"] = str(
        inspect.signature(run_thinking_cycle)
    )

    kwargs = {
        "data": data,
        "old_result": {
            "source": "ns3d_flux_visible_history",
            "visible_snapshot_count": len(visible),
        },
        "unresolved": unresolved,
        "root": str(
            Path.home() / "malysh_project"
        ),
    }

    signature = inspect.signature(
        run_thinking_cycle
    )

    filtered = {
        key: value
        for key, value in kwargs.items()
        if key in signature.parameters
    }

    output = run_thinking_cycle(**filtered)

    result["status"] = "completed"
    result["output"] = output

except Exception as exc:
    result["status"] = "failed"
    result["error"] = {
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc(),
    }

(report / "malysh_blind_output.json").write_text(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
        default=str,
    ),
    encoding="utf-8",
)

print("[INFO] Malysh observer status:", result["status"])

if result["thinking_signature"]:
    print(
        "[INFO] thinking signature:",
        result["thinking_signature"],
    )

if result["status"] == "failed":
    print(
        "[WARN] Malysh observer failed, "
        "but physics and Git synchronization remain preserved."
    )
    print("[WARN]", result["error"]["message"])
else:
    print("[PASS] Malysh completed blind observation")
PY

# ------------------------------------------------------------
# 6. Автоматическая оценка доступных численных прогнозов
# ------------------------------------------------------------

python - "$REPORT" <<'PY'
import json
import math
import sys
from pathlib import Path

report = Path(sys.argv[1])

task = json.loads(
    (report / "blind_task.json").read_text(
        encoding="utf-8"
    )
)

target = json.loads(
    (report / "hidden_target.json").read_text(
        encoding="utf-8"
    )
)["hidden_snapshot"]

visible = task["visible_snapshots"]

previous = visible[-2]
current = visible[-1]

def extrapolate(a, b):
    return [
        b_value + (b_value - a_value)
        for a_value, b_value in zip(a, b)
    ]

baseline_flux = extrapolate(
    previous["cumulative_flux"],
    current["cumulative_flux"],
)

baseline_energy = [
    max(0.0, value)
    for value in extrapolate(
        previous["energy_spectrum"],
        current["energy_spectrum"],
    )
]

def relative_error(predicted, actual):
    numerator = sum(
        (p - a) ** 2
        for p, a in zip(predicted, actual)
    ) ** 0.5

    denominator = (
        sum(a * a for a in actual) ** 0.5
        + 1e-30
    )

    return numerator / denominator

baseline = {
    "flux_relative_error": relative_error(
        baseline_flux,
        target["cumulative_flux"],
    ),

    "energy_relative_error": relative_error(
        baseline_energy,
        target["energy_spectrum"],
    ),

    "predicted_flux_peak_shell": int(
        max(
            range(len(baseline_flux)),
            key=lambda index: abs(
                baseline_flux[index]
            ),
        )
    ),

    "actual_flux_peak_shell":
        int(target["flux_peak_shell"]),
}

baseline["peak_shell_error"] = abs(
    baseline["predicted_flux_peak_shell"]
    - baseline["actual_flux_peak_shell"]
)

score = {
    "schema": "malysh.ns3d-blind-score.v1",

    "target_step": target["step"],
    "target_time": target["time"],

    "baseline": baseline,

    "malysh_numeric_score": None,

    "note": (
        "Malysh numeric score remains null unless the existing "
        "thinking output exposes an explicit machine-readable "
        "flux vector. The full Malysh output is preserved "
        "without inventing missing numbers."
    ),
}

(report / "blind_score.json").write_text(
    json.dumps(
        score,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print("[PASS] baseline blind score created")
print(
    "[INFO] baseline flux error:",
    f'{baseline["flux_relative_error"]:.6e}',
)
print(
    "[INFO] baseline energy error:",
    f'{baseline["energy_relative_error"]:.6e}',
)
print(
    "[INFO] baseline peak-shell error:",
    baseline["peak_shell_error"],
)
PY

# ------------------------------------------------------------
# 7. Локальная проверка на секреты и очень большие файлы
# ------------------------------------------------------------

echo
echo "=== PRE-COMMIT SAFETY SCAN ==="

SUSPICIOUS="$REPORT/suspicious_paths.txt"

find . \
    -path './.git' -prune -o \
    -type f \
    \( \
        -iname '*.pem' -o \
        -iname '*.key' -o \
        -iname '*token*' -o \
        -iname '*secret*' -o \
        -iname '*credential*' \
    \) \
    -print > "$SUSPICIOUS"

if [ -s "$SUSPICIOUS" ]; then
    echo "[FAIL] Найдены потенциально секретные файлы:"
    cat "$SUSPICIOUS"
    echo
    echo "Git commit и push остановлены."
    exit 4
fi

echo "[PASS] suspicious filename scan"

LARGE="$REPORT/large_files_over_25mb.txt"

find . \
    -path './.git' -prune -o \
    -type f \
    -size +25M \
    -print > "$LARGE"

if [ -s "$LARGE" ]; then
    echo "[FAIL] Найдены файлы больше 25 MB:"
    cat "$LARGE"
    echo
    echo "Git commit и push остановлены."
    exit 5
fi

echo "[PASS] no files over 25 MB"

# ------------------------------------------------------------
# 8. Safety tag до коммита
# ------------------------------------------------------------

echo
echo "=== SAFETY TAG ==="

git tag -a "$TAG" \
    -m "Safety point before flux experiment synchronization $STAMP"

echo "[PASS] Created tag: $TAG"

# ------------------------------------------------------------
# 9. Коммит всех текущих изменений
# Ничего не удаляется и не отбрасывается.
# ------------------------------------------------------------

echo
echo "=== STAGE ALL PROJECT CHANGES ==="

git add -A

git diff --cached --stat \
    | tee "$REPORT/staged_stat.txt"

git diff --cached --name-status \
    > "$REPORT/staged_name_status.txt"

if git diff --cached --quiet; then
    echo "[INFO] Нет новых изменений для коммита."
    COMMIT_CREATED="no"
else
    git commit \
        -m "Preserve Malysh updates and NS acoustic flux experiments"

    COMMIT_CREATED="yes"
    echo "[PASS] Local commit created:"
    git log -1 --oneline
fi

# ------------------------------------------------------------
# 10. Безопасная синхронизация с remote
# ------------------------------------------------------------

echo
echo "=== REMOTE SYNCHRONIZATION ==="

REMOTE_COUNT="$(
    git remote | wc -l | tr -d ' '
)"

if [ "$REMOTE_COUNT" -eq 0 ]; then
    echo "[WARN] Git remote отсутствует."
    echo "[PASS] Изменения сохранены локально и в backup."
    printf '%s\n' "no_remote" \
        > "$REPORT/sync_status.txt"
else
    if git remote | grep -qx origin; then
        REMOTE="origin"
    else
        REMOTE="$(git remote | head -n 1)"
    fi

    echo "[INFO] Remote: $REMOTE"

    git remote get-url "$REMOTE" \
        | tee "$REPORT/remote_url.txt"

    git fetch "$REMOTE" --tags

    REMOTE_REF="$REMOTE/$BRANCH"

    if git show-ref \
        --verify \
        --quiet \
        "refs/remotes/$REMOTE/$BRANCH"
    then
        COUNTS="$(
            git rev-list \
                --left-right \
                --count \
                "$BRANCH...$REMOTE_REF"
        )"

        AHEAD="$(printf '%s' "$COUNTS" | awk '{print $1}')"
        BEHIND="$(printf '%s' "$COUNTS" | awk '{print $2}')"

        echo "[INFO] Ahead:  $AHEAD"
        echo "[INFO] Behind: $BEHIND"

        {
            echo "ahead=$AHEAD"
            echo "behind=$BEHIND"
        } > "$REPORT/ahead_behind.txt"

        if [ "$AHEAD" -gt 0 ] && [ "$BEHIND" -gt 0 ]; then
            echo "[FAIL] Local and remote histories diverged."
            echo "[INFO] Автоматическое слияние запрещено."
            echo "[INFO] Локальный commit, tag и backup сохранены."
            printf '%s\n' "diverged_manual_review_required" \
                > "$REPORT/sync_status.txt"
            exit 6
        fi

        if [ "$BEHIND" -gt 0 ]; then
            echo "[INFO] Linear remote update detected."
            git rebase "$REMOTE_REF"
            echo "[PASS] Rebase complete"
        fi
    fi

    git push -u "$REMOTE" "$BRANCH"
    git push "$REMOTE" "$TAG"

    printf '%s\n' "pushed" \
        > "$REPORT/sync_status.txt"

    echo "[PASS] Branch pushed: $REMOTE/$BRANCH"
    echo "[PASS] Safety tag pushed: $TAG"
fi

# ------------------------------------------------------------
# 11. Финальный отчёт
# ------------------------------------------------------------

HEAD_AFTER="$(git rev-parse HEAD)"

git status --short \
    | tee "$REPORT/status_after.txt"

git log -5 --oneline \
    > "$REPORT/recent_commits.txt"

{
    echo "timestamp=$STAMP"
    echo "branch=$BRANCH"
    echo "head_before=$HEAD_BEFORE"
    echo "head_after=$HEAD_AFTER"
    echo "backup=$BACKUP"
    echo "tag=$TAG"
    echo "commit_created=$COMMIT_CREATED"
    echo "flux_source=$FLUX_JSON"
    echo "report=$REPORT"
} > "$REPORT/summary.txt"

echo
echo "============================================================"
echo " COMPLETE"
echo "============================================================"
echo "Branch       : $BRANCH"
echo "HEAD before  : $HEAD_BEFORE"
echo "HEAD after   : $HEAD_AFTER"
echo "Safety tag   : $TAG"
echo "Backup       : $BACKUP"
echo "Report       : $REPORT"
echo
echo "Malysh output:"
echo "$REPORT/malysh_blind_output.json"
echo
echo "Blind score:"
echo "$REPORT/blind_score.json"
echo "============================================================"
