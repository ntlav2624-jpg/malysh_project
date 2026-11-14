"""
Bridge from a completed ONE-Malysh thinking cycle to the isolated
development hypothesis exchange.

The bridge does not:

* run the thinking cycle;
* alter MindState;
* execute the proposed experiment;
* call an external reviewer automatically;
* grant decision authority;
* modify canonical source code.

It interprets an already completed cycle and produces an immutable
hypothesis candidate for external criticism and later experiment.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from malysh_system.development_hypotheses import (
    HypothesisRecord,
    build_hypothesis,
    create_review_packet,
    publish_hypothesis,
)


SCHEMA = "malysh.thinking-hypothesis-bridge.v1"
SUBJECT = "Malysh"


def _mapping(
    value: Any,
) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return deepcopy(dict(value))

    return {}


def _list(
    value: Any,
) -> list:
    if isinstance(value, list):
        return deepcopy(value)

    if value is None:
        return []

    return [deepcopy(value)]


def _find_snapshot(
    cycle: Mapping[str, Any],
) -> dict[str, Any]:
    for key in (
        "mind",
        "snapshot",
        "mind_snapshot",
    ):
        value = cycle.get(key)

        if isinstance(value, Mapping):
            return deepcopy(dict(value))

    return {}


def _find_joint_choice(
    cycle: Mapping[str, Any],
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    direct = cycle.get(
        "joint_choice"
    )

    if isinstance(direct, Mapping):
        return deepcopy(dict(direct))

    observations = _mapping(
        snapshot.get("observations")
    )

    reflections = _mapping(
        snapshot.get("reflections")
    )

    for source in (
        observations,
        reflections,
    ):
        for key in (
            "JointChoice",
            "joint_choice",
        ):
            value = source.get(key)

            if isinstance(value, Mapping):
                return deepcopy(dict(value))

    return {}


def _find_interlayer(
    cycle: Mapping[str, Any],
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    for key in (
        "interlayer",
        "interlayer_result",
        "interlayer_observers",
    ):
        value = cycle.get(key)

        if isinstance(value, Mapping):
            return deepcopy(dict(value))

    observations = _mapping(
        snapshot.get("observations")
    )

    for key in (
        "InterLayer",
        "InterLayerObservers",
        "interlayer",
    ):
        value = observations.get(key)

        if isinstance(value, Mapping):
            return deepcopy(dict(value))

    return {}


def _find_branches(
    cycle: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    joint_choice: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    candidates = _mapping(
        joint_choice.get("candidates")
    )

    main = (
        candidates.get("main")
        if isinstance(
            candidates.get("main"),
            Mapping,
        )
        else
        snapshot.get("main")
    )

    possible = (
        candidates.get("possible")
        if isinstance(
            candidates.get("possible"),
            Mapping,
        )
        else
        snapshot.get("possible")
    )

    negative = (
        cycle.get("negative")
        if isinstance(
            cycle.get("negative"),
            Mapping,
        )
        else
        snapshot.get("negative")
    )

    unresolved = (
        cycle.get("unresolved")
        if isinstance(
            cycle.get("unresolved"),
            Mapping,
        )
        else
        snapshot.get("unresolved")
    )

    return {
        "primary":
            _mapping(main)
            or
            {
                "status": "unavailable",
                "may_be_wrong": True,
            },

        "possible":
            _mapping(possible)
            or
            {
                "status": "possible",
                "revisable": True,
            },

        "negative":
            _mapping(negative)
            or
            {
                "status": "no_negative_result",
                "decision_authority": False,
            },

        "unresolved":
            _mapping(unresolved)
            or
            {
                "status": "unresolved",
                "questions": [
                    "The thinking cycle did not publish "
                    "an explicit unresolved branch."
                ],
            },
    }


def _organ_evidence(
    snapshot: Mapping[str, Any],
) -> list[dict[str, Any]]:
    observations = _mapping(
        snapshot.get("observations")
    )

    reflections = _mapping(
        snapshot.get("reflections")
    )

    evidence = []

    for channel, values in (
        ("observation", observations),
        ("reflection", reflections),
    ):
        for organ, value in sorted(
            values.items(),
            key=lambda item: str(item[0]),
        ):
            evidence.append(
                {
                    "channel": channel,
                    "organ": str(organ),
                    "value": deepcopy(value),
                }
            )

    return evidence


def _derive_claim(
    branches: Mapping[str, Any],
    joint_choice: Mapping[str, Any],
) -> str:
    primary = _mapping(
        branches.get("primary")
    )

    for key in (
        "claim",
        "conclusion",
        "result",
        "hypothesis",
        "selected",
    ):
        value = primary.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    deliberation = _mapping(
        joint_choice.get("deliberation")
    )

    state = deliberation.get(
        "state"
    )

    if isinstance(state, str) and state.strip():
        return (
            "The current thinking cycle produced "
            f"joint deliberation state {state.strip()}."
        )

    return (
        "The current internal observations may contain "
        "a reusable development pattern."
    )


def build_from_thinking_cycle(
    cycle_result: Mapping[str, Any],
    *,
    claim: str | None = None,
    hypothesis_id: str | None = None,
) -> tuple[HypothesisRecord, dict[str, Any]]:
    if not isinstance(
        cycle_result,
        Mapping,
    ):
        raise TypeError(
            "cycle_result must be a mapping"
        )

    cycle = deepcopy(
        dict(cycle_result)
    )

    snapshot = _find_snapshot(cycle)

    subject = (
        snapshot.get("subject")
        or
        cycle.get("subject")
    )

    if subject not in (
        None,
        SUBJECT,
    ):
        raise ValueError(
            "thinking cycle subject must be Malysh"
        )

    joint_choice = _find_joint_choice(
        cycle,
        snapshot,
    )

    interlayer = _find_interlayer(
        cycle,
        snapshot,
    )

    branches = _find_branches(
        cycle,
        snapshot,
        joint_choice,
    )

    evidence = _organ_evidence(
        snapshot
    )

    if interlayer:
        evidence.append(
            {
                "channel": "interlayer",
                "organ": "InterLayer",
                "value": interlayer,
            }
        )

    if joint_choice:
        evidence.append(
            {
                "channel": "deliberation",
                "organ": "JointChoice",
                "value": joint_choice,
            }
        )

    deliberation = _mapping(
        joint_choice.get("deliberation")
    )

    decision_state = (
        deliberation.get("state")
        or
        "unresolved"
    )

    record = build_hypothesis(
        hypothesis_id=hypothesis_id,

        claim=(
            claim.strip()
            if isinstance(claim, str)
            and claim.strip()
            else
            _derive_claim(
                branches,
                joint_choice,
            )
        ),

        rationale=[
            (
                "The hypothesis was derived from a completed "
                "ONE-Malysh thinking cycle."
            ),
            (
                "Primary, possible, negative and unresolved "
                "branches remain separate."
            ),
            (
                "Internal observations are evidence, not votes "
                "and not execution authority."
            ),
            (
                "Joint deliberation state is "
                f"{decision_state}."
            ),
        ],

        primary=branches["primary"],
        possible=branches["possible"],
        negative=branches["negative"],
        unresolved=branches["unresolved"],

        evidence=evidence,

        proposed_experiment={
            "type":
                "controlled_functional_comparison",

            "same_input":
                True,

            "compare": [
                "organ output",
                "downstream observation",
                "joint deliberation",
                "canonical state",
            ],

            "success_contract": {
                "hypothesis_effect_visible":
                    True,

                "canonical_state_preserved":
                    True,

                "decision_authority_preserved":
                    True,

                "automatic_execution":
                    False,
            },
        },

        invariants=[
            "subject remains Malysh",
            "canonical state remains unchanged",
            "primary branch remains preserved",
            "possible branch remains preserved",
            "negative results remain preserved",
            "unresolved questions remain explicit",
            "observations are not converted to votes",
            "no automatic experiment execution",
            "no automatic canonical-core modification",
            "external review is not final truth",
        ],

        provenance={
            "subject":
                SUBJECT,

            "origin":
                "completed_thinking_cycle",

            "bridge_schema":
                SCHEMA,

            "cycle_schema":
                cycle.get("schema"),

            "joint_deliberation_state":
                decision_state,

            "canonical_seen":
                deepcopy(
                    snapshot.get(
                        "canonical",
                        {},
                    )
                ),

            "independent_internal_hypothesis":
                True,
        },
    )

    bridge_result = {
        "schema":
            SCHEMA,

        "status":
            "hypothesis_built",

        "hypothesis_id":
            record.hypothesis_id,

        "evidence_count":
            len(evidence),

        "branches_preserved":
            list(branches),

        "joint_deliberation_state":
            decision_state,

        "canonical_seen":
            deepcopy(
                snapshot.get(
                    "canonical",
                    {},
                )
            ),

        "decision_authority":
            False,

        "state_commit":
            False,

        "automatic_execution":
            False,

        "canonical_core_modified":
            False,
    }

    return record, bridge_result


def publish_from_thinking_cycle(
    cycle_result: Mapping[str, Any],
    storage_root: str | Path,
    *,
    claim: str | None = None,
    hypothesis_id: str | None = None,
    review_packet_path: str | Path | None = None,
) -> dict[str, Any]:
    source_before = deepcopy(
        dict(cycle_result)
    )

    record, bridge = build_from_thinking_cycle(
        cycle_result,
        claim=claim,
        hypothesis_id=hypothesis_id,
    )

    publication = publish_hypothesis(
        record,
        storage_root,
    )

    packet = create_review_packet(
        record.to_dict()
    )

    packet_path = None

    if review_packet_path is not None:
        target = Path(
            review_packet_path
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            packet,
            encoding="utf-8",
        )

        packet_path = str(target)

    if source_before != dict(cycle_result):
        raise RuntimeError(
            "hypothesis bridge modified "
            "the thinking-cycle result"
        )

    return {
        "schema":
            "malysh.thinking-hypothesis-publication.v1",

        "status":
            "published",

        "bridge":
            bridge,

        "publication":
            publication,

        "hypothesis":
            record.to_dict(),

        "review_packet":
            packet,

        "review_packet_path":
            packet_path,

        "source_unchanged":
            True,

        "decision_authority":
            False,

        "state_commit":
            False,

        "automatic_execution":
            False,

        "canonical_core_modified":
            False,
    }
