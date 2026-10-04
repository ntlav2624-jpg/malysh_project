import json
import glob
import os
from datetime import datetime
import math

class MalyshEngine:
    def __init__(self, vault_dir="memory_vault"):
        self.vault_dir = vault_dir
        if not os.path.exists(self.vault_dir):
            os.makedirs(self.vault_dir)
        
        self._load_state()

    def _load_state(self):
        files = sorted(glob.glob(os.path.join(self.vault_dir, "passport_*.json")))
        self.history = []
        for f in files:
            with open(f, "r") as file:
                self.history.append(json.load(file))
        
        self.generation = len(self.history) + 1
        
        if self.history:
            last_p = self.history[-1]
            self.theta = last_p.get("theta", 1.01)
            self.energy = last_p.get("energy", 100.0)
            self.eta = last_p.get("eta", 0.0005)
            self.r7_val = last_p.get("r7_val", 0.0712)
            self.prev_error = last_p.get("J", {}).get("pred", 1.0)
            self.prev_theta = self.theta
            self.prev_energy = self.energy
        else:
            self.theta = 1.01
            self.energy = 100.0
            self.eta = 0.0005
            self.r7_val = 0.0712
            self.prev_error = 1.0
            self.prev_theta = self.theta
            self.prev_energy = self.energy

    def predict_next_strategy(self):
        if not self.history:
            return "ADAPTIVE_STRATEGY"
            
        last_p = self.history[-1]
        K = last_p.get("K_metric", 1.0)
        cls = last_p.get("signal_class", "smooth")
        recent_classes = [p.get("signal_class") for p in self.history[-3:]]
        
        if K < 1.0 and cls == "smooth":
            return "RESONANCE_SEARCH"
        elif recent_classes.count("chaotic") >= 2:
            return "DAMPING_STRATEGY"
        elif 1.0 <= K < 3.0 and cls in ("smooth", "harmonic"):
            return "ADAPTIVE_STRATEGY"
        else:
            return "DAMPING_STRATEGY"

    def process_array(self, data, source_name="memory_stream"):
        predicted_strat = self.predict_next_strategy()
        
        if predicted_strat == "RESONANCE_SEARCH":
            self.r7_val = min(0.2, self.r7_val * 1.03)
        elif predicted_strat == "DAMPING_STRATEGY":
            self.eta *= 0.9
        
        n = len(data)
        if n == 0:
            return {"error": "Empty data array"}
        
        base = sum(data) / n
        trend = (data[-1] - data[0]) / max(1, n - 1)
        amplitude = (max(data) - min(data)) / 2.0
        variance = sum((x - base)**2 for x in data) / n
        noise = variance / (amplitude + 1e-5)
        
        # Предварительный расчет K для адаптивной геометрии
        # Сначала сделаем черновой прогноз с текущим r7_val
        temp_forecast = base + trend + amplitude * math.sin(math.pi / 4.0) * (self.theta) + self.r7_val * math.cos(2.0 * math.pi / 7.0)
        temp_l_pred = abs(temp_forecast - data[-1])
        temp_J = 0.6 * temp_l_pred + 0.3 * 0.0 + 0.1 * abs(self.energy - 100.0) / 100.0
        temp_K = temp_J / (math.exp(-temp_J) + 1e-6)

        # ДИНАМИЧЕСКАЯ ГЕОМЕТРИЯ РЕЗОНАНСА R7
        delta = 0.01      # коэффициент роста резонанса
        epsilon = 0.005   # коэффициент подавления хаоса
        
        old_r7 = self.r7_val
        self.r7_val = old_r7 + delta * math.sin(self.theta) - epsilon * temp_K
        self.r7_val = max(0.01, min(0.2, self.r7_val)) # Ограничение в разумных пределах

        # 1. Финальный прогноз (+10 шагов) с новой геометрией R7
        forecast_10 = []
        for i in range(1, 11):
            t_component = base + trend * i
            h_component = amplitude * math.sin(i * math.pi / 4.0) * (self.theta ** i)
            r7_component = self.r7_val * math.cos(i * 2.0 * math.pi / 7.0)
            y_pred = t_component + h_component + r7_component
            forecast_10.append(y_pred)
            
        l_pred = abs(forecast_10[0] - data[-1])
        
        if len(forecast_10) >= 3:
            second_derivatives = [abs(forecast_10[i+2] - 2*forecast_10[i+1] + forecast_10[i]) for i in range(len(forecast_10)-2)]
            l_smooth = sum(second_derivatives) / len(second_derivatives)
        else:
            l_smooth = 0.0
            
        target_energy = 100.0
        l_energy = abs(self.energy - target_energy) / target_energy
        
        w1, w2, w3 = 0.6, 0.3, 0.1
        J_total = w1 * l_pred + w2 * l_smooth + w3 * l_energy
        
        delta_l = abs(l_pred - self.prev_error)
        delta_theta_meta = abs(self.theta - self.prev_theta)
        delta_energy = abs(self.energy - self.prev_energy)
        S_n = delta_l + delta_theta_meta + delta_energy
        
        if S_n > 5.0:
            self.eta *= 0.5
            penalty_factor = 2.0
        else:
            penalty_factor = 1.0

        confidence = math.exp(-J_total) * math.exp(-S_n)
        K = J_total / (confidence + 1e-6)

        if K < 1.0:
            signal_class = "smooth"
            mode = "RESONANCE_O7"
        elif K < 3.0:
            signal_class = "harmonic"
            mode = "ACTIVE_5"
        else:
            signal_class = "chaotic"
            mode = "SPIRAL_FLOW"

        if signal_class == "smooth" and K < 1.5:
            actual_strategy = "RESONANCE_SEARCH"
        elif signal_class == "chaotic":
            actual_strategy = "DAMPING_STRATEGY"
        else:
            actual_strategy = "ADAPTIVE_STRATEGY"

        strat_mult = 1.05 if predicted_strat == "RESONANCE_SEARCH" else (0.5 if predicted_strat == "DAMPING_STRATEGY" else 1.0)
        old_theta = self.theta
        grad_approx = (J_total if l_pred == 0 else J_total * (forecast_10[0] - data[-1]) / l_pred)
        self.theta -= self.eta * grad_approx * penalty_factor * strat_mult
        delta_theta = abs(self.theta - old_theta)
        
        # Локальный стабилизатор R7
        gamma_r7 = 0.01
        self.r7_val = max(0.01, min(0.2, self.r7_val - gamma_r7 * l_pred))
        
        alpha, beta, gamma_en = 1.0, 0.5, 10.0
        self.energy = max(10.0, min(200.0, self.energy + alpha * amplitude - beta * noise - gamma_en * delta_theta))
            
        passport = {
            "generation": self.generation,
            "timestamp": datetime.now().isoformat(),
            "source": source_name,
            "mode": mode,
            "predicted_strategy": predicted_strat,
            "applied_strategy": actual_strategy,
            "signal_class": signal_class,
            "confidence": round(confidence, 5),
            "K_metric": round(K, 4),
            "J": {
                "pred": round(l_pred, 4),
                "smooth": round(l_smooth, 4),
                "energy": round(l_energy, 4),
                "total": round(J_total, 4)
            },
            "S_n": round(S_n, 4),
            "theta": round(self.theta, 5),
            "eta": round(self.eta, 6),
            "r7_val": round(self.r7_val, 5),
            "energy": round(self.energy, 1),
            "forecast_10": [round(x, 2) for x in forecast_10]
        }
        
        filename = os.path.join(self.vault_dir, f"passport_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json")
        with open(filename, "w") as f:
            json.dump(passport, f, indent=4)
            
        return passport
