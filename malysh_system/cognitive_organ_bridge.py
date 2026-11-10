"""
Bridge between the existing Cognitive Flow Controller and the real,
already-published organs of ONE Malysh.

This module does not create a replacement cognitive architecture.

Input provenance:
    MindState.observations
    MindState.reflections

Output:
    CognitiveFlow observation
    CognitiveFlow reflection

The bridge:
    uses attach_cognitive_flow()
    proves get_cognitive_flow() returns the same controller
    imports only real published organ outputs
    does not execute organs
    does not overwrite canonical state
    does not modify Human Layer branches
    does not authorize transactions
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, is_dataclass
from enum import Enum
import inspect
from typing import Any, Mapping

from malysh_system.cognitive_flow import (
    BranchKind,
    CognitiveFlowController,
    ThoughtKind,
)
from malysh_system.cognitive_flow_integration import (
    attach_cognitive_flow,
    get_cognitive_flow,
)
from malysh_system.protocols import OrganResult


ORGAN = "CognitiveFlow"

SCHEMA = "malysh.cognitive-organ-bridge.v1"


def authority_flags() -> dict[str, bool]:
    return {
        "decision_authority":
            False,

        "automatic_execution":
            False,

        "external_control":
            False,

        "organ_execution":
            False,

        "state_write":
            False,

        "state_commit":
            False,

        "canonical_write":
            False,

        "main_answer_write":
            False,

        "possible_branch_write":
            False,

        "transaction_authorized":
            False,

        "winner_selection":
            False,
    }


def _shape(
    value: Any,
) -> dict[str, Any]:
    """
    Produce deterministic metadata without inventing organ semantics.
    """

    if value is None:
        return {
            "type": "none",
            "size": 0,
            "keys": [],
        }

    if isinstance(
        value,
        Mapping,
    ):
        return {
            "type": "mapping",
            "size": len(value),
            "keys": sorted(
                str(key)
                for key in value
            ),
        }

    if isinstance(
        value,
        (list, tuple),
    ):
        return {
            "type": type(value).__name__,
            "size": len(value),
            "keys": [],
        }

    return {
        "type": type(value).__name__,
        "size": 1,
        "keys": [],
    }


def _state_id(
    organ_name: str,
) -> str:
    normalized = "".join(
        character.lower()
        if character.isalnum()
        else "_"
        for character in organ_name
    ).strip("_")

    return (
        "organ_observation_"
        +
        normalized
    )


def _build_add_state_arguments(
    controller: CognitiveFlowController,
    state_id: str,
    organ_name: str,
    organ_value: Any,
) -> tuple[list[Any], dict[str, Any]]:
    """
    Adapt to the installed add_state() signature by parameter meaning.

    Unknown required parameters are rejected rather than guessed.
    """

    signature = inspect.signature(
        controller.add_state
    )

    payload = {
        "subject":
            "Malysh",

        "source":
            "MindState.observations",

        "organ":
            organ_name,

        "shape":
            _shape(organ_value),

        "value":
            deepcopy(organ_value),

        "execution_authorized":
            False,

        "canonical_claim":
            False,
    }

    semantic_values = {
        "state_id":
            state_id,

        "id":
            state_id,

        "identifier":
            state_id,

        "name":
            state_id,

        "kind":
            ThoughtKind.OBSERVATION,

        "thought_kind":
            ThoughtKind.OBSERVATION,

        "state_kind":
            ThoughtKind.OBSERVATION,

        "payload":
            payload,

        "content":
            payload,

        "value":
            payload,

        "data":
            payload,

        "metadata":
            payload,

        "sign":
            1,

        "confidence":
            1.0,

        "evidence":
            (
                "MindState.observations:"
                +
                organ_name,
            ),

        "priority":
            1.0,

        "active":
            False,

        "source":
            organ_name,

        "label":
            organ_name,

        "title":
            organ_name,
    }

    positional = []
    keywords = {}

    for parameter in (
        signature.parameters.values()
    ):
        if parameter.name == "self":
            continue

        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        if parameter.name in semantic_values:
            value = semantic_values[
                parameter.name
            ]

        elif (
            parameter.default
            is not
            inspect.Parameter.empty
        ):
            continue

        else:
            raise TypeError(
                "unsupported required add_state parameter: "
                + parameter.name
            )

        if parameter.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            positional.append(
                value
            )
        else:
            keywords[
                parameter.name
            ] = value

    return (
        positional,
        keywords,
    )


def _add_observation_state(
    controller: CognitiveFlowController,
    state_id: str,
    organ_name: str,
    organ_value: Any,
) -> None:
    """
    Add one real organ observation unless already represented.
    """

    existing = controller.states

    if state_id in existing:
        return

    positional, keywords = (
        _build_add_state_arguments(
            controller,
            state_id,
            organ_name,
            organ_value,
        )
    )

    controller.add_state(
        *positional,
        **keywords,
    )


def _cycle_to_dict(
    value: Any,
) -> Any:
    """
    Convert Cognitive Flow values into persistence-safe containers.

    The Mind persistence codec intentionally supports ordinary scalar
    values and Python containers. Cognitive Flow dataclasses and Enum
    instances are therefore normalized here, at the organ boundary,
    rather than teaching persistence about one specific organ.

    Tuple remains tuple so the existing lossless codec can preserve
    tuple identity.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (
            bool,
            int,
            float,
            str,
        ),
    ):
        return value

    if isinstance(
        value,
        Enum,
    ):
        return _cycle_to_dict(
            value.value
        )

    if is_dataclass(value):
        return {
            field.name:
                _cycle_to_dict(
                    getattr(
                        value,
                        field.name,
                    )
                )
            for field in fields(value)
        }

    if isinstance(
        value,
        Mapping,
    ):
        return {
            _cycle_to_dict(key):
                _cycle_to_dict(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        list,
    ):
        return [
            _cycle_to_dict(item)
            for item in value
        ]

    if isinstance(
        value,
        tuple,
    ):
        return tuple(
            _cycle_to_dict(item)
            for item in value
        )

    if hasattr(value, "to_dict"):
        converted = value.to_dict()

        if converted is value:
            raise TypeError(
                "to_dict returned the original object: "
                + type(value).__name__
            )

        return _cycle_to_dict(
            converted
        )

    if hasattr(value, "__dict__"):
        return {
            str(key):
                _cycle_to_dict(item)
            for key, item
            in vars(value).items()
            if not str(key).startswith("_")
        }

    raise TypeError(
        "unsupported Cognitive Flow value: "
        + type(value).__name__
    )


def compute_cognitive_organ_bridge(
    mind: Any,
) -> tuple[
    CognitiveFlowController,
    dict[str, Any],
]:
    """
    Feed real published organ outputs into the existing controller.
    """

    before = mind.snapshot()

    observations = deepcopy(
        before["observations"]
    )

    if not observations:
        raise ValueError(
            "Cognitive Flow requires real organ observations"
        )

    attached = attach_cognitive_flow(
        mind
    )

    controller = get_cognitive_flow(
        mind
    )

    if not isinstance(
        controller,
        CognitiveFlowController,
    ):
        raise TypeError(
            "attached object is not CognitiveFlowController"
        )

    if (
        attached is not None
        and
        attached is not controller
    ):
        raise RuntimeError(
            "attach/get controller identity mismatch"
        )

    if (
        get_cognitive_flow(mind)
        is not controller
    ):
        raise RuntimeError(
            "second Cognitive Flow controller detected"
        )

    imported_state_ids = []

    for organ_name, organ_value in sorted(
        observations.items()
    ):
        if organ_name == ORGAN:
            continue

        state_id = _state_id(
            organ_name
        )

        _add_observation_state(
            controller,
            state_id,
            organ_name,
            organ_value,
        )

        imported_state_ids.append(
            state_id
        )

    if not imported_state_ids:
        raise RuntimeError(
            "no real organ states imported"
        )

    controller.activate(
        imported_state_ids
    )

    cycle_result = (
        controller.cycle_once()
    )

    snapshot = (
        controller.export_snapshot()
    )

    if not isinstance(
        snapshot,
        Mapping,
    ):
        raise TypeError(
            "Cognitive Flow snapshot must be a mapping"
        )

    def branch_name(
        value: Any,
    ) -> str | None:
        """
        Resolve a branch identifier from the actual public object.

        No missing branch is fabricated. Unknown structures are
        rejected by the branch-set invariant below.
        """

        if value is None:
            return None

        if hasattr(value, "value"):
            return str(value.value)

        if isinstance(value, str):
            return value

        for attribute in (
            "branch",
            "kind",
            "name",
            "branch_kind",
        ):
            candidate = getattr(
                value,
                attribute,
                None,
            )

            if candidate is not None:
                return branch_name(
                    candidate
                )

        return None

    def add_branch(
        name_value: Any,
        branch_value: Any,
    ) -> None:
        name = branch_name(
            name_value
        )

        if name is None:
            name = branch_name(
                branch_value
            )

        if name is None:
            return

        branches[name] = (
            _cycle_to_dict(
                branch_value
            )
        )

    branches: dict[str, Any] = {}

    raw_branches = getattr(
        cycle_result,
        "branches",
        None,
    )

    if isinstance(
        raw_branches,
        Mapping,
    ):
        for name, value in (
            raw_branches.items()
        ):
            add_branch(
                name,
                value,
            )

    elif isinstance(
        raw_branches,
        (list, tuple),
    ):
        for item in raw_branches:
            if (
                isinstance(item, tuple)
                and
                len(item) == 2
            ):
                add_branch(
                    item[0],
                    item[1],
                )
            else:
                add_branch(
                    None,
                    item,
                )

    elif raw_branches is not None:
        add_branch(
            None,
            raw_branches,
        )

    # Some CycleResult contracts expose each branch as a separate
    # public field rather than through one mapping. We read only
    # fields that actually exist on the returned object.
    for branch_kind in BranchKind:
        branch_value = None

        for attribute in (
            branch_kind.value,
            branch_kind.value + "_branch",
        ):
            if hasattr(
                cycle_result,
                attribute,
            ):
                branch_value = getattr(
                    cycle_result,
                    attribute,
                )
                break

        if branch_value is not None:
            add_branch(
                branch_kind,
                branch_value,
            )

    expected_branches = {
        value.value
        for value in BranchKind
    }

    branch_names = set(
        branches
    )

    result = {
        "organ":
            ORGAN,

        "schema":
            SCHEMA,

        "subject":
            before["subject"],

        "controller_identity":
            id(controller),

        "second_controller_created":
            False,

        "source":
            "real_mind_state_organs",

        "imported_organs":
            sorted(
                name
                for name in observations
                if name != ORGAN
            ),

        "imported_state_ids":
            sorted(
                imported_state_ids
            ),

        "imported_state_count":
            len(imported_state_ids),

        "cycle_result":
            _cycle_to_dict(
                cycle_result
            ),

        "branches":
            branches,

        "branch_names":
            sorted(branch_names),

        "expected_branch_names":
            sorted(expected_branches),

        "cognitive_snapshot":
            deepcopy(
                dict(snapshot)
            ),

        "canonical_before":
            deepcopy(
                before["canonical"]
            ),

        **authority_flags(),
    }

    result["invariants"] = {
        "one_subject":
            result["subject"]
            ==
            "Malysh",

        "real_organ_source":
            result["source"]
            ==
            "real_mind_state_organs",

        "real_organs_imported":
            result[
                "imported_state_count"
            ]
            >
            0,

        "controller_identity_stable":
            (
                get_cognitive_flow(mind)
                is
                controller
            ),

        "no_second_controller":
            (
                result[
                    "second_controller_created"
                ]
                is False
            ),

        "controller_snapshot_present":
            bool(
                result[
                    "cognitive_snapshot"
                ]
            ),

        "branch_set_preserved":
            expected_branches.issubset(
                branch_names
            ),

        "no_decision_authority":
            (
                result[
                    "decision_authority"
                ]
                is False
            ),

        "no_organ_execution":
            (
                result["organ_execution"]
                is False
            ),

        "no_external_control":
            (
                result["external_control"]
                is False
            ),

        "no_state_commit":
            (
                result["state_commit"]
                is False
            ),

        "no_canonical_write":
            (
                result["canonical_write"]
                is False
            ),

        "no_transaction":
            (
                result[
                    "transaction_authorized"
                ]
                is False
            ),

        "no_winner_selection":
            (
                result["winner_selection"]
                is False
            ),
    }

    result["invariant_ok"] = all(
        result["invariants"].values()
    )

    return (
        controller,
        result,
    )


def integrate_cognitive_organ_bridge(
    mind: Any,
) -> OrganResult:
    """
    Publish the existing controller's result as an internal organ.
    """

    before = mind.snapshot()

    protected = {
        key: deepcopy(before[key])
        for key in (
            "subject",
            "canonical",
            "experience",
            "human",
            "main",
            "possible",
        )
    }

    try:
        controller, result = (
            compute_cognitive_organ_bridge(
                mind
            )
        )

        if not result["invariant_ok"]:
            failed = [
                name
                for name, passed
                in result["invariants"].items()
                if passed is not True
            ]

            raise RuntimeError(
                "Cognitive organ bridge invariants failed: "
                + ", ".join(failed)
            )

        mind.observe(
            ORGAN,
            result,
        )

        mind.reflect(
            ORGAN,
            {
                "schema":
                    result["schema"],

                "source":
                    result["source"],

                "imported_organs":
                    deepcopy(
                        result[
                            "imported_organs"
                        ]
                    ),

                "branch_names":
                    deepcopy(
                        result[
                            "branch_names"
                        ]
                    ),

                "invariant_ok":
                    result["invariant_ok"],

                **authority_flags(),
            },
        )

        after = mind.snapshot()

        for key, expected in (
            protected.items()
        ):
            if after[key] != expected:
                raise RuntimeError(
                    "Cognitive Flow mutated protected field: "
                    + key
                )

        if not mind.invariant():
            raise RuntimeError(
                "MindState invariant failed after Cognitive Flow"
            )

        if (
            get_cognitive_flow(mind)
            is not
            controller
        ):
            raise RuntimeError(
                "controller identity changed after publication"
            )

        return OrganResult(
            organ=ORGAN,
            status="ok",
            data=result,
        )

    except Exception as error:
        return OrganResult(
            organ=ORGAN,
            status="error",
            data={},
            error=(
                type(error).__name__
                + ": "
                + str(error)
            ),
        )
