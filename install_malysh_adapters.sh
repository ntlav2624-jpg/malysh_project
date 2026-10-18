#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[1/6] Создаю каталог адаптеров..."

mkdir -p malysh_system/adapters
touch malysh_system/adapters/__init__.py

echo "[2/6] Создаю реестр адаптированных органов..."

cat > config/adapters.json <<'JSON'
{
  "schema_version": 1,
  "enabled_in_production": false,
  "default_timeout_seconds": 30,
  "adapters": [
    {
      "id": "chaos_handler",
      "name": "Chaos and Uncertainty Handler",
      "path": "malysh_chaos.py",
      "category": "dynamics.chaos",
      "capabilities": [
        "chaos_analysis",
        "uncertainty_estimation",
        "lyapunov_horizon"
      ],
      "certified": true,
      "production_enabled": false,
      "priority": 79
    },
    {
      "id": "chaos_bypass",
      "name": "Lyapunov Bypass Engine",
      "path": "malysh_chaos_bypass.py",
      "category": "dynamics.chaos",
      "capabilities": [
        "chaos_bypass",
        "attractor_fallback",
        "strategy_evaluation"
      ],
      "certified": true,
      "production_enabled": false,
      "priority": 78
    },
    {
      "id": "bony_paraproduct",
      "name": "Bony Paraproduct Engine",
      "path": "malysh_bony_paraproduct_engine.py",
      "category": "math.bony",
      "capabilities": [
        "bony_decomposition",
        "clebsch_gluing",
        "nonlinear_bounds"
      ],
      "certified": true,
      "production_enabled": false,
      "priority": 77
    },
    {
      "id": "weighted_bony",
      "name": "Weighted Bony Closure",
      "path": "malysh_weighted_bony_closure.py",
      "category": "math.bony",
      "capabilities": [
        "weighted_tail_bound",
        "dynamic_cutoff",
        "closure_stability"
      ],
      "certified": true,
      "production_enabled": false,
      "priority": 76
    },
    {
      "id": "navier_continuum",
      "name": "Navier Continuum Closure",
      "path": "malysh_navier_continuum_closure.py",
      "category": "physics.navier",
      "capabilities": [
        "continuum_closure",
        "partition_residuals",
        "littlewood_paley"
      ],
      "certified": true,
      "production_enabled": false,
      "priority": 75
    },
    {
      "id": "navier_dynamic",
      "name": "Navier Dynamic Engine",
      "path": "malysh_navier_dynamic.py",
      "category": "physics.navier",
      "capabilities": [
        "dynamic_evolution",
        "flow_step",
        "stability_analysis"
      ],
      "certified": true,
      "production_enabled": false,
      "priority": 74
    },
    {
      "id": "navier_spectral",
      "name": "Navier Spectral Engine",
      "path": "malysh_navier_spectral.py",
      "category": "physics.navier",
      "capabilities": [
        "spectral_majorant",
        "helicity_dissipation",
        "spectral_stability"
      ],
      "certified": true,
      "production_enabled": false,
      "priority": 73
    },
    {
      "id": "plasma_vortex",
      "name": "Plasma Vortex Engine",
      "path": "malysh_plasma_vortex.py",
      "category": "physics.plasma",
      "capabilities": [
        "plasma_evolution",
        "vortex_dynamics",
        "field_stability"
      ],
      "certified": true,
      "production_enabled": false,
      "priority": 72
    },
    {
      "id": "astrophysical_turbulence",
      "name": "Astrophysical Turbulence Solver",
      "path": "astrophysical_turbulence.py",
      "category": "physics.turbulence",
      "capabilities": [
        "turbulence_simulation",
        "accretion_flow",
        "energy_transport"
      ],
      "certified": true,
      "production_enabled": false,
      "priority": 71
    }
  ]
}
JSON

echo "[3/6] Создаю единый адаптер..."

cat > malysh_system/adapters/process_adapter.py <<'PY'
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

    def validate(self) -> listproblems: list[str] = []
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


def build_adapters() -> listconfig = load_adapter_config()
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
PY

echo "[4/6] Создаю лабораторный тест адаптеров..."

