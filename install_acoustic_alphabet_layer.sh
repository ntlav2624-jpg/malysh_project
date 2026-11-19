#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/malysh_project"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_ROOT="$HOME/malysh_backups"
BACKUP="$BACKUP_ROOT/malysh_before_acoustic_alphabet_$STAMP.tar.gz"
TAG="pre-acoustic-alphabet-$STAMP"
REPORT="$ROOT/experiments/ns_acoustic_external/integration_reports/$STAMP"

cd "$ROOT"

mkdir -p "$BACKUP_ROOT"
mkdir -p "$REPORT"

echo "============================================================"
echo " MALYSH: INSTALL ACOUSTIC ALPHABET LAYER"
echo "============================================================"
echo "Project : $ROOT"
echo "Report  : $REPORT"
echo "Tag     : $TAG"
echo

git rev-parse --is-inside-work-tree >/dev/null

BRANCH="$(git branch --show-current)"
HEAD_BEFORE="$(git rev-parse HEAD)"

if [ -z "$BRANCH" ]; then
    echo "[FAIL] Detached HEAD"
    exit 1
fi

git status --short > "$REPORT/status_before.txt"
git diff > "$REPORT/diff_before.patch"
git diff --cached > "$REPORT/cached_diff_before.patch"

echo "[PASS] Branch: $BRANCH"
echo "[PASS] HEAD:   $HEAD_BEFORE"

# ============================================================
# 1. BACKUP
# ============================================================

echo
echo "=== BACKUP ==="

tar \
    --exclude='./.git' \
    -czf "$BACKUP" \
    -C "$ROOT" \
    .

test -s "$BACKUP"

echo "[PASS] Backup:"
ls -lh "$BACKUP"

# ============================================================
# 2. SAFETY TAG
# ============================================================

echo
echo "=== SAFETY TAG ==="

git tag -a "$TAG" \
    -m "Safety point before Acoustic Alphabet integration $STAMP"

echo "[PASS] Created: $TAG"

# ============================================================
# 3. ACOUSTIC ALPHABET OBSERVER
# ============================================================

