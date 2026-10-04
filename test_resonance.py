import json
from malysh_engine import MalyshEngine

print("=== ТЕСТ СТРАТЕГИИ RESONANCE_SEARCH ===")

# Плавный, предсказуемый поток данных
smooth_stream = [50, 52, 55, 53, 56, 58, 60]

engine = MalyshEngine()
res = engine.process_array(smooth_stream, source_name="Smooth_Resonance_Run")

print(f"\n[Результат теста]")
print(f"  └─ Класс сигнала: {res['signal_class']}")
print(f"  └─ Стратегия: {res['strategy']}")
print(f"  └─ Режим: {res['mode']}")
print(f"  └─ Метрика K: {res['K_metric']}")
print(f"  └─ Уверенность C: {res['confidence']}")
print(f"  └─ Параметр R7: {res['r7_val']}")

print("\n[Готово]: Резонансный контур проверен.")
