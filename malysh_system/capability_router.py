from __future__ import annotations

import ast
import json
import operator
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

KEYWORDS = {
    "adaptation": ["адапт", "поколен", "прогноз", "эволюц"],
    "engine": ["ядро", "организм", "систем", "общий анализ"],
    "dynamics.chaos": ["хаос", "неопредел", "ляпунов", "аттрактор"],
    "math.bony": ["bony", "парапроизвед", "замыкан", "нелинейн"],
    "physics.navier": [
        "поток", "жидк", "navier", "устойчив",
        "спектр", "вязк", "гидродинами", "вихр"
    ],
    "physics.plasma": ["плазм", "plasma", "магнит", "заряженн"],
    "physics.turbulence": ["турбул", "turbulence", "аккрец"],
    "analysis.cuneiform": [
        "шумер", "клинопис", "табличк", "cuneiform", "аккад"
    ],
}


KEYWORDS.update({
    "analysis.cuneiform": [
        "шумер",
        "шумерск",
        "клинопис",
        "табличк",
        "cuneiform",
        "аккад",
        "перевод",
        "морфолог",
    ],
    "geometry.phase": [
        "фаз",
        "phase",
        "связь фаз",
        "сопряж",
        "entanglement",
    ],
    "engine.apsu": [
        "apsu",
        "апсу",
        "энергет",
        "энерги",
        "симуляц",
    ],
    "engine": [
        "ядро",
        "организм",
        "систем",
        "общий анализ",
        "энергет",
        "мощност",
        "импульс",
        "meso",
        "enki",
    ],
    "physics.navier": [
        "поток",
        "жидк",
        "navier",
        "устойчив",
        "спектр",
        "вязк",
        "гидродинами",
        "вихр",
        "blowup",
    ],
    "analysis.batch": [
        "batch",
        "пакет",
        "поток данных",
        "серия данных",
    ],
    "prediction": [
        "прогноз",
        "prediction",
        "transition",
        "переход",
        "tube",
        "траектор",
    ],
    "diagnostic.stress": [
        "стресс",
        "stress",
        "taylor",
        "диагност",
        "предельн",
    ],
    "physics.legacy": [
        "legacy",
        "физическ",
        "старая физика",
    ],
})


# PHASE1_LOGIC_GEOMETRY_KEYWORDS
KEYWORDS.update({
    "logic.firmware": [
        "firmware",
        "прошив",
        "компилятор",
        "pam-4",
        "pam4",
        "четверич",
        "сигнал",
    ],
    "geometry.toroidal": [
        "тороид",
        "toroid",
        "xyzt",
        "геометрия трубы",
        "тороидальная геометрия",
        "резонансный путь",
    ],
})


# PHASE2_NATIVE_ENGINE_KEYWORDS
KEYWORDS.update({
    "engine.memory": [
        "старое ядро",
        "нативное ядро",
        "malysh engine",
        "малыш engine",
        "обработай массив",
        "числовой поток",
        "ряд данных",
        "следующая стратегия",
        "стратегия потока",
        "forecast 10",
        "прогноз 10",
    ],
})


# RECALLED_SEQUENCE_SKILL
KEYWORDS.update({
    "memory.sequence_skill": [
        "обработай массив",
        "проанализируй массив",
        "числовой ряд",
        "числовой поток",
        "ряд данных",
        "последовательност",
        "следующая стратегия",
        "стратегия потока",
        "forecast 10",
        "прогноз 10",
        "старый малыш",
        "прежний малыш",
        "malysh engine",
    ],
})

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))




def recalled_skills() -> list:
    return [
        {
            "id": "native_malysh_engine",
            "source": "recalled_skill",
            "category": "memory.sequence_skill",
            "available": True,
        }
    ]


