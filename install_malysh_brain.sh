#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[1/5] Создаю протокол..."

cat > malysh_system/protocols.py <<'PY'
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import uuid


@dataclass
class Command:
    text: str
    command_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    mode: str = "auto"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OrganResult:
    organ: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
PY


echo "[2/5] Создаю реестр органов..."

cat > malysh_system/registry.py <<'PY'
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "malysh_system" / "organ_inventory.json"


def load_organs() -> listif not INVENTORY.exists():
        return []

    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    organs = []

    for module in data.get("modules", []):
        if not module.get("syntax_ok", False):
            continue

        path = module["path"]

        # Служебные файлы мозга не считаем вычислительными органами.
        if path.startswith("malysh_system/"):
            continue

        organs.append(
            {
                "name": path,
                "category": module.get("category", "unclassified"),
                "path": path,
                "has_main": module.get("has_main", False),
                "classes": module.get("classes", []),
                "functions": module.get("functions", []),
            }
        )

    return organs
PY


echo "[3/5] Создаю Command Bus и Orchestrator..."

cat > malysh_system/orchestrator.py <<'PY'
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

    def select_organs(self, command: Command) -> listif command.mode == "all":
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
PY


echo "[4/5] Создаю интерфейс команд..."

cat > malysh_system/brain.py <<'PY'
from __future__ import annotations

import argparse
import json

from malysh_system.orchestrator import Orchestrator, synthesize
from malysh_system.registry import load_organs


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="malysh-brain",
        description="Единая нервная система Малыша",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    ask = sub.add_parser("ask")
    ask.add_argument("text")
    ask.add_argument("--all", action="store_true")

    sub.add_parser("organs")

    arguments = parser.parse_args()

    if arguments.command == "organs":
        print(
            json.dumps(
                load_organs(),
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if arguments.command == "ask":
        orchestrator = Orchestrator()

        plan = orchestrator.plan(
            arguments.text,
            all_organs=arguments.all,
        )

        print(synthesize(plan))


if __name__ == "__main__":
    main()
PY


echo "[5/5] Проверяю..."

python -m py_compile \
    malysh_system/protocols.py \
    malysh_system/registry.py \
    malysh_system/orchestrator.py \
    malysh_system/brain.py

echo
echo "=== ТЕСТ НЕРВНОЙ СИСТЕМЫ ==="

python -m malysh_system.brain ask --all \
    "Проверить состояние единого организма"

echo
echo "=== GIT STATUS ==="
git status --short

echo
echo "ГОТОВО."
echo
echo "Пример команды:"
echo 'python -m malysh_system.brain ask --all "Исследуй состояние системы"'
