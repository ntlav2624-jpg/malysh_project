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
echo "MALYSH: COMPLETE COGNITIVE FLOW"
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

for file in \
    "$MODULE" \
    "$INTEGRATION" \
    "$TEST" \
    "$CONFIG"
do
    test -f "$file" || {
        echo "STOP: missing file: $file"
        exit 1
    }
done

echo "[PASS] HEAD unchanged"
echo "[PASS] safety tag exists"
echo "[PASS] Git index empty"
echo "[PASS] generated files exist"

# ------------------------------------------------------------
# 2. SAVE CURRENT VERSION
# ------------------------------------------------------------

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="runtime/cognitive_flow/cognitive_flow.missing_colon.${STAMP}.py"

mkdir -p runtime/cognitive_flow
cp "$MODULE" "$BACKUP"

echo "[PASS] diagnostic copy:"
echo "       $BACKUP"

# ------------------------------------------------------------
# 3. ADD THE MISSING COLON
# ------------------------------------------------------------

python - "$MODULE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

broken = "    def _frontier(self) -> set\n"
fixed = "    def _frontier(self) -> set:\n"

count = text.count(broken)

if count != 1:
    print(
        "STOP: expected exactly one missing-colon "
        f"signature, found {count}",
        file=sys.stderr,
    )
    sys.exit(1)

path.write_text(
    text.replace(
        broken,
        fixed,
        1,
    ),
    encoding="utf-8",
)

print("[PASS] missing colon added")
PY

echo
echo "=== FINAL _frontier FUNCTION ==="

grep -n -A14 -B2 \
    'def _frontier' \
    "$MODULE"

# Exact source checks.
grep -Fx \
    '    def _frontier(self) -> set:' \
    "$MODULE" \
    >/dev/null

grep -Fx \
    '        frontier: set[str] = set()' \
    "$MODULE" \
    >/dev/null

if grep -n 'setfrontier' "$MODULE"; then
    echo "STOP: corrupted token remains"
    exit 1
fi

echo "[PASS] function signature verified"

# ------------------------------------------------------------
# 4. SYNTAX AND CONFIG
# ------------------------------------------------------------

python -m py_compile \
    "$MODULE" \
    "$INTEGRATION" \
    "$TEST"

echo "[PASS] Python syntax"

python -m json.tool \
    "$CONFIG" \
    >/dev/null

echo "[PASS] JSON configuration"

# ------------------------------------------------------------
# 5. FUNCTIONAL TESTS
# ------------------------------------------------------------

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python "$TEST"

echo "[PASS] functional tests"

# ------------------------------------------------------------
# 6. INDEPENDENT SMOKE TEST
# ------------------------------------------------------------

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python - <<'PY'
from malysh_system.cognitive_flow import (
    RelationKind,
    ThoughtKind,
    create_default_controller,
)

controller = create_default_controller()

controller.add_state(
    state_id="input",
    content="new observation",
    kind=ThoughtKind.OBSERVATION,
    source="perception",
    confidence=1.0,
    initial_attention=1.0,
    active=True,
)

state_definitions = (
    ("primary", ThoughtKind.PROPOSAL),
    ("possible", ThoughtKind.POSSIBLE),
    ("negative", ThoughtKind.NEGATIVE_RESULT),
    ("unresolved", ThoughtKind.UNRESOLVED),
)

for state_id, kind in state_definitions:
    controller.add_state(
        state_id=state_id,
        content=state_id,
        kind=kind,
        source="smoke",
        confidence=0.8,
    )

relation_definitions = (
    (
        "relation-primary",
        "primary",
        RelationKind.SUPPORTS,
        1,
    ),
    (
        "relation-possible",
        "possible",
        RelationKind.SUGGESTS,
        1,
    ),
    (
        "relation-negative",
        "negative",
        RelationKind.CONTRADICTS,
        -1,
    ),
    (
        "relation-unresolved",
        "unresolved",
        RelationKind.REQUIRES,
        0,
    ),
)

for relation_id, target, kind, sign in relation_definitions:
    controller.add_relation(
        relation_id=relation_id,
        sources=["input"],
        target=target,
        kind=kind,
        sign=sign,
        confidence=1.0,
        evidence=1.0,
        priority=1.0,
    )

result = controller.cycle_once()

