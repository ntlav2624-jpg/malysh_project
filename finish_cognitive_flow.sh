#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/malysh_project"
cd "$ROOT"

MODULE="malysh_system/cognitive_flow.py"
INTEGRATION="malysh_system/cognitive_flow_integration.py"
TEST="tests/test_cognitive_flow.py"
CONFIG="config/cognitive_flow.json"

BEFORE="744cfcb14a1fefa569808dbbaa099beb45625ac5"
TAG="pre-cognitive-flow-20261110_013919"

echo "============================================================"
echo "MALYSH: FINISH COGNITIVE FLOW"
echo "============================================================"

# ------------------------------------------------------------
# 1. SAFETY
# ------------------------------------------------------------

CURRENT="$(git rev-parse HEAD)"

if [ "$CURRENT" != "$BEFORE" ]; then
    echo "STOP: HEAD changed."
    echo "Expected: $BEFORE"
    echo "Actual  : $CURRENT"
    exit 1
fi

git rev-parse "$TAG" >/dev/null 2>&1 || {
    echo "STOP: safety tag missing: $TAG"
    exit 1
}

if [ -n "$(git diff --cached --name-only)" ]; then
    echo "STOP: Git index is not empty:"
    git diff --cached --name-only
    exit 1
fi

for f in \
    "$MODULE" \
    "$INTEGRATION" \
    "$TEST" \
    "$CONFIG"
do
    test -f "$f" || {
        echo "STOP: missing $f"
        exit 1
    }
done

echo "[PASS] HEAD unchanged"
echo "[PASS] safety tag exists"
echo "[PASS] Git index empty"
echo "[PASS] four generated files exist"

# ------------------------------------------------------------
# 2. SHOW BROKEN AREA BEFORE MODIFICATION
# ------------------------------------------------------------

echo
echo "=== CURRENT _frontier AREA ==="

grep -n -A22 -B4 \
    '_frontier' \
    "$MODULE" \
    | head -35 || true

# ------------------------------------------------------------
# 3. REPAIR BY LINE BOUNDARIES, NOT PYTHON PARSING
# ------------------------------------------------------------

python - "$MODULE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])

text = path.read_text(
    encoding="utf-8"
)

start_marker = "    def _frontier"
end_marker = "    def _propagate_attention"

start = text.find(start_marker)
end = text.find(end_marker, start + 1)

if start < 0:
    raise SystemExit(
        "STOP: _frontier start marker not found"
    )

if end < 0:
    raise SystemExit(
        "STOP: _propagate_attention marker not found"
    )

if end <= start:
    raise SystemExit(
        "STOP: method order invalid"
    )

if text.find(
    start_marker,
    start + len(start_marker),
    end,
) >= 0:
    raise SystemExit(
        "STOP: duplicate _frontier marker"
    )

replacement = '''    def _frontier(self) -> setfrontier: set[str] = set()

        for relation in self._relations.values():
            if set(
                relation.sources
            ).issubset(self._active):
                frontier.add(
                    relation.target
                )

        return frontier

'''

new_text = (
    text[:start]
    + replacement
    + text[end:]
)

path.write_text(
    new_text,
    encoding="utf-8",
)

print(
    "[PASS] _frontier replaced "
    "between exact method boundaries"
)
PY

# ------------------------------------------------------------
# 4. VERIFY REPAIRED SOURCE
# ------------------------------------------------------------

echo
echo "=== REPAIRED _frontier AREA ==="

grep -n -A20 -B3 \
    'def _frontier' \
    "$MODULE"

if grep -n \
    'setfrontier' \
    "$MODULE"
then
    echo "STOP: corrupted token remains"
    exit 1
fi

echo "[PASS] corrupted token absent"

# Check tabs in Python source.
if grep -n $'\t' \
    "$MODULE" \
    "$INTEGRATION" \
    "$TEST"
then
    echo "STOP: tab indentation detected"
    exit 1
fi

echo "[PASS] no tab indentation detected"

# ------------------------------------------------------------
# 5. PYTHON SYNTAX
# ------------------------------------------------------------

python -m py_compile \
    "$MODULE" \
    "$INTEGRATION" \
    "$TEST"

echo "[PASS] Python syntax"

python -m json.tool \
    "$CONFIG" \
    >/dev/null

echo "[PASS] JSON"

# ------------------------------------------------------------
# 6. STANDARD-LIBRARY FUNCTIONAL TESTS
# ------------------------------------------------------------

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python "$TEST"

echo "[PASS] functional tests"

# ------------------------------------------------------------
# 7. INDEPENDENT SMOKE TEST
# ------------------------------------------------------------

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python - <<'PY'
from malysh_system.cognitive_flow import (
    RelationKind,
    ThoughtKind,
    create_default_controller,
)

c = create_default_controller()

c.add_state(
    state_id="input",
    content="input",
    kind=ThoughtKind.OBSERVATION,
    source="perception",
    confidence=1.0,
    initial_attention=1.0,
    active=True,
)

