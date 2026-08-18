import os
import json
import re
from collections import Counter, defaultdict

class MalyshCuneiformEngine:
    def __init__(self, data_dir="./cuneiform_data"):
        self.data_dir = data_dir
        self.corpus = []
        self.sign_frequencies = Counter()
        self.bigram_frequencies = defaultdict(Counter)
        self.transition_matrix = {}
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def clean_token(self, token):
        cleaned = re.sub(r'[\[\]\?!#()xX…\-\*]', '', token)
        return cleaned.strip().lower()

    def load_corpus_from_text(self, filepath):
        if not os.path.exists(filepath):
            print(f"Файл {filepath} не найден.")
            return False
        
        count_lines = 0
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                
                raw_signs = line.strip().split()
                signs = [self.clean_token(t) for t in raw_signs]
                signs = [s for s in signs if s]
                
                if signs:
                    self.corpus.append(signs)
                    self.sign_frequencies.update(signs)
                    for i in range(len(signs) - 1):
                        self.bigram_frequencies[signs[i]][signs[i+1]] += 1
                count_lines += 1
                        
        self._build_transition_matrix()
        print(f"Обработано строк: {count_lines}. Валидных предложений: {len(self.corpus)}. Уникальных знаков: {len(self.sign_frequencies)}")
        return True

    def _build_transition_matrix(self):
        for sign, nexts in self.bigram_frequencies.items():
            total = sum(nexts.values())
            self.transition_matrix[sign] = {n: count / total for n, count in nexts.items()}

    def predict_next(self, sign):
        clean_s = self.clean_token(sign)
        if clean_s in self.transition_matrix:
            return sorted(self.transition_matrix[clean_s].items(), key=lambda x: x[1], reverse=True)
        return []

    def find_patterns(self, min_frequency=2):
        patterns = defaultdict(int)
        for doc in self.corpus:
            for length in range(2, 5):
                for i in range(len(doc) - length + 1):
                    seq = tuple(doc[i:i+length])
                    patterns[seq] += 1
                    
        filtered_patterns = {seq: count for seq, count in patterns.items() if count >= min_frequency}
        return sorted(filtered_patterns.items(), key=lambda x: x[1], reverse=True)

    def export_analysis(self, output_path="cuneiform_analysis.json"):
        data = {
            "total_documents": len(self.corpus),
            "unique_signs": len(self.sign_frequencies),
            "top_signs": self.sign_frequencies.most_common(20),
            "top_patterns": [{"sequence": list(seq), "count": count} for seq, count in self.find_patterns()[:15]],
            "transition_matrix_sample": {k: trans_v for k, trans_v in list(self.transition_matrix.items())[:5]}
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Полный вероятностный отчет сохранен в {output_path}")

if __name__ == "__main__":
    engine = MalyshCuneiformEngine()
    engine.load_corpus_from_text("test_cuneiform.txt")
    print("Прогноз для знака 'diš':", engine.predict_next("diš"))
    engine.export_analysis()
