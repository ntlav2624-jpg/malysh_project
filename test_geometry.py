from malysh_engine import MalyshEngine

print("=== ТЕСТ ДИНАМИЧЕСКОЙ ГЕОМЕТРИИ РЕЗОНАНСА (R7) ===")

engine = MalyshEngine()

# Поток 1: Плавный линейный ряд
res1 = engine.process_array([10, 15, 20, 25, 30], source_name="Geo_Smooth")
print(f"\n[Тест 1: Плавный сигнал]")
print(f"  └─ Класс: {res1['signal_class']}")
print(f"  └─ Метрика K: {res1['K_metric']}")
print(f"  └─ Геометрия R7: {res1['r7_val']}")

# Поток 2: Хаотический/резкий скачок
res2 = engine.process_array([30, 80, 10, 95, 20], source_name="Geo_Chaotic")
print(f"\n[Тест 2: Хаотический сигнал]")
print(f"  └─ Класс: {res2['signal_class']}")
print(f"  └─ Метрика K: {res2['K_metric']}")
print(f"  └─ Геометрия R7: {res2['r7_val']}")

print("\n[Готово]: Динамика геометрии проверена.")