cat > malysh_system/acoustic_alphabet_observer.py <<'PY'
"""
Acoustic Alphabet observer for one canonical Malysh.

The observer adds a compositional interpretation:

    S_a (+) S_b -> S_(a+b)

For spectral modes:

    S_p (+) S_q -> S_(p+q)

The signed scalar T(k|p,q) describes the direction and strength
of an interaction.

Temporal alphabet:

    S_next = S_current + Delta_1 + Delta_2

where:

    Delta_1 = S_current - S_previous
    Delta_2 = Delta_1 - (S_previous - S_old)

The observer has no decision authority and cannot modify the main
answer, possible branch, execution gate, or transaction result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


SCHEMA = "malysh.acoustic-alphabet-observer.v1"
LAYER_NAME = "AcousticAlphabet"


@dataclass(frozen=True)
class AlphabetSymbol:
    """One alphabet symbol with optional physical weight."""

    value: float
    label: str = ""
    weight: float = 1.0

    def compose(self, other: "AlphabetSymbol") -> "AlphabetSymbol":
        return AlphabetSymbol(
            value=self.value + other.value,
            label=f"({self.label}+{other.label})",
            weight=self.weight * other.weight,
        )


def compose_numbers(a: float, b: float) -> float:
    """S_a (+) S_b -> S_(a+b)."""

    return float(a) + float(b)


def compose_modes(
    p: Sequence[int],
    q: Sequence[int],
) -> tuple[int, ...]:
    """Vector form p + q = k."""

    if len(p) != len(q):
        raise ValueError("mode dimensions must match")

    return tuple(
        int(a) + int(b)
        for a, b in zip(p, q)
    )


def zero_identity(value: float) -> bool:
    """S_0 (+) S_n = S_n."""

    numeric = float(value)

    return (
        compose_numbers(0.0, numeric) == numeric
        and compose_numbers(numeric, 0.0) == numeric
    )


def temporal_predict(
    old: Sequence[float],
    previous: Sequence[float],
    current: Sequence[float],
) -> list"""
    Temporal alphabet:

        next = current + delta_1 + delta_2
             = 3*current - 3*previous + old
    """

    if not (
        len(old)
        == len(previous)
        == len(current)
    ):
        raise ValueError("temporal symbol dimensions must match")

    output: list[float] = []

    for x0, x1, x2 in zip(
        old,
        previous,
        current,
    ):
        delta_previous = float(x1) - float(x0)
        delta_current = float(x2) - float(x1)
        delta_change = delta_current - delta_previous

        output.append(
            float(x2)
            + delta_current
            + delta_change
        )

    return output


def interaction_record(
    p: Sequence[int],
    q: Sequence[int],
    transfer: float | None = None,
) -> dict[str, Any]:
    """
    Build a testable triad record.

    transfer > 0: contribution into k.
    transfer < 0: contribution out of k.
    """

    k = compose_modes(p, q)

    if transfer is None:
        direction = "unknown"
    elif transfer > 0:
        direction = "into_k"
    elif transfer < 0:
        direction = "out_of_k"
    else:
        direction = "neutral"

    return {
        "p": list(map(int, p)),
        "q": list(map(int, q)),
        "k": list(k),
        "invariant": all(
            int(p[i]) + int(q[i]) == k[i]
            for i in range(len(k))
        ),
        "transfer": (
            None
            if transfer is None
            else float(transfer)
        ),
        "direction": direction,
    }


def _numeric_sequence(value: Any) -> list[float] | None:
    if not isinstance(value, (list, tuple)):
        return None

    converted: list[float] = []

    for item in value:
        if isinstance(item, bool):
            return None

        if not isinstance(item, (int, float)):
            return None

        converted.append(float(item))

    return converted


def _extract_temporal_context(
    old_result: Any,
    unresolved: Any,
) -> dict[str, Any]:
    """
    Read structured semantic history when available.

    This function never invents unavailable values.
    """

    sources: list[Any] = [
        old_result,
        unresolved,
    ]

    for source in sources:
        if not isinstance(source, Mapping):
            continue

        context = source.get("semantic_context", source)

        if not isinstance(context, Mapping):
            continue

        history = context.get("visible_snapshots")

        if not isinstance(history, list) or len(history) < 3:
            continue

        selected = history[-3:]

        fields: dict[str, list[list[float]]] = {}

        for field in (
            "cumulative_flux",
            "energy_spectrum",
        ):
            values: list[list[float]] = []

            for snapshot in selected:
                if not isinstance(snapshot, Mapping):
                    values = []
                    break

                numeric = _numeric_sequence(
                    snapshot.get(field)
                )

                if numeric is None:
                    values = []
                    break

                values.append(numeric)

            if len(values) == 3:
                fields[field] = values

        if fields:
            return {
                "available": True,
                "fields": fields,
                "source": "structured_semantic_context",
            }

    return {
        "available": False,
        "fields": {},
        "source": "no_structured_temporal_context",
    }


def observe(
    *,
    data: Iterable[int] | None = None,
    old_result: Any = None,
    unresolved: Any = None,
) -> dict[str, Any]:
    """
    Produce an independent observer result.

    The result is descriptive and predictive only. It must not be
    treated as a winner, action, permission, or transaction.
    """

    temporal = _extract_temporal_context(
        old_result,
        unresolved,
    )

    predictions: dict[str, Any] = {}

    if temporal["available"]:
        for field, values in temporal["fields"].items():
            predictions[field] = temporal_predict(
                values[0],
                values[1],
                values[2],
            )

    data_list = (
        list(data)
        if data is not None
        else []
    )

    return {
        "organ": LAYER_NAME,
        "schema": SCHEMA,
        "status": "observed",
        "principle": {
            "number_composition":
                "S_a plus S_b produces S_(a+b)",
            "spectral_composition":
                "S_p plus S_q produces S_(p+q)",
            "temporal_composition":
                "S_next = S_current + Delta_1 + Delta_2",
            "zero_identity":
                "S_0 plus S_n equals S_n",
            "weighted_interaction":
                "T(k|p,q) gives direction and strength",
        },
        "input_summary": {
            "data_count": len(data_list),
            "structured_context":
                temporal["available"],
            "structured_source":
                temporal["source"],
        },
        "prediction": {
            "available": bool(predictions),
            "fields": predictions,
            "kind": (
                "alphabet_temporal_prediction"
                if predictions
                else "no_structured_prediction"
            ),
        },
        "invariants": {
            "zero_identity": zero_identity(7.0),
            "mode_composition_example":
                compose_modes((1, 0, 0), (0, 1, 0))
                == (1, 1, 0),
            "temporal_decomposition_example":
                temporal_predict([1.0], [2.0], [4.0])
                == [7.0],
            "decision_authority": False,
            "main_answer_write": False,
            "possible_branch_write": False,
            "winner_selection": False,
            "execution_authority": False,
            "transaction_authority": False,
            "replace_existing_logic": False,
        },
        "decision_authority": False,
        "main_answer_write": False,
        "possible_branch_write": False,
        "winner_selection": False,
        "affects_main_answer": False,
        "revisable": True,
    }
PY

# ============================================================
# 4. KMBP BRIDGE
# ============================================================

cat > malysh_system/kmbp_acoustic_alphabet.py <<'PY'
"""
KMBP bridge for the Acoustic Alphabet observer.

