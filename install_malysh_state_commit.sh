#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[1/6] Создаю резервную копию Orchestrator..."

cp \
  malysh_system/orchestrator.py \
  malysh_system/orchestrator.py.before_state_commit

echo "[2/6] Создаю транзакционный слой состояния..."

cat > malysh_system/transaction.py <<'PY'
from __future__ import annotations

import os
from typing import Any

from malysh_system.protocols import Command, OrganResult
from malysh_system.supervisor import (
    CHECKPOINT_DIR,
    LOCK_PATH,
    STATE_PATH,
    WAL_PATH,
    StateStore,
    WAL,
    state_hash,
    utc_now,
)


class OrganismTransaction:
    def __init__(self) -> None:
        self.store = StateStore(
            STATE_PATH,
            CHECKPOINT_DIR,
        )
        self.wal = WAL(WAL_PATH)
        self.lock_acquired = False
        self.command_id: str | None = None

    def acquire_lock(self, command_id: str) -> None:
        LOCK_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            descriptor = os.open(
                LOCK_PATH,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
        except FileExistsError as error:
            raise RuntimeError(
                "Организм уже выполняет транзакцию или "
                "остался аварийный lock. Проверь процесс, "
                "затем используй: python malysh.py unlock"
            ) from error

        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
        ) as handle:
            handle.write(
                f'{{"pid": {os.getpid()}, '
                f'"command_id": "{command_id}", '
                f'"created_at": "{utc_now()}"}}'
            )

        self.lock_acquired = True

    def release_lock(self) -> None:
        if self.lock_acquired:
            LOCK_PATH.unlink(missing_ok=True)
            self.lock_acquired = False

    def begin(self, command: Command) -> dict[str, Any]:
        self.command_id = command.command_id
        self.acquire_lock(command.command_id)

        state = self.store.load()
        next_generation = (
            int(state.get("generation", 0)) + 1
        )

        state["status"] = "running"
        state["active_cycle"] = command.command_id

        self.wal.append(
            "ORGANISM_COMMAND_BEGIN",
            {
                "cycle_id": command.command_id,
                "generation": next_generation,
                "command": command.text,
                "mode": command.mode,
            },
        )

        self.store.save(state)
        return state

    def commit(
        self,
        command: Command,
        results: list[OrganResult],
    ) -> tuple[dict[str, Any], str]:
        state = self.store.load()

        errors = [
            result
            for result in results
            if result.status != "ok"
        ]

        state.setdefault("modules", {})

        for result in results:
            data = dict(result.data)

            state["modules"][result.organ] = {
                "name": result.organ,
                "status": result.status,
                "return_code": data.get("return_code"),
                "duration_seconds": data.get(
                    "duration_seconds"
                ),
                "log": data.get("log"),
                "output_tail": data.get(
                    "output_tail",
                    "",
                ),
                "error": result.error,
            }

            self.wal.append(
                "ORGAN_RESULT",
                {
                    "cycle_id": command.command_id,
                    "organ": result.organ,
                    "status": result.status,
                    "return_code": data.get(
                        "return_code"
                    ),
                    "log": data.get("log"),
                },
            )

        next_generation = (
            int(state.get("generation", 0)) + 1
        )

        state["generation"] = next_generation
        state["virtual_time"] = (
            int(state.get("virtual_time", 0)) + 1
        )
        state["status"] = (
            "degraded"
            if errors
            else "ready"
        )
        state["active_cycle"] = None

        state["last_cycle"] = {
            "cycle_id": command.command_id,
            "command": command.text,
            "completed_at": utc_now(),
            "module_count": len(results),
            "error_count": len(errors),
            "execution_mode": "orchestrated",
        }

        state.setdefault("metrics", {})
        state["metrics"]["last_successful_organs"] = (
            len(results) - len(errors)
        )
        state["metrics"]["last_failed_organs"] = (
            len(errors)
        )

        self.store.save(state)
        digest = state_hash(state)

        checkpoint = self.store.checkpoint(state)

        self.wal.append(
            "STATE_COMMIT",
            {
                "cycle_id": command.command_id,
                "generation": next_generation,
                "virtual_time": state["virtual_time"],
                "state_hash": digest,
                "checkpoint": str(checkpoint),
                "source": "orchestrator",
            },
        )

        self.release_lock()

        return state, str(checkpoint)

    def abort(
        self,
        command: Command,
        error: BaseException,
    ) -> None:
        try:
            state = self.store.load()
            state["status"] = "degraded"
            state["active_cycle"] = None

            state["last_abort"] = {
                "cycle_id": command.command_id,
                "command": command.text,
                "timestamp": utc_now(),
                "error": (
                    f"{type(error).__name__}: {error}"
                ),
            }

            self.wal.append(
                "ORGANISM_COMMAND_ABORT",
                state["last_abort"],
            )

            self.store.save(state)

        finally:
            self.release_lock()
PY

