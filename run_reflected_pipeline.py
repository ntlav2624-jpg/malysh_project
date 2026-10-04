import math

class MalyshResonanceEngine:
    def __init__(self, R6=12.0, R5=4.5, theta_0=0.0, a=0.05, k=0.08):
        self.R6 = R6
        self.R5 = R5
        self.theta_0 = theta_0
        self.a = a
        self.k = k

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

    def generate_bounded_trajectory(self, phi_0=0.0, d_phi=0.05, n_max=300):
        """Генерирует спираль с отражением от стенки шестиугольника"""
        v6 = self.generate_hexagon_vertices()
        v5 = self.generate_pentagon_vertices()
        
        trajectory = []
        n7_nodes = []
        
        x, y = 0.0, 0.0
        vx, vy = math.cos(phi_0), math.sin(phi_0)
        
        for n in range(n_max + 1):
            phi_n = phi_0 + n * d_phi
            r_n = self.a * math.exp(self.k * phi_n)
            
            # Базовая точка спирали
            xn = r_n * math.cos(phi_n)
            yn = r_n * math.sin(phi_n)
            
            # Проверка на выход за шестиугольник (стенку)
            if not self._is_inside_polygon((xn, yn), v6):
                # Эффект отражения: инвертируем вектор и смещаем внутрь к центру
                xn *= 0.85
                yn *= 0.85
            
            trajectory.append((n, (xn, yn)))
            
            # Проверка попадания во внутренний пятиугольник (N7)
            if self._is_inside_polygon((xn, yn), v5):
                n7_nodes.append(n)
                
        return {
            "n7_indices": n7_nodes,
            "trajectory": trajectory
        }

class MalyshDataPipeline:
    def __init__(self, n7_nodes, trajectory):
        self.n7_set = set(n7_nodes)
        self.trajectory = trajectory

    def _operator_7(self, state_val, point):
        x, y = point
        # Нелинейный резонанс с ограничением (сатурацией) через tanh или делением
        raw = state_val * 1.618 + math.sin(x) * math.cos(y)
        return max(-1000.0, min(1000.0, raw)) # Держим значения в стабильном диапазоне

    def _standard_step(self, state_val):
        return state_val * 0.98

    def execute_stream(self, initial_state=1.0):
        stream_log = []
        current_state = initial_state
        
        print(f"\n[Pipeline Start] Запуск замкнутого контура для {len(self.trajectory)} точек...")
        
        for n, point in self.trajectory:
            if n in self.n7_set:
                current_state = self._operator_7(current_state, point)
                mode = "RESONANCE_O7"
            else:
                current_state = self._standard_step(current_state)
                mode = "STANDARD"
                
            stream_log.append({
                "step": n,
                "point": point,
                "state": current_state,
                "mode": mode
            })
        return stream_log

if __name__ == "__main__":
    engine = MalyshResonanceEngine(R6=12.0, R5=4.5, theta_0=0.5, a=0.08, k=0.06)
    geo_data = engine.generate_bounded_trajectory(phi_0=0.0, d_phi=0.05, n_max=350)
    
    pipeline = MalyshDataPipeline(
        n7_nodes=geo_data["n7_indices"],
        trajectory=geo_data["trajectory"]
    )
    
    results = pipeline.execute_stream(initial_state=1.0)
    
    print("\n[Результаты работы замкнутой системы (последние 5 шагов)]")
    for res in results[-5:]:
        print(f"Шаг {res['step']:3d} | Режим: {res['mode']:13s} | Состояние: {res['state']:.4f}")
