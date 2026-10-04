import json
from malysh_engine import MalyshEngine

streams = {
    "1_Synthetic_Sine": [10.0, 12.5, 15.0, 16.2, 14.8, 12.1, 10.5, 12.0, 14.5],
    "2_Physical_Sensor": [22.1, 22.3, 22.2, 22.8, 23.5, 23.1, 23.6, 24.0, 23.8],
    "3_Chaotic_Lottery": [5, 82, 12, 94, 3, 67, 45, 19, 88]
}

print("=== ТЕСТ ИНТЕЛЛЕКТУАЛЬНОГО КЛАССИФИКАТОРА (GEN 11) ===")

for name, data in streams.items():
    engine = MalyshEngine()
    res = engine.process_array(data, source_name=name)
    
    print(f"\n[Поток]: {name}")
    print(f"  └─ Класс сигнала (Class) : {res['signal_class']}")
    print(f"  └─ Режим контура (Mode)  : {res['mode']}")
    print(f"  └─ Коэффициент K         : {res['K_metric']}")
    print(f"  └─ Уверенность (C)       : {res['confidence']}")
    print(f"  └─ Общий штраф (J)       : {res['J']['total']}")

print("\n[Готово]: Поколения с классификацией зафиксированы.")
