#!/usr/bin/env bash
set -euo pipefail

cd ~/malysh_project || exit 1

SOURCE="archive_experiments/run_malysh_v12_recalculate_82.py"
TARGET="run_malysh_v12_recalculate_83_real.py"
LOG83="malysh_v12_recalculated_83.log"
JSON82="malysh_v12_recalculated_82.json"
JSON83="malysh_v12_recalculated_83.json"

if [[ ! -f "$SOURCE" ]]; then
    echo "[ERROR] Не найден архивный движок: $SOURCE"
    exit 1
fi

cp -p "$SOURCE" "$TARGET"

python3 - <<'PY'
from pathlib import Path

path = Path("run_malysh_v12_recalculate_83_real.py")
text = path.read_text(encoding="utf-8")

old_load = '''def load_history():
    history = []

    for raw in RAW_DRAWS:
'''

new_load = '''def load_history():
    history = []

    runtime_draws = list(RAW_DRAWS)

    fact_82_raw = "5.16.32.34.38.8.9"
    fact_82 = list(parse_draw(fact_82_raw))

    expected_fact = [5, 16, 32, 34, 38, 8, 9]

    if fact_82 != expected_fact:
        raise RuntimeError(
            "parse_draw неверно обработал факт №82: "
            + repr(fact_82)
        )

    fact_exists = any(
        list(parse_draw(raw)) == fact_82
        for raw in runtime_draws
    )

    if not fact_exists:
        runtime_draws.append(fact_82_raw)

    for raw in runtime_draws:
'''

if old_load not in text:
    raise SystemExit(
        "[ERROR] Не найден исходный блок load_history()"
    )

text = text.replace(old_load, new_load, 1)

replacements = (
    (
        "if len(history) != 81:",
        "if len(history) != 82:",
    ),
    (
        "Ожидалось 81 состояние",
        "Ожидалось 82 состояния",
    ),
    (
        "[ПОЛНЫЙ ПЕРЕСЧЁТ №82:",
        "[ПОЛНЫЙ ПЕРЕСЧЁТ №83:",
    ),
    (
        '" [✓] 81 историческое состояние"',
        '" [✓] 82 исторических состояния"',
    ),
    (
        '" [✓] 567 входных значений"',
        '" [✓] 574 входных значения"',
    ),
    (
        '"target": 82',
        '"target": 83',
    ),
    (
        '"history": 81',
        '"history": 82',
    ),
    (
        '"malysh_v12_recalculated_82.json"',
        '"malysh_v12_recalculated_83.json"',
    ),
)

for old, new in replacements:
    if old not in text:
        raise SystemExit(
            "[ERROR] Не найден маркер: " + repr(old)
        )

    text = text.replace(old, new)

old_report = '''    report = {
        "target": 83,
        "history": 82,
        "geometry": "bounded_toroidal",
'''

new_report = '''    report = {
        "target": 83,
        "history": 82,
        "total_values": 574,
        "actual_state_82": {
            "main": [5, 16, 32, 34, 38],
            "euro": [8, 9],
            "raw": "5.16.32.34.38.8.9",
        },
        "calculation_mode": (
            "fixed_legacy_probes_"
            "history_dependent_bounded_toroidal"
        ),
        "geometry": "bounded_toroidal",
'''

if old_report not in text:
    raise SystemExit(
        "[ERROR] Не найден блок report"
    )

text = text.replace(
    old_report,
    new_report,
    1,
)

path.write_text(text, encoding="utf-8")

print("[OK] Создан движок:", path)
PY

python3 -m py_compile "$TARGET"

echo "[OK] Синтаксис движка №83 проверен"

rm -f "$LOG83" "$JSON83"

python3 "$TARGET" 2>&1 | tee "$LOG83"

echo
echo "=================================================================================================="
echo " КОНТРОЛЬ РЕАЛЬНОГО РАСЧЁТА №83"
echo "=================================================================================================="

python3 - <<'PY'
from pathlib import Path
import json
import sys

json82_path = Path("malysh_v12_recalculated_82.json")
json83_path = Path("malysh_v12_recalculated_83.json")

if not json83_path.exists():
    raise SystemExit("[ERROR] JSON №83 не создан")

