#!/usr/bin/env python3

from pathlib import Path
import argparse
import json

from malysh_system.thinking_hypothesis_bridge import (
    publish_from_thinking_cycle,
)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Publish a completed ONE-Malysh thinking cycle "
            "as an isolated development hypothesis."
        )
    )

    parser.add_argument(
        "--cycle-result",
        required=True,
    )

    parser.add_argument(
        "--storage",
        default=(
            "runtime/development_hypotheses"
        ),
    )

    parser.add_argument(
        "--review-packet",
    )

    parser.add_argument(
        "--claim",
    )

    parser.add_argument(
        "--hypothesis-id",
    )

    args = parser.parse_args()

    source = json.loads(
        Path(
            args.cycle_result
        ).read_text(
            encoding="utf-8"
        )
    )

    result = publish_from_thinking_cycle(
        source,
        args.storage,
        claim=args.claim,
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
        )
    )


if __name__ == "__main__":
    main()
