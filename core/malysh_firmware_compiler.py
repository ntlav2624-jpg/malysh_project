import json
class FirmwareCompiler:
    def __init__(self, raw_signal="6EQUJ5"):
        self.raw_signal = raw_signal
        self.char_map = {"5": 5, "6": 6, "E": 14, "J": 19, "Q": 26, "U": 30}
    def decode_signal(self):
        amplitudes = []
        for char in self.raw_signal:
            if char in self.char_map: amplitudes.append(self.char_map[char])
            elif char.isdigit(): amplitudes.append(int(char))
            else: amplitudes.append(ord(char) % 32)
        return amplitudes
    def compile_firmware(self):
        amps = self.decode_signal()
        total_power = sum(amps) if sum(amps) > 0 else 1
        nodes, zones_registry = [], {"ROOT": [], "JILS": [], "TAIL": [], "PHASE": []}
        voltage_steps = {0: 0.0, 1: 1.2, 2: 2.4, 3: 3.6}
        for i, val in enumerate(amps):
            q_state = val % 4
            energy_weight = round(val / total_power, 4)
            zone = "ROOT" if q_state == 0 else ("JILS" if q_state == 1 else ("TAIL" if q_state == 2 else "PHASE"))
            node_data = {"node_id": i + 1, "symbol": self.raw_signal[i], "amplitude": val, "energy_weight": energy_weight, "quaternary_state": q_state, "zone": zone, "electrical_params": {"voltage_v": voltage_steps.get(q_state, 0.0), "logic_level": f"PAM-4_L{q_state}"}}
            nodes.append(node_data)
            zones_registry[zone].append(node_data)
        return {"signature": self.raw_signal, "total_power": total_power, "zones": zones_registry, "nodes": nodes}
if __name__ == "__main__":
    compiler = FirmwareCompiler("6EQUJ5")
    firmware = compiler.compile_firmware()
    with open("core/malysh_firmware.json", "w", encoding="utf-8") as f:
        json.dump(firmware, f, ensure_ascii=False, indent=4)
    print("[SUCCESS] Прошивка скомпилирована в core/malysh_firmware.json")
