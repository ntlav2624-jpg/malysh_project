#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

from malysh_system.development_hypotheses import (
    build_external_review,
    build_hypothesis,
    create_review_packet,
    inspect_storage,
    publish_external_review,
    publish_hypothesis,
)


DEFAULT_STORAGE = Path(
    "runtime/development_hypotheses"
)


def load_json(path: str) -> dict:
    return json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )


def command_propose(args):
    source = load_json(args.input)

    record = build_hypothesis(
        claim=source["claim"],
        rationale=source["rationale"],
        primary=source["primary"],
        possible=source["possible"],
        negative=source["negative"],
        unresolved=source["unresolved"],
        evidence=source["evidence"],
        proposed_experiment=
            source["proposed_experiment"],
        invariants=source["invariants"],
        provenance=source["provenance"],
        hypothesis_id=source.get(
            "hypothesis_id"
        ),
    )

    result = publish_hypothesis(
        record,
        args.storage,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )


def command_export(args):
    hypothesis = load_json(args.hypothesis)

    packet = create_review_packet(
        hypothesis
    )

    if args.output:
        Path(args.output).write_text(
            packet,
            encoding="utf-8",
        )

        print(args.output)
    else:
        print(packet)


def command_review(args):
    hypothesis = load_json(args.hypothesis)
    source = load_json(args.input)

    review = build_external_review(
        hypothesis=hypothesis,
        reviewer=source["reviewer"],
        assessment=source["assessment"],
        reasoning=source["reasoning"],
        supported_points=
            source["supported_points"],
        challenged_points=
            source["challenged_points"],
        required_tests=
            source["required_tests"],
        reviewer_hypothesis=
            source["reviewer_hypothesis"],
    )

    result = publish_external_review(
        review,
        args.storage,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )


def command_inspect(args):
    print(
        json.dumps(
            inspect_storage(
                args.storage
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


def parser():
    root = argparse.ArgumentParser(
        description=(
            "Malysh hypothesis exchange: "
            "Malysh proposes, Copilot reviews, "
            "experiment decides."
        )
    )

    root.add_argument(
        "--storage",
        default=str(DEFAULT_STORAGE),
    )

    commands = root.add_subparsers(
        required=True,
    )

    propose = commands.add_parser(
        "propose"
    )

    propose.add_argument(
        "--input",
        required=True,
    )

    propose.set_defaults(
        handler=command_propose
    )

    export = commands.add_parser(
        "export"
    )

    export.add_argument(
        "--hypothesis",
        required=True,
    )

    export.add_argument(
        "--output",
    )

    export.set_defaults(
        handler=command_export
    )

    review = commands.add_parser(
        "review"
    )

    review.add_argument(
        "--hypothesis",
        required=True,
    )

    review.add_argument(
        "--input",
        required=True,
    )

    review.set_defaults(
        handler=command_review
    )

    inspect = commands.add_parser(
        "inspect"
    )

    inspect.set_defaults(
        handler=command_inspect
    )

    return root


def main():
    args = parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
