import os
import json
import glob
from datetime import datetime

vault_dir = "memory_vault"
files = sorted(glob.glob(os.path.join(vault_dir, "passport_*.json")))

if not files:
    print("[Ошибка]: Нет данных в memory_vault для формирования паспорта.")
    exit(0)

history = []
for f in files:
    with open(f, "r") as file:
        history.append(json.load(file))

# Сбор аналитики
total_gens = len(history)
modes_count = {}
classes_stat = {}
phases = {"Phase_1_Formation": [], "Phase_2_StressTest": []}

for p in history:
    gen = p.get("generation", 0)
    mode = p.get("mode", "N/A")
    s_class = p.get("signal_class", "unknown")
    
    modes_count[mode] = modes_count.get(mode, 0) + 1
    
    if s_class not in classes_stat:
        classes_stat[s_class] = {"count": 0, "j_sum": 0.0, "c_sum": 0.0}
    classes_stat[s_class]["count"] += 1
    classes_stat[s_class]["j_sum"] += p.get("J", {}).get("total", 0.0)
    classes_stat[s_class]["c_sum"] += p.get("confidence", 0.0)

    if gen <= 7:
        phases["Phase_1_Formation"].append(gen)
    else:
        phases["Phase_2_StressTest"].append(gen)

# Формирование Markdown-документа паспорта
report = f"""# Единый паспорт проекта «Малыш» (MalyshEngine)
**Дата генерации:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Версия ядра:** Gen 7+ (Интеллектуальный контур с классификацией K)  

---

## 1. Общая информация о системе
* **Архитектура:** Многокритериальный оптимизатор с мета-стабилизацией и классификацией сигналов.
* **Ключевые модули:** 
  * Адаптивный градиент ($\eta$)
  * Энергетический баланс (Energy Pool)
  * Резонансный узел ($R_7$)
  * Функция штрафа ($J$) и мета-стабилизатор ($S_n$)
  * Классификатор характера потока ($K$) и автоматическое переключение режимов.

---

## 2. Сводка поколений
| Gen | Источник / Поток | Режим | Класс | Conf (C) | J_total | S_n | Theta | Энергия |
|:---:|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|
"""

for p in history:
    gen = p.get("generation", 0)
    source = p.get("source", "N/A")[:15]
    mode = p.get("mode", "N/A")
    s_class = p.get("signal_class", "unknown")
    conf = p.get("confidence", 0.0)
    j_tot = p.get("J", {}).get("total", 0.0)
    s_n = p.get("S_n", 0.0)
    theta = p.get("theta", 0.0)
    energy = p.get("energy", 0.0)
    report += f"| {gen} | {source} | {mode} | {s_class} | {conf:.4f} | {j_tot:.4f} | {s_n:.4f} | {theta:.4f} | {energy:.1f} |\n"

report += f"""
---

## 3. Фазы эволюции
* **Фаза 1: Становление (Поколения {phases['Phase_1_Formation'][0]}–{phases['Phase_1_Formation'][-1]})**  
  Формирование базовой устойчивости, отладка формул паспортов, накопление резонансной стабильности.
* **Фаза 2: Стресс-тесты и адаптация (Поколения {phases['Phase_2_StressTest'][0]}–{phases['Phase_2_StressTest'][-1]})**  
  Столкновение с разнородными потоками (синтетика, физика, хаос), задействование динамических режимов (`SPIRAL_FLOW`) и удержание энергетического баланса под нагрузкой.

---

## 4. Профиль режимов
| Режим | Частота | Интерпретация |
|:---|:---:|:---|
"""

for mode, count in modes_count.items():
    interp = "активная адаптация / баланс"
    if "RESONANCE" in mode: interp = "тонкая настройка / резонанс"
    elif "SPIRAL" in mode: interp = "реакция на турбулентность / хаос"
    elif "STABLE" in mode: interp = "стабилизация контура"
    report += f"| {mode} | {count} | {interp} |\n"

report += f"""
---

## 5. Профиль сигналов (Классификация K)
"""

for sc, data in classes_stat.items():
    avg_j = data["j_sum"] / data["count"]
    avg_c = data["c_sum"] / data["count"]
    report += f"* **Класс [{sc}]:** запусков: {data['count']}, ср. штраф J: `{avg_j:.4f}`, ср. уверенность C: `{avg_c:.4f}`\n"

report += f"""
---

## 6. Итоговое резюме проекта
Система **MalyshEngine** успешно трансформировалась из локального скрипта прогнозирования в самостоятельный многоканальный аналитический контур. «Малыш» умеет дифференцировать структуру поступающих данных через метрику характера $K$, автоматически переключать режимы работы под воздействием внешней среды и фиксировать каждый шаг в стандартизированных паспортах телеметрии.
"""

# Сохранение паспорта в файл
with open("malysh_project_passport.md", "w", encoding="utf-8") as f:
    f.write(report)

print("[Успех]: Единый паспорт проекта успешно скомпилирован и сохранен в 'malysh_project_passport.md'!")
