from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from malysh_system.executor import OrganExecutor
from malysh_system.protocols import Command, OrganResult
from malysh_system.registry import load_organs


ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "runtime" / "state.json"
BUS_PATH = ROOT / "runtime" / "command_bus.jsonl"


class SharedContext:
    def load_state(self) -> dict[str, Any]:
        if not STATE_PATH.exists():
            return {}

        try:
            return json.loads(
                STATE_PATH.read_text(encoding="utf-8")
            )
        except Exception:
            return {}


class CommandBus:
    def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        BUS_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        event = {
            "type": event_type,
            "payload": payload,
        }

        with BUS_PATH.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                json.dumps(
                    event,
                    ensure_ascii=False,
                )
                + "\n"
            )


class Orchestrator:
    def __init__(self) -> None:
        self.context = SharedContext()
        self.bus = CommandBus()
        self.organs = load_organs()

    def select_organs(
        self,
        command: Command,
    ) -> list[dict[str, Any]]:
        if command.mode == "all":
            return self.organs

        text = command.text.lower()

        hints = {
            "physics.navier": [
                "navier",
                "жидк",
                "поток",
                "устойчив",
            ],
            "physics.plasma": [
                "plasma",
                "плазм",
            ],
            "physics.turbulence": [
                "turbulence",
                "турбул",
            ],
            "physics.vortex": [
                "vortex",
                "вихр",
            ],
            "geometry": [
                "geometry",
                "геометр",
            ],
            "geometry.phase": [
                "phase",
                "фаз",
            ],
            "geometry.toroidal": [
                "toroid",
                "тороид",
                "xyzt",
            ],
            "logic.q4": [
                "q4",
                "base-4",
                "base 4",
                "четверич",
            ],
            "logic.firmware": [
                "firmware",
                "прошив",
            ],
            "dynamics.chaos": [
                "chaos",
                "хаос",
            ],
            "resonance": [
                "resonance",
                "резонанс",
            ],
            "prediction": [
                "predict",
                "forecast",
                "прогноз",
            ],
            "adaptation": [
                "adaptive",
                "адапт",
                "поколен",
            ],
            "engine": [
                "engine",
                "двигател",
                "ядро",
            ],
            "math.bony": [
                "bony",
            ],
        }

        selected = []

        for organ in self.organs:
            category = organ["category"]
            keywords = hints.get(category, [])

            if any(
                keyword in text
                for keyword in keywords
            ):
                selected.append(organ)

        return selected if selected else self.organs

    def process(
        self,
        text: str,
        all_organs: bool = False,
        execute: bool = False,
    ) -> dict[str, Any]:
        command = Command(
            text=text,
            mode="all" if all_organs else "auto",
        )

        self.bus.publish(
            "COMMAND_RECEIVED",
            command.to_dict(),
        )

        selected = self.select_organs(command)
        state = self.context.load_state()

        self.bus.publish(
            "PLAN_CREATED",
            {
                "command_id": command.command_id,
                "selected_organs": [
                    item["name"]
                    for item in selected
                ],
            },
        )

        if execute:
            executor = OrganExecutor()

            results = executor.execute(
                command=command,
                selected_inventory=selected,
                context=state,
                all_organs=all_organs,
            )

            self.bus.publish(
                "EXECUTION_COMPLETED",
                {
                    "command_id": command.command_id,
                    "results": [
                        {
                            "organ": result.organ,
                            "status": result.status,
                        }
                        for result in results
                    ],
                },
            )
        else:
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
            "executed": execute,
            "organism_generation": state.get(
                "generation"
            ),
            "organism_status": state.get("status"),
            "selected_organs": len(selected),
            "executed_organs": (
                len(results)
                if execute
                else 0
            ),
            "results": [
                result.to_dict()
                for result in results
            ],
        }


def synthesize(plan: dict[str, Any]) -> str:
    command = plan["command"]["text"]
    generation = plan.get("organism_generation")
    organism_status = plan.get("organism_status")
    executed = bool(plan.get("executed"))

    results = plan.get("results", [])
    successful = sum(
        1
        for item in results
        if item.get("status") == "ok"
    )
    failed = sum(
        1
        for item in results
        if item.get("status")
        in {"error", "exception", "timeout"}
    )

    categories = sorted(
        {
            item.get("data", {}).get(
                "category",
                "unclassified",
            )
            for item in results
        }
    )

    lines = [
        "=" * 68,
        "МАЛЫШ: ЕДИНЫЙ ОРГАНИЗМ",
        "=" * 68,
        f"Команда       : {command}",
        f"Поколение     : {generation}",
        f"Состояние     : {organism_status}",
        f"Режим         : {'EXECUTE' if executed else 'PLAN'}",
        f"Выбрано       : {plan.get('selected_organs', 0)}",
        f"Исполнено     : {plan.get('executed_organs', 0)}",
        f"Успешно       : {successful}",
        f"Ошибок        : {failed}",
        f"Контуры       : {', '.join(categories)}",
        "-" * 68,
    ]

    if executed:
        for item in results:
            data = item.get("data", {})
            lines.append(
                f"[{item['status'].upper():9}] "
                f"{item['organ']:<20} "
                f"{data.get('duration_seconds', 0):>9.3f} s"
            )

            output_tail = data.get("output_tail", "").strip()

            if output_tail:
                compact = output_tail.splitlines()[-1]
                lines.append(
                    f"  Итог: {compact[:160]}"
                )

            if item.get("error"):
                lines.append(
                    f"  Ошибка: {item['error']}"
                )
    else:
        lines.extend(
            [
                "План построен без запуска органов.",
                "Для исполнения добавь флаг --execute.",
            ]
        )

    lines.append("=" * 68)
    return "\n".join(lines)
