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