assert result.primary.selected_id == "primary"
assert result.possible.selected_id == "possible"
assert result.negative.selected_id == "negative"
assert result.unresolved.selected_id == "unresolved"

assert result.invariant_failures == ()
assert result.execution_allowed is False

attention_sum = sum(
    result.attention.values()
)

assert abs(attention_sum - 1.0) < 1e-12

assert all(
    value >= 0.0
    for value in result.attention.values()
)

assert any(
    relation.sign < 0
    for relation in controller.relations
)

wal_before = controller.wal
controller.cycle_once()
wal_after = controller.wal

assert wal_after[:len(wal_before)] == wal_before

print("[PASS] primary    =", result.primary.selected_id)
print("[PASS] possible   =", result.possible.selected_id)
print("[PASS] negative   =", result.negative.selected_id)
print("[PASS] unresolved =", result.unresolved.selected_id)
print("[PASS] attention  =", attention_sum)
print("[PASS] negative relation preserved")
print("[PASS] WAL append-only")
PY

echo "[PASS] independent smoke test"

# ------------------------------------------------------------
# 7. STAGE ONLY THE FOUR IMPLEMENTATION FILES
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
    echo "STOP: staged set mismatch."
    echo
    echo "EXPECTED:"
    printf '%s\n' "$EXPECTED"
    echo
    echo "ACTUAL:"
    printf '%s\n' "$ACTUAL"

    git reset -- \
        "$MODULE" \
        "$INTEGRATION" \
        "$TEST" \
        "$CONFIG" \
        >/dev/null

    echo "Our files were removed from the Git index."
    echo "No commit created."
    exit 1
fi

echo "[PASS] exact staged file set"

git diff --cached --check

echo "[PASS] staged diff check"

echo
echo "=== STAGED SUMMARY ==="
git diff --cached --stat

# ------------------------------------------------------------
# 8. COMMIT
# ------------------------------------------------------------

git commit \
    -m "architecture: add cognitive flow controller"

AFTER="$(git rev-parse HEAD)"

echo
echo "[PASS] commit created:"
echo "       $AFTER"

# ------------------------------------------------------------
# 9. VERIFY EXACT COMMIT CONTENT
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
    echo "STOP: commit contains unexpected paths."
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
# 10. POST-COMMIT TESTS
# ------------------------------------------------------------

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python "$TEST"

echo "[PASS] post-commit functional tests"

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python - <<'PY'
from malysh_system.cognitive_flow import (
    CognitiveFlowController,
    create_default_controller,
)

from malysh_system.cognitive_flow_integration import (
    attach_cognitive_flow,
    get_cognitive_flow,
)

controller = create_default_controller()

assert isinstance(
    controller,
    CognitiveFlowController,
)

class Malysh:
    def __init__(self):
        self.internal_organs = {
            "legacy": object()
        }
        self.organ_registry = {}

malysh = Malysh()
legacy = malysh.internal_organs["legacy"]

attached = attach_cognitive_flow(
    malysh,
)

assert get_cognitive_flow(
    malysh
) is attached

assert malysh.cognitive_flow is attached

assert (
    malysh.internal_organs["legacy"]
    is legacy
)

assert (
    malysh.internal_organs[
        "cognitive_flow"
    ]
    is attached
)

assert (
    malysh.organ_registry[
        "cognitive_flow"
    ]["subject_count"]
    == 1
)

print("[PASS] import")
print("[PASS] integration adapter")
print("[PASS] one controller instance")
print("[PASS] legacy reference preserved")
PY

# ------------------------------------------------------------
# 11. FINAL REPORT
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
echo "Backup     : $BACKUP"

echo
echo "Architecture:"
echo "K -> R -> W -> J -> A/rho -> Phi -> O"

echo
echo "Branches:"
echo "primary + possible + negative + unresolved"

echo
echo "Committed files:"
git diff-tree \
    --no-commit-id \
    --name-only \
    -r \
    "$AFTER"

echo
echo "[PASS] one unified Malysh"
echo "[PASS] negative results preserved"
echo "[PASS] attention normalized"
echo "[PASS] relation references checked"
echo "[PASS] append-only WAL"
echo "[PASS] observers separated from execution"
echo "[PASS] legacy reference preserved"
echo "[PASS] exact four-file Git commit"

echo
echo "Working tree:"
git status --short

echo "============================================================"
