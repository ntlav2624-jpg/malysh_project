from __future__ import annotations

import json
from pathlib import Path

from malysh_system.protocols import Command, OrganResult
from malysh_system.registry import load_organs


ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "runtime" / "state.json"
BUS_PATH = ROOT / "runtime" / "command_bus.jsonl"


class SharedContext:
    def load_state(self) -> dict:
        if not STATE_PATH.exists():
            return {}

        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}


class CommandBus:
    def publish(self, command: Command) -> None:
        BUS_PATH.parent.mkdir(parents=True, exist_ok=True)

        with BUS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(command.to_dict(), ensure_ascii=False) + "\n"
            )


class Orchestrator:
    def __init__(self) -> None:
        self.context = SharedContext()
        self.bus = CommandBus()
        self.organs = load_organs()

    def select_organs(self, command: Command) -> list:
        if command.mode == "all":
            return self.organs

        text = command.text.lower()

        hints = {
            "physics.navier": ["navier", "жидк", "поток", "устойчив"],
            "physics.plasma": ["plasma", "плазм"],
            "physics.turbulence": ["turbulence", "турбул"],
            "physics.vortex": ["vortex", "вихр"],
            "geometry": ["geometry", "геометр"],
            "geometry.phase": ["phase", "фаз"],
            "geometry.toroidal": ["toroid", "тороид", "xyzt"],
            "logic.q4": ["q4", "base-4", "base 4", "четверич"],
            "logic.firmware": ["firmware"],
            "dynamics.chaos": ["chaos", "хаос"],
            "resonance": ["resonance", "резонанс"],
            "prediction": ["predict", "forecast", "прогноз"],
            "adaptation": ["adaptive", "адапт"],
            "engine": ["engine", "двигател", "ядро"],
            "math.bony": ["bony"],
        }

        selected = []

        for organ in self.organs:
            category = organ["category"]
            keywords = hints.get(category, [])

            if any(word in text for word in keywords):
                selected.append(organ)

        # Пока семантика команды неизвестна, весь организм
        # участвует на уровне анализа, но автоматически
        # произвольные старые скрипты не запускаются.
        return selected if selected else self.organs

    def plan(self, text: str, all_organs: bool = False) -> dict:
        command = Command(
            text=text,
            mode="all" if all_organs else "auto",
        )

        self.bus.publish(command)

        selected = self.select_organs(command)
        state = self.context.load_state()

        results = [
            OrganResult(
                organ=organ["name"],
                status="selected",
                data={
                    "category": organ["category"],
                    "has_main": organ["has_main"],
                },
            )
            for organ in selected
        ]

        return {
            "command": command.to_dict(),
            "organism_generation": state.get("generation"),
            "organism_status": state.get("status"),
            "selected_organs": len(selected),
            "results": [r.to_dict() for r in results],
        }


def synthesize(plan: dict) -> str:
    command = plan["command"]["text"]
    count = plan["selected_organs"]
    generation = plan.get("organism_generation")
    status = plan.get("organism_status")

    categories = sorted(
        {
            item["data"]["category"]
            for item in plan["results"]
        }
    )

    lines = [
        "=" * 68,
        "МАЛЫШ: ЕДИНАЯ НЕРВНАЯ СИСТЕМА",
        "=" * 68,
        f"Команда      : {command}",
        f"Поколение    : {generation}",
        f"Состояние    : {status}",
        f"Органов      : {count}",
        f"Контуры      : {', '.join(categories)}",
        "-" * 68,
        "Команда зарегистрирована в Command Bus.",
        "Orchestrator построил план организма.",
        "",
        "ВАЖНО:",
        "Этот этап намеренно НЕ запускает автоматически",
        "все старые Python-файлы.",
        "Сначала каждому органу будет назначен безопасный",
        "единый интерфейс выполнения.",
        "=" * 68,
    ]

    return "\n".join(lines)
