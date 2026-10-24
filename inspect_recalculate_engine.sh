#!/usr/bin/env bash
set -euo pipefail

cd ~/malysh_project || exit 1

F="archive_experiments/run_malysh_v12_recalculate_82.py"

if [[ ! -f "$F" ]]; then
    echo "[ERROR] Не найден: $F"
    exit 1
fi

OUT="inspect_recalculate_engine.log"
: > "$OUT"

exec > >(tee -a "$OUT") 2>&1

section() {
    echo
    printf '%*s\n' 110 '' | tr ' ' '='
    echo " $1"
    printf '%*s\n' 110 '' | tr ' ' '='
}

section "1. HISTORY / STATS"
sed -n '60,180p' "$F"

section "2. ПЕРВЫЙ БЛОК ПЕРЕСЧЕТА"
sed -n '180,340p' "$F"

section "3. ВТОРОЙ БЛОК ПЕРЕСЧЕТА"
sed -n '340,500p' "$F"

section "4. MAIN: ПРОХОЖДЕНИЕ V1-V18"
sed -n '600,760p' "$F"

section "5. ФИНАЛЬНАЯ АГРЕГАЦИЯ"
sed -n '760,940p' "$F"

section "6. REPORT / JSON"
sed -n '1080,1160p' "$F"

section "7. ИМЕНА ВСЕХ ФУНКЦИЙ"
grep -nE '^def ' "$F" || true

section "8. ГДЕ ИСПОЛЬЗУЕТСЯ HISTORY/STATS"
grep -nE \
    'history|stats\[|history_size|main_vector|expert_index|phase' \
    "$F" || true

section "9. ГДЕ ВЫЗЫВАЮТСЯ V1-V18"
grep -nE \
    'expert$$history$$|EXPERTS|for index.*expert' \
    "$F" || true

section "10. СИНТАКСИС"
python3 -m py_compile "$F"

echo "[OK] Архивный движок синтаксически исправен"

section "11. ИТОГ"
echo "Источник:"
echo "  $F"
echo
echo "Диагностический лог:"
echo "  $OUT"
echo
echo "Никакие рабочие файлы не изменены."
