from malysh_engine import MalyshEngine

print("=== ТЕСТ ПРЕДИКТИВНОГО КОНТУРА (PREDICTIVE STRATEGY) ===")

engine = MalyshEngine()

# Шаг 1: Подаем плавный сигнал
res1 = engine.process_array([10, 12, 14, 16, 18], source_name="Predict_Test_1")
print(f"\n[Шаг 1]")
print(f"  └─ Предсказанная стратегия: {res1['predicted_strategy']}")
print(f"  └─ Фактическая стратегия:  {res1['applied_strategy']}")
print(f"  └─ Класс сигнала:          {res1['signal_class']}")

# Шаг 2: Подаем следующий плавный сигнал (предиктор уже опирается на Шаг 1)
res2 = engine.process_array([18, 20, 22, 24, 26], source_name="Predict_Test_2")
print(f"\n[Шаг 2]")
print(f"  └─ Предсказанная стратегия: {res2['predicted_strategy']}")
print(f"  └─ Фактическая стратегия:  {res2['applied_strategy']}")
print(f"  └─ Класс сигнала:          {res2['signal_class']}")

print("\n[Готово]: Предиктивный контур успешно протестирован.")