def organs() -> list:
    result = []

    production = load(ROOT / "config" / "organs.json")
    for item in production.get("organs", []):
        result.append({
            "id": item["id"],
            "source": "production",
            "category": item.get("category", "unclassified"),
            "available": item.get("enabled", False) and item.get("safe", False),
        })

    adapters = load(ROOT / "config" / "adapters.json")
    for item in adapters.get("adapters", []):
        result.append({
            "id": item["id"],
            "source": "adapter",
            "category": item.get("category", "unclassified"),
            "available": item.get("certified", False),
        })

    result.extend(recalled_skills())

    return result


def arithmetic_node(node):
    if isinstance(node, ast.Expression):
        return arithmetic_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Недопустимая константа")

    if isinstance(node, ast.BinOp):
        fn = OPS.get(type(node.op))
        if fn is None:
            raise ValueError("Недопустимая операция")
        return fn(
            arithmetic_node(node.left),
            arithmetic_node(node.right),
        )

    if isinstance(node, ast.UnaryOp):
        fn = OPS.get(type(node.op))
        if fn is None:
            raise ValueError("Недопустимая операция")
        return fn(arithmetic_node(node.operand))

    raise ValueError("Недопустимое выражение")

def arithmetic(text: str):
    expression = text.lower()

    replacements = {
        "плюс": "+",
        "минус": "-",
        "умножить на": "*",
        "умножить": "*",
        "разделить на": "/",
        "делить на": "/",
    }

    for old, new in replacements.items():
        expression = expression.replace(old, new)

    expression = expression.replace(",", ".")
    expression = re.sub(r"[^0-9+\-*/().%\s]", " ", expression)
    expression = re.sub(r"\s+", " ", expression).strip()

    if not expression or not re.search(r"[+\-*/%]", expression):
        return None

    try:
        tree = ast.parse(expression, mode="eval")
        return expression, arithmetic_node(tree)
    except Exception:
        return None


def route(text: str) -> dict:
    available_organs = organs()
    calculated = arithmetic(text)

    if calculated is not None:
        expression, value = calculated

        return {
            "intent": "arithmetic",
            "command": text,
            "expression": expression,
            "result": value,
            "selected": ["builtin_arithmetic"],
            "skipped": [item["id"] for item in available_organs],
        }

    lowered = text.lower()
    selected = []
    decisions = []

    for organ in available_organs:
        words = KEYWORDS.get(organ["category"], [])
        matched = [word for word in words if word in lowered]

        execute = bool(matched and organ["available"])

        if execute:
            selected.append(organ["id"])

        decisions.append({
            "id": organ["id"],
            "category": organ["category"],
            "decision": "execute" if execute else "skip",
            "matched": matched,
        })

    if not selected:
        selected = ["generation7", "grand_unified"]

        for item in decisions:
            if item["id"] in selected:
                item["decision"] = "execute"
                item["matched"] = ["fallback"]

    return {
        "intent": "semantic",
        "command": text,
        "selected": selected,
        "skipped": [
            item["id"]
            for item in decisions
            if item["decision"] == "skip"
        ],
        "decisions": decisions,
    }


def main() -> None:
    text = " ".join(sys.argv[1:]).strip()

    if not text:
        raise SystemExit(
            'Использование: python -m malysh_system.capability_router "запрос"'
        )

    report = route(text)

    print("=" * 68)
    print("МАЛЫШ: SEMANTIC CAPABILITY ROUTER")
    print("=" * 68)
    print("Запрос  :", report["command"])
    print("Intent  :", report["intent"])
    print("Выбрано :", ", ".join(report["selected"]))
    print("SKIP    :", len(report["skipped"]))

    if report["intent"] == "arithmetic":
        print("Пример :", report["expression"])
        print("Ответ  :", report["result"])
    else:
        print("-" * 68)

        for item in report["decisions"]:
            print(
                f"[{item['decision'].upper():7}] "
                f"{item['id']:<26} "
                f"{','.join(item['matched'])}"
            )

    print("-" * 68)
    print("Режим PLAN. Органы не запускались.")
    print("=" * 68)


if __name__ == "__main__":
    main()
