#!/usr/bin/env bash
set -euo pipefail

cd ~/malysh_project || exit 1

RUNNER="run_malysh_v12_full_state83.py"
EXPERTS="dynamic_experts_state83.py"
BACKUP="${RUNNER}.before_raw_draws_assignment.bak"
LOG="malysh_v12_full_state83.log"
JSON="malysh_v12_chirality_result_83.json"

if [[ ! -f "$RUNNER" ]]; then
    echo "[ERROR] Не найден $RUNNER"
    exit 1
fi

if [[ ! -f "$EXPERTS" ]]; then
    echo "[ERROR] Не найден $EXPERTS"
    echo "[INFO] Сначала необходимо создать динамических экспертов"
    exit 1
fi

cp -p "$RUNNER" "$BACKUP"

python3 - <<'PY'
from pathlib import Path
import re

path = Path("run_malysh_v12_full_state83.py")
text = path.read_text(encoding="utf-8")

already_fixed = re.search(
    r"\braw_draws\s*=\s*prepare_history\s*\(",
    text,
)

if already_fixed:
    print("[OK] raw_draws уже получает результат prepare_history()")
else:
    pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]*)prepare_history\s*\(\s*"
        r"state_source\s*,\s*"
        r"expert_master\s*,?\s*"
        r"\)"
    )

    match = pattern.search(text)

    if not match:
        print("[ERROR] Вызов prepare_history() не найден")
        print()
        print("Найденные упоминания:")

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if "prepare_history" in line:
                print(f"{number}: {line}")

        raise SystemExit(1)

    indent = match.group("indent")

    replacement = (
        indent
        + "raw_draws = prepare_history(\n"
        + indent
        + "    state_source,\n"
        + indent
        + "    expert_master,\n"
        + indent
        + ")"
    )

    text = (
        text[:match.start()]
        + replacement
        + text[match.end():]
    )

    path.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "[OK] Результат prepare_history() "
        "присвоен переменной raw_draws"
    )

updated = path.read_text(encoding="utf-8")

required = [
    "raw_draws = prepare_history(",
    "dynamic_experts_state83",
    "dynamic_experts_state83.install",
    "exec(compiled, namespace)",
]

missing = [
    item
    for item in required
    if item not in updated
]

if missing:
    print("[ERROR] В запускателе отсутствуют элементы:")

    for item in missing:
        print("  -", item)

    raise SystemExit(2)

print("[OK] Динамический контур найден")
PY

if ! python3 -m py_compile \
    dynamic_experts_state83.py \
    run_malysh_v12_full_state83.py \
    run_state82_no_mirror.py \
    run_chiral_v12_full_master.py \
    run_v12_real_chirality_interface.py \
    run_pipeline.py \
    run_reflected_pipeline.py
then
    echo "[ERROR] Ошибка компиляции"
    echo "[INFO] Восстанавливаю $BACKUP"

    cp -p "$BACKUP" "$RUNNER"
    exit 3
fi

echo "[OK] Синтаксис полного контура проверен"

echo
echo "=== КОНТРОЛЬ ИСПРАВЛЕННОГО УЧАСТКА ==="

grep -n -A 6 -B 3 \
    'raw_draws = prepare_history' \
    "$RUNNER" || true

rm -f "$LOG" "$JSON"

echo
echo "=================================================================================================="
echo " ЗАПУСК РЕАЛЬНОГО ПЕРЕСЧЁТА МАЛЫША №83"
echo "=================================================================================================="

set +e

python3 "$RUNNER" 2>&1 \
    | tee "$LOG"

run_status=${PIPESTATUS[0]}

set -e

if [[ "$run_status" -ne 0 ]]; then
    echo
    echo "[ERROR] Расчёт завершился с кодом $run_status"
    echo
    echo "=== ПОСЛЕДНИЕ СТРОКИ ЖУРНАЛА ==="

    tail -n 50 "$LOG"
    exit "$run_status"
fi

echo
echo "=================================================================================================="
echo " ПРОВЕРКА ДИНАМИЧЕСКОГО ПЕРЕСЧЁТА №83"
echo "=================================================================================================="

if grep -Fq \
    "NameError: name 'raw_draws' is not defined" \
    "$LOG"
then
    echo "[ERROR] raw_draws всё ещё недоступен"
    exit 4
else
    echo "[OK] Ошибка raw_draws устранена"
fi

if grep -Fq \
    "Пересчитано экспертов" \
    "$LOG"
then
    echo "[OK] Динамический слой выполнен"
else
    echo "[ERROR] Динамический слой не запускался"
    exit 5
fi

changed_line="$(
    grep -F \
        "Изменено против №82" \
        "$LOG" \
        | tail -n 1 \
        || true
)"

if [[ -n "$changed_line" ]]; then
    echo "$changed_line"
else
    echo "[ERROR] Нет контроля изменения V1-V18"
    exit 6
fi

echo
echo "=== ДИНАМИЧЕСКИЕ V1-V18 ==="

grep -E \
    '$$V([1-9]|1[0-8])$$ MAIN №83' \
    "$LOG" \
    | head -n 18 \
    || true

echo
echo "=== ПОЛНЫЙ ИНТЕРФЕЙС ==="

for pattern in \
    "Исторических состояний : 82" \
    "Всего входных значений : 574" \
    "РАСЧЁТ №83" \
    "ДЕТАЛЬНЫЙ ВЫВОД ПО 18 ЭКСПЕРТНЫМ ВЕКТОРАМ" \
    "ПЛОТНОСТЬ БЕЗ ХИРАЛЬНОСТИ" \
    "ПЛОТНОСТЬ С ХИРАЛЬНОСТЬЮ" \
    "ИТОГОВЫЙ РАСЧЁТ СОСТОЯНИЯ №83" \
    "НАВИГАЦИОННАЯ КАРТА МАЛЫША №83" \
    "ОБЩЕЕ ПОЛЕ ДВУХ ВЕТВЕЙ" \
    "ЧЕЛОВЕЧЕСКИЙ ИТОГ МАЛЫША №83" \
    "ROOT / JILS / TAIL №83"
do
    if grep -Fq "$pattern" "$LOG"; then
        printf '[OK]   %s\n' "$pattern"
    else
        printf '[MISS] %s\n' "$pattern"
    fi
done

echo
echo "=== JSON №83 ==="

if [[ ! -f "$JSON" ]]; then
    echo "[ERROR] JSON №83 не создан"
    exit 7
fi

python3 - <<'PY'
import json
from pathlib import Path

path = Path("malysh_v12_chirality_result_83.json")

data = json.loads(
    path.read_text(encoding="utf-8")
)

vectors = data.get("vectors", [])

print("[OK] Файл              :", path)
print("[OK] target_state      :", data.get("target_state"))
print("[OK] historical_states :", data.get("historical_states"))
print("[OK] total_values      :", data.get("total_values"))
print("[OK] vectors           :", len(vectors))

if data.get("target_state") != 83:
    raise SystemExit("[ERROR] target_state не равен 83")

if data.get("historical_states") != 82:
    raise SystemExit(
        "[ERROR] historical_states не равен 82"
    )

if data.get("total_values") != 574:
    raise SystemExit(
        "[ERROR] total_values не равен 574"
    )

if len(vectors) != 18:
    raise SystemExit(
        "[ERROR] число экспертных векторов не равно 18"
    )
PY

echo
echo "=================================================================================================="
echo " ГОТОВО: ДИНАМИЧЕСКИЙ РАСЧЁТ №83 ВЫПОЛНЕН"
echo "=================================================================================================="
