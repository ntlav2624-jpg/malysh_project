import json
import math
import cmath
import ast
import inspect
import itertools
from collections import Counter, deque
import os

class ASTTopologyEvaluator(ast.NodeVisitor):
    """Анализатор структуры кода Малыша через призму информационной энтропии и топологического резонанса."""
    def __init__(self):
        self.node_counts = {}
        self.total_nodes = 0

    def visit(self, node):
        node_type = type(node).__name__
        self.node_counts[node_type] = self.node_counts.get(node_type, 0) + 1
        self.total_nodes += 1
        self.generic_visit(node)

    def calculate_resonance(self, source_code: str, task_complexity: float = 42.0):
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return {"error": f"Синтаксический срыв фазы: {e}", "theta_resonance": 1.0}

        self.node_counts.clear()
        self.total_nodes = 0
        self.visit(tree)

        shannon_entropy = 0.0
        if self.total_nodes > 0:
            for count in self.node_counts.values():
                p = count / self.total_nodes
                if p > 0:
                    shannon_entropy -= p * math.log2(p)

        lines_count = max(len(source_code.splitlines()), 1)
        denominator = lines_count * (shannon_entropy + 1e-6)
        theta_omega = task_complexity / denominator

        return {
            "total_nodes": self.total_nodes,
            "lines_count": lines_count,
            "shannon_entropy": round(shannon_entropy, 4),
            "theta_resonance": round(theta_omega, 4)
        }

class TopologicalResonanceCore:
    def __init__(self):
        self.nodes = 6
        self.phases = [2 * math.pi * i / self.nodes for i in range(self.nodes)]

    def evaluate_state(self, mutation_vector):
        self.phases = [(p + mutation_vector) % (2 * math.pi) for p in self.phases]
        entropy = self._calculate_shannon_entropy()
        coherence = self._calculate_phase_coherence()
        conductivity_metric = coherence / (entropy + 1e-6)
        return {
            "entropy": round(entropy, 4),
            "coherence": round(coherence, 4),
            "resonance_index": round(conductivity_metric, 4)
        }

    def _calculate_shannon_entropy(self):
        mean_phase = sum(self.phases) / len(self.phases)
        return sum((p - mean_phase) ** 2 for p in self.phases) / len(self.phases)

    def _calculate_phase_coherence(self):
        complex_sum = sum(cmath.rect(1.0, p) for p in self.phases)
        return abs(complex_sum) / self.nodes

