import json
from malysh_engine import MalyshEngine

streams = {
    "1_Synthetic_Sine": [10.0, 12.5, 15.0, 16.2, 14.8, 12.1, 10.5, 12.0, 14.5],
    "2_Physical_Sensor": [22.1, 22.3, 22.2, 22.8, 23.5, 23.1, 23.6, 24.0, 23.8],
    "3_Chaotic_Lottery": [5, 82, 12, 94, 3, 67, 45, 19, 88]
}

print("=== СРАВНИТЕЛЬНЫЙ АНАЛИЗ ПОТОКОВ ЧЕРЕЗ MALYSH ENGINE ===")

for name, data in streams.items():
    engine = MalyshEngine()
    result = engine.process_array(data, source_name=name)
    
    print(f"\n[Поток]: {name}")
    print(f"  └─ Режим (Mode)       : {result['mode']}")
    print(f"  └─ Уверенность (C)    : {result['confidence']}")
    print(f"  └─ Общий штраф (J)    : {result['J']['total']}")
    print(f"  └─ Мета-стабильность  : {result['S_n']}")
    print(f"  └─ Энергия системы    : {result['energy']}")
    print(f"  └─ Прогноз (+3 шага)  : {result['forecast_10'][:3]}")

print("\n[Анализ завершен]: Все паспорта зафиксированы в memory_vault/")
