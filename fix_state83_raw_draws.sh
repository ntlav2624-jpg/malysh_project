#!/usr/bin/env bash
set -euo pipefail

cd ~/malysh_project || exit 1

F="run_malysh_v12_full_state83.py"
BACKUP="${F}.before_raw_draws_fix"

if [[ ! -f "$F" ]]; then
    echo "[ERROR] Не найден $F"
    exit 1
fi

cp -p "$F" "$BACKUP"

python3 - <<'PY'
from pathlib import Path

path = Path("run_malysh_v12_full_state83.py")
text = path.read_text(encoding="utf-8")

anchor = '''    state_source.RAW_DRAWS = raw_draws
    expert_master.RAW_DRAWS = raw_draws
    expert_master.parse_draw = parse_draw
'''

if anchor not in text:
    raise SystemExit(
        "[ERROR] Не найден блок синхронизации RAW_DRAWS. "
        "Файл восстановлен из backup."
    )

replacement = '''    state_source.RAW_DRAWS = raw_draws
    expert_master.RAW_DRAWS = raw_draws
    expert_master.parse_draw = parse_draw

    # Передаём историю в runtime namespace явно.
    # Это устраняет NameError для динамического слоя,
    # не добавляя факт №82 повторно.
    runtime_raw_draws = raw_draws
'''

text = text.replace(anchor, replacement, 1)

old_namespace = '''    namespace = {
        "__name__": "__main__",
        "__file__": str(INTERFACE),
        "__package__": None,
        "__cached__": None,
    }
'''

new_namespace = '''    namespace = {
        "__name__": "__main__",
        "__file__": str(INTERFACE),
        "__package__": None,
        "__cached__": None,

        # Runtime history №83.
        "raw_draws": runtime_raw_draws,
        "RAW_DRAWS": runtime_raw_draws,
        "parse_draw": parse_draw,
    }
'''

if old_namespace not in text:
    raise SystemExit(
        "[ERROR] Не найден namespace интерфейса."
    )

text = text.replace(
    old_namespace,
    new_namespace,
    1,
)

path.write_text(text, encoding="utf-8")

print("[OK] raw_draws передан в runtime namespace")
PY

if ! python3 -m py_compile \
    run_malysh_v12_full_state83.py \
    run_state82_no_mirror.py \
    run_chiral_v12_full_master.py \
    run_v12_real_chirality_interface.py \
    run_pipeline.py \
    run_reflected_pipeline.py
then
    echo "[ERROR] Ошибка синтаксиса. Восстанавливаю backup."
    cp -p "$BACKUP" "$F"
    exit 1
fi

echo "[OK] Синтаксис проверен"

rm -f \
    malysh_v12_full_state83.log \
    malysh_v12_chirality_result_83.json

echo
echo "=================================================================================================="
echo " ЗАПУСК ПОЛНОГО РАСЧЁТА №83"
echo "=================================================================================================="

python3 run_malysh_v12_full_state83.py 2>&1 \
    | tee malysh_v12_full_state83.log

echo
echo "=================================================================================================="
echo " ПРОВЕРКА №83"
echo "=================================================================================================="

if grep -Fq \
    "NameError: name 'raw_draws' is not defined" \
    malysh_v12_full_state83.log
then
    echo "[ERROR] raw_draws всё ещё недоступен"
    exit 2
else
    echo "[OK] NameError raw_draws отсутствует"
fi

for pattern in \
    "Исторических состояний   : 82" \
    "Всего входных значений   : 574" \
    "ДЕТАЛЬНЫЙ ВЫВОД ПО 18 ЭКСПЕРТНЫМ ВЕКТОРАМ" \
    "ПЛОТНОСТЬ БЕЗ ХИРАЛЬНОСТИ" \
    "ПЛОТНОСТЬ С ХИРАЛЬНОСТЬЮ" \
    "ИТОГОВЫЙ РАСЧЁТ СОСТОЯНИЯ №83" \
    "НАВИГАЦИОННАЯ КАРТА МАЛЫША №83" \
    "ОБЩЕЕ ПОЛЕ ДВУХ ВЕТВЕЙ" \
    "ЧЕЛОВЕЧЕСКИЙ ИТОГ МАЛЫША №83"
do
    if grep -Fq "$pattern" malysh_v12_full_state83.log; then
        printf '[OK]   %s\n' "$pattern"
    else
        printf '[MISS] %s\n' "$pattern"
    fi
done

echo
echo "=== ДИНАМИЧЕСКИЙ ПЕРЕСЧЁТ ==="

grep -E \
    'Пересчитано экспертов|Изменено против №82|$$V[0-9]+$$.*MAIN №83' \
    malysh_v12_full_state83.log \
    | head -n 50 \
    || true

echo
echo "=== JSON №83 ==="

if [[ -f malysh_v12_chirality_result_83.json ]]; then
    echo "[OK] JSON №83 создан"
    ls -l malysh_v12_chirality_result_83.json
else
    echo "[ERROR] JSON №83 не создан"
    exit 3
fi

echo
echo "=================================================================================================="
echo " ГОТОВО"
echo "=================================================================================================="