states = [
    (
        "primary",
        ThoughtKind.PROPOSAL,
    ),
    (
        "possible",
        ThoughtKind.POSSIBLE,
    ),
    (
        "negative",
        ThoughtKind.NEGATIVE_RESULT,
    ),
    (
        "unresolved",
        ThoughtKind.UNRESOLVED,
    ),
]

for state_id, kind in states:
    c.add_state(
        state_id=state_id,
        content=state_id,
        kind=kind,
        source="smoke",
        confidence=0.8,
    )

relations = [
    (
        "rp",
        "primary",
        RelationKind.SUPPORTS,
        1,
    ),
    (
        "rposs",
        "possible",
        RelationKind.SUGGESTS,
        1,
    ),
    (
        "rneg",
        "negative",
        RelationKind.CONTRADICTS,
        -1,
    ),
    (
        "runres",
        "unresolved",
        RelationKind.REQUIRES,
        0,
    ),
]

for relation_id, target, kind, sign in relations:
    c.add_relation(
        relation_id=relation_id,
        sources=["input"],
        target=target,
        kind=kind,
        sign=sign,
        confidence=1.0,
        evidence=1.0,
        priority=1.0,
    )

result = c.cycle_once()

assert result.primary.selected_id == "primary"
assert result.possible.selected_id == "possible"
assert result.negative.selected_id == "negative"
assert result.unresolved.selected_id == "unresolved"

assert result.invariant_failures == ()
assert not result.execution_allowed

assert abs(
    sum(result.attention.values())
    - 1.0
) < 1e-12

assert all(
    value >= 0.0
    for value in result.attention.values()
)

negative_relations = [
    relation
    for relation in c.relations
    if relation.sign < 0
]

assert len(negative_relations) == 1

wal_before = c.wal

c.cycle_once()

assert c.wal[:len(wal_before)] == wal_before

print(
    "[PASS] primary   =",
    result.primary.selected_id
)

print(
    "[PASS] possible  =",
    result.possible.selected_id
)

print(
    "[PASS] negative  =",
    result.negative.selected_id
)

print(
    "[PASS] unresolved=",
    result.unresolved.selected_id
)

print(
    "[PASS] attention =",
    sum(result.attention.values())
)

print(
    "[PASS] negative relation preserved"
)

print(
    "[PASS] WAL append-only"
)
PY

echo "[PASS] independent smoke test"

# ------------------------------------------------------------
# 8. STAGE EXACTLY FOUR FILES
# ------------------------------------------------------------

git add -- \
    "$MODULE" \
    "$INTEGRATION" \
    "$TEST" \
    "$CONFIG"

EXPECTED="$(
    printf '%s\n' \
        "$CONFIG" \
        "$MODULE" \
        "$INTEGRATION" \
        "$TEST" \
    | sort
)"

ACTUAL="$(
    git diff --cached \
        --name-only \
    | sort
)"

if [ "$ACTUAL" != "$EXPECTED" ]; then
    echo "STOP: staged set mismatch"
    echo
    echo "EXPECTED:"
    printf '%s\n' "$EXPECTED"
    echo
    echo "ACTUAL:"
    printf '%s\n' "$ACTUAL"
    exit 1
fi

echo "[PASS] exact staged set"

# ------------------------------------------------------------
# 9. COMMIT
# ------------------------------------------------------------

git commit \
    -m "architecture: add cognitive flow controller"

AFTER="$(git rev-parse HEAD)"

echo "[PASS] commit created"
echo "       $AFTER"

# ------------------------------------------------------------
# 10. VERIFY COMMIT
# ------------------------------------------------------------

COMMITTED="$(
    git diff-tree \
        --no-commit-id \
        --name-only \
        -r \
        "$AFTER" \
    | sort
)"

if [ "$COMMITTED" != "$EXPECTED" ]; then
    echo "STOP: unexpected commit content"
    echo
    echo "EXPECTED:"
    printf '%s\n' "$EXPECTED"
    echo
    echo "COMMITTED:"
    printf '%s\n' "$COMMITTED"
    exit 1
fi

echo "[PASS] exact commit content"

# ------------------------------------------------------------
# 11. POST-COMMIT TEST
# ------------------------------------------------------------

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python "$TEST"

echo "[PASS] post-commit tests"

# ------------------------------------------------------------
# 12. REPORT
# ------------------------------------------------------------

echo
echo "============================================================"
echo "COGNITIVE FLOW INSTALLED"
echo "============================================================"

echo "Root       : $ROOT"
echo "Branch     : $(git branch --show-current)"
echo "Before     : $BEFORE"
echo "Safety tag : $TAG"
echo "Commit     : $AFTER"

echo
echo "Architecture:"
echo "K -> R -> W -> J -> A/rho -> Phi -> O"

echo
echo "Human branches:"
echo "primary + possible + negative + unresolved"

echo
echo "[PASS] one unified Malysh"
echo "[PASS] negative results preserved"
echo "[PASS] attention invariant"
echo "[PASS] relation invariant"
echo "[PASS] WAL append-only"
echo "[PASS] observers separated from execution"
echo "[PASS] legacy untouched by installer"
echo "[PASS] exact four-file Git commit"

echo
echo "Working tree:"
git status --short

echo "============================================================"
