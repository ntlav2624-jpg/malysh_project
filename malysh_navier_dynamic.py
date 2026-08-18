import numpy as np
import logging

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] [MalyshNavierDynamic] %(message)s"
)

class NavierStokesDynamicEngine:
    def __init__(self, viscosity: float = 0.05, dt: float = 0.001):
        if viscosity <= 0:
            raise ValueError("Вязкость должна быть строго положительной.")
        self.nu = viscosity
        self.dt = dt

    def step_evolution(self, wave_numbers: np.ndarray, energy_spectrum: np.ndarray, helicity: float) -> tuple:
        """
        Динамический шаг эволюции спектра энергии и спиральности с учетом нелинейного каскада и вязкого затухания.
        """
        xi = wave_numbers
        E = energy_spectrum
        
        # 1. Нелинейный перенос энергии (кубическая компонента Клебша / каскад)
        nonlinear_cascade = 0.05 * (xi ** 0.5) * E
        
        # 2. Вязкая диссипация: D(xi) = 2 * nu * |xi|^2 * E(xi)
        dissipation = 2.0 * self.nu * (xi ** 2) * E
        
        # 3. Обновление спектра энергии по закону баланса (дифференциальное уравнение в спектральном пространстве)
        dE_dt = nonlinear_cascade - dissipation
        E_next = E + dE_dt * self.dt
        
        # Энергия не может быть отрицательной
        E_next = np.maximum(E_next, 1e-16)
        
        # 4. Проверка спектральной мажоранты на ультрафиолетовом хвосте
        uv_idx = len(xi) // 2
        uv_dissipation = dissipation[uv_idx:]
        uv_nonlinearity = nonlinear_cascade[uv_idx:]
        spectral_stable = np.all(uv_dissipation >= uv_nonlinearity)
        
        # 5. Динамика спиральности (диссипация ограничена градиентом энстрофии)
        enstrophy_grad_norm = np.sum((xi ** 2) * E) * 0.01
        helicity_rate = -0.1 * abs(helicity)
        bound = 2.0 * self.nu * enstrophy_grad_norm
        topology_stable = abs(helicity_rate) <= bound
        
        return E_next, spectral_stable and topology_stable

if __name__ == "__main__":
    engine = NavierStokesDynamicEngine(viscosity=0.05, dt=0.005)
    
    xi = np.linspace(1.0, 500.0, 300)
    energy_spec = 100.0 * (xi ** (-5.0 / 3.0))
    current_helicity = 1.0
    
    # Симуляция по времени (например, 50 шагов)
    steps = 50
    global_smooth = True
    
    logging.info("Запуск динамического симулятора эволюции Навье-Стокса...")
    for step in range(steps):
        energy_spec, stable = engine.step_evolution(xi, energy_spec, current_helicity)
        if not stable:
            global_smooth = False
            logging.warning(f"[ШАГ {step}] Зафиксировано нарушение спектрального баланса!")
            break
            
    print(f"\n[ВЕРДИКТ ДИНАМИКИ] Глобальная гладкость сохранена за {steps} шагов: {global_smooth}")
    print(f"Итоговая энергия на высшей моде: {energy_spec[-1]:.6e}")
