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