The bridge makes Acoustic Alphabet experience visible from KMBP
without changing KMBP's existing computation, decision authority,
or historical semantics.
"""

from __future__ import annotations

from typing import Any, Iterable

from malysh_system.acoustic_alphabet_observer import (
    SCHEMA as ALPHABET_SCHEMA,
    observe as observe_acoustic_alphabet,
)


SCHEMA = "malysh.kmbp-acoustic-alphabet-bridge.v1"
BRIDGE_NAME = "KMBP_ACOUSTIC_ALPHABET"


def observe_kmbp_acoustic_alphabet(
    *,
    data: Iterable[int] | None = None,
    old_result: Any = None,
    unresolved: Any = None,
    kmbp_result: Any = None,
) -> dict[str, Any]:
    """
    Attach a read-only Acoustic Alphabet observation to KMBP.

    Existing KMBP output is referenced but never rewritten.
    """

    alphabet = observe_acoustic_alphabet(
        data=data,
        old_result=old_result,
        unresolved=unresolved,
    )

    return {
        "organ": BRIDGE_NAME,
        "schema": SCHEMA,
        "alphabet_schema": ALPHABET_SCHEMA,
        "status": "observed",
        "role": (
            "Read-only KMBP experience bridge. "
            "No replacement of existing KMBP logic."
        ),
        "kmbp_result_present":
            kmbp_result is not None,
        "alphabet_observation":
            alphabet,
        "invariants": {
            "kmbp_result_unchanged": True,
            "existing_kmbp_logic_preserved": True,
            "legacy_experience_preserved": True,
            "decision_authority": False,
            "main_answer_write": False,
            "possible_branch_write": False,
            "winner_selection": False,
            "execution_authority": False,
            "transaction_authority": False,
        },
        "decision_authority": False,
        "main_answer_write": False,
        "possible_branch_write": False,
        "winner_selection": False,
        "affects_main_answer": False,
        "revisable": True,
    }
PY

# ============================================================
# 5. CYCLE ATTACHMENT
# ============================================================

cat > malysh_system/acoustic_alphabet_integration.py <<'PY'
"""
Safe attachment of Acoustic Alphabet observations to a cycle result.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from malysh_system.acoustic_alphabet_observer import (
    observe as observe_acoustic_alphabet,
)
from malysh_system.kmbp_acoustic_alphabet import (
    observe_kmbp_acoustic_alphabet,
)


SCHEMA = "malysh.acoustic-alphabet-integration.v1"


def _read_kmbp_result(result: Mapping[str, Any]) -> Any:
    for key in (
        "kmbp",
        "KMBP",
    ):
        if key in result:
            return result[key]

    mind = result.get("mind")

    if isinstance(mind, Mapping):
        observations = mind.get("observations")

        if isinstance(observations, Mapping):
            return observations.get("KMBP")

    return None


