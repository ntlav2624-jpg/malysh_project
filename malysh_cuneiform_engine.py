import os
import json
import re
from collections import Counter, defaultdict

class MalyshCuneiformEngine567:
    def __init__(self, data_dir="./cuneiform_data"):
        self.data_dir = data_dir
        self.corpus = []
        self.sign_frequencies = Counter()
        self.bigram_frequencies = defaultdict(Counter)
        self.transition_matrix = {}
        self.attractors = set()
        
        # Словарь значений и переводов знаков (клинописный глоссарий)
        self.dictionary = {
            "an-na": ("небо / Ану", "heaven / Anu"),
            "nun": ("князь / владыка", "prince / lord"),
            "dingir": ("бог / божество", "god / deity"),
            "gal-gal": ("великие", "great"),
            "an-unna": ("Анунна (пантеон)", "Anunna pantheon"),
            "ki": ("земля / место", "earth / place"),
            "en": ("господин / жрец", "lord / priest"),
            "abzu": ("подземный океан (Абзу)", "subterranean waters (Abzu)"),
            "lugal": ("царь / правитель", "king / ruler"),
            "unug": ("Урук", "Uruk"),
            "e2": ("дом / храм", "house / temple"),
            "sag": ("голова / человек", "head / person"),
            "gu7": ("есть / питаться", "to eat / consume"),
            "udu": ("овца", "sheep")
        }

        # Базис для обучения поля
        self.base_corpus = [
            ["an-na", "nun", "dingir", "gal-gal"],
            ["dingir", "an-unna", "ki", "en"],
            ["abzu", "en", "nun", "an-na"],
            ["gal-gal", "dingir", "unug", "ki"],
            ["e2", "gal", "unug", "ki"],
            ["sag", "gu7", "e2", "abzu"]
        ]
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def clean_token(self, token):
        cleaned = re.sub(r'[\[\]\?!#()xX…\-\*\{\}]', '', token)
        return cleaned.strip().lower()

    def load_corpus_from_text(self, filepath):
        for signs in self.base_corpus:
            self.corpus.append(signs)
            self.sign_frequencies.update(signs)
            for i in range(len(signs) - 1):
                self.bigram_frequencies[signs[i]][signs[i+1]] += 1

        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    raw_signs = line.strip().split()
                    if raw_signs and re.match(r'^\d+\.$', raw_signs[0]):
                        raw_signs = raw_signs[1:]
                    signs = [self.clean_token(t) for t in raw_signs]
                    signs = [s for s in signs if s and s not in ('...', 'x', 'xx')]
                    if signs:
                        self.corpus.append(signs)
                        self.sign_frequencies.update(signs)
                        for i in range(len(signs) - 1):
                            self.bigram_frequencies[signs[i]][signs[i+1]] += 1
                            
        self._build_topological_field()
        return True

    def _build_topological_field(self):
        for sign, nexts in self.bigram_frequencies.items():
            total = sum(nexts.values())
            self.transition_matrix[sign] = {n: count / total for n, count in nexts.items()}
        for sign, freq in self.sign_frequencies.items():
            if freq >= 2:
                self.attractors.add(sign)

    def evaluate_topological_tension(self, seq):
        tension = 0.0
        for i in range(len(seq) - 1):
            s1, s2 = seq[i], seq[i+1]
            if s1 in self.transition_matrix and s2 in self.transition_matrix[s1]:
                tension += (1.0 - self.transition_matrix[s1][s2])
            else:
                tension += 2.0
        return tension

    def restore_gap(self, left_sign, right_sign):
        clean_l = self.clean_token(left_sign)
        clean_r = self.clean_token(right_sign)
        best_candidate = None
        min_tension = float('inf')
        
        for cand in self.sign_frequencies.keys():
            seq = [clean_l, cand, clean_r]
            tension = self.evaluate_topological_tension(seq)
            if tension < min_tension:
                min_tension = tension
                best_candidate = cand
        return best_candidate, min_tension

    def translate_tablet(self, filepath):
        if not os.path.exists(filepath):
            print(f"Файл {filepath} не найден.")
            return
        
        print(f"\n================ TRANSLATION REPORT: {filepath} ================")
        with open(filepath, 'r', encoding='utf-8') as f:
            line_idx = 1
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                
                raw_line = line.strip()
                # Удаляем нумерацию строк в начале, если есть
                clean_line_str = re.sub(r'^\d+\.\s*', '', raw_line)
                tokens = clean_line_str.split()
                
                restored_sequence = []
                i = 0
                while i < len(tokens):
                    token = tokens[i]
                    # Проверяем на наличие повреждения/пропуска ([x], [...], или отсутствие)
                    is_gap = ('[' in token and ']' in token) or token in ('...', 'x', 'xx', '[x]')
                    
                    if is_gap and i > 0 and i < len(tokens) - 1:
                        left = self.clean_token(tokens[i-1])
                        right = self.clean_token(tokens[i+1])
                        cand, tension = self.restore_gap(left, right)
                        restored_sequence.append(f"[{cand}*]")
                    elif not is_gap:
                        cleaned = self.clean_token(token)
                        if cleaned:
                            restored_sequence.append(cleaned)
                    i += 1
                
                # Перевод последовательности по глоссарию
                translation_parts = []
                for s in restored_sequence:
                    pure_s = s.replace('[', '').replace(']', '').replace('*', '')
                    if pure_s in self.dictionary:
                        translation_parts.append(self.dictionary[pure_s][0])
                    else:
                        translation_parts.append(f"({pure_s})")
                
                print(f"Строка {line_idx}:")
                print(f"  Исходник:  {raw_line}")
                print(f"  Восстанов: {' — '.join(restored_sequence)}")
                print(f"  Перевод:   {' / '.join(translation_parts)}")
                print("-" * 60)
                line_idx += 1

if __name__ == "__main__":
    engine = MalyshCuneiformEngine567()
    engine.load_corpus_from_text("anunnaki_raw_tablet.txt")
    engine.translate_tablet("anunnaki_raw_tablet.txt")
