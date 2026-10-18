#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[1/6] Создаю конфигурацию исполнительных органов..."

cat > config/organs.json <<'JSON'
{
  "schema_version": 1,
  "timeout_seconds": 120,
  "continue_on_error": true,
  "organs": [
    {
      "id": "generation7",
      "name": "Generation 7",
      "path": "malysh_master.py",
      "category": "adaptation",
      "command": ["python", "malysh_master.py"],
      "enabled": true,
      "safe": true,
      "priority": 100
    },
    {
      "id": "grand_unified",
      "name": "Grand Unified Core",
      "path": "core/malysh_master_engine.py",
      "category": "engine",
      "command": ["python", "core/malysh_master_engine.py"],
      "enabled": true,
      "safe": true,
      "priority": 90
    },
    {
      "id": "navier_resonance",
      "name": "Navier Resonance",
      "path": "run_malysh_all.py",
      "category": "physics.navier",
      "command": ["python", "run_malysh_all.py"],
      "enabled": true,
      "safe": true,
      "priority": 80
    }
  ]
}
JSON

echo "[2/6] Создаю исполнитель органов..."

cat > malysh_system/executor.py <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from malysh_system.protocols import Command, OrganResult


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "organs.json"
LOG_DIR = ROOT / "runtime" / "organ_logs"
RESULT_DIR = ROOT / "runtime" / "results"


