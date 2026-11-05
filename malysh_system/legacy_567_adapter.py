from __future__ import annotations

import importlib.util
import math
import sys

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any


ROOT = Path(__file__).resolve().parent.parent

ENGINE_PATH = (
    ROOT
    / "malysh_cuneiform_engine.py"
)


GAP_MARKERS = {
    "x",
    "xx",
    "...",
    "[x]",
    "[...]",
}


def load_567_module():
    """
    Load the existing historical implementation.

    The adapter does not rewrite or replace the legacy engine.
    """

    if not ENGINE_PATH.exists():
        raise FileNotFoundError(
            f"567 engine not found: {ENGINE_PATH}"
        )

    module_name = "malysh_legacy_567_engine"

    spec = importlib.util.spec_from_file_location(
        module_name,
        ENGINE_PATH,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Cannot load 567 engine from {ENGINE_PATH}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[module_name] = module

    spec.loader.exec_module(
        module
    )

    return module


def validate_sequence(
    sequence: list[str],
) -> tuple[str, str, str]:
    """
    The first adapter contract is intentionally narrow:

        left -> gap -> right

    This guarantees a real and inspectable 567 computation.
    """

    if not isinstance(sequence, list):
        raise TypeError(
            "567 input must be a list"
        )

    if len(sequence) != 3:
        raise ValueError(
            "567 input must contain exactly "
            "left, gap and right"
        )

    left = str(sequence[0]).strip()

    gap = str(sequence[1]).strip()

    right = str(sequence[2]).strip()

    if not left or not right:
        raise ValueError(
            "567 boundary signs cannot be empty"
        )

    if gap.lower() not in GAP_MARKERS:
        raise ValueError(
            "middle token is not a recognized gap"
        )

    return left, gap, right


def observe_567(
    sequence: list[str],
) -> dict[str, Any]:
    """
    Execute the historical MalyshCuneiformEngine567.

    Real input:
        [left, gap, right]

    Real calculation:
        corpus frequencies
        transition topology
        candidate comparison
        minimum topological tension

    Returned result is an internal observation only.
    """

    left, gap, right = validate_sequence(
        sequence
    )

    module = load_567_module()

    engine_class = getattr(
        module,
        "MalyshCuneiformEngine567",
        None,
    )

    if engine_class is None:
        raise AttributeError(
            "MalyshCuneiformEngine567 is missing"
        )

    with TemporaryDirectory(
        prefix="malysh_567_"
    ) as temporary_directory:

        engine = engine_class(
            data_dir=temporary_directory
        )

        # A deliberately missing optional input file makes the
        # historical engine load its built-in base corpus only.
        # No synthetic corpus is introduced by the adapter.

        missing_corpus = (
            Path(temporary_directory)
            / "no_external_corpus.txt"
        )

        loaded = engine.load_corpus_from_text(
            str(missing_corpus)
        )

        if loaded is not True:
            raise RuntimeError(
                "567 corpus initialization failed"
            )

        restored, tension = engine.restore_gap(
            left,
            right,
        )

        if restored is None:
            raise RuntimeError(
                "567 did not restore the gap"
            )

        if not isinstance(
            tension,
            (int, float),
        ):
            raise TypeError(
                "567 tension is not numeric"
            )

        tension = float(tension)

        if not math.isfinite(tension):
            raise ValueError(
                "567 tension is not finite"
            )

        result = {
            "organ":
                "567",

            "subject":
                "Malysh",

            "mode":
                "legacy_topological_gap_restoration",

            "input": {
                "sequence": [
                    left,
                    gap,
                    right,
                ],

                "left":
                    left,

                "gap":
                    gap,

                "right":
                    right,
            },

            "output": {
                "restored_sign":
                    restored,

                "restored_sequence": [
                    left,
                    restored,
                    right,
                ],

                "topological_tension":
                    tension,
            },

            "evidence": {
                "engine_class":
                    engine_class.__name__,

                "corpus_sequences":
                    len(engine.corpus),

                "unique_signs":
                    len(engine.sign_frequencies),

                "transition_sources":
                    len(engine.transition_matrix),

                "attractors":
                    sorted(engine.attractors),
            },

            "functional_invariant": (
                len(engine.corpus) > 0
                and
                len(engine.sign_frequencies) > 0
                and
                len(engine.transition_matrix) > 0
                and
                restored
                in engine.sign_frequencies
            ),

            "decision_authority":
                False,

            "automatic_execution":
                False,

            "state_write":
                False,

            "state_commit":
                False,
        }

    if not result[
        "functional_invariant"
    ]:
        raise RuntimeError(
            "567 functional invariant failed"
        )

    return result
