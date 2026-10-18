from __future__ import annotations

import json
import os

from core.malysh_firmware_compiler import FirmwareCompiler


def signal_from_environment() -> str:
    text = os.environ.get(
        "MALYSH_COMMAND_TEXT",
        "",
    )

    upper = text.upper()

    for token in upper.replace(",", " ").split():
        compact = "".join(
            char
            for char in token
            if char.isalnum()
        )

        if len(compact) >= 4:
            if any(char.isdigit() for char in compact):
                return compact

    return "6EQUJ5"


def main() -> None:
    signal = signal_from_environment()

    result = FirmwareCompiler(
        signal
    ).compile_firmware()

    summary = {
        "organ": "firmware_compiler",
        "signature": result["signature"],
        "total_power": result["total_power"],
        "node_count": len(result["nodes"]),
        "zones": {
            name: len(nodes)
            for name, nodes in result["zones"].items()
        },
    }

    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
