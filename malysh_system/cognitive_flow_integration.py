from __future__ import annotations

from typing import Any

from malysh_system.cognitive_flow import (
    CognitiveFlowController,
    create_default_controller,
)


ATTRIBUTE = "cognitive_flow"


def attach_cognitive_flow(
    mind: Any,
    *,
    controller=None,
    replace=False,
):
    existing = getattr(
        mind,
        ATTRIBUTE,
        None,
    )

    if existing is not None and not replace:
        if not isinstance(
            existing,
            CognitiveFlowController,
        ):
            raise TypeError(
                "Existing cognitive_flow "
                "has incompatible type"
            )

        return existing

    controller = (
        controller
        if controller is not None
        else create_default_controller()
    )

    setattr(
        mind,
        ATTRIBUTE,
        controller,
    )

    organs = getattr(
        mind,
        "internal_organs",
        None,
    )

    if isinstance(organs, dict):
        organs.setdefault(
            ATTRIBUTE,
            controller,
        )

    registry = getattr(
        mind,
        "organ_registry",
        None,
    )

    if isinstance(registry, dict):
        registry.setdefault(
            ATTRIBUTE,
            {
                "instance": controller,
                "role": (
                    "thought-flow coordination"
                ),
                "subject_count": 1,
            },
        )

    return controller


def get_cognitive_flow(
    mind: Any,
):
    value = getattr(
        mind,
        ATTRIBUTE,
        None,
    )

    if not isinstance(
        value,
        CognitiveFlowController,
    ):
        raise RuntimeError(
            "cognitive flow not attached"
        )

    return value
