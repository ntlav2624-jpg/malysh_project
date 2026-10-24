#!/usr/bin/env bash
set -u

cd ~/malysh_project || exit 1

LOG="trace_malysh_experts.log"
: > "$LOG"

section() {
    printf '\n%s\n' \
        "==================================================================================================" \
        "$1" \
        "==================================================================================================" \
        | tee -a "$LOG"
}

run_search() {
    local title="$1"
    shift

    section "$title"

    "$@" 2>&1 | tee -a "$LOG" || true
}

section "1. ВСЕ РАБОЧИЕ PYTHON-ФАЙЛЫ"

find . \
    -path './.git' -prune -o \
    -path './archive_experiments' -prune -o \
    -type f -name '*.py' -print \
    | sort \
    | tee -a "$LOG"

run_search \
    "2. ВСЕ ФУНКЦИИ EXPERT_VN В РАБОЧЕМ ДЕРЕВЕ" \
    grep -RInE \
    --include='*.py' \
    --exclude-dir='.git' \
    --exclude-dir='archive_experiments' \
    'def[[:space:]]+expert_v[0-9]+|expert_v[0-9]+'

run_search \
    "3. КОНТРОЛЬНЫЙ ВЕКТОР V1 В РАБОЧЕМ ДЕРЕВЕ" \
    grep -RInE \
    --include='*.py' \
    --include='*.json' \
    --include='*.txt' \
    --exclude-dir='.git' \
    --exclude-dir='archive_experiments' \
    '17[^0-9]+45[^0-9]+7[^0-9]+43[^0-9]+30'

run_search \
    "4. НАЗВАНИЯ ЭКСПЕРТОВ" \
    grep -RInE \
    --include='*.py' \
    --include='*.json' \
    --exclude-dir='.git' \
    --exclude-dir='archive_experiments' \
    'EWMA Frequency|Кластерный резонанс|Модульная гармоника|Historical Accuracy|Camp Accuracy'

run_search \
    "5. ПОДОЗРИТЕЛЬНЫЕ ВЫЧИСЛИТЕЛЬНЫЕ ФУНКЦИИ" \
    grep -RInE \
    --include='*.py' \
    --exclude-dir='.git' \
    --exclude-dir='archive_experiments' \
    'def[[:space:]].*(expert|vector|predict|forecast|pipeline|history|state)|generate.*vector|build.*vector|make.*vector'

run_search \
    "6. ЗАГРУЗКА И ПЕРЕДАЧА ИСТОРИИ" \
    grep -RInE \
    --include='*.py' \
    --exclude-dir='.git' \
    --exclude-dir='archive_experiments' \
    'history|states|draws|RAW|parse_draw|json\.load|read_text|run_path|exec\('

run_search \
    "7. ВЫЗОВЫ MASTER И PIPELINE" \
    grep -RInE \
    --include='*.py' \
    --exclude-dir='.git' \
    --exclude-dir='archive_experiments' \
    'run_chiral_v12_full_master|run_pipeline|run_reflected_pipeline|run_state82_no_mirror'

section "8. GIT: ИСТОРИЯ MASTER-ФАЙЛА"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git log \
        --all \
        --oneline \
        --decorate \
        -- run_chiral_v12_full_master.py \
        2>&1 | tee -a "$LOG" || true
else
    echo "[INFO] Каталог не является Git-репозиторием" | tee -a "$LOG"
fi

section "9. GIT: КОММИТЫ С КОНТРОЛЬНЫМ V1"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git log \
        --all \
        --oneline \
        -S'17, 45, 7, 43, 30' \
        -- '*.py' '*.json' \
        2>&1 | tee -a "$LOG" || true
fi

section "10. GIT: КОММИТЫ С EXPERT_V1"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git log \
        --all \
        --oneline \
        -S'expert_v1' \
        -- '*.py' \
        2>&1 | tee -a "$LOG" || true
fi

section "11. GIT: КОММИТЫ С ПЕРЕДАЧЕЙ HISTORY В EXPERT"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git log \
        --all \
        --oneline \
        -G'expert.*\(.*(history|states|draws|H)' \
        -- '*.py' \
        2>&1 | tee -a "$LOG" || true
fi

section "12. PYTHON AST: ФУНКЦИИ, КЛАССЫ И ВЫЗОВЫ EXPERT"

python3 - <<'PY' 2>&1 | tee -a "$LOG"
import ast
from pathlib import Path

root = Path(".")
excluded = {".git", "archive_experiments", "__pycache__"}

for path in sorted(root.rglob("*.py")):
    if any(part in excluded for part in path.parts):
        continue

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except Exception as exc:
        print(f"[PARSE ERROR] {path}: {exc}")
        continue

    hits = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            low = node.name.lower()
            if any(key in low for key in (
                "expert",
                "vector",
                "predict",
                "forecast",
                "history",
                "pipeline",
            )):
                args = [arg.arg for arg in node.args.args]
                hits.append(
                    f"line {node.lineno}: def {node.name}"
                    f"({', '.join(args)})"
                )

        elif isinstance(node, ast.ClassDef):
            low = node.name.lower()
            if any(key in low for key in (
                "expert",
                "vector",
                "pipeline",
            )):
                hits.append(
                    f"line {node.lineno}: class {node.name}"
                )

        elif isinstance(node, ast.Call):
            func = node.func

            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            else:
                name = ""

            if "expert" in name.lower():
                hits.append(
                    f"line {node.lineno}: call {name}(...)"
                )

    if hits:
        print(f"\n[{path}]")
        for hit in hits:
            print(f"  {hit}")
PY

section "13. СТАТИЧЕСКИЕ СПИСКИ, ПОХОЖИЕ НА MAIN/EURO"

python3 - <<'PY' 2>&1 | tee -a "$LOG"
import ast
from pathlib import Path

excluded = {".git", "archive_experiments", "__pycache__"}

for path in sorted(Path(".").rglob("*.py")):
    if any(part in excluded for part in path.parts):
        continue

    try:
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )
    except Exception:
        continue

    hits = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple)):
            continue

        values = []

        for item in node.elts:
            if isinstance(item, ast.Constant) and isinstance(item.value, int):
                values.append(item.value)
            else:
                values = []
                break

        if len(values) == 5 and all(1 <= value <= 50 for value in values):
            hits.append(
                f"line {node.lineno}: MAIN-like {values}"
            )
        elif len(values) == 2 and all(1 <= value <= 12 for value in values):
            hits.append(
                f"line {node.lineno}: EURO-like {values}"
            )

    if hits:
        print(f"\n[{path}]")
        for hit in hits[:100]:
            print(f"  {hit}")
PY

section "14. ИТОГ"

echo "[OK] Диагностика завершена" | tee -a "$LOG"
echo "[OK] Полный результат: $LOG" | tee -a "$LOG"

echo
echo "Краткие совпадения:"
grep -nE \
    'expert_v[0-9]+|EWMA Frequency|17[^0-9]+45[^0-9]+7[^0-9]+43[^0-9]+30|MAIN-like' \
    "$LOG" \
    | head -n 120 \
    || true
