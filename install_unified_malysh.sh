#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[1/6] Создание резервной копии..."

if [ -f malysh.py ] && [ ! -f malysh_physical_legacy.py ]; then
    cp malysh.py malysh_physical_legacy.py
fi

echo "[2/6] Создание структуры..."

mkdir -p malysh_system/modules
mkdir -p runtime/checkpoints
mkdir -p runtime/logs
mkdir -p runtime/locks
mkdir -p config

touch malysh_system/__init__.py
touch malysh_system/modules/__init__.py

echo "[3/6] Создание конфигурации..."

cat > config/malysh.json <<'JSON'
{
  "schema_version": 1,
  "system_name": "Malysh Unified System",
  "strict_mode": false,
  "continue_on_module_error": true,
  "modules": [
    {
      "name": "generation7",
      "enabled": true,
      "command": ["python", "malysh_master.py"]
    },
    {
      "name": "grand_unified",
      "enabled": true,
      "command": ["python", "core/malysh_master_engine.py"]
    },
    {
      "name": "navier_resonance",
      "enabled": true,
      "command": ["python", "run_malysh_all.py"]
    }
  ]
}
JSON

echo "[4/6] Создание супервизора..."

cat > malysh_system/supervisor.py <<'PY'
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "malysh.json"
RUNTIME_DIR = ROOT / "runtime"
STATE_PATH = RUNTIME_DIR / "state.json"
WAL_PATH = RUNTIME_DIR / "malysh.wal.jsonl"
CHECKPOINT_DIR = RUNTIME_DIR / "checkpoints"
LOG_DIR = RUNTIME_DIR / "logs"
LOCK_PATH = RUNTIME_DIR / "locks" / "malysh.lock"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def state_hash(state: dict) -> str:
    encoded = json.dumps(
        state,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


class WAL:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type: str, payload: dict) -> dict:
        event = {
            "event_id": uuid.uuid4().hex,
            "timestamp": utc_now(),
            "type": event_type,
            "payload": payload,
        }

        encoded = json.dumps(event, ensure_ascii=False)

        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(encoded + "\n")
            handle.flush()
            os.fsync(handle.fileno())

        return event

    def read_valid_events(self) -> listif not self.path.exists():
            return []

        events = []

        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    print(
                        f"[WAL] Повреждённая строка {line_number} пропущена.",
                        file=sys.stderr,
                    )

        return events


class StateStore:
    def __init__(self, state_path: Path, checkpoint_dir: Path):
        self.state_path = state_path
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def initial_state() -> dict:
        return {
            "schema_version": 1,
            "system_name": "Malysh Unified System",
            "generation": 0,
            "virtual_time": 0,
            "status": "initialized",
            "active_cycle": None,
            "last_cycle": None,
            "modules": {},
            "metrics": {},
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }

    def load(self) -> dict:
        return load_json(self.state_path, self.initial_state())

    def save(self, state: dict) -> None:
        state["updated_at"] = utc_now()
        atomic_write_json(self.state_path, state)

    def checkpoint(self, state: dict) -> Path:
        checkpoint_name = (
            f"state_g{state.get('generation', 0):06d}_"
            f"{int(time.time())}.json"
        )
        checkpoint_path = self.checkpoint_dir / checkpoint_name
        atomic_write_json(checkpoint_path, state)
        return checkpoint_path

    def latest_checkpoint(self) -> Path | None:
        candidates = sorted(self.checkpoint_dir.glob("state_*.json"))
        return candidates[-1] if candidates else None


class ProcessModule:
    def __init__(self, spec: dict):
        self.name = spec["name"]
        self.command = spec["command"]
        self.enabled = bool(spec.get("enabled", True))

    def execute(self, cycle_id: str) -> dict:
        started = time.monotonic()
        log_path = LOG_DIR / f"{cycle_id}_{self.name}.log"

        try:
            process = subprocess.run(
                self.command,
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )

            output = process.stdout or ""
            log_path.write_text(output, encoding="utf-8")

            return {
                "name": self.name,
                "status": "ok" if process.returncode == 0 else "error",
                "return_code": process.returncode,
                "duration_seconds": round(time.monotonic() - started, 6),
                "log": str(log_path.relative_to(ROOT)),
                "output_tail": output[-2000:],
            }

        except Exception as error:
            message = f"{type(error).__name__}: {error}"
            log_path.write_text(message + "\n", encoding="utf-8")

            return {
                "name": self.name,
                "status": "exception",
                "return_code": None,
                "duration_seconds": round(time.monotonic() - started, 6),
                "log": str(log_path.relative_to(ROOT)),
                "output_tail": message,
            }


