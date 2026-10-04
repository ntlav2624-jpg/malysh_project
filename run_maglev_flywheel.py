import math

class MaglevFlywheelSystem:
    def __init__(self, initial_energy=100.0, damping=0.02):
        self.energy = initial_energy  # Сразу задаем общую энергию в системе (Джоули)
        self.gamma = damping          # Коэффициент потерь (воздух + вихревые токи)

    def simulate(self, steps=150, dt=0.05):
        print("\n[Малыш: Корректная симуляция затухания энергии]")
        history = []
        
        for s in range(steps):
            t = s * dt
            # Энергия строго убывает по экспоненте из-за потерь на трение/левитацию
            current_energy = self.energy * math.exp(-self.gamma * t)
            
            # Эффект резонансного биения (перераспределение между пружиной и маховиком)
            modulation = 0.85 + 0.15 * math.cos(t * 3.14)
            e_spring = current_energy * modulation
            e_flywheel = current_energy * (1.0 - modulation)
            
            history.append((t, current_energy, e_spring, e_flywheel))
            
        return history

if __name__ == "__main__":
    system = MaglevFlywheelSystem(initial_energy=100.0, damping=0.04)
    results = system.simulate(steps=150, dt=0.05)
    
    print("\nРезультат честного расчета затухания:")
    print(f"Старт:    Время = {results[0][0]:.2f}с | Энергия = {results[0][1]:.4f} Дж")
    print(f"Середина: Время = {results[75][0]:.2f}с | Энергия = {results[75][1]:.4f} Дж")
    print(f"Финал:    Время = {results[-1][0]:.2f}с | Энергия = {results[-1][1]:.4f} Дж")
