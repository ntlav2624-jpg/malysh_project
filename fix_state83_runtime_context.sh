#!/usr/bin/env bash
set -euo pipefail

cd ~/malysh_project || exit 1

F="run_malysh_v12_full_state83.py"
BACKUP="${F}.before_runtime_context_fix"

if [[ ! -f "$F" ]]; then
    echo "[ERROR] Не найден $F"
    exit 1
fi

cp -p "$F" "$BACKUP"

python3 - <<'PY'
from pathlib import Path
import re

path = Path("run_malysh_v12_full_state83.py")
text = path.read_text(encoding="utf-8")

# После синхронизации модулей создаём единый runtime-контекст.
anchor = '''    state_source.RAW_DRAWS = raw_draws
    expert_master.RAW_DRAWS = raw_draws
    expert_master.parse_draw = parse_draw
'''

if anchor not in text:
    raise SystemExit(
        "[ERROR] Не найден блок синхронизации истории"
    )

inject = anchor + '''
    # Единый runtime-контекст полного расчёта №83.
    runtime_raw_draws = raw_draws
    runtime_parse_draw = parse_draw
    runtime_state_source = state_source
    runtime_expert_master = expert_master
'''

# Не дублируем блок при повторном запуске.
if "runtime_parse_draw = parse_draw" not in text:
    text = text.replace(anchor, inject, 1)

# Находим namespace, используемый exec().
pattern = re.compile(
    r'''    namespace = \{
.*?
    \}
''',
    re.DOTALL,
)

match = pattern.search(text)

if not match:
    raise SystemExit(
        "[ERROR] Не найден namespace для exec()"
    )

new_namespace = '''    namespace = {
        "__name__": "__main__",
        "__file__": str(INTERFACE),
        "__package__": None,
        "__cached__": None,

        # История №83.
        "raw_draws": runtime_raw_draws,
        "RAW_DRAWS": runtime_raw_draws,

        # Парсер истории.
        "parse_draw": runtime_parse_draw,

        # Модули-источники.
        "state_source": runtime_state_source,
        "expert_master": runtime_expert_master,

        # Параметры состояния.
        "TARGET_STATE": TARGET_STATE,
        "FACT_MAIN": FACT_MAIN,
        "FACT_EURO": FACT_EURO,
        "FACT_FLAT": FACT_FLAT,
    }
'''

text = (
    text[:match.start()]
    + new_namespace
    + text[match.end():]
)

path.write_text(text, encoding="utf-8")

print("[OK] Полный runtime-контекст №83 установлен")
PY

echo
echo "=== ПРОВЕРКА КОНТЕКСТА ==="

grep -nE \
    'runtime_raw_draws|runtime_parse_draw|"parse_draw"|"RAW_DRAWS"|namespace = ' \
    "$F" \
    | head -n 50

echo
echo "=== СИНТАКСИС ==="

if ! python3 -m py_compile \
    run_malysh_v12_full_state83.py \
    run_v12_real_chirality_interface.py \
    run_chiral_v12_full_master.py \
    run_state82_no_mirror.py \
    run_pipeline.py \
    run_reflected_pipeline.py
then
    echo "[ERROR] Синтаксис нарушен. Восстанавливаю файл."
    cp -p "$BACKUP" "$F"
    exit 1
fi

echo "[OK] Синтаксис проверен"

rm -f \
    malysh_v12_full_state83.log \
    malysh_v12_chirality_result_83.json

echo
echo "=================================================================================================="
echo " ЗАПУСК ПОЛНОГО №83"
echo "=================================================================================================="

set +e

python3 run_malysh_v12_full_state83.py 2>&1 \
    | tee malysh_v12_full_state83.log

STATUS=${PIPESTATUS[0]}

set -e

echo
echo "=================================================================================================="
echo " КОНТРОЛЬ"
echo "=================================================================================================="

if [[ "$STATUS" -ne 0 ]]; then
    echo "[ERROR] Расчёт завершился с кодом $STATUS"
    echo
    echo "=== ПОСЛЕДНИЕ СТРОКИ ==="
    tail -n 60 malysh_v12_full_state83.log
    exit "$STATUS"
fi

echo "[OK] Python завершился без ошибки"

if grep -Fq \
    "NameError: name 'parse_draw' is not defined" \
    malysh_v12_full_state83.log
then
    echo "[ERROR] parse_draw всё ещё недоступен"
    exit 2
else
    echo "[OK] parse_draw доступен"
fi

if grep -Fq \
    "NameError: name 'raw_draws' is not defined" \
    malysh_v12_full_state83.log
then
    echo "[ERROR] raw_draws всё ещё недоступен"
    exit 3
else
    echo "[OK] raw_draws доступен"
fi

echo
echo "=== ИНВАРИАНТЫ И СЕКЦИИ ==="

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
echo "=== ПРОВЕРКА ДИНАМИЧЕСКИХ ЭКСПЕРТОВ ==="

grep -E \
    'Пересчитано экспертов|Изменено против №82|MAIN №83|динамическ|Динамическ' \
    malysh_v12_full_state83.log \
    | head -n 80 \
    || true

echo
echo "=== JSON №83 ==="

if [[ ! -f malysh_v12_chirality_result_83.json ]]; then
    echo "[ERROR] JSON №83 не создан"
    exit 4
fi

python3 - <<'PY'
import json
from pathlib import Path

path = Path("malysh_v12_chirality_result_83.json")
data = json.loads(path.read_text(encoding="utf-8"))

print("[OK] JSON:", path)
print(" target_state      :", data.get("target_state"))
print(" historical_states :", data.get("historical_states"))
print(" total_values      :", data.get("total_values"))
print(" vectors           :", len(data.get("vectors", [])))
PY

echo
echo "=================================================================================================="
echo " [OK] ПОЛНЫЙ КОНТУР №83 ЗАВЕРШЁН"
echo "=================================================================================================="