def load_executor_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise RuntimeError(
            f"Конфигурация органов отсутствует: {CONFIG_PATH}"
        )

    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def context_digest(context: dict[str, Any]) -> str:
    encoded = json.dumps(
        context,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


class OrganExecutor:
    def __init__(self) -> None:
        self.config = load_executor_config()
        self.timeout = int(
            self.config.get("timeout_seconds", 120)
        )
        self.continue_on_error = bool(
            self.config.get("continue_on_error", True)
        )

        LOG_DIR.mkdir(parents=True, exist_ok=True)
        RESULT_DIR.mkdir(parents=True, exist_ok=True)

    def available_organs(self) -> list[dict[str, Any]]:
        organs = []

        for spec in self.config.get("organs", []):
            if not spec.get("enabled", False):
                continue

            if not spec.get("safe", False):
                continue

            organs.append(spec)

        return sorted(
            organs,
            key=lambda item: int(item.get("priority", 0)),
            reverse=True,
        )

    def select_specs(
        self,
        selected_inventory: list[dict[str, Any]],
        all_organs: bool,
    ) -> list[dict[str, Any]]:
        available = self.available_organs()

        if all_organs:
            return available

        selected_paths = {
            item.get("path")
            for item in selected_inventory
            if item.get("path")
        }

        matched = [
            spec
            for spec in available
            if spec.get("path") in selected_paths
        ]

        return matched if matched else available

    def execute_one(
        self,
        spec: dict[str, Any],
        command: Command,
        context: dict[str, Any],
    ) -> OrganResult:
        organ_id = str(spec["id"])
        command_vector = list(spec["command"])
        started = time.monotonic()

        log_path = (
            LOG_DIR
            / f"{command.command_id}_{organ_id}.log"
        )

        environment = os.environ.copy()
        environment["MALYSH_COMMAND_ID"] = command.command_id
        environment["MALYSH_COMMAND_TEXT"] = command.text
        environment["MALYSH_COMMAND_MODE"] = command.mode
        environment["MALYSH_CONTEXT_HASH"] = context_digest(context)

        try:
            process = subprocess.run(
                command_vector,
                cwd=ROOT,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=self.timeout,
                check=False,
            )

            output = process.stdout or ""
            log_path.write_text(output, encoding="utf-8")

            status = (
                "ok"
                if process.returncode == 0
                else "error"
            )

            return OrganResult(
                organ=organ_id,
                status=status,
                data={
                    "name": spec.get("name", organ_id),
                    "category": spec.get(
                        "category",
                        "unclassified",
                    ),
                    "command": command_vector,
                    "return_code": process.returncode,
                    "duration_seconds": round(
                        time.monotonic() - started,
                        6,
                    ),
                    "log": str(log_path.relative_to(ROOT)),
                    "output_tail": output[-2000:],
                },
                error=(
                    None
                    if process.returncode == 0
                    else f"Код возврата: {process.returncode}"
                ),
            )

        except subprocess.TimeoutExpired as error:
            output = error.stdout or ""

            if isinstance(output, bytes):
                output = output.decode(
                    "utf-8",
                    errors="replace",
                )

            message = (
                f"Превышен тайм-аут {self.timeout} секунд"
            )

            log_path.write_text(
                str(output) + "\n" + message + "\n",
                encoding="utf-8",
            )

            return OrganResult(
                organ=organ_id,
                status="timeout",
                data={
                    "name": spec.get("name", organ_id),
                    "category": spec.get(
                        "category",
                        "unclassified",
                    ),
                    "duration_seconds": round(
                        time.monotonic() - started,
                        6,
                    ),
                    "log": str(log_path.relative_to(ROOT)),
                    "output_tail": str(output)[-2000:],
                },
                error=message,
            )

        except Exception as error:
            message = f"{type(error).__name__}: {error}"

            log_path.write_text(
                message + "\n",
                encoding="utf-8",
            )

            return OrganResult(
                organ=organ_id,
                status="exception",
                data={
                    "name": spec.get("name", organ_id),
                    "category": spec.get(
                        "category",
                        "unclassified",
                    ),
                    "duration_seconds": round(
                        time.monotonic() - started,
                        6,
                    ),
                    "log": str(log_path.relative_to(ROOT)),
                    "output_tail": "",
                },
                error=message,
            )

    def execute(
        self,
        command: Command,
        selected_inventory: list[dict[str, Any]],
        context: dict[str, Any],
        all_organs: bool = False,
    ) -> listspecs = self.select_specs(
            selected_inventory,
            all_organs,
        )

        results: list[OrganResult] = []

        for spec in specs:
            result = self.execute_one(
                spec,
                command,
                context,
            )
            results.append(result)

            if (
                result.status != "ok"
                and not self.continue_on_error
            ):
                break

        payload = {
            "command": command.to_dict(),
            "context_hash": context_digest(context),
            "results": [
                result.to_dict()
                for result in results
            ],
        }

        result_path = (
            RESULT_DIR
            / f"{command.command_id}.json"
        )

        result_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return results
PY

echo "[3/6] Обновляю Orchestrator..."

cat > malysh_system/orchestrator.py <<'PY'
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
PY

echo "[4/6] Обновляю интерфейс мозга..."

cat > malysh_system/brain.py <<'PY'
from __future__ import annotations

import argparse
import json

from malysh_system.orchestrator import (
    Orchestrator,
    synthesize,
)
from malysh_system.registry import load_organs


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="malysh-brain",
        description="Единая нервная система Малыша",
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    ask = sub.add_parser(
        "ask",
        help="Передать команду организму",
    )
    ask.add_argument("text")
    ask.add_argument(
        "--all",
        action="store_true",
        help="Выбрать весь организм",
    )
    ask.add_argument(
        "--execute",
        action="store_true",
        help="Запустить безопасные исполнительные органы",
    )

    sub.add_parser(
        "organs",
        help="Показать инвентаризацию органов",
    )

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

        plan = orchestrator.process(
            text=arguments.text,
            all_organs=arguments.all,
            execute=arguments.execute,
        )

        print(synthesize(plan))


if __name__ == "__main__":
    main()
PY

echo "[5/6] Обновляю .gitignore..."

touch .gitignore

for pattern in \
    "runtime/organ_logs/" \
    "runtime/results/" \
    "runtime/command_bus.jsonl"
do
    if ! grep -qxF "$pattern" .gitignore; then
        printf '%s\n' "$pattern" >> .gitignore
    fi
done

echo "[6/6] Проверяю исполнительный слой..."

python -m py_compile \
  malysh_system/protocols.py \
  malysh_system/registry.py \
  malysh_system/executor.py \
  malysh_system/orchestrator.py \
  malysh_system/brain.py

echo
echo "=== БЕЗОПАСНЫЙ ТЕСТ ПЛАНИРОВАНИЯ ==="

python -m malysh_system.brain ask --all \
  "Проверить готовность исполнительных органов"

echo
echo "=== ДОСТУПНЫЕ ИСПОЛНИТЕЛЬНЫЕ ОРГАНЫ ==="

python - <<'PY'
from malysh_system.executor import OrganExecutor

executor = OrganExecutor()

for organ in executor.available_organs():
    print(
        f"{organ['id']:20} "
        f"{organ['category']:20} "
        f"{organ['path']}"
    )
PY

echo
echo "=== GIT STATUS ==="
git status --short

echo
echo "Установка исполнительного слоя завершена."
echo
echo "Реальный запуск:"
echo 'python -m malysh_system.brain ask --all --execute "Выполни единый цикл организма"'