data83 = json.loads(
    json83_path.read_text(encoding="utf-8")
)

checks = {
    "target": data83.get("target") == 83,
    "history": data83.get("history") == 82,
    "total_values": data83.get("total_values") == 574,
    "vectors": len(data83.get("vectors", [])) == 18,
}

failed = [
    name
    for name, status in checks.items()
    if not status
]

if failed:
    print("[ERROR] Нарушены инварианты:", failed)
    print(
        "[DEBUG] target:",
        data83.get("target"),
    )
    print(
        "[DEBUG] history:",
        data83.get("history"),
    )
    print(
        "[DEBUG] total_values:",
        data83.get("total_values"),
    )
    print(
        "[DEBUG] vectors:",
        len(data83.get("vectors", [])),
    )
    sys.exit(1)

print("[OK] target       : 83")
print("[OK] history      : 82")
print("[OK] total_values : 574")
print("[OK] vectors      : 18")

final83 = data83["final"]
direct83 = final83["without_chirality"]
chiral83 = final83["with_chirality"]

print()
print("ФИНАЛ №83")
print()
print("БЕЗ ХИРАЛЬНОСТИ")
print(" MAIN :", direct83["main"])
print(" EURO :", direct83["euro"])
print()
print("С ХИРАЛЬНОСТЬЮ")
print(" MAIN :", chiral83["main"])
print(" EURO :", chiral83["euro"])

if not json82_path.exists():
    print()
    print("[INFO] JSON №82 отсутствует")
    print("[INFO] Сравнение с №82 пропущено")
    sys.exit(0)

data82 = json.loads(
    json82_path.read_text(encoding="utf-8")
)

vectors82 = data82.get("vectors", [])
vectors83 = data83.get("vectors", [])

changed_experts = []
score_only_changes = []
vector_changes = []

for index, vector83 in enumerate(vectors83):
    expert_id = index + 1

    if index >= len(vectors82):
        changed_experts.append(expert_id)
        vector_changes.append(expert_id)
        continue

    vector82 = vectors82[index]

    direct82 = vector82.get(
        "without_chirality",
        {},
    )
    direct83_item = vector83.get(
        "without_chirality",
        {},
    )

    chiral82 = vector82.get(
        "with_chirality",
        {},
    )
    chiral83_item = vector83.get(
        "with_chirality",
        {},
    )

    numbers82 = {
        "direct_main": direct82.get("main"),
        "direct_euro": direct82.get("euro"),
        "chiral_main": chiral82.get("main"),
        "chiral_euro": chiral82.get("euro"),
    }

    numbers83 = {
        "direct_main": direct83_item.get("main"),
        "direct_euro": direct83_item.get("euro"),
        "chiral_main": chiral83_item.get("main"),
        "chiral_euro": chiral83_item.get("euro"),
    }

    all82 = {
        "direct": direct82,
        "chiral": chiral82,
    }

    all83 = {
        "direct": direct83_item,
        "chiral": chiral83_item,
    }

    if all82 != all83:
        changed_experts.append(expert_id)

    if numbers82 != numbers83:
        vector_changes.append(expert_id)
    elif all82 != all83:
        score_only_changes.append(expert_id)

print()
print("СРАВНЕНИЕ С №82")
print(
    "Изменились результаты экспертов:",
    changed_experts or "нет",
)
print(
    "Изменились выбранные числа:",
    vector_changes or "нет",
)
print(
    "Изменились только оценки поля:",
    score_only_changes or "нет",
)

final_changed = (
    data82.get("final")
    != data83.get("final")
)

if final_changed:
    print("[OK] Финал №83 отличается от №82")
else:
    print(
        "[WARN] Финал сохранился, несмотря на "
        "изменение исторического поля"
    )

if not changed_experts:
    print(
        "[ERROR] Добавление факта №82 не изменило "
        "ни векторы, ни оценки поля"
    )
    sys.exit(2)

print()
print(
    "[OK] Подтверждён исторически зависимый "
    "тороидальный пересчёт №83"
)
PY

echo
echo "=================================================================================================="
echo " ГОТОВО"
echo "=================================================================================================="
echo "Движок : $TARGET"
echo "Лог    : $LOG83"
echo "JSON   : $JSON83"