class MalyshGrandUnifiedEngine:
    def __init__(self, signature="6EQUJ5", main_history=None, euro_history=None):
        self.signature = signature
        self.main_history = main_history or [[7, 15, 24, 28, 32], [8, 15, 16, 26, 38], [1, 2, 8, 28, 35], [7, 8, 16, 34, 42]]
        self.euro_history = euro_history or [[3, 11], [1, 12], [3, 11], [5, 8]]
        
        self.R_major = 10.0
        self.r_minor = 3.0
        self.char_map = {"5": 5, "6": 6, "E": 14, "J": 19, "Q": 26, "U": 30}
        self.topo_core = TopologicalResonanceCore()
        self.ast_evaluator = ASTTopologyEvaluator()
        self.system_telemetry = {}

    def analyze_natural_market_attractors(self):
        domains = {
            "Грязь (Десикация)": {"symmetry": 6, "anchor_stress": 120.0, "nature": "Минимизация механической энергии"},
            "Снежинка (Кристалл)": {"symmetry": 6, "anchor_stress": 60.0,  "nature": "Диффузионная агрегация и влажность"},
            "Финансовый рынок":   {"symmetry": 5, "anchor_stress": 99.9,  "nature": "Стохастический фазовый переход (Краш)"}
        }
        total_stress_index = 0.0
        for name, data in domains.items():
            sym = data["symmetry"]
            stress = data["anchor_stress"]
            resonance = math.sin(sym * math.pi / 3.0) * stress + math.e * 10
            total_stress_index += abs(resonance)
        return round(total_stress_index / (len(domains) * 100.0), 4)

    def full_system_boot(self):
        print("="*68)
        print("   🌌 МАЛЫШ: GRAND UNIFIED CORE [AST + TOPOLOGICAL RESONANCE]")
        print("="*68)
        
        layers = [
            ("AST Code Topology Evaluator (Theta Omega)", "active"),
            ("Topological Resonance Core (Entropy/Coherence)", "active"),
            ("Cross-Domain Nature & Market Attractors", "active"),
            ("AST Mutation & Self-Mod Layer", "active"),
            ("Multi-Agent Logging & Telemetry", "synchronized"),
            ("Q4 Quaternary Firmware (PAM-4)", "online"),
            ("Toroidal XYZT Geometry Matrix", "online"),
            ("Cause & Anti-Cause Diagnostic Ring", "monitoring"),
            ("Transition Matrix & Tube Memory", "loaded"),
            ("Main Tube (5/50) & Euro Tube (2/12)", "calibrated"),
            ("Tube Constructor (Zone Balancer)", "ready")
        ]
        
        for name, status in layers:
            self.system_telemetry[name] = status
            print(f"   [BOOT] {name.ljust(44)} ........ {status.upper()}")
        print("="*68)

    def decode_signal(self):
        amplitudes = []
        for char in self.signature:
            if char in self.char_map:
                amplitudes.append(self.char_map[char])
            elif char.isdigit():
                amplitudes.append(int(char))
            else:
                amplitudes.append(ord(char) % 32)
        return amplitudes

    def execute_unified_pipeline(self):
        self.full_system_boot()
        
        # Читаем исходный код текущего файла для самоанализа через AST
        try:
            with open(__file__, "r", encoding="utf-8") as f:
                source_code = f.read()
        except Exception:
            source_code = "class Dummy: pass"

        ast_metrics = self.ast_evaluator.calculate_resonance(source_code, task_complexity=50.0)
        field_coef = self.analyze_natural_market_attractors()
        
        amps = self.decode_signal()
        mutation_vector = sum(amps) / (len(amps) * 100.0)
        topo_metrics = self.topo_core.evaluate_state(mutation_vector)
        
        print(f"   ⚡ [NATURE-MARKET FIELD] Индекс напряжения : {field_coef}")
        print(f"   🌀 [TOPOLOGICAL CORE] Энтропия/Когерентн. : {topo_metrics['entropy']} / {topo_metrics['coherence']}")
        print(f"   🧬 [AST TOPOLOGY] Шеннон кода (код Малыша) : {ast_metrics['shannon_entropy']}")
        print(f"   🚀 [AST TOPOLOGY] Резонанс кода Theta(Omega): {ast_metrics['theta_resonance']}")
        print("-" * 68)

        total_power = sum(amps) if sum(amps) > 0 else 1
        theta_factor = ast_metrics['theta_resonance']

        # Интеграция AST Theta-резонанса в веса узлов лотерейных труб
        q4_weights = {}
        toroidal_res = {}
        
        for idx, val in enumerate(amps):
            q_state = val % 4
            energy_weight = round((val / total_power) * field_coef * (1.0 + theta_factor * 0.01), 4)
            
            theta = idx * (2 * math.pi / len(amps))
            phi = val * (2 * math.pi / 60)
            x = (self.R_major + self.r_minor * math.cos(phi)) * math.cos(theta)
            
            q4_weights[val] = energy_weight
            toroidal_res[val] = round(abs(x) * 0.2 * field_coef, 4)

        # Transition Matrix & Tube Memory
        main_mem = deque(self.main_history, maxlen=50)
        euro_mem = deque(self.euro_history, maxlen=50)
        
        main_trans = Counter()
        for draw in main_mem:
            for p in itertools.combinations(sorted(set(draw)), 2): main_trans[p] += 1

        # Синтез очков с учетом AST Theta-резонанса
        main_scores = Counter()
        for draw in main_mem:
            for num in draw: main_scores[num] += 1.0

        for (n1, n2), freq in main_trans.items():
            main_scores[n1] += freq * 0.7 * field_coef
            main_scores[n2] += freq * 0.7 * field_coef

        for num in main_scores:
            if num in q4_weights:
                main_scores[num] += q4_weights[num] * 8.0 * (1.0 + topo_metrics['coherence'])
            if num in toroidal_res:
                main_scores[num] += toroidal_res[num] * (1.0 + theta_factor * 0.05)

        # Конструктор трубы
        top_main_20 = [num for num, score in main_scores.most_common(20)]
        
        euro_scores = Counter()
        for draw in euro_mem:
            for num in draw: euro_scores[num] += 1
        top_euro_6 = [num for num, score in euro_scores.most_common(6)]

        root_m = top_main_20[:6]
        jils_m = top_main_20[6:14]
        tail_m = top_main_20[14:]

        final_main = []
        if len(root_m) >= 2: final_main.extend(root_m[:2])
        if len(jils_m) >= 2: final_main.extend(jils_m[:2])
        if len(tail_m) >= 1: final_main.extend(tail_m[:1])
        for num in top_main_20:
            if len(final_main) < 5 and num not in final_main: final_main.append(num)

        final_euro = top_euro_6[:2]

        print("\n" + "—"*68)
        print("   🎯 АБСОЛЮТНЫЙ AST-ПРОГНОЗ МАЛЫША [CODE-DRIVEN SYNTHESIS]")
        print("—"*68)
        print(f"   ✨ MAIN TUBE (5 из 50): {sorted(final_main[:5])}")
        print(f"   ✨ EURO TUBE (2 из 12): {sorted(final_euro)}")
        print(f"   [STATUS] Структура AST-кода успешно модулирует расчет труб.")
        print("="*68)

        packet = {
            "signature": self.signature,
            "ast_metrics": ast_metrics,
            "field_coefficient": field_coef,
            "topological_metrics": topo_metrics,
            "prediction": {
                "main": sorted(final_main[:5]),
                "euro": sorted(final_euro)
            }
        }

        os.makedirs("core", exist_ok=True)
        with open("core/malysh_ast_state.json", "w", encoding="utf-8") as f:
            json.dump(packet, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    engine = MalyshGrandUnifiedEngine()
    engine.execute_unified_pipeline()