def attach_acoustic_alphabet(
    cycle_result: Any,
    *,
    data: Iterable[int] | None = None,
    old_result: Any = None,
    unresolved: Any = None,
) -> dict[str, Any]:
    """
    Return an augmented copy.

    The original result is not mutated. Existing fields are preserved.
    """

    if not isinstance(cycle_result, Mapping):
        return {
            "original_result": cycle_result,
            "acoustic_alphabet_integration_error":
                "cycle_result_is_not_mapping",
        }

    augmented = deepcopy(dict(cycle_result))

    kmbp_result = _read_kmbp_result(augmented)

    layer = observe_acoustic_alphabet(
        data=data,
        old_result=old_result,
        unresolved=unresolved,
    )

    kmbp_bridge = observe_kmbp_acoustic_alphabet(
        data=data,
        old_result=old_result,
        unresolved=unresolved,
        kmbp_result=kmbp_result,
    )

    augmented["acoustic_alphabet"] = layer

    experience = augmented.setdefault(
        "experience",
        {},
    )

    if isinstance(experience, dict):
        experience[
            "KMBP_ACOUSTIC_ALPHABET"
        ] = kmbp_bridge

    mind = augmented.setdefault(
        "mind",
        {},
    )

    if isinstance(mind, dict):
        observations = mind.setdefault(
            "observations",
            {},
        )

        if isinstance(observations, dict):
            observations[
                "AcousticAlphabet"
            ] = layer

            observations[
                "KMBP_AcousticAlphabet"
            ] = kmbp_bridge

    invariants = augmented.setdefault(
        "invariants",
        {},
    )

    if isinstance(invariants, dict):
        invariants.update({
            "acoustic_alphabet_observer_present":
                True,
            "kmbp_acoustic_alphabet_bridge_present":
                True,
            "acoustic_alphabet_no_decision_authority":
                True,
            "acoustic_alphabet_no_main_answer_write":
                True,
            "acoustic_alphabet_no_possible_write":
                True,
            "acoustic_alphabet_no_winner_selection":
                True,
            "acoustic_alphabet_existing_logic_preserved":
                True,
        })

    augmented[
        "acoustic_alphabet_integration"
    ] = {
        "schema": SCHEMA,
        "status": "attached",
        "original_result_mutated": False,
        "decision_authority": False,
        "main_answer_write": False,
        "possible_branch_write": False,
        "winner_selection": False,
        "replace_existing_logic": False,
    }

    return augmented
PY

# ============================================================
# 6. FUNCTIONAL TESTS
# ============================================================

mkdir -p tests

cat > tests/test_acoustic_alphabet_observer.py <<'PY'
from copy import deepcopy

from malysh_system.acoustic_alphabet_observer import (
    compose_modes,
    compose_numbers,
    interaction_record,
    observe,
    temporal_predict,
    zero_identity,
)
from malysh_system.acoustic_alphabet_integration import (
    attach_acoustic_alphabet,
)
from malysh_system.kmbp_acoustic_alphabet import (
    observe_kmbp_acoustic_alphabet,
)


def test_number_composition():
    assert compose_numbers(1, 1) == 2
    assert compose_numbers(1, 2) == 3
    assert compose_numbers(2, 3) == 5
    assert compose_numbers(4, 5) == 9


def test_zero_identity():
    for value in range(10):
        assert zero_identity(value)


def test_mode_composition():
    assert compose_modes(
        (1, 0, 0),
        (0, 1, 0),
    ) == (1, 1, 0)

    assert compose_modes(
        (1, 1, 1),
        (1, -1, 1),
    ) == (2, 0, 2)


def test_weighted_interaction():
    positive = interaction_record(
        (1, 1, 1),
        (1, -1, 1),
        transfer=0.25,
    )

    negative = interaction_record(
        (1, 1, 1),
        (-1, 1, 1),
        transfer=-0.10,
    )

    assert positive["k"] == [2, 0, 2]
    assert positive["direction"] == "into_k"
    assert positive["invariant"] is True

    assert negative["direction"] == "out_of_k"
    assert negative["invariant"] is True


