#!/usr/bin/env bash
set -euo pipefail

cd ~/malysh_project

echo "=================================================================================================="
echo " МАЛЫШ v12 - ПОИСК РЕАЛЬНОГО ИСТОЧНИКА V1-V18 ДЛЯ РАСЧЕТА №83"
echo "=================================================================================================="

FILES=(
    run_malysh_v12_state83.py
    run_state82_no_mirror.py
    run_chiral_v12_full_master.py
    run_v12_real_chirality_interface.py
    run_pipeline.py
    run_reflected_pipeline.py
)

echo
echo "=== 1. ПРОВЕРКА ФАЙЛОВ ==="

for f in "${FILES[@]}"; do
    if [[ -f "$f" ]]; then
        printf "[OK]   %s\n" "$f"
    else
        printf "[MISS] %s\n" "$f"
    fi
done

echo
echo "=== 2. ЖЕСТКИЕ ПРИВЯЗКИ К №82 ==="

grep -RIn \
    --include='*.py' \
    --exclude-dir=archive_experiments \
    -E '№82|STATE.?82|state.?82|target_state.*82|result_82|_82\.json' \
    . || true

echo
echo "=== 3. ИЩЕМ КОНТРОЛЬНЫЙ V1 №82 ==="

grep -RIn \
    --include='*.py' \
    --include='*.json' \
    --exclude-dir=archive_experiments \
    -E '17[^0-9]+45[^0-9]+7[^0-9]+43[^0-9]+30' \
    . || true

echo
echo "=== 4. ИЩЕМ ОПРЕДЕЛЕНИЯ ЭКСПЕРТОВ ==="

grep -RIn \
    --include='*.py' \
    --exclude-dir=archive_experiments \
    -E \
'EWMA Frequency|Кластерный резонанс|Модульная гармоника|Historical Accuracy|Camp Accuracy|expert_vectors|EXPERT_VECTORS|experts|EXPERTS' \
    . || true

echo
echo "=== 5. ИЩЕМ ГЕНЕРАЦИЮ / ЗАГРУЗКУ ВЕКТОРОВ ==="

grep -RIn \
    --include='*.py' \
    --exclude-dir=archive_experiments \
    -E \
'json\.load|json\.loads|read_text|open\(|runpy|import_module|exec\(|vectors|vector|predictions|prediction|forecast' \
    "${FILES[@]}" 2>/dev/null || true

echo
echo "=== 6. ЦЕПОЧКА IMPORT / RUNPY ==="

grep -nE \
    '^(from |import )|runpy|run_path|exec\(|compile\(' \
    "${FILES[@]}" 2>/dev/null || true

echo
echo "=== 7. ПРОВЕРКА ИСТОРИИ 82 / 574 ==="

grep -RIn \
    --include='*.py' \
    --exclude-dir=archive_experiments \
    -E \
'567|574|len$$history$$|len$$states$$|parse_draw|RAW|history' \
    "${FILES[@]}" 2>/dev/null || true

echo
echo "=== 8. ГДЕ ЗАПУСКАЮТСЯ PIPELINE ==="

grep -RIn \
    --include='*.py' \
    --exclude-dir=archive_experiments \
    -E \
'run_pipeline|run_reflected_pipeline' \
    . || true

echo
echo "=== 9. СИНТАКСИС ==="

python3 -m py_compile "${FILES[@]}"

echo "[OK] Все основные файлы компилируются"

echo
echo "=================================================================================================="
echo " ДИАГНОСТИКА ЗАВЕРШЕНА"
echo "=================================================================================================="
echo
echo "Если V1 [17,45,7,43,30] найден в исходнике/JSON,"
echo "мы увидим точное место хранения старых V1-V18."
echo
echo "Если он нигде не хранится, значит нужно проследить функцию,"
echo "которая генерирует V1-V18 и проверить, получает ли она 82 состояния."
