import os
import json
import glob

vault_dir = "memory_vault"
files = sorted(glob.glob(os.path.join(vault_dir, "passport_*.json")))

if not files:
    print("[Ошибка]: Нет данных в memory_vault для глубокого анализа.")
    exit(0)

history = []
for f in files:
    with open(f, "r") as file:
        history.append(json.load(file))

total_gens = len(history)
classes_stat = {}
modes_count = {}
resonance_points = []
turbulence_points = []

for p in history:
    gen = p.get("generation", 0)
    s_class = p.get("signal_class", "unknown")
    mode = p.get("mode", "N/A")
    j_tot = p.get("J", {}).get("total", 0.0)
    conf = p.get("confidence", 0.0)
    energy = p.get("energy", 0.0)
    s_n = p.get("S_n", 0.0)
    
    # Статистика по классам
    if s_class not in classes_stat:
        classes_stat[s_class] = {"count": 0, "j_sum": 0.0, "c_sum": 0.0}
    classes_stat[s_class]["count"] += 1
    classes_stat[s_class]["j_sum"] += j_tot
    classes_stat[s_class]["c_sum"] += conf
    
    # Подсчет режимов
    modes_count[mode] = modes_count.get(mode, 0) + 1
    
    # Поиск точек резонанса и турбулентности
    if s_n < 0.05 and j_tot < 1.0:
        resonance_points.append(gen)
    if energy > 180.0 or j_tot > 4.0:
        turbulence_points.append(gen)

print(f"=== ГЛУБЫЙ АНАЛИЗ ИСТОРИИ ПОКОЛЕНИЙ (Всего: {total_gens}) ===")

print("\n1. Статистика по классам сигналов:")
for sc, data in classes_stat.items():
    avg_j = data["j_sum"] / data["count"]
    avg_c = data["c_sum"] / data["count"]
    print(f"   • Класс [{sc}]: запусків={data['count']}, ср. J={avg_j:.4f}, ср. C={avg_c:.4f}")

print("\n2. Распределение режимов контура:")
for mode, count in modes_count.items():
    print(f"   • Режим {mode}: {count} раз(а)")

print(f"\n3. Точки резонанса (стабильность): поколения {resonance_points if resonance_points else 'нет'}")
print(f"4. Точки турбулентности (высокая энергия/штраф): поколения {turbulence_points if turbulence_points else 'нет'}")
print("\n[Анализ завершен]: Профиль системы построен.")
