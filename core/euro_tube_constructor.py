import itertools
from collections import Counter, deque

class DualTubeConstructor:
    def __init__(self, main_history, euro_history):
        self.main_memory = deque(main_history, maxlen=50)
        self.euro_memory = deque(euro_history, maxlen=50)
        
        self.main_transitions = Counter()
        self.euro_transitions = Counter()
        
        self._build_transitions()

    def _build_transitions(self):
        for draw in self.main_memory:
            sorted_draw = sorted(list(set(draw)))
            for p in itertools.combinations(sorted_draw, 2):
                self.main_transitions[p] += 1

        for draw in self.euro_memory:
            sorted_draw = sorted(list(set(draw)))
            for p in itertools.combinations(sorted_draw, 2):
                self.euro_transitions[p] += 1

    def calculate_path_strength(self, pool_type='main'):
        transitions = self.main_transitions if pool_type == 'main' else self.euro_transitions
        memory = self.main_memory if pool_type == 'main' else self.euro_memory

        node_scores = Counter()
        for draw in memory:
            for num in draw:
                node_scores[num] += 1

        for (n1, n2), freq in transitions.items():
            node_scores[n1] += freq * 0.5
            node_scores[n2] += freq * 0.5

        return node_scores

    def construct_prediction(self):
        main_strengths = self.calculate_path_strength('main')
        euro_strengths = self.calculate_path_strength('euro')

        top_main_20 = [num for num, score in main_strengths.most_common(20)]
        top_euro_6 = [num for num, score in euro_strengths.most_common(6)]

        root_m = top_main_20[:6]
        jils_m = top_main_20[6:14]
        tail_m = top_main_20[14:]

        final_main = []
        if len(root_m) >= 2: final_main.extend(root_m[:2])
        if len(jils_m) >= 2: final_main.extend(jils_m[:2])
        if len(tail_m) >= 1: final_main.extend(tail_m[:1])

        for num in top_main_20:
            if len(final_main) < 5 and num not in final_main:
                final_main.append(num)

        final_euro = top_euro_6[:2]

        print("="*50)
        print("   🔮 ДВУХКОНТУРНЫЙ КОНСТРУКТОР ТРУБЫ (EUROJACKPOT)")
        print("="*50)
        print(f"   [MAIN_TUBE] Расширенная воронка TOP-20 получена.")
        print(f"   [ZONES_M] ROOT: {root_m[:3]}... | JILS: {jils_m[:3]}... | TAIL: {tail_m[:3]}...")
        print(f"   ✨ Итоговый прогноз MAIN (5 из 50): {sorted(final_main[:5])}")
        print(f"   ✨ Итоговый прогноз EURO (2 из 12): {sorted(final_euro)}")
        print("="*50)

if __name__ == "__main__":
    sample_main = [[7, 15, 24, 28, 32], [8, 15, 16, 26, 38], [1, 2, 8, 28, 35], [7, 8, 16, 34, 42]]
    sample_euro = [[3, 11], [1, 12], [3, 11], [5, 8]]
    
    constructor = DualTubeConstructor(sample_main, sample_euro)
    constructor.construct_prediction()