echo "[3/6] Подключаю транзакцию к Orchestrator..."

python - <<'PY'
from pathlib import Path

path = Path("malysh_system/orchestrator.py")
text = path.read_text(encoding="utf-8")

import_anchor = (
    "from malysh_system.registry import load_organs\n"
)

import_replacement = (
    "from malysh_system.registry import load_organs\n"
    "from malysh_system.transaction import OrganismTransaction\n"
)

if "OrganismTransaction" not in text:
    if import_anchor not in text:
        raise SystemExit(
            "ERROR: точка добавления импорта не найдена"
        )

    text = text.replace(
        import_anchor,
        import_replacement,
        1,
    )

init_anchor = (
    "        self.organs = load_organs()\n"
)

init_replacement = (
    "        self.organs = load_organs()\n"
    "        self.transaction = OrganismTransaction()\n"
)

if "self.transaction = OrganismTransaction()" not in text:
    if init_anchor not in text:
        raise SystemExit(
            "ERROR: точка инициализации не найдена"
        )

    text = text.replace(
        init_anchor,
        init_replacement,
        1,
    )

old_execute = '''        if execute:
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
'''

new_execute = '''        checkpoint = None

        if execute:
            executor = OrganExecutor()
            self.transaction.begin(command)

            try:
                results = executor.execute(
                    command=command,
                    selected_inventory=selected,
                    context=state,
                    all_organs=all_organs,
                )

                state, checkpoint = self.transaction.commit(
                    command,
                    results,
                )

            except BaseException as error:
                self.transaction.abort(
                    command,
                    error,
                )
                raise

            self.bus.publish(
                "EXECUTION_COMPLETED",
                {
                    "command_id": command.command_id,
                    "generation": state.get("generation"),
                    "checkpoint": checkpoint,
                    "results": [
                        {
                            "organ": result.organ,
                            "status": result.status,
                        }
                        for result in results
                    ],
                },
            )
'''

if "self.transaction.begin(command)" not in text:
    if old_execute not in text:
        raise SystemExit(
            "ERROR: блок исполнения Orchestrator не найден"
        )

    text = text.replace(
        old_execute,
        new_execute,
        1,
    )

return_anchor = (
    '            "executed": execute,\n'
    '            "organism_generation": state.get(\n'
)

return_replacement = (
    '            "executed": execute,\n'
    '            "checkpoint": checkpoint,\n'
    '            "organism_generation": state.get(\n'
)

if '"checkpoint": checkpoint' not in text:
    if return_anchor not in text:
        raise SystemExit(
            "ERROR: блок результата Orchestrator не найден"
        )

    text = text.replace(
        return_anchor,
        return_replacement,
        1,
    )

path.write_text(text, encoding="utf-8")
print("OK: Orchestrator подключён к транзакции")
PY

echo "[4/6] Добавляю checkpoint в итоговый отчёт..."

python - <<'PY'
from pathlib import Path

path = Path("malysh_system/orchestrator.py")
text = path.read_text(encoding="utf-8")

anchor = (
    '        f"Ошибок        : {failed}",\n'
    '        f"Контуры       : {\', \'.join(categories)}",\n'
)

replacement = (
    '        f"Ошибок        : {failed}",\n'
    '        f"Checkpoint    : {plan.get(\'checkpoint\')}",\n'
    '        f"Контуры       : {\', \'.join(categories)}",\n'
)

if 'f"Checkpoint    :' not in text:
    if anchor not in text:
        raise SystemExit(
            "ERROR: точка отчёта checkpoint не найдена"
        )

    text = text.replace(
        anchor,
        replacement,
        1,
    )

path.write_text(text, encoding="utf-8")
print("OK: checkpoint добавлен в отчёт")
PY

echo "[5/6] Проверяю синтаксис..."

python -m py_compile \
  malysh_system/supervisor.py \
  malysh_system/protocols.py \
  malysh_system/registry.py \
  malysh_system/executor.py \
  malysh_system/transaction.py \
  malysh_system/orchestrator.py \
  malysh_system/brain.py

echo "PYTHON SYNTAX: OK"

echo "[6/6] Выполняю безопасный PLAN-тест..."

python -m malysh_system.brain ask --all \
  "Проверить транзакционный слой организма"

echo
echo "=== ПРОВЕРКА, ЧТО PLAN НЕ ИЗМЕНИЛ ПОКОЛЕНИЕ ==="

python - <<'PY'
import json
from pathlib import Path

path = Path("runtime/state.json")
state = json.loads(path.read_text(encoding="utf-8"))

print("generation  :", state.get("generation"))
print("virtual_time:", state.get("virtual_time"))
print("status      :", state.get("status"))
print("active_cycle:", state.get("active_cycle"))
PY

echo
echo "=== GIT STATUS ==="

git status --short

echo
echo "Транзакционный слой установлен."
echo "Реальный EXECUTE пока не запускался."
