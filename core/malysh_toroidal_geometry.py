import json
import math

class ToroidalTubeGeometry:
    def __init__(self, raw_signal="6EQUJ5"):
        self.raw_signal = raw_signal
        self.R_major = 10.0
        self.r_minor = 3.0
        self.char_map = {"5": 5, "6": 6, "E": 14, "J": 19, "Q": 26, "U": 30}

    def decode_signal(self):
        amplitudes = []
        for char in self.raw_signal:
            if char in self.char_map:
                amplitudes.append(self.char_map[char])
            elif char.isdigit():
                amplitudes.append(int(char))
            else:
                amplitudes.append(ord(char) % 32)
        return amplitudes

    def compute_geometry(self):
        amps = self.decode_signal()
        n = len(amps)
        nodes = []
        cumulative_phase = 0.0

        for idx, val in enumerate(amps):
            theta = idx * (2 * math.pi / n)
            phi = val * (2 * math.pi / 60)
            cumulative_phase += phi

            # Тороидальные координаты (X, Y, Z)
            x = (self.R_major + self.r_minor * math.cos(phi)) * math.cos(theta)
            y = (self.R_major + self.r_minor * math.cos(phi)) * math.sin(theta)
            z = self.r_minor * math.sin(phi)
            t_coord = round(cumulative_phase, 4)

            # Привязка зоны трубы по углу phi
            if phi < math.pi / 2:
                zone = "ROOT"
            elif phi < math.pi:
                zone = "JILS"
            elif phi < 3 * math.pi / 2:
                zone = "TAIL"
            else:
                zone = "PHASE"

            node_data = {
                "node_id": idx + 1,
                "symbol": self.raw_signal[idx],
                "amplitude": val,
                "coords_xyz": [round(x, 3), round(y, 3), round(z, 3)],
                "time_coord_t": t_coord,
                "zone": zone
            }
            nodes.append(node_data)

        # Расчет евклидовой и резонансной длин
        euclid_length = 0.0
        resonance_length = 0.0
        for i in range(len(nodes)):
            p1 = nodes[i]["coords_xyz"]
            p2 = nodes[(i + 1) % len(nodes)]["coords_xyz"]
            dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))
            euclid_length += dist
            val_diff = abs(nodes[i]["amplitude"] - nodes[(i + 1) % len(nodes)]["amplitude"])
            resonance_length += dist + (val_diff * 0.1)

        geometry_packet = {
            "signature": self.raw_signal,
            "toroidal_metrics": {
                "R_major": self.R_major,
                "r_minor": self.r_minor,
                "euclidean_path": round(euclid_length, 3),
                "resonance_path": round(resonance_length, 3)
            },
            "nodes": nodes
        }
        return geometry_packet

if __name__ == "__main__":
    geo = ToroidalTubeGeometry("6EQUJ5")
    result = geo.compute_geometry()
    
    print("="*60)
    print(f"   🪐 ТОРОИДАЛЬНАЯ ГЕОМЕТРИЯ ТРУБЫ [{result['signature']}]")
    print("="*60)
    print(f"   [METRICS] Евклидова длина: {result['toroidal_metrics']['euclidean_path']}")
    print(f"   [METRICS] Резонансная длина: {result['toroidal_metrics']['resonance_path']}")
    print("-" * 60)
    for node in result["nodes"]:
        print(f"   [{node['zone']}] Узел {node['node_id']} ({node['symbol']}, amp={node['amplitude']}) -> XYZT: {node['coords_xyz'] + [node['time_coord_t']]}")
    print("="*60)
    
    with open("core/toroidal_geometry.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    print("   [SUCCESS] Пространственная геометрия сохранена в core/toroidal_geometry.json")
    print("="*60)
