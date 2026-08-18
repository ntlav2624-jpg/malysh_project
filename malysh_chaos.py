import math
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [ChaosEngine] %(message)s")

class ChaosAndUncertaintyHandler:
    @staticmethod
    def calculate_lyapunov_horizon(initial_error: float = 1e-15, lyapunov_exponent: float = 0.1) -> float:
        """Рассчитывает максимальный горизонт предсказания хаотической системы (в сутках)"""
        # t_max = ln(1 / initial_error) / lambda
        t_max = math.log(1.0 / initial_error) / lyapunov_exponent
        logging.info(f"[Хаос] Горизонт прогноза для ошибки {initial_error}: {t_max:.1f} дней.")
        return t_max

    @staticmethod
    def evaluate_incomplete_data_risk(known_features_pct: float) -> str:
        """Оценивает степень риска при неполноте входных данных (например, структуры белка)"""
        uncertainty = 100.0 - known_features_pct
        if uncertainty > 50.0:
            logging.warning(f"[Неполнота данных] Неизвестно {uncertainty}% параметров. Требуется байесовское моделирование (Monte Carlo).")
            return "PROBABILISTIC_ENSEMBLE_REQUIRED"
        return "DETERMINISTIC_SOLVABLE"

if __name__ == "__main__":
    handler = ChaosAndUncertaintyHandler()
    horizon = handler.calculate_lyapunov_horizon()
    print(f"Максимальный предел точного прогноза погоды: {horizon:.1f} дней.")
    
    status = handler.evaluate_incomplete_data_risk(known_features_pct=30.0)
    print(f"Статус обработки неполных данных вируса: {status}")
