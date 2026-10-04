import json
import glob
import os
from datetime import datetime
import math

class HierarchicalMemory:
    def __init__(self):
        if not os.path.exists("memory_vault"):
            os.makedirs("memory_vault")
            
    def load_all_passports(self):
        files = sorted(glob.glob("memory_vault/passport_*.json"))
        history = []
        for f in files:
            with open(f, "r") as file:
                history.append(json.load(file))
        return history

    def get_memory_layers(self):
        all_h = self.load_all_passports()
        short_term = all_h[-3:] if len(all_h) >= 3 else all_h
        medium_term = all_h[-10:] if len(all_h) >= 10 else all_h
        long_term = all_h
        return short_term, medium_term, long_term

    def store_passport(self, passport_data):
        filename = f"memory_vault/passport_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        with open(filename, "w") as f:
            json.dump(passport_data, f, indent=4)
        print(f"[Архив]: Паспорт Поколения 7 зафиксирован.")

class Generation7Core:
    def __init__(self):
        self.memory = HierarchicalMemory()
        short, medium, long = self.memory.get_memory_layers()
        self.generation = len(long) + 1
        
        # Загрузка состояния из истории или инициализация
        if medium:
            last_p = medium[-1]
            self.theta = last_p.get("theta", 1.01)
            self.energy = last_p.get("energy", 100.0)
            self.eta = last_p.get("eta", 0.0005)
            self.r7_val = last_p.get("r7_val", 0.0712)
            self.prev_error = last_p.get("error", 1.0)
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

    def compute_forecast(self, data):
        n = len(data)
        if n == 0:
            return []
        
        base = sum(data) / n
        trend = (data[-1] - data[0]) / max(1, n - 1)
        amplitude = (max(data) - min(data)) / 2.0
        
        forecast = []
        for i in range(1, 11):
            t_component = base + trend * i
            h_component = amplitude * math.sin(i * math.pi / 4.0) * (self.theta ** i)
            r7_component = self.r7_val * math.cos(i * 2.0 * math.pi / 7.0)
            
            y_pred = t_component + h_component + r7_component
            forecast.append(y_pred)
            
        return forecast

    def run(self):
        print(f"--- Многокритериальный контур 'Малыш' (Поколение Gen {self.generation}) активирован ---")
        files = glob.glob("data_*.txt")
        
        if not files:
            self.energy -= 2.0
            print(f"[Автономный контур]: Данные отсутствуют. Энергия снижена до {self.energy:.1f}.")
            return

        for df in files:
            with open(df, 'r') as f:
                data = [float(line.strip()) for line in f if line.strip()]
            
            if not data:
                continue
                
            n = len(data)
            amplitude = max(data) - min(data)
            variance = sum((x - sum(data)/n)**2 for x in data) / n
            noise = variance / (amplitude + 1e-5)
            
            # 1. Прогноз
            forecast_10 = self.compute_forecast(data)
            l_pred = abs(forecast_10[0] - data[-1])
            
            # 2. Штраф за «дёрганость» (L_smooth через вторую производную на прогнозе)
            if len(forecast_10) >= 3:
                second_derivatives = [abs(forecast_10[i+2] - 2*forecast_10[i+1] + forecast_10[i]) for i in range(len(forecast_10)-2)]
                l_smooth = sum(second_derivatives) / len(second_derivatives)
            else:
                l_smooth = 0.0
                
            # 3. Штраф за отклонение энергии от целевого диапазона (цель: 100.0)
            target_energy = 100.0
            l_energy = abs(self.energy - target_energy) / target_energy
            
            # 4. Многокритериальная целевая функция J с весами
            w1, w2, w3 = 0.6, 0.3, 0.1
            J = w1 * l_pred + w2 * l_smooth + w3 * l_energy
            
            # 5. Мета-стабилизатор S_n (контроль разброса параметров между поколениями)
            delta_l = abs(l_pred - self.prev_error)
            delta_theta_meta = abs(self.theta - self.prev_theta)
            delta_energy = abs(self.energy - self.prev_energy)
            S_n = delta_l + delta_theta_meta + delta_energy
            
            # Коррекция параметров контура при высоком S_n (мета-стабилизация)
            if S_n > 5.0:
                self.eta *= 0.5            # Снижаем шаг обучения
                self.r7_val *= 0.8         # Сжимаем диапазон R7
                penalty_factor = 2.0       # Усиливаем штраф
            else:
                penalty_factor = 1.0

            # 6. Обновление θ через градиент многокритериальной функции J
            old_theta = self.theta
            grad_approx = (J if l_pred == 0 else J * (forecast_10[0] - data[-1]) / l_pred)
            self.theta -= self.eta * grad_approx * penalty_factor
            delta_theta = abs(self.theta - old_theta)
            
            # 7. Резонансная коррекция R7 по ошибке
            gamma_r7 = 0.01
            self.r7_val = self.r7_val - gamma_r7 * l_pred
            self.r7_val = max(0.01, min(0.2, self.r7_val))
            
            # 8. Строгий энергетический баланс
            alpha, beta, gamma_en = 1.0, 0.5, 10.0
            self.energy = self.energy + alpha * amplitude - beta * noise - gamma_en * delta_theta
            self.energy = max(10.0, min(200.0, self.energy))
            
            # 9. Метрические режимы
            if self.energy > 130.0:
                mode = "ACTIVE_5"
            elif self.energy < 50.0:
                mode = "STABLE_6"
            elif variance > 30.0:
                mode = "SPIRAL_FLOW"
            else:
                mode = "RESONANCE_O7"
            
            print(f"[Инженерный контур - Поколение 7]: Источник {df}")
            print(f"  └─ Целевая функция (J)       : {J:.4f} (Pred: {l_pred:.2f}, Smooth: {l_smooth:.2f}, Energy: {l_energy:.2f})")
            print(f"  └─ Мета-стабильность (S_n)   : {S_n:.4f}")
            print(f"  └─ Выбранный режим           : {mode}")
            print(f"  └─ Адаптивный шаг η          : {self.eta:.6f}")
            print(f"  └─ Параметр θ                : {self.theta:.5f}")
            print(f"  └─ Резонанс R7               : {self.r7_val:.5f}")
            print(f"  └─ Энергетический пул        : {self.energy:.1f}")
            print(f"  └─ Усиленный прогноз (+10)   : {[round(x, 2) for x in forecast_10]}")
            
            passport = {
                "generation": self.generation,
                "timestamp": datetime.now().isoformat(),
                "source": df,
                "mode": mode,
                "theta": self.theta,
                "eta": self.eta,
                "r7_val": self.r7_val,
                "energy": self.energy,
                "error": l_pred,
                "J_score": J,
                "S_n": S_n,
                "forecast_10": forecast_10
            }
            self.memory.store_passport(passport)
            
            # Сохраняем состояния для следующего поколения
            self.prev_error = l_pred
            self.prev_theta = self.theta
            self.prev_energy = self.energy
            print(f"[Исполнитель]: Многокритериальный цикл Поколения 7 завершен.\n")

if __name__ == "__main__":
    system = Generation7Core()
    system.run()