def test_temporal_alphabet():
    predicted = temporal_predict(
        [1.0, 2.0],
        [2.0, 4.0],
        [4.0, 8.0],
    )

    assert predicted == [7.0, 14.0]


def test_observer_structured_prediction():
    snapshots = [
        {
            "cumulative_flux": [1.0, 2.0],
            "energy_spectrum": [4.0, 8.0],
        },
        {
            "cumulative_flux": [2.0, 4.0],
            "energy_spectrum": [5.0, 10.0],
        },
        {
            "cumulative_flux": [4.0, 8.0],
            "energy_spectrum": [7.0, 14.0],
        },
    ]

    result = observe(
        data=[1, 2, 3],
        old_result={
            "semantic_context": {
                "visible_snapshots": snapshots,
            },
        },
    )

    assert result["prediction"]["available"] is True
    assert result["decision_authority"] is False
    assert result["main_answer_write"] is False
    assert result["winner_selection"] is False


def test_kmbp_bridge_preserves_kmbp():
    kmbp = {
        "legacy": True,
        "value": 567,
    }

    before = deepcopy(kmbp)

    bridge = observe_kmbp_acoustic_alphabet(
        data=[1, 2, 3],
        kmbp_result=kmbp,
    )

    assert kmbp == before
    assert bridge["decision_authority"] is False
    assert (
        bridge["invariants"]
        ["existing_kmbp_logic_preserved"]
        is True
    )


def test_cycle_attachment_does_not_mutate_source():
    source = {
        "main_answer": "unchanged",
        "kmbp": {
            "legacy": True,
        },
        "invariants": {
            "old": True,
        },
    }

    before = deepcopy(source)

    result = attach_acoustic_alphabet(
        source,
        data=[1, 2, 3],
    )

    assert source == before
    assert result["main_answer"] == "unchanged"
    assert result["kmbp"] == source["kmbp"]
    assert (
        result["invariants"]
        ["acoustic_alphabet_observer_present"]
        is True
    )
    assert (
        result["invariants"]
        ["acoustic_alphabet_no_decision_authority"]
        is True
    )
PY

# ============================================================
# 7. SAFE THINKING CYCLE PATCH
# ============================================================

echo
echo "=== PATCH THINKING CYCLE ==="

python - "$ROOT" "$REPORT" <<'PY'
import ast
import json
import sys
from pathlib import Path


root = Path(sys.argv[1])
report = Path(sys.argv[2])

path = root / "malysh_system/thinking_cycle.py"

if not path.exists():
    raise SystemExit(
        "[FAIL] malysh_system/thinking_cycle.py not found"
    )

source = path.read_text(encoding="utf-8")

marker = "# ACOUSTIC_ALPHABET_INTEGRATION_V1"

if marker in source:
    print("[INFO] Integration marker already present")
    raise SystemExit(0)

tree = ast.parse(source)

target = None

for node in tree.body:
    if (
        isinstance(node, ast.FunctionDef)
        and node.name == "run_thinking_cycle"
    ):
        target = node
        break

if target is None:
    raise SystemExit(
        "[FAIL] run_thinking_cycle not found"
    )

returns = [
    node
    for node in ast.walk(target)
    if (
        isinstance(node, ast.Return)
        and isinstance(node.value, ast.Name)
        and node.value.id == "result"
    )
]

if len(returns) != 1:
    raise SystemExit(
        "[FAIL] Expected exactly one `return result` "
        f"inside run_thinking_cycle, found {len(returns)}"
    )

return_node = returns[0]

lines = source.splitlines()

insert_index = return_node.lineno - 1
indent = " " * return_node.col_offset

