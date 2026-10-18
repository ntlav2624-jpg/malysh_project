from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from malysh_system.protocols import Command, OrganResult


ROOT = Path(__file__).resolve().parent.parent.parent
ADAPTER_CONFIG = ROOT / "config" / "adapters.json"


def load_adapter_config() -> dict[str, Any]:
    if not ADAPTER_CONFIG.exists():
        raise RuntimeError(
            f"Реестр адаптеров отсутствует: {ADAPTER_CONFIG}"
        )

    return json.loads(
        ADAPTER_CONFIG.read_text(encoding="utf-8")
    )


def digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def compact_context(
    context: dict[str, Any],
) -> dict[str, Any]:
    modules = context.get("modules", {})

    module_statuses = {
        name: data.get("status")
        for name, data in modules.items()
        if isinstance(data, dict)
    }

    return {
        "schema_version": context.get(
            "schema_version"
        ),
        "system_name": context.get("system_name"),
        "generation": context.get("generation"),
        "virtual_time": context.get(
            "virtual_time"
        ),
        "status": context.get("status"),
        "last_cycle": context.get("last_cycle"),
        "metrics": context.get("metrics", {}),
        "module_statuses": module_statuses,
    }


class ProcessOrganAdapter:
    def __init__(
        self,
        spec: dict[str, Any],
        timeout_seconds: int,
    ) -> None:
        self.spec = spec
        self.timeout_seconds = timeout_seconds

    @property
    def organ_id(self) -> str:
        return str(self.spec["id"])

    def validate(self) -> list:
        problems: list[str] = []
        path = ROOT / self.spec["path"]

        if not path.exists():
            problems.append(
                f"Файл отсутствует: {self.spec['path']}"
            )

        if not self.spec.get("certified", False):
            problems.append(
                "Орган не имеет сертификата"
            )

        if not self.spec.get("capabilities"):
            problems.append(
                "Список capabilities пуст"
            )

        return problems

    def invoke(
        self,
        command: Command,
        context: dict[str, Any],
        dry_run: bool = True,
    ) -> OrganResult:
        problems = self.validate()

        if problems:
            return OrganResult(
                organ=self.organ_id,
                status="adapter_invalid",
                data={
                    "category": self.spec.get(
                        "category",
                        "unclassified",
                    ),
                    "capabilities": self.spec.get(
                        "capabilities",
                        [],
                    ),
                    "validation_errors": problems,
                },
                error="; ".join(problems),
            )

        compact = compact_context(context)
        path = ROOT / self.spec["path"]

        if dry_run:
            return OrganResult(
                organ=self.organ_id,
                status="adapter_ready",
                data={
                    "name": self.spec.get("name"),
                    "path": self.spec["path"],
                    "category": self.spec.get(
                        "category"
                    ),
                    "capabilities": self.spec.get(
                        "capabilities",
                        [],
                    ),
                    "command_id": command.command_id,
                    "command_text": command.text,
                    "context_hash": digest_payload(
                        compact
                    ),
                    "production_enabled": bool(
                        self.spec.get(
                            "production_enabled",
                            False,
                        )
                    ),
                },
            )

        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT)
        environment["MPLBACKEND"] = "Agg"
        environment["MALYSH_ADAPTER_MODE"] = "1"
        environment["MALYSH_COMMAND_ID"] = (
            command.command_id
        )
        environment["MALYSH_COMMAND_TEXT"] = (
            command.text
        )
        environment["MALYSH_COMMAND_MODE"] = (
            command.mode
        )
        environment["MALYSH_CONTEXT_JSON"] = (
            json.dumps(
                compact,
                ensure_ascii=False,
                default=str,
            )
        )
        environment["MALYSH_CONTEXT_HASH"] = (
            digest_payload(compact)
        )

        started = time.monotonic()

        try:
            with tempfile.TemporaryDirectory(
                prefix=(
                    f"malysh_adapter_"
                    f"{self.organ_id}_"
                )
            ) as temporary_directory:
                process = subprocess.run(
                    [
                        sys.executable,
                        str(path),
                    ],
                    cwd=temporary_directory,
                    env=environment,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=self.timeout_seconds,
                    check=False,
                )

            output = process.stdout or ""
            status = (
                "ok"
                if process.returncode == 0
                else "error"
            )

            return OrganResult(
                organ=self.organ_id,
                status=status,
                data={
                    "name": self.spec.get("name"),
                    "path": self.spec["path"],
                    "category": self.spec.get(
                        "category"
                    ),
                    "capabilities": self.spec.get(
                        "capabilities",
                        [],
                    ),
                    "return_code": process.returncode,
                    "duration_seconds": round(
                        time.monotonic() - started,
                        6,
                    ),
                    "context_hash": digest_payload(
                        compact
                    ),
                    "output_tail": output[-2000:],
                    "execution_environment": (
                        "isolated_adapter"
                    ),
                },
                error=(
                    None
                    if process.returncode == 0
                    else (
                        "Код возврата: "
                        f"{process.returncode}"
                    )
                ),
            )

        except subprocess.TimeoutExpired as error:
            output = error.stdout or ""

            if isinstance(output, bytes):
                output = output.decode(
                    "utf-8",
                    errors="replace",
                )

            return OrganResult(
                organ=self.organ_id,
                status="timeout",
                data={
                    "name": self.spec.get("name"),
                    "path": self.spec["path"],
                    "category": self.spec.get(
                        "category"
                    ),
                    "capabilities": self.spec.get(
                        "capabilities",
                        [],
                    ),
                    "duration_seconds": round(
                        time.monotonic() - started,
                        6,
                    ),
                    "output_tail": str(output)[-2000:],
                    "execution_environment": (
                        "isolated_adapter"
                    ),
                },
                error=(
                    "Превышен тайм-аут "
                    f"{self.timeout_seconds} секунд"
                ),
            )

        except Exception as error:
            return OrganResult(
                organ=self.organ_id,
                status="exception",
                data={
                    "name": self.spec.get("name"),
                    "path": self.spec["path"],
                    "category": self.spec.get(
                        "category"
                    ),
                    "capabilities": self.spec.get(
                        "capabilities",
                        [],
                    ),
                    "duration_seconds": round(
                        time.monotonic() - started,
                        6,
                    ),
                    "output_tail": "",
                    "execution_environment": (
                        "isolated_adapter"
                    ),
                },
                error=(
                    f"{type(error).__name__}: {error}"
                ),
            )


def build_adapters() -> list:
    config = load_adapter_config()
    timeout_seconds = int(
        config.get(
            "default_timeout_seconds",
            30,
        )
    )

    adapters = [
        ProcessOrganAdapter(
            spec=spec,
            timeout_seconds=timeout_seconds,
        )
        for spec in config.get("adapters", [])
    ]

    return sorted(
        adapters,
        key=lambda adapter: int(
            adapter.spec.get("priority", 0)
        ),
        reverse=True,
    )
