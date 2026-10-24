#!/usr/bin/env bash
set -euo pipefail

cd ~/malysh_project || exit 1

OUT="diagnose_expert_origins.log"
: > "$OUT"

exec > >(tee -a "$OUT") 2>&1

line() {
    printf '%*s\n' 110 '' | tr ' ' '='
}

section() {
    echo
    line
    echo " $1"
    line
}

section "1. ТЕКУЩИЕ ТЕЛА EXPERT_V1 ... EXPERT_V18"

if [[ -f run_chiral_v12_full_master.py ]]; then
    sed -n '1,110p' run_chiral_v12_full_master.py
else
    echo "[MISS] run_chiral_v12_full_master.py"
fi

section "2. ВСЕ ФУНКЦИИ EXPERT_VN В РАБОЧЕМ ДЕРЕВЕ"

grep -RIn \
    --include='*.py' \
    --exclude-dir='.git' \
    --exclude-dir='__pycache__' \
    --exclude-dir='archive_experiments' \
    -E '^def expert_v([1-9]|1[0-8])\(' \
    . || true

section "3. ВСЕ УПОМИНАНИЯ КОНТРОЛЬНОГО V1"

grep -RIn \
    --include='*.py' \
    --include='*.json' \
    --include='*.txt' \
    --include='*.md' \
    --exclude-dir='.git' \
    --exclude-dir='__pycache__' \
    -E '17[^0-9]+45[^0-9]+7[^0-9]+43[^0-9]+30' \
    . || true

section "4. ФАЙЛЫ С ЛОГИКОЙ ПРОГНОЗА И ЭКСПЕРТОВ"

find . \
    -path './.git' -prune -o \
    -path './__pycache__' -prune -o \
    -type f \
    \( \
        -iname '*expert*' -o \
        -iname '*forecast*' -o \
        -iname '*predict*' -o \
        -iname '*chir*' -o \
        -iname '*state8*' -o \
        -iname '*master*' \
    \) \
    -print \
    | sort

section "5. ПОДОЗРИТЕЛЬНЫЕ ВЫЧИСЛИТЕЛЬНЫЕ ФУНКЦИИ"

grep -RIn \
    --include='*.py' \
    --exclude-dir='.git' \
    --exclude-dir='__pycache__' \
    -E \
'def .*forecast|def .*predict|def .*expert|forecast_[0-9]+|Counter\(|most_common\(|ewma|markov|momentum|similarity|entropy|historical' \
    . || true

section "6. RUN_STATE82_NO_MIRROR.PY"

if [[ -f run_state82_no_mirror.py ]]; then
    sed -n '1,230p' run_state82_no_mirror.py
else
    echo "[MISS] run_state82_no_mirror.py"
fi

section "7. RUN_MALYSH_CHIRALITY_COMPARE.PY"

if [[ -f run_malysh_chirality_compare.py ]]; then
    sed -n '1,360p' run_malysh_chirality_compare.py
else
    echo "[MISS] run_malysh_chirality_compare.py"
fi

section "8. GIT: ИСТОРИЯ RUN_CHIRAL_V12_FULL_MASTER.PY"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git log \
        --all \
        --date=iso \
        --format='%H %ad %s' \
        -- run_chiral_v12_full_master.py || true
else
    echo "[WARN] Каталог не является Git-репозиторием"
fi

section "9. GIT: КОММИТЫ С КОНТРОЛЬНЫМ V1"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git log \
        --all \
        -S'17, 45, 7, 43, 30' \
        --date=iso \
        --format='%H %ad %s' || true
fi

section "10. GIT: КОММИТЫ С EXPERT_V1"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git log \
        --all \
        -S'def expert_v1' \
        --date=iso \
        --format='%H %ad %s' || true
fi

section "11. GIT: ВЕРСИИ MASTER-ФАЙЛА, ГДЕ EXPERT ИСПОЛЬЗУЕТ H"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    commits="$(
        git log \
            --all \
            --format='%H' \
            -- run_chiral_v12_full_master.py \
            | awk '!seen[$0]++'
    )"

    found=0

    while IFS= read -r commit; do
        [[ -n "$commit" ]] || continue

        if ! git cat-file -e \
            "${commit}:run_chiral_v12_full_master.py" \
            2>/dev/null; then
            continue
        fi

        content="$(
            git show \
                "${commit}:run_chiral_v12_full_master.py" \
                2>/dev/null || true
        )"

        [[ -n "$content" ]] || continue

        if printf '%s\n' "$content" \
            | grep -Eq \
            'h\[|h\.|len$$h$$|Counter\(h|for .* in h|history'; then

            found=1

            echo
            echo "[CANDIDATE] $commit"

            git show \
                -s \
                --date=iso \
                --format='%H%n%ad%n%s' \
                "$commit"

            printf '%s\n' "$content" \
                | grep -nE \
                '^def expert_v|h\[|h\.|len$$h$$|Counter\(h|for .* in h|history' \
                | head -n 100
        fi
    done <<< "$commits"

    if [[ "$found" -eq 0 ]]; then
        echo "[INFO] В Git-версиях master-файла использование h не найдено"
    fi
fi

section "12. GIT: ПОИСК EXPERT_V1 ВО ВСЕХ PYTHON-ФАЙЛАХ КОММИТОВ"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    found=0

    while IFS= read -r commit; do
        [[ -n "$commit" ]] || continue

        while IFS= read -r file; do
            [[ -n "$file" ]] || continue

            content="$(
                git show "${commit}:${file}" 2>/dev/null || true
            )"

            [[ -n "$content" ]] || continue

            if printf '%s\n' "$content" \
                | grep -q '^def expert_v1'; then

                found=1
                echo
                echo "[FOUND] commit=$commit file=$file"

                git show \
                    -s \
                    --date=iso \
                    --format='%ad %s' \
                    "$commit"

                printf '%s\n' "$content" \
                    | grep -n -A 12 -B 2 '^def expert_v1' \
                    | head -n 50
            fi
        done < <(
            git ls-tree \
                -r \
                --name-only \
                "$commit" \
                | grep '\.py$' || true
        )
    done < <(
        git rev-list --all | awk '!seen[$0]++'
    )

    if [[ "$found" -eq 0 ]]; then
        echo "[INFO] def expert_v1 в Git-истории не найден"
    fi
fi

section "13. ИТОГ"

echo "Диагностический журнал:"
echo "  $OUT"
echo
echo "Критерий реального кандидата:"
echo "  1. Содержит expert_v1 ... expert_v18 или генератор 18 векторов."
echo "  2. Использует переданную историю h/history."
echo "  3. Не возвращает только фиксированные списки."
echo "  4. Может быть проверен отдельно на 81 и 82 состояниях."
echo
echo "Никакие рабочие файлы этим скриптом не изменены."
