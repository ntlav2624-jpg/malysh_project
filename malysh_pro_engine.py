import os
import json
import re
from collections import Counter, defaultdict

class MalyshProCuneiformEngine:
    def __init__(self, data_dir="./cuneiform_data"):
        self.data_dir = data_dir
        self.corpus = []
        self.sign_frequencies = Counter()
        self.bigram_frequencies = defaultdict(Counter)
        self.transition_matrix = {}
        
        # Расширенный полисемантический глоссарий с контекстными правилами
        self.dictionary = {
            "an-na": {
                "default": ("небо / бог Ану", "heaven / Anu"),
                "context": {"nun": ("небесный владыка", "heavenly lord")}
            },
            "nun": {
                "default": ("князь / владыка", "prince / lord"),
                "context": {"an-na": ("князь небес", "prince of heaven")}
            },
            "dingir": {
                "default": ("бог / божество", "god / deity"),
                "context": {"ki": ("божество земли", "deity of earth")}
            },
            "gal-gal": {
                "default": ("великие", "great")
            },
            "an-unna": {
                "default": ("Анунна (пантеон)", "Anunna pantheon")
            },
            "ki": {
                "default": ("земля / место", "earth / place"),
                "context": {"en": ("место господина", "place of the lord")}
            },
            "en": {
                "default": ("господин / жрец", "lord / priest")
            },
            "abzu": {
                "default": ("подземный океан (Абзу)", "subterranean waters (Abzu)")
            },
            "lugal": {
                "default": ("царь / правитель", "king / ruler")
            },
            "unug": {
                "default": ("Урук", "Uruk")
            },
            "e2": {
                "default": ("дом / храм", "house / temple")
            }
        }

        self.base_corpus = [
            ["an-na", "nun", "dingir", "gal-gal"],
            ["dingir", "an-unna", "ki", "en"],
            ["abzu", "en", "nun", "an-na"],
            ["gal-gal", "dingir", "unug", "ki"],
            ["e2", "gal", "unug", "ki"]
        ]
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def clean_token(self, token):
        cleaned = re.sub(r'[\[\]\?!#()xX…\-\*\{\}]', '', token)
        return cleaned.strip().lower()

    def parse_morphology(self, token):
        """Выделяет корневую морфему и падежный аффикс (-e, -ak, -a, -ra)"""
        affixes = {"e": "эргатив", "ak": "генитив", "a": "локатив", "ra": "датив"}
        for aff, name in affixes.items():
            if token.endswith("-" + aff) and len(token) > len(aff) + 1:
                base = token[:-(len(aff)+1)]
                return base, name
        return token, "абсолютив"

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

    def evaluate_topological_tension(self, seq):
        tension = 0.0
        for i in range(len(seq) - 1):
            s1, s2 = seq[i], seq[i+1]
            if s1 in self.transition_matrix and s2 in self.transition_matrix[s1]:
                tension += (1.0 - self.transition_matrix[s1][s2])
            else:
                tension += 2.0 # Штраф за разрыв поля
        return tension

    def restore_gap(self, left_sign, right_sign, damage_factor=1.0):
        clean_l = self.clean_token(left_sign)
        clean_r = self.clean_token(right_sign)
        best_candidate = None
        min_tension = float('inf')
        
        for cand in self.sign_frequencies.keys():
            seq = [clean_l, cand, clean_r]
            tension = self.evaluate_topological_tension(seq) * damage_factor
            if tension < min_tension:
                min_tension = tension
                best_candidate = cand
        return best_candidate, min_tension

    def translate_and_analyze(self, filepath, output_json="translation_report.json"):
        if not os.path.exists(filepath):
            print(f"Файл {filepath} не найден.")
            return
        
        report_data = []
        print(f"\n========== MALYSH PRO EPIGRAPHIC REPORT: {filepath} ==========")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            line_idx = 1
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                
                raw_line = line.strip()
                clean_line_str = re.sub(r'^\d+\.\s*', '', raw_line)
                tokens = clean_line_str.split()
                
                restored_sequence = []
                line_tensions = []
                
                i = 0
                while i < len(tokens):
                    token = tokens[i]
                    is_gap = ('[' in token and ']' in token) or token in ('...', 'x', 'xx', '[x]')
                    
                    if is_gap and i > 0 and i < len(tokens) - 1:
                        left = self.clean_token(tokens[i-1])
                        right = self.clean_token(tokens[i+1])
                        # Коэффициент повреждения выше, если символ полностью стерт ([x])
                        dmg = 1.5 if '[x]' in token or token == 'x' else 1.0
                        cand, tension = self.restore_gap(left, right, damage_factor=dmg)
                        restored_sequence.append(f"[{cand}*]")
                        line_tensions.append(round(tension, 3))
                    elif not is_gap:
                        cleaned = self.clean_token(token)
                        if cleaned:
                            restored_sequence.append(cleaned)
                    i += 1
                
                # Морфологический анализ и контекстный перевод
                translation_parts = []
                for idx, s in enumerate(restored_sequence):
                    pure_s = s.replace('[', '').replace(']', '').replace('*', '')
                    base, morph = self.parse_morphology(pure_s)
                    
                    # Контекстный выбор перевода по соседям
                    trans_item = self.dictionary.get(base, ({'default': (base, base)},))
                    if isinstance(trans_item, dict):
                        trans_text = trans_item["default"][0]
                        # Проверяем соседей для полисемии
                        prev_sign = restored_sequence[idx-1].replace('[','').replace(']','').replace('*','') if idx > 0 else ""
                        next_sign = restored_sequence[idx+1].replace('[','').replace(']','').replace('*','') if idx < len(restored_sequence)-1 else ""
                        if "context" in trans_item:
                            if prev_sign in trans_item["context"]:
                                trans_text = trans_item["context"][prev_sign][0]
                            elif next_sign in trans_item["context"]:
                                trans_text = trans_item["context"][next_sign][0]
                    else:
                        trans_text = base

                    morph_note = f" ({morph})" if morph != "абсолютив" else ""
                    translation_parts.append(f"{trans_text}{morph_note}")

                line_report = {
                    "line": line_idx,
                    "source": raw_line,
                    "restored": restored_sequence,
                    "tensions": line_tensions,
                    "translation": translation_parts
                }
                report_data.append(line_report)

                print(f"Строка {line_idx}:")
                print(f"  Исходник:   {raw_line}")
                print(f"  Восстанов:  {' — '.join(restored_sequence)}")
                print(f"  Напряжение: {line_tensions}")
                print(f"  Перевод:    {' / '.join(translation_parts)}")
                print("-" * 60)
                line_idx += 1

        with open(output_json, 'w', encoding='utf-8') as jf:
            json.dump(report_data, jf, ensure_ascii=False, indent=4)
        print(f"Академический отчет сохранен в файл: {output_json}")

if __name__ == "__main__":
    engine = MalyshProCuneiformEngine()
    engine.load_corpus_from_text("anunnaki_raw_tablet.txt")
    engine.translate_and_analyze("anunnaki_raw_tablet.txt")
