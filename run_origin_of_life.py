import math
import random

class MalyshBiogenesisEngine:
    def __init__(self, R6=12.0, R5=4.5, theta_0=0.5, a=0.05, k=0.06):
        self.R6 = R6
        self.R5 = R5
        self.theta_0 = theta_0
        self.a = a
        self.k = k

    def generate_hexagon_vertices(self):
        return [(self.R6 * math.cos(math.pi / 3.0 * i), self.R6 * math.sin(math.pi / 3.0 * i)) for i in range(6)]

    def generate_pentagon_vertices(self):
        return [(self.R5 * math.cos(2.0 * math.pi / 5.0 * j + self.theta_0), self.R5 * math.sin(2.0 * math.pi / 5.0 * j + self.theta_0)) for j in range(5)]

    def _is_inside(self, point, vertices):
        x, y = point
        n = len(vertices)
        for i in range(n):
            p_i, p_next = vertices[i], vertices[(i + 1) % n]
            nx, ny = p_next[1] - p_i[1], -(p_next[0] - p_i[0])
            if (nx * (x - p_i[0]) + ny * (y - p_i[1])) > 0:
                return False
        return True

    def simulate_geological_phase(self, n_max=400):
        v6 = self.generate_hexagon_vertices()
        v5 = self.generate_pentagon_vertices()
        
        trajectory = []
        n7_nodes = []
        
        phi_n = 0.0
        for n in range(n_max + 1):
            phi_n += 0.045
            r_n = self.a * math.exp(self.k * phi_n)
            xn, yn = r_n * math.cos(phi_n), r_n * math.sin(phi_n)
            
            # Ограничение внешней стенкой шестиугольника (химический бассейн)
            if not self._is_inside((xn, yn), v6):
                xn *= 0.82
                yn *= 0.82
                
            trajectory.append((n, (xn, yn)))
            
            # Попадание в ядро пятиугольника — каталитический узел N7
            if self._is_inside((xn, yn), v5):
                n7_nodes.append(n)
                
        return {"n7_indices": n7_nodes, "trajectory": trajectory}

class BiogenesisSimulator:
    def __init__(self, n7_nodes, trajectory):
        self.n7_set = set(n7_nodes)
        self.trajectory = trajectory

    def run_simulation(self):
        print("\n[Эволюционный синтез] Инициализация хаотичного бульона...")
        
        # Начальное состояние: высокий уровень энтропии (хаоса)
        order_parameter = 0.05 
        history = []
        
        life_spark_step = None

        for n, point in self.trajectory:
            if n in self.n7_set:
                # Резонансный узел: резкий фазовый скачок порядка (искра жизни)
                order_parameter = min(1.0, order_parameter * 1.618 + 0.25)
                if order_parameter >= 0.99 and life_spark_step is None:
                    life_spark_step = n
                mode = "CATALYTIC_RESONANCE"
            else:
                # Фоновые флуктуации (случайный дрейф молекул)
                noise = random.uniform(-0.02, 0.03)
                order_parameter = max(0.0, min(1.0, order_parameter * 0.99 + noise))
                mode = "DIFFUSION"
                
            history.append({
                "step": n,
                "order": order_parameter,
                "mode": mode
            })
            
        return history, life_spark_step

if __name__ == "__main__":
    engine = MalyshBiogenesisEngine()
    geo = engine.simulate_geological_phase()
    
    sim = BiogenesisSimulator(geo["n7_indices"], geo["trajectory"])
    results, spark_step = sim.run_simulation()
    
    print(f"\n[Результат моделирования зарождения жизни]")
    if spark_step:
        print(f"-> КРИТИЧЕСКИЙ ФАЗОВЫЙ ПЕРЕХОД: Стабильный код жизни зафиксирован на шаге {spark_step}!")
    else:
        print("-> Система осталась в до-биологическом состоянии.")
        
    print("\nПоследние 5 шагов системы (уровень упорядоченности от 0 до 1):")
    for res in results[-5:]:
        print(f"Шаг {res['step']:3d} | Режим: {res['mode']:21s} | Уровень порядка: {res['order']:.4f}")
