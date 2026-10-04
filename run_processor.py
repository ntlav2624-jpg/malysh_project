import math

class MalyshResonanceEngine:
    def __init__(self, R6=12.0, R5=4.5, theta_0=0.0, a=0.05, k=0.06, freq_mod=0.04):
        self.R6 = R6
        self.R5 = R5
        self.theta_0 = theta_0
        self.a = a
        self.k = k
        self.freq_mod = freq_mod

    def generate_hexagon_vertices(self, center=(0.0, 0.0)):
        cx, cy = center
        return [
            (cx + self.R6 * math.cos((math.pi / 3.0) * i),
             cy + self.R6 * math.sin((math.pi / 3.0) * i))
            for i in range(6)
        ]

    def generate_pentagon_vertices(self, center=(0.0, 0.0)):
        cx, cy = center
        return [
            (cx + self.R5 * math.cos((2.0 * math.pi / 5.0) * j + self.theta_0),
             cy + self.R5 * math.sin((2.0 * math.pi / 5.0) * j + self.theta_0))
            for j in range(5)
        ]

    def _is_inside_polygon(self, point, vertices):
        x, y = point
        n = len(vertices)
        for i in range(n):
            p_i = vertices[i]
            p_next = vertices[(i + 1) % n]
            ex = p_next[0] - p_i[0]
            ey = p_next[1] - p_i[1]
            nx = ey
            ny = -ex
            rx = x - p_i[0]
            ry = y - p_i[1]
            if (nx * rx + ny * ry) > 0:
                return False
        return True

    def generate_bounded_trajectory(self, phi_0=0.0, base_d_phi=0.05, n_max=350):
        v6 = self.generate_hexagon_vertices()
        v5 = self.generate_pentagon_vertices()
        
        trajectory = []
        n7_nodes = []
        
        phi_n = phi_0
        for n in range(n_max + 1):
            d_phi_n = base_d_phi * (1.0 + self.freq_mod * math.sin(n * 0.15))
            phi_n += d_phi_n
            
            r_n = self.a * math.exp(self.k * phi_n)
            xn = r_n * math.cos(phi_n)
            yn = r_n * math.sin(phi_n)
            
            if not self._is_inside_polygon((xn, yn), v6):
                xn *= 0.85
                yn *= 0.85
            
            trajectory.append((n, (xn, yn), phi_n))
            
            if self._is_inside_polygon((xn, yn), v5):
                n7_nodes.append(n)
                
        return {
            "n7_indices": n7_nodes,
            "trajectory": trajectory
        }

class MalyshDataProcessor:
    def __init__(self, n7_nodes, trajectory):
        self.n7_set = set(n7_nodes)
        self.trajectory = trajectory

    def process_stream(self, input_data):
        """Обрабатывает входящий поток данных (числа, команды, символы) через резонансную сеть"""
        output_log = []
        data_idx = 0
        
        for n, point, phi_n in self.trajectory:
            if data_idx >= len(input_data):
                break
            
            current_item = input_data[data_idx]
            
            if n in self.n7_set:
                # В узле резонанса N7 выполняем нелинейную математическую обработку / трансформацию
                if isinstance(current_item, (int, float)):
                    transformed = round(current_item * 1.618 + math.sin(point[0]) * 10, 2)
                else:
                    # Для символьных строк — фазовое преобразование (сдвиг кодов символов)
                    shift = int(math.degrees(phi_n) % 5)
                    transformed = "".join([chr(ord(c) + shift) for c in str(current_item)])
                mode = "RESONANCE_TRANSFORM"
            else:
                # В обычном режиме передаем данные без изменений или с легкой задержкой
                transformed = current_item
                mode = "PASS_THROUGH"
                
            output_log.append({
                "step": n,
                "input": current_item,
                "output": transformed,
                "mode": mode
            })
            data_idx += 1
            
        return output_log

if __name__ == "__main__":
    engine = MalyshResonanceEngine()
    geo_data = engine.generate_bounded_trajectory()
    
    processor = MalyshDataProcessor(geo_data["n7_indices"], geo_data["trajectory"])
    
    # Поток пользовательских данных для обработки (например, массив числовых значений)
    my_data_stream = [i * 5 for i in range(120)]
    
    results = processor.process_stream(my_data_stream)
    
    print("\n[Результаты работы вычислительного процессора 'Малыш']")
    for res in results[-10:]:
        print(f"Шаг {res['step']:3d} | Режим: {res['mode']:19s} | Вход: {res['input']} -> Выход: {res['output']}")
