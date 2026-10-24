#!/usr/bin/env bash
set -euo pipefail

cd ~/malysh_project || exit 1

SOURCE="archive_experiments/run_malysh_v12_recalculate_82.py"
OUTPUT="real_recalculate_code.txt"

if [[ ! -f "$SOURCE" ]]; then
    echo "[ERROR] Не найден $SOURCE"
    exit 1
fi

{
    echo "===== IMPORTS / EXPERTS ====="
    sed -n '1,68p' "$SOURCE"

    echo
    echo "===== HISTORY / STATS ====="
    sed -n '69,197p' "$SOURCE"

    echo
    echo "===== TRANSFORM BLOCK 1 ====="
    sed -n '198,346p' "$SOURCE"

    echo
    echo "===== TRANSFORM BLOCK 2 ====="
    sed -n '347,500p' "$SOURCE"

    echo
    echo "===== MAIN EXECUTION ====="
    sed -n '600,760p' "$SOURCE"

    echo
    echo "===== AGGREGATION ====="
    sed -n '760,940p' "$SOURCE"

    echo
    echo "===== REPORT / JSON ====="
    sed -n '1080,1160p' "$SOURCE"

    echo
    echo "===== FUNCTION INDEX ====="
    grep -nE '^def ' "$SOURCE" || true
} > "$OUTPUT"

python3 -m py_compile "$SOURCE"

echo "[OK] Реальный движок компилируется"
echo "[OK] Код извлечён в $OUTPUT"
echo
echo "Размер:"
wc -l -c "$OUTPUT"
echo
echo "Первые функции:"
grep -nE '^def ' "$OUTPUT" | head -n 40 || true
