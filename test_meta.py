from malysh_engine import MalyshEngine

print("=== ТЕСТ МЕТА-СТРАТЕГИЧЕСКОГО КОНТУРА (M-METRIC) ===")

engine = MalyshEngine()

# Тест 1: Плавный сигнал
res1 = engine.process_array([50, 51, 52, 53, 54], source_name="Meta_Smooth")
print(f"\n[Шаг 1: Smooth]")
print(f"  └─ Стратегия: {res1['strategy']}")
print(f"  └─ Мета-метрика M: {res1['meta_metric_M']}")
print(f"  └─ Режим: {res1['mode']}")

# Тест 2: Тот же гладкий поток (накапливаем историю)
res2 = engine.process_array([54, 55, 56, 57, 58], source_name="Meta_Smooth_2")
print(f"\n[Шаг 2: Smooth Continued]")
print(f"  └─ Стратегия: {res2['strategy']}")
print(f"  └─ Мета-метрика M: {res2['meta_metric_M']}")
print(f"  └─ Режим: {res2['mode']}")

print("\n[Готово]: Мета-стратегический контур протестирован.")