cat > malysh_system/adapter_lab.py <<'PY'
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from malysh_system.adapters.process_adapter import (
    build_adapters,
)
from malysh_system.protocols import Command


ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "runtime" / "state.json"
REPORT_DIR = ROOT / "runtime" / "adapter_lab"
REPORT_PATH = REPORT_DIR / "latest.json"


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}

    return json.loads(
        STATE_PATH.read_text(encoding="utf-8")
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="malysh-adapter-lab",
        description=(
            "Лабораторная проверка адаптеров "
            "организма Малыш"
        ),
    )

    parser.add_argument(
        "--invoke",
        action="store_true",
        help=(
            "Выполнить изолированный запуск "
            "адаптированных органов"
        ),
    )

    parser.add_argument(
        "--text",
        default=(
            "Проверить готовность "
            "адаптированных органов"
        ),
    )

    arguments = parser.parse_args()

    command = Command(
        text=arguments.text,
        mode="adapter_lab",
    )
    context = load_state()
    adapters = build_adapters()

    results = [
        adapter.invoke(
            command=command,
            context=context,
            dry_run=not arguments.invoke,
        )
        for adapter in adapters
    ]

    ready_statuses = {
        "adapter_ready",
        "ok",
    }

    summary = {
        "total": len(results),
        "ready": sum(
            result.status in ready_statuses
            for result in results
        ),
        "failed": sum(
            result.status not in ready_statuses
            for result in results
        ),
        "invoke": bool(arguments.invoke),
        "generation_before": context.get(
            "generation"
        ),
        "virtual_time_before": context.get(
            "virtual_time"
        ),
    }

    report = {
        "schema_version": 1,
        "mode": (
            "isolated_invoke"
            if arguments.invoke
            else "adapter_dry_run"
        ),
        "production_registry_modified": False,
        "command": command.to_dict(),
        "context_generation": context.get(
            "generation"
        ),
        "context_virtual_time": context.get(
            "virtual_time"
        ),
        "summary": summary,
        "results": [
            result.to_dict()
            for result in results
        ],
    }

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    REPORT_PATH.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 72)
    print("МАЛЫШ: ЛАБОРАТОРИЯ АДАПТЕРОВ")
    print("=" * 72)
    print(
        f"Режим          : "
        f"{report['mode']}"
    )
    print(
        f"Поколение      : "
        f"{report['context_generation']}"
    )
    print(
        f"Виртуальное t  : "
        f"{report['context_virtual_time']}"
    )
    print(
        f"Адаптеров      : "
        f"{summary['total']}"
    )
    print(
        f"Готово         : "
        f"{summary['ready']}"
    )
    print(
        f"Ошибок         : "
        f"{summary['failed']}"
    )
    print("-" * 72)

    for result in results:
        capabilities = ",".join(
            result.data.get(
                "capabilities",
                [],
            )
        )

        print(
            f"[{result.status.upper():15}] "
            f"{result.organ:<26}"
        )
        print(
            f"  capabilities: {capabilities}"
        )

        if result.error:
            print(
                f"  error: {result.error}"
            )

    print("-" * 72)
    print(
        "Боевой config/organs.json "
        "НЕ изменялся."
    )
    print(
        "Центральная транзакция "
        "НЕ выполнялась."
    )
    print(
        "Отчёт: runtime/adapter_lab/latest.json"
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
PY

echo "[5/6] Обновляю .gitignore..."

touch .gitignore

for pattern in \
  "runtime/adapter_lab/" \
  "runtime/adapter_lab/latest.json"
do
    if ! grep -qxF "$pattern" .gitignore; then
        printf '%s\n' "$pattern" >> .gitignore
    fi
done

echo "[6/6] Проверяю Adapter Layer..."

python -m json.tool \
  config/adapters.json >/dev/null

python -m py_compile \
  malysh_system/adapters/__init__.py \
  malysh_system/adapters/process_adapter.py \
  malysh_system/adapter_lab.py

echo "ADAPTER SYNTAX: OK"

echo
echo "=== DRY-RUN АДАПТЕРОВ ==="

python -m malysh_system.adapter_lab

echo
echo "=== ПРОВЕРКА СОСТОЯНИЯ ==="

python - <<'PY'
import json
from pathlib import Path

state = json.loads(
    Path("runtime/state.json").read_text(
        encoding="utf-8"
    )
)

print("generation  :", state.get("generation"))
print("virtual_time:", state.get("virtual_time"))
print("status      :", state.get("status"))
print("active_cycle:", state.get("active_cycle"))
PY

echo
echo "=== КОНТРОЛЬ БОЕВОГО РЕЕСТРА ==="

python - <<'PY'
import json
from pathlib import Path

config = json.loads(
    Path("config/organs.json").read_text(
        encoding="utf-8"
    )
)

print(
    "Боевых органов:",
    len(config.get("organs", [])),
)

for organ in config.get("organs", []):
    print(
        f"  {organ['id']}: "
        f"safe={organ['safe']}"
    )
PY

echo
echo "=== GIT STATUS ==="

git status --short

echo
echo "Adapter Layer установлен."
echo "Боевой EXECUTE не выполнялся."
echo "Изолированный invoke пока не выполнялся."
