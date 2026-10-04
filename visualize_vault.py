import os
import json
import glob

vault_dir = "memory_vault"
files = sorted(glob.glob(os.path.join(vault_dir, "passport_*.json")))

if not files:
    print("[Ошибка]: В архиве memory_vault нет паспортов для визуализации.")
    exit(0)

history = []
for f in files:
    with open(f, "r") as file:
        history.append(json.load(file))

print(f"=== ТЕЛЕМЕТРИЧЕСКИЙ ОТЧЕТ ПОКОЛЕНИЙ (Всего: {len(history)}) ===")
print(f"{'Gen':<5} | {'Source':<20} | {'Mode':<14} | {'Conf (C)':<8} | {'J_total':<8} | {'S_n':<8} | {'Energy':<8}")
print("-" * 80)

for p in history:
    gen = p.get("generation", 0)
    source = p.get("source", "unknown")[:18]
    mode = p.get("mode", "N/A")
    conf = p.get("confidence", 0.0)
    j_tot = p.get("J", {}).get("total", 0.0)
    s_n = p.get("S_n", 0.0)
    en = p.get("energy", 0.0)
    
    print(f"{gen:<5} | {source:<20} | {mode:<14} | {conf:<8.4f} | {j_tot:<8.4f} | {s_n:<8.4f} | {en:<8.1f}")

# Простейшая ASCII-гистограмма для J_total по поколениям
print("\n=== ДИНАМИКА ЦЕЛЕВОЙ ФУНКЦИИ (J_total) ===")
max_j = max([p.get("J", {}).get("total", 1.0) for p in history]) or 1.0
for p in history:
    gen = p.get("generation", 0)
    j_tot = p.get("J", {}).get("total", 0.0)
    bar_len = int(30 * (j_tot / max_j))
    bar = "█" * bar_len
    print(f"Gen {gen:2d} | {bar} ({j_tot:.4f})")

print("\n[Визуализация завершена]: Телеметрия построена по историческим данным.")