block = [
    indent + marker,
    indent + "try:",
    indent + "    from malysh_system.acoustic_alphabet_integration import (",
    indent + "        attach_acoustic_alphabet,",
    indent + "    )",
    indent + "    result = attach_acoustic_alphabet(",
    indent + "        result,",
    indent + "        data=data,",
    indent + "        old_result=old_result,",
    indent + "        unresolved=unresolved,",
    indent + "    )",
    indent + "except Exception as acoustic_alphabet_error:",
    indent + "    if isinstance(result, dict):",
    indent + "        diagnostics = result.setdefault(",
    indent + "            'diagnostics',",
    indent + "            {},",
    indent + "        )",
    indent + "        if isinstance(diagnostics, dict):",
    indent + "            diagnostics[",
    indent + "                'acoustic_alphabet_error'",
    indent + "            ] = {",
    indent + "                'type': type(",
    indent + "                    acoustic_alphabet_error",
    indent + "                ).__name__,",
    indent + "                'message': str(",
    indent + "                    acoustic_alphabet_error",
    indent + "                ),",
    indent + "                'decision_authority': False,",
    indent + "            }",
]

patched_lines = (
    lines[:insert_index]
    + block
    + lines[insert_index:]
)

patched = "\n".join(patched_lines) + "\n"

# Syntax validation before writing.
ast.parse(patched)

backup = (
    path.parent
    / f"thinking_cycle.py.before_acoustic_alphabet"
)

backup.write_text(source, encoding="utf-8")
path.write_text(patched, encoding="utf-8")

report_data = {
    "schema":
        "malysh.acoustic-alphabet-patch-report.v1",
    "file": str(path),
    "backup": str(backup),
    "function": "run_thinking_cycle",
    "return_line_before_patch":
        return_node.lineno,
    "marker": marker,
    "syntax_valid": True,
}

