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
    ) -> list:
        specs = self.select_specs(
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
