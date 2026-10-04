from malysh_pro_engine import MalyshProCuneiformEngine

if __name__ == "__main__":
    engine = MalyshProCuneiformEngine()
    engine.load_corpus_from_text("unknown_royal_tablet.txt")
    engine.translate_and_analyze("unknown_royal_tablet.txt", output_json="royal_tablet_report.json")
