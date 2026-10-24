import math

from n7_interface import classify_n7_interface

class MalyshResonanceEngine:
    def __init__(self, R6=10.0, R5=5.0, theta_0=0.0, a=0.1, k=0.05):
        self.R6 = R6
        self.R5 = R5
        self.theta_0 = theta_0
        self.a = a
        self.k = k

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

    def generate_spiral_trajectory(self, phi_0=0.0, d_phi=0.1, n_max=300):
        trajectory = []
        for n in range(n_max + 1):
            phi_n = phi_0 + n * d_phi
            r_n = self.a * math.exp(self.k * phi_n)
            xn = r_n * math.cos(phi_n)
            yn = r_n * math.sin(phi_n)
            trajectory.append((xn, yn))
        return trajectory

    def compute_n7_nodes(
        self,
        phi_0=0.0,
        d_phi=0.1,
        n_max=300,
        interface_tolerance=None,
    ):
        """
        Вычисляет N7 как интерфейс R5 <-> R6.

        R5 является пятиугольной структурой.
        R6 является шестиугольной структурой.
        N7 является оператором перехода.
        """
        vertices_6 = self.generate_hexagon_vertices()
        vertices_5 = self.generate_pentagon_vertices()

        spiral = self.generate_spiral_trajectory(
            phi_0,
            d_phi,
            n_max,
        )

        valid_points = [
            (index, point)
            for index, point in enumerate(spiral)
            if self._is_inside_polygon(
                point,
                vertices_6,
            )
        ]

        interface = classify_n7_interface(
            trajectory=valid_points,
            vertices_5=vertices_5,
            vertices_6=vertices_6,
            tolerance=interface_tolerance,
        )

        return {
            "n7_indices": interface["indices"],
            "n7_nodes": interface["nodes"],
            "n7_mode": interface["mode"],
            "n7_tolerance": interface["tolerance"],
            "n7_minimum_score": (
                interface["minimum_score"]
            ),
            "n7_forward": interface["forward"],
            "n7_reverse": interface["reverse"],
            "valid_trajectory": valid_points,
            "total_checked": len(spiral),
        }


# --- Инициализация и запуск цикла ---
engine = MalyshResonanceEngine(R6=12.0, R5=4.5, theta_0=0.5, a=0.05, k=0.08)
result = engine.compute_n7_nodes(phi_0=0.0, d_phi=0.05, n_max=400)
n7_set = set(result["n7_indices"])

state = {"energy": 1.0, "mode": "standard"}

for n, point in result["valid_trajectory"]:
    if n in n7_set:
        state["mode"] = "resonance_active"
        state["energy"] *= 1.618  # золотое сечение
        print(f"[Node 7 Triggered] Шаг {n}: точка {point}, режим: {state['mode']}")
    else:
        state["mode"] = "standard"
        state["energy"] *= 0.99  # затухающий шаг
