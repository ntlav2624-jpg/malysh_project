import math

class MalyshResonanceEngine:
    def __init__(self, R6=12.0, R5=4.5, theta_0=0.0, a=0.05, k=0.06, freq_mod=0.03):
        self.R6 = R6
        self.R5 = R5
        self.theta_0 = theta_0
        self.a = a
        self.k = k
        self.freq_mod = freq_mod # Коэффициент частотного сдвига внутри спирали

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
            # 1. Частотный сдвиг: модуляция шага приращения фазы
            d_phi_n = base_d_phi * (1.0 + self.freq_mod * math.sin(n * 0.15))
            phi_n += d_phi_n
            
            r_n = self.a * math.exp(self.k * phi_n)
            xn = r_n * math.cos(phi_n)
            yn = r_n * math.sin(phi_n)
            
            if not self._is_inside_polygon((xn, yn), v6):
                xn *= 0.85
                yn *= 0.85
            
            # Сохраняем шаг, координаты и текущую фазу спирали
            trajectory.append((n, (xn, yn), phi_n))
            
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

    def _phase_detector(self, point, phi_n):
        """2. Фазовый детектор: вычисляет отклонение пространственной фазы от расчетной"""
        x, y = point
        spatial_phase = math.atan2(y, x)
        phase_error = spatial_phase - (phi_n % (2 * math.pi))
        return phase_error

    def _adaptive_operator_7(self, state_val, point, phi_n):
        """3. Адаптивный режим O_7: усиление меняется в зависимости от фазовой ошибки"""
        phase_error = self._phase_detector(point, phi_n)
        
        # Динамический коэффициент на базе золотого сечения и фазы
        adaptive_gain = 1.618 + 0.382 * math.cos(phase_error)
        
        raw = state_val * adaptive_gain + math.sin(point[0]) * math.cos(point[1])
        return max(-1000.0, min(1000.0, raw))

    def _standard_step(self, state_val):
        return state_val * 0.98

    def execute_stream(self, initial_state=1.0):
        stream_log = []
        current_state = initial_state
        
        print(f"\n[Pipeline Start] Запуск адаптивного контура для {len(self.trajectory)} точек...")
        
        for n, point, phi_n in self.trajectory:
            if n in self.n7_set:
                current_state = self._adaptive_operator_7(current_state, point, phi_n)
                mode = "ADAPTIVE_O7"
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
    engine = MalyshResonanceEngine(R6=12.0, R5=4.5, theta_0=0.5, a=0.05, k=0.06, freq_mod=0.04)
    geo_data = engine.generate_bounded_trajectory(phi_0=0.0, base_d_phi=0.05, n_max=350)
    
    pipeline = MalyshDataPipeline(
        n7_nodes=geo_data["n7_indices"],
        trajectory=geo_data["trajectory"]
    )
    
    results = pipeline.execute_stream(initial_state=1.0)
    
    print("\n[Результаты адаптивной системы (последние 5 шагов)]")
    for res in results[-5:]:
        print(f"Шаг {res['step']:3d} | Режим: {res['mode']:12s} | Состояние: {res['state']:.4f}")
