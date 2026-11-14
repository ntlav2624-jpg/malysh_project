"""
Thought confluence for ONE Malysh.

The confluence resolves the thought selected by CognitiveFlow,
preserves primary/possible/negative/unresolved, prepares an
external-review packet and proposes a shared experiment.

It does not:

* choose a winner;
* convert evidence into votes;
* execute the experiment;
* grant authority to Malysh or Copilot;
* modify the canonical core.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterator
import json

from malysh_system.development_hypotheses import (
    HypothesisRecord,
    build_hypothesis,
    create_review_packet,
    publish_hypothesis,
)


SCHEMA = "malysh.thought-confluence.v1"
SUBJECT = "Malysh"

STATE_ID_TO_ORGAN = {
    "organ_observation_fullreflections":
        "FullReflections",

    "organ_observation_humanlayer":
        "HumanLayer",

    "organ_observation_kmbp":
        "KMBP",

    "organ_observation_o3":
        "O3",

    "organ_observation_o4":
        "O4",

    "organ_observation_o5":
        "O5",

    "organ_observation_omni":
        "Omni",

    "organ_observation_swarm":
        "Swarm",
}


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return deepcopy(dict(value))

    return {}


def _as_branch(
    value: Any,
    *,
    default_status: str,
) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return deepcopy(dict(value))

    if isinstance(value, list):
        return {
            "status": default_status,
            "items": deepcopy(value),
        }

    if value is None:
        return {
            "status": default_status,
        }

    return {
        "status": default_status,
        "value": deepcopy(value),
    }


def _walk(
    value: Any,
    path: str = "$",
) -> Iterator[tuple[str, Any]]:
    yield path, value

    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(
                child,
                f"{path}.{key}",
            )

    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(
                child,
                f"{path}[{index}]",
            )


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


def _find_named_mapping(
    value: Any,
    name: str,
) -> tuple[str | None, dict[str, Any]]:
    for path, node in _walk(value):
        if not isinstance(node, Mapping):
            continue

        if name in node:
            candidate = node[name]

            if isinstance(candidate, Mapping):
                return (
                    f"{path}.{name}",
                    deepcopy(dict(candidate)),
                )

        if node.get("organ") == name:
            return (
                path,
                deepcopy(dict(node)),
            )

    return None, {}


def _find_cognitive_flow(
    cycle: Mapping[str, Any],
) -> tuple[str | None, dict[str, Any]]:
    for path, node in _walk(cycle):
        if not isinstance(node, Mapping):
            continue

        if (
            node.get("organ") == "CognitiveFlow"
            or
            node.get("schema")
            ==
            "malysh.cognitive-organ-bridge.v1"
        ):
            return (
                path,
                deepcopy(dict(node)),
            )

    return None, {}


def _resolve_selected_primary(
    cycle: Mapping[str, Any],
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    flow_path, flow = _find_cognitive_flow(
        cycle
    )

    branches = _mapping(
        flow.get("branches")
    )

    primary_branch = _mapping(
        branches.get("primary")
    )

    selected_id = primary_branch.get(
        "selected_id"
    )

    score = primary_branch.get(
        "score"
    )

    selected_organ = (
        STATE_ID_TO_ORGAN.get(
            str(selected_id)
        )
        if selected_id is not None
        else None
    )

    observations = _mapping(
        snapshot.get("observations")
    )

    reflections = _mapping(
        snapshot.get("reflections")
    )

    payload = {}
    source_channel = None
    source_path = None

    if (
        selected_organ
        and
        isinstance(
            observations.get(selected_organ),
            Mapping,
        )
    ):
        payload = deepcopy(
            dict(
                observations[selected_organ]
            )
        )

        source_channel = "observation"
        source_path = (
            "$.mind.observations."
            + selected_organ
        )

    elif (
        selected_organ
        and
        isinstance(
            reflections.get(selected_organ),
            Mapping,
        )
    ):
        payload = deepcopy(
            dict(
                reflections[selected_organ]
            )
        )

        source_channel = "reflection"
        source_path = (
            "$.mind.reflections."
            + selected_organ
        )

    elif selected_organ:
        source_path, payload = (
            _find_named_mapping(
                cycle,
                selected_organ,
            )
        )

        if payload:
            source_channel = "recursive"

    return {
        "flow_path":
            flow_path,

        "selected_id":
            selected_id,

        "selected_organ":
            selected_organ,

        "score":
            score,

        "source_channel":
            source_channel,

        "source_path":
            source_path,

        "payload":
            payload,

        "resolved":
            bool(
                selected_organ
                and
                payload
            ),
    }


def _find_first_key(
    value: Any,
    keys: tuple[str, ...],
) -> tuple[str | None, Any]:
    for path, node in _walk(value):
        if not isinstance(node, Mapping):
            continue

        for key in keys:
            if key in node:
                candidate = node[key]

                if candidate not in (
                    None,
                    {},
                    [],
                    "",
                ):
                    return (
                        f"{path}.{key}",
                        deepcopy(candidate),
                    )

    return None, None


def _extract_full_reflection_branches(
    full: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    primary_path, primary = _find_first_key(
        full,
        (
            "voice_a",
            "main",
            "primary",
            "as_now",
        ),
    )

    possible_path, possible = _find_first_key(
        full,
        (
            "voice_b",
            "possible",
            "alternative",
        ),
    )

    negative_path, negative = _find_first_key(
        full,
        (
            "negative",
            "contradictions",
        ),
    )

    unresolved_path, unresolved = _find_first_key(
        full,
        (
            "unresolved",
            "tests_needed",
        ),
    )

    return {
        "primary": {
            "source_path":
                primary_path,

            "value":
                _as_branch(
                    primary,
                    default_status=
                        "selected_primary",
                ),
        },

        "possible": {
            "source_path":
                possible_path,

            "value":
                _as_branch(
                    possible,
                    default_status=
                        "possible",
                ),
        },

        "negative": {
            "source_path":
                negative_path,

            "value":
                _as_branch(
                    negative,
                    default_status=
                        "no_negative_result",
                ),
        },

        "unresolved": {
            "source_path":
                unresolved_path,

            "value":
                _as_branch(
                    unresolved,
                    default_status=
                        "unresolved",
                ),
        },
    }


def extract_real_thought(
    cycle_result: Mapping[str, Any],
) -> dict[str, Any]:
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

    if subject != SUBJECT:
        raise ValueError(
            "cycle subject must be Malysh"
        )

    selection = _resolve_selected_primary(
        cycle,
        snapshot,
    )

    selected_payload = _mapping(
        selection.get("payload")
    )

    reflection_branches = (
        _extract_full_reflection_branches(
            selected_payload
        )
    )

    snapshot_main = snapshot.get("main")
    snapshot_possible = snapshot.get(
        "possible"
    )
    snapshot_negative = snapshot.get(
        "negative"
    )
    snapshot_unresolved = snapshot.get(
        "unresolved"
    )

    primary = (
        _as_branch(
            snapshot_main,
            default_status="primary",
        )
        if snapshot_main not in (
            None,
            {},
            [],
        )
        else
        reflection_branches[
            "primary"
        ][
            "value"
        ]
    )

    possible = (
        _as_branch(
            snapshot_possible,
            default_status="possible",
        )
        if snapshot_possible not in (
            None,
            {},
            [],
        )
        else
        reflection_branches[
            "possible"
        ][
            "value"
        ]
    )

    negative = (
        _as_branch(
            snapshot_negative,
            default_status="negative",
        )
        if snapshot_negative not in (
            None,
            {},
            [],
        )
        else
        reflection_branches[
            "negative"
        ][
            "value"
        ]
    )

    unresolved = (
        _as_branch(
            snapshot_unresolved,
            default_status="unresolved",
        )
        if snapshot_unresolved not in (
            None,
            {},
            [],
        )
        else
        reflection_branches[
            "unresolved"
        ][
            "value"
        ]
    )

    if selection["resolved"]:
        primary = {
            "status":
                "selected_primary",

            "selected_id":
                selection["selected_id"],

            "selected_organ":
                selection[
                    "selected_organ"
                ],

            "selection_score":
                selection["score"],

            "source_channel":
                selection[
                    "source_channel"
                ],

            "source_path":
                selection["source_path"],

            "may_be_wrong":
                True,

            "result":
                primary,

            "selected_payload":
                selected_payload,
        }

    if not possible:
        possible = {
            "status":
                "possible",

            "revisable":
                True,
        }

    if not negative:
        negative = {
            "status":
                "no_negative_result",

            "decision_authority":
                False,
        }

    if not unresolved:
        unresolved = {
            "status":
                "unresolved",

            "questions": [
                "No explicit unresolved branch "
                "was published."
            ],
        }

    _, human_layer = _find_named_mapping(
        cycle,
        "HumanLayer",
    )

    _, joint_choice = _find_named_mapping(
        cycle,
        "JointChoice",
    )

    return {
        "schema":
            SCHEMA,

        "subject":
            SUBJECT,

        "selection":
            selection,

        "branches": {
            "primary":
                primary,

            "possible":
                possible,

            "negative":
                negative,

            "unresolved":
                unresolved,
        },

        "human_layer":
            human_layer,

        "joint_choice":
            joint_choice,

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


def _derive_claim(
    thought: Mapping[str, Any],
) -> str:
    selection = _mapping(
        thought.get("selection")
    )

    organ = selection.get(
        "selected_organ"
    )

    if organ:
        return (
            "CognitiveFlow selected "
            f"{organ} as primary evidence; "
            "its development pattern should be "
            "tested by controlled comparison."
        )

    return (
        "The current thought contains candidate "
        "development evidence requiring functional testing."
    )


def build_confluence_hypothesis(
    cycle_result: Mapping[str, Any],
    *,
    hypothesis_id: str | None = None,
) -> tuple[
    HypothesisRecord,
    dict[str, Any],
]:
    source_before = deepcopy(
        dict(cycle_result)
    )

    thought = extract_real_thought(
        cycle_result
    )

    branches = _mapping(
        thought.get("branches")
    )

    selection = _mapping(
        thought.get("selection")
    )

    evidence = [
        {
            "channel":
                "cognitive_selection",

            "organ":
                "CognitiveFlow",

            "selected_id":
                selection.get(
                    "selected_id"
                ),

            "selected_organ":
                selection.get(
                    "selected_organ"
                ),

            "score":
                selection.get("score"),

            "source_path":
                selection.get(
                    "source_path"
                ),

            "resolved":
                selection.get(
                    "resolved"
                ),
        },
        {
            "channel":
                "selected_primary_payload",

            "organ":
                (
                    selection.get(
                        "selected_organ"
                    )
                    or
                    "unresolved"
                ),

            "value":
                deepcopy(
                    selection.get(
                        "payload",
                        {},
                    )
                ),
        },
        {
            "channel":
                "human_layer",

            "organ":
                "HumanLayer",

            "value":
                deepcopy(
                    thought.get(
                        "human_layer",
                        {},
                    )
                ),
        },
        {
            "channel":
                "joint_choice",

            "organ":
                "JointChoice",

            "value":
                deepcopy(
                    thought.get(
                        "joint_choice",
                        {},
                    )
                ),
        },
    ]

    record = build_hypothesis(
        hypothesis_id=hypothesis_id,

        claim=_derive_claim(thought),

        rationale=[
            (
                "The hypothesis was extracted from "
                "a completed real thinking cycle."
            ),
            (
                "CognitiveFlow selected a concrete "
                "internal organ as primary evidence."
            ),
            (
                "The selected result may be wrong "
                "and remains subject to experiment."
            ),
            (
                "Malysh and Copilot meet through "
                "a non-authoritative bridge."
            ),
        ],

        primary=_mapping(
            branches.get("primary")
        ),

        possible=_mapping(
            branches.get("possible")
        ),

        negative=_mapping(
            branches.get("negative")
        ),

        unresolved=_mapping(
            branches.get("unresolved")
        ),

        evidence=evidence,

        proposed_experiment={
            "type":
                "malysh_copilot_controlled_confluence",

            "same_input":
                True,

            "malysh_position":
                "preserved",

            "copilot_position":
                "independent_external_hypothesis",

            "compare": [
                "Malysh prediction",
                "Copilot prediction",
                "organ output",
                "downstream observation",
                "joint deliberation",
                "canonical state",
            ],

            "outcomes": {
                "supports_malysh":
                    "observed result matches "
                    "Malysh prediction",

                "supports_copilot":
                    "observed result matches "
                    "Copilot prediction",

                "supports_both":
                    "shared prediction is observed",

                "supports_neither":
                    "both hypotheses are revised",
            },

            "winner_selection":
                False,

            "result_becomes_experience":
                True,

            "automatic_execution":
                False,
        },

        invariants=[
            "subject remains Malysh",
            "selected primary evidence remains preserved",
            "possible branch remains revisable",
            "negative result remains explicit",
            "unresolved questions remain explicit",
            "Copilot review is not final truth",
            "evidence is not converted to votes",
            "no winner is selected by the bridge",
            "no automatic experiment execution",
            "no automatic canonical-core modification",
        ],

        provenance={
            "subject":
                SUBJECT,

            "origin":
                "real_thinking_cycle_confluence",

            "confluence_schema":
                SCHEMA,

            "selected_id":
                selection.get(
                    "selected_id"
                ),

            "selected_organ":
                selection.get(
                    "selected_organ"
                ),

            "canonical_seen":
                deepcopy(
                    thought.get(
                        "canonical_seen",
                        {},
                    )
                ),

            "independent_malysh_position":
                True,

            "external_reviewer":
                "Microsoft 365 Copilot",
        },
    )

    if source_before != dict(
        cycle_result
    ):
        raise RuntimeError(
            "confluence modified cycle input"
        )

    return record, thought


def publish_confluence(
    cycle_result: Mapping[str, Any],
    storage_root: str | Path,
    *,
    hypothesis_id: str | None = None,
    review_packet_path: str | Path | None = None,
) -> dict[str, Any]:
    record, thought = (
        build_confluence_hypothesis(
            cycle_result,
            hypothesis_id=
                hypothesis_id,
        )
    )

    publication = publish_hypothesis(
        record,
        storage_root,
    )

    packet = create_review_packet(
        record.to_dict()
    )

    target_path = None

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

        target_path = str(target)

    return {
        "schema":
            "malysh.thought-confluence-publication.v1",

        "status":
            "published",

        "thought":
            thought,

        "hypothesis":
            record.to_dict(),

        "publication":
            publication,

        "review_packet":
            packet,

        "review_packet_path":
            target_path,

        "malysh_position_preserved":
            True,

        "copilot_position":
            "pending_external_review",

        "winner_selected":
            False,

        "experiment_decides":
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