class MalyshSupervisor:
    def __init__(self):
        self.config = load_json(CONFIG_PATH, {})
        self.wal = WAL(WAL_PATH)
        self.store = StateStore(STATE_PATH, CHECKPOINT_DIR)

        self.modules = [
            ProcessModule(spec)
            for spec in self.config.get("modules", [])
            if spec.get("enabled", True)
        ]

    def acquire_lock(self) -> None:
        LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)

        try:
            descriptor = os.open(
                LOCK_PATH,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
        except FileExistsError:
            raise RuntimeError(
                "Малыш уже запущен или остался аварийный lock. "
                "Проверь процесс, затем используй: python malysh.py unlock"
            )

        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "pid": os.getpid(),
                        "created_at": utc_now(),
                    },
                    ensure_ascii=False,
                )
            )

    def release_lock(self) -> None:
        LOCK_PATH.unlink(missing_ok=True)

    def run_cycle(self) -> dict:
        self.acquire_lock()

        try:
            state = self.store.load()
            cycle_id = uuid.uuid4().hex
            next_generation = int(state.get("generation", 0)) + 1

            state["status"] = "running"
            state["active_cycle"] = cycle_id

            self.wal.append(
                "STEP_BEGIN",
                {
                    "cycle_id": cycle_id,
                    "generation": next_generation,
                },
            )
            self.store.save(state)

            results = []
            continue_on_error = bool(
                self.config.get("continue_on_module_error", True)
            )

            for module in self.modules:
                self.wal.append(
                    "MODULE_BEGIN",
                    {
                        "cycle_id": cycle_id,
                        "module": module.name,
                    },
                )

                result = module.execute(cycle_id)
                results.append(result)
                state["modules"][module.name] = result

                self.wal.append(
                    "MODULE_RESULT",
                    {
                        "cycle_id": cycle_id,
                        "module": module.name,
                        "status": result["status"],
                        "return_code": result["return_code"],
                        "log": result["log"],
                    },
                )

                self.store.save(state)

                if result["status"] != "ok" and not continue_on_error:
                    break

            errors = [
                result
                for result in results
                if result["status"] != "ok"
            ]

            state["generation"] = next_generation
            state["virtual_time"] = int(state.get("virtual_time", 0)) + 1
            state["status"] = "degraded" if errors else "ready"
            state["active_cycle"] = None
            state["last_cycle"] = {
                "cycle_id": cycle_id,
                "completed_at": utc_now(),
                "module_count": len(results),
                "error_count": len(errors),
            }

            digest = state_hash(state)

            self.wal.append(
                "STATE_COMMIT",
                {
                    "cycle_id": cycle_id,
                    "generation": next_generation,
                    "state_hash": digest,
                },
            )

            self.store.save(state)
            checkpoint_path = self.store.checkpoint(state)

            print("=" * 68)
            print("МАЛЫШ: ЕДИНЫЙ ЦИКЛ ЗАВЕРШЁН")
            print(f"Цикл       : {cycle_id}")
            print(f"Поколение  : {next_generation}")
            print(f"Состояние  : {state['status']}")
            print(f"Модулей    : {len(results)}")
            print(f"Ошибок     : {len(errors)}")
            print(f"Checkpoint : {checkpoint_path.relative_to(ROOT)}")
            print("=" * 68)

            for result in results:
                print(
                    f"[{result['status'].upper():9}] "
                    f"{result['name']:<20} "
                    f"{result['duration_seconds']:>9.3f} s"
                )

            return state

        finally:
            self.release_lock()

    def status(self) -> None:
        state = self.store.load()
        print(json.dumps(state, ensure_ascii=False, indent=2))

    def inspect(self) -> None:
        state = self.store.load()
        events = self.wal.read_valid_events()

        report = {
            "state": state,
            "state_hash": state_hash(state),
            "wal_events": len(events),
            "configured_modules": [
                module.name for module in self.modules
            ],
            "lock_exists": LOCK_PATH.exists(),
            "latest_checkpoint": (
                str(self.store.latest_checkpoint().relative_to(ROOT))
                if self.store.latest_checkpoint()
                else None
            ),
        }

        print(json.dumps(report, ensure_ascii=False, indent=2))

    def recover(self) -> None:
        checkpoint = self.store.latest_checkpoint()

        if checkpoint is None:
            print("[RECOVER] Checkpoint отсутствует.")
            return

        recovered_state = load_json(
            checkpoint,
            self.store.initial_state(),
        )
        recovered_state["status"] = "recovered"
        recovered_state["active_cycle"] = None

        self.wal.append(
            "STATE_RECOVERED",
            {
                "checkpoint": str(checkpoint.relative_to(ROOT)),
                "generation": recovered_state.get("generation", 0),
            },
        )

        self.store.save(recovered_state)
        LOCK_PATH.unlink(missing_ok=True)

        print(
            "[RECOVER] Состояние восстановлено из "
            f"{checkpoint.relative_to(ROOT)}"
        )

    def unlock(self) -> None:
        if LOCK_PATH.exists():
            LOCK_PATH.unlink()
            print("[LOCK] Аварийный lock удалён.")
        else:
            print("[LOCK] Lock отсутствует.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="malysh",
        description="Единый супервизор системы Малыш",
    )

    parser.add_argument(
        "command",
        choices=["run", "step", "status", "inspect", "recover", "unlock"],
    )

    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    supervisor = MalyshSupervisor()

    if arguments.command in {"run", "step"}:
        supervisor.run_cycle()
    elif arguments.command == "status":
        supervisor.status()
    elif arguments.command == "inspect":
        supervisor.inspect()
    elif arguments.command == "recover":
        supervisor.recover()
    elif arguments.command == "unlock":
        supervisor.unlock()


if __name__ == "__main__":
    main()
PY

echo "[5/6] Создание единой точки входа..."

cat > malysh.py <<'PY'
#!/usr/bin/env python3

from malysh_system.supervisor import main


if __name__ == "__main__":
    main()
PY

chmod +x malysh.py

echo "[6/6] Обновление .gitignore..."

touch .gitignore

for pattern in \
    "runtime/logs/" \
    "runtime/locks/" \
    "runtime/checkpoints/" \
    "runtime/state.json" \
    "runtime/malysh.wal.jsonl"
do
    if ! grep -qxF "$pattern" .gitignore; then
        printf '%s\n' "$pattern" >> .gitignore
    fi
done

python -m py_compile \
    malysh.py \
    malysh_system/supervisor.py

echo
echo "Установка завершена."
echo "Проверка: python malysh.py inspect"
echo "Запуск:   python malysh.py run"
