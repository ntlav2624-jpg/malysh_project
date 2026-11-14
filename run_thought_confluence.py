#!/usr/bin/env python3

from pathlib import Path
import argparse
import json

from malysh_system.thought_confluence import (
    publish_confluence,
)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Resolve Malysh's selected real thought "
            "and prepare a Malysh-Copilot confluence."
        )
    )

    parser.add_argument(
        "--cycle-result",
        required=True,
    )

    parser.add_argument(
        "--storage",
        required=True,
    )

    parser.add_argument(
        "--review-packet",
        required=True,
    )

    parser.add_argument(
        "--hypothesis-id",
    )

    args = parser.parse_args()

    cycle = json.loads(
        Path(
            args.cycle_result
        ).read_text(
            encoding="utf-8"
        )
    )

    result = publish_confluence(
        cycle,
        args.storage,
        hypothesis_id=
            args.hypothesis_id,
        review_packet_path=
            args.review_packet,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
