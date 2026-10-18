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