(report / "patch_report.json").write_text(
    json.dumps(
        report_data,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print("[PASS] thinking_cycle patched safely")
print("[PASS] original backup:", backup)
PY

# ============================================================
# 8. SYNTAX AND TESTS
# ============================================================

echo
echo "=== PYTHON SYNTAX ==="

python -m py_compile \
    malysh_system/acoustic_alphabet_observer.py \
    malysh_system/kmbp_acoustic_alphabet.py \
    malysh_system/acoustic_alphabet_integration.py \
    malysh_system/thinking_cycle.py \
    tests/test_acoustic_alphabet_observer.py

echo "[PASS] Python syntax"

echo
echo "=== PYTEST ==="

if python -m pytest --version >/dev/null 2>&1; then
    python -m pytest \
        -q \
        tests/test_acoustic_alphabet_observer.py \
        | tee "$REPORT/pytest.log"
else
    echo "[WARN] pytest unavailable, running direct test harness"

    PYTHONPATH="$ROOT" python - <<'PY' \
        | tee "$REPORT/direct_tests.log"
from tests.test_acoustic_alphabet_observer import (
    test_cycle_attachment_does_not_mutate_source,
    test_kmbp_bridge_preserves_kmbp,
    test_mode_composition,
    test_number_composition,
    test_observer_structured_prediction,
    test_temporal_alphabet,
    test_weighted_interaction,
    test_zero_identity,
)

tests = [
    test_number_composition,
    test_zero_identity,
    test_mode_composition,
    test_weighted_interaction,
    test_temporal_alphabet,
    test_observer_structured_prediction,
    test_kmbp_bridge_preserves_kmbp,
    test_cycle_attachment_does_not_mutate_source,
]

for test in tests:
    test()
    print("[PASS]", test.__name__)
PY
fi

# ============================================================
# 9. REAL THINKING CYCLE SMOKE TEST
# ============================================================

echo
echo "=== REAL THINKING CYCLE SMOKE TEST ==="

PYTHONPATH="$ROOT" python - "$REPORT" <<'PY' \
    | tee "$REPORT/smoke_test.log"
import json
import sys
from pathlib import Path

from malysh_system.thinking_cycle import (
    run_thinking_cycle,
)

report = Path(sys.argv[1])

snapshots = [
    {
        "cumulative_flux": [1.0, 2.0, 3.0],
        "energy_spectrum": [4.0, 5.0, 6.0],
    },
    {
        "cumulative_flux": [2.0, 4.0, 6.0],
        "energy_spectrum": [5.0, 7.0, 9.0],
    },
    {
        "cumulative_flux": [4.0, 8.0, 12.0],
        "energy_spectrum": [7.0, 10.0, 13.0],
    },
]

result = run_thinking_cycle(
    data=[1, 2, 3, 4],
    old_result={
        "semantic_context": {
            "visible_snapshots": snapshots,
        },
    },
    unresolved={
        "kind":
            "acoustic_alphabet_smoke_test",
    },
    root=Path.home() / "malysh_project",
)

assert isinstance(result, dict)

assert "acoustic_alphabet" in result

assert (
    result["acoustic_alphabet"]
    ["decision_authority"]
    is False
)

assert (
    result["acoustic_alphabet"]
    ["main_answer_write"]
    is False
)

assert (
    result["acoustic_alphabet"]
    ["prediction"]
    ["available"]
    is True
)

mind = result.get("mind", {})
observations = mind.get("observations", {})

assert "AcousticAlphabet" in observations
assert "KMBP_AcousticAlphabet" in observations

experience = result.get("experience", {})

assert "KMBP_ACOUSTIC_ALPHABET" in experience

smoke = {
    "schema":
        "malysh.acoustic-alphabet-smoke.v1",
    "pass": True,
    "observer_present": True,
    "kmbp_bridge_present": True,
    "prediction_available":
        result["acoustic_alphabet"]
        ["prediction"]
        ["available"],
    "decision_authority":
        result["acoustic_alphabet"]
        ["decision_authority"],
    "main_answer_write":
        result["acoustic_alphabet"]
        ["main_answer_write"],
    "existing_logic_preserved":
        result["invariants"]
        ["acoustic_alphabet_existing_logic_preserved"],
}

(report / "smoke_result.json").write_text(
    json.dumps(
        smoke,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print("[PASS] real thinking cycle completed")
print("[PASS] AcousticAlphabet observation present")
print("[PASS] KMBP_AcousticAlphabet bridge present")
print("[PASS] prediction available")
print("[PASS] decision authority remains false")
print("[PASS] main answer write remains false")
PY

# ============================================================
# 10. A/B EVIDENCE VERIFICATION
# ============================================================

echo
echo "=== VERIFY A/B EVIDENCE ==="

LATEST_AB="$(
    find "$ROOT/experiments/ns_acoustic_external/runs" \
        -maxdepth 1 \
        -type d \
        -name 'alphabet_test_*' \
    | sort \
    | tail -n 1
)"

if [ -z "$LATEST_AB" ]; then
    echo "[FAIL] No alphabet_test_* evidence found"
    exit 2
fi

(
    cd "$LATEST_AB"
    sha256sum -c acoustic_alphabet_test.sha256
) | tee "$REPORT/ab_hash_verification.txt"

cp \
    "$LATEST_AB/acoustic_alphabet_test.json" \
    "$REPORT/accepted_ab_evidence.json"

cp \
    "$LATEST_AB/acoustic_alphabet_test.sha256" \
    "$REPORT/accepted_ab_evidence.sha256"

# ============================================================
# 11. SAFETY SCAN
# ============================================================

echo
echo "=== PRE-COMMIT SAFETY SCAN ==="

find . \
    -path './.git' -prune -o \
    -type f \
    \( \
        -iname '*.pem' -o \
        -iname '*.key' -o \
        -iname '*credential*' -o \
        -iname '*secret*' -o \
        -iname '*token*' \
    \) \
    -print > "$REPORT/suspicious_paths.txt"

if [ -s "$REPORT/suspicious_paths.txt" ]; then
    echo "[FAIL] Potential secret files:"
    cat "$REPORT/suspicious_paths.txt"
    exit 3
fi

echo "[PASS] No suspicious filenames"

find . \
    -path './.git' -prune -o \
    -type f \
    -size +25M \
    -print > "$REPORT/large_files.txt"

if [ -s "$REPORT/large_files.txt" ]; then
    echo "[FAIL] Files larger than 25 MB:"
    cat "$REPORT/large_files.txt"
    exit 4
fi

echo "[PASS] No files over 25 MB"

# ============================================================
# 12. COMMIT
# ============================================================

echo
echo "=== GIT DIFF ==="

git status --short \
    | tee "$REPORT/status_before_commit.txt"

git diff --stat \
    | tee "$REPORT/diff_stat.txt"

git add -A

git diff --cached --stat \
    | tee "$REPORT/staged_stat.txt"

git diff --cached --name-status \
    > "$REPORT/staged_name_status.txt"

if git diff --cached --quiet; then
    echo "[FAIL] Nothing staged"
    exit 5
fi

git commit \
    -m "Add Acoustic Alphabet observer and KMBP bridge"

COMMIT="$(git rev-parse HEAD)"

echo "[PASS] Commit: $COMMIT"

# ============================================================
# 13. SAFE REMOTE SYNC
# ============================================================

echo
echo "=== REMOTE SYNC ==="

if ! git remote | grep -q .; then
    echo "[WARN] No Git remote"
    SYNC_STATUS="no_remote"
else
    if git remote | grep -qx origin; then
        REMOTE="origin"
    else
        REMOTE="$(git remote | head -n 1)"
    fi

    git fetch "$REMOTE" --tags

    REMOTE_REF="$REMOTE/$BRANCH"

    if git show-ref \
        --verify \
        --quiet \
        "refs/remotes/$REMOTE/$BRANCH"
    then
        COUNTS="$(
            git rev-list \
                --left-right \
                --count \
                "$BRANCH...$REMOTE_REF"
        )"

        AHEAD="$(printf '%s' "$COUNTS" | awk '{print $1}')"
        BEHIND="$(printf '%s' "$COUNTS" | awk '{print $2}')"

        echo "[INFO] Ahead:  $AHEAD"
        echo "[INFO] Behind: $BEHIND"

        {
            echo "ahead=$AHEAD"
            echo "behind=$BEHIND"
        } > "$REPORT/ahead_behind.txt"

        if [ "$AHEAD" -gt 0 ] && [ "$BEHIND" -gt 0 ]; then
            echo "[FAIL] Local and remote diverged"
            echo "[INFO] Commit, tag and backup are preserved"
            printf '%s\n' \
                "diverged_manual_review_required" \
                > "$REPORT/sync_status.txt"
            exit 6
        fi

        if [ "$BEHIND" -gt 0 ]; then
            git rebase "$REMOTE_REF"
        fi
    fi

    git push -u "$REMOTE" "$BRANCH"
    git push "$REMOTE" "$TAG"

    SYNC_STATUS="pushed"

    echo "[PASS] Branch pushed"
    echo "[PASS] Safety tag pushed"
fi

printf '%s\n' "$SYNC_STATUS" \
    > "$REPORT/sync_status.txt"

# ============================================================
# 14. FINAL REPORT COMMIT
# ============================================================

HEAD_AFTER="$(git rev-parse HEAD)"

{
    echo "timestamp=$STAMP"
    echo "branch=$BRANCH"
    echo "head_before=$HEAD_BEFORE"
    echo "head_after=$HEAD_AFTER"
    echo "tag=$TAG"
    echo "backup=$BACKUP"
    echo "report=$REPORT"
    echo "sync_status=$SYNC_STATUS"
} > "$REPORT/summary.txt"

git add "$REPORT"

if ! git diff --cached --quiet; then
    git commit \
        -m "Complete Acoustic Alphabet integration report"

    if [ "$SYNC_STATUS" = "pushed" ]; then
        git push
    fi
fi

echo
echo "============================================================"
echo " ACOUSTIC ALPHABET INTEGRATION COMPLETE"
echo "============================================================"
echo "Branch      : $BRANCH"
echo "HEAD before : $HEAD_BEFORE"
echo "HEAD after  : $(git rev-parse HEAD)"
echo "Safety tag  : $TAG"
echo "Backup      : $BACKUP"
echo "Report      : $REPORT"
echo
echo "Installed:"
echo "  malysh_system/acoustic_alphabet_observer.py"
echo "  malysh_system/kmbp_acoustic_alphabet.py"
echo "  malysh_system/acoustic_alphabet_integration.py"
echo
echo "Invariants:"
echo "  decision_authority=False"
echo "  main_answer_write=False"
echo "  possible_branch_write=False"
echo "  winner_selection=False"
echo "  replace_existing_logic=False"
echo "============================================================"
