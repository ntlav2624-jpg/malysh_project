from malysh_engine import MalyshEngine

print("=== ОПЕРАЦИЯ: ВЫТЕСНЕНИЕ ХАОСА ПЛАВНЫМИ СИГНАЛАМИ ===")

smooth_streams = [
    [50, 52, 54, 56, 58, 60],
    [60, 62, 64, 66, 68, 70],
    [70, 72, 74, 76, 78, 80]
]

for i, stream in enumerate(smooth_streams, 1):
    engine = MalyshEngine()
    res = engine.process_array(stream, source_name=f"Smooth_Wave_{i}")
    print(f"\n[Шаг {i}]")
    print(f"  └─ Источник: Smooth_Wave_{i}")
    print(f"  └─ Класс сигнала: {res['signal_class']}")
    print(f"  └─ Стратегия: {res['strategy']}")
    print(f"  └─ Режим: {res['mode']}")
    print(f"  └─ Метрика K: {res['K_metric']}")
    print(f"  └─ Уверенность C: {res['confidence']}")
    print(f"  └─ Параметр R7: {res['r7_val']}")

print("\n[Готово]: История обновлена гладкими потоками.")
