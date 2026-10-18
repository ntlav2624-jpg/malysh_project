from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from malysh_system.passport_memory import (
    DEFAULT_VAULT,
    analyze_vault,
    render_passport_markdown,
    write_passport,
)


DEFAULT_OUTPUT = Path(
    "malysh_project_passport.md"
)


def build_passport(
    vault_dir: Path = DEFAULT_VAULT,
    generated_at: str | None = None,
) -> tuple[
    str,
    dict[str, Any],
]:
    """
    Формирует паспорт в памяти без записи файла.
    """
    analysis = analyze_vault(
        vault_dir
    )

    document = render_passport_markdown(
        analysis,
        generated_at=generated_at,
    )

    return document, analysis


def save_passport(
    output_path: Path = DEFAULT_OUTPUT,
    vault_dir: Path = DEFAULT_VAULT,
    generated_at: str | None = None,
) -> Path:
    """
    Явная операция экспорта паспорта.
    """
    return write_passport(
        output_path=output_path,
        vault_dir=vault_dir,
        generated_at=generated_at,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="malysh-passport",
    )

    parser.add_argument(
        "--vault",
        type=Path,
        default=DEFAULT_VAULT,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    parser.add_argument(
        "--stdout",
        action="store_true",
    )

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.stdout:
        document, analysis = build_passport(
            vault_dir=args.vault,
        )

        print(document)
        print(
            "Passports:",
            analysis["passport_count"],
        )
        return

    output = save_passport(
        output_path=args.output,
        vault_dir=args.vault,
    )

    print(
        "паспорт сохранён:",
        output,
    )


if __name__ == "__main__":
    main()
