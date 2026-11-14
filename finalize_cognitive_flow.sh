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
echo "MALYSH: FINALIZE COGNITIVE FLOW"
echo "============================================================"

# ============================================================
# 1. SAFETY
# ============================================================

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
    echo "STOP: Git index already contains staged files:"
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
        echo "STOP: missing file: $f"
        exit 1
    }
done

echo "[PASS] HEAD unchanged"
echo "[PASS] safety tag exists"
echo "[PASS] Git index empty"
echo "[PASS] generated files exist"

# ============================================================
# 2. ARCHIVE CURRENT BROKEN MODULE
# ============================================================

STAMP="$(date +%Y%m%d_%H%M%S)"

BACKUP="runtime/cognitive_flow/cognitive_flow.pre_final_fix.${STAMP}.py"

mkdir -p runtime/cognitive_flow

cp "$MODULE" "$BACKUP"

echo "[PASS] backup:"
echo "       $BACKUP"

# ============================================================
# 3. REPAIR EXACTLY ONE BROKEN LINE
# ============================================================

python - "$MODULE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])

text = path.read_text(
    encoding="utf-8"
)

broken = (
    "    def _frontier(self) -> "
    "setfrontier: set[str] = set()\n"
)

fixed = (
    "    def _frontier(self) -> set\n"
    "        frontier: set[str] = set()\n"
)

count = text.count(broken)

if count != 1:
    print(
        "STOP: expected exactly one broken signature; "
        f"found {count}",
        file=sys.stderr,
    )
    sys.exit(1)

text = text.replace(
    broken,
    fixed,
    1,
)

path.write_text(
    text,
    encoding="utf-8",
)

print("[PASS] exact signature repaired")
PY

# ============================================================
# 4. INSPECT FUNCTION
# ============================================================

echo
echo "=== _frontier AFTER FIX ==="

grep -n -A15 -B2 \
    'def _frontier' \
    "$MODULE"

echo

if grep -n \
    'setfrontier' \
    "$MODULE"
then
    echo "STOP: corrupted token remains"
    exit 1
fi

echo "[PASS] corrupted token absent"

# ============================================================
# 5. COMPILE
# ============================================================

python -m py_compile \
    "$MODULE" \
    "$INTEGRATION" \
    "$TEST"

echo "[PASS] Python syntax"

python -m json.tool \
    "$CONFIG" \
    >/dev/null

echo "[PASS] JSON configuration"

# ============================================================
# 6. FUNCTIONAL TESTS
# ============================================================

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python "$TEST"

echo "[PASS] functional tests"

# ============================================================
# 7. INDEPENDENT CORE TEST
# ============================================================

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

definitions = (
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
)

for state_id, kind in definitions:
    c.add_state(
        state_id=state_id,
        content=state_id,
        kind=kind,
        source="smoke",
        confidence=0.8,
    )

relations = (
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
)

for rid, target, kind, sign in relations:
    c.add_relation(
        relation_id=rid,
        sources=["input"],
        target=target,
        kind=kind,
        sign=sign,
        confidence=1.0,
        evidence=1.0,
        priority=1.0,
    )

r = c.cycle_once()

assert r.primary.selected_id == "primary"
assert r.possible.selected_id == "possible"
assert r.negative.selected_id == "negative"
assert r.unresolved.selected_id == "unresolved"

assert r.invariant_failures == ()

assert abs(
    sum(r.attention.values())
    - 1.0
) < 1e-12

assert all(
    value >= 0.0
    for value in r.attention.values()
)

assert any(
    relation.sign < 0
    for relation in c.relations
)

wal_before = c.wal

c.cycle_once()

assert c.wal[:len(wal_before)] == wal_before

print("[PASS] primary   :", r.primary.selected_id)
print("[PASS] possible  :", r.possible.selected_id)
print("[PASS] negative  :", r.negative.selected_id)
print("[PASS] unresolved:", r.unresolved.selected_id)

print(
    "[PASS] attention :",
    sum(r.attention.values())
)

print("[PASS] negative relation preserved")
print("[PASS] WAL append-only")
PY

echo "[PASS] independent smoke test"

# ============================================================
# 8. STAGE EXACTLY FOUR FILES
# ============================================================

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

echo "[PASS] exact staged file set"

# ============================================================
# 9. SHOW WHAT WILL BE COMMITTED
# ============================================================

echo
echo "=== COMMIT CONTENT ==="

git diff --cached --stat
git diff --cached --check

echo "[PASS] staged diff check"

# ============================================================
# 10. COMMIT
# ============================================================

git commit \
    -m "architecture: add cognitive flow controller"

AFTER="$(git rev-parse HEAD)"

echo
echo "[PASS] commit created:"
echo "       $AFTER"

# ============================================================
# 11. VERIFY EXACT COMMIT
# ============================================================

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

# ============================================================
# 12. POST-COMMIT FUNCTIONAL TEST
# ============================================================

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python "$TEST"

echo "[PASS] post-commit tests"

# ============================================================
# 13. IMPORT TEST
# ============================================================

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python - <<'PY'
from malysh_system.cognitive_flow import (
    CognitiveFlowController,
    create_default_controller,
)

from malysh_system.cognitive_flow_integration import (
    attach_cognitive_flow,
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

m = Malysh()

legacy_before = (
    m.internal_organs["legacy"]
)

attached = attach_cognitive_flow(m)

assert attached is m.cognitive_flow

assert (
    m.internal_organs["legacy"]
    is legacy_before
)

assert (
    m.internal_organs[
        "cognitive_flow"
    ]
    is attached
)

print("[PASS] import")
print("[PASS] integration")
print("[PASS] legacy reference preserved")
print("[PASS] one controller instance")
PY

# ============================================================
# 14. FINAL REPORT
# ============================================================

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
echo "[PASS] one unified Malysh"
echo "[PASS] negative results preserved"
echo "[PASS] attention normalized"
echo "[PASS] relation references checked"
echo "[PASS] WAL append-only"
echo "[PASS] observers do not execute actions"
echo "[PASS] legacy reference preserved"
echo "[PASS] Git safety tag preserved"
echo "[PASS] exact four-file commit"

echo
echo "Committed files:"

git diff-tree \
    --no-commit-id \
    --name-only \
    -r \
    "$AFTER"

echo
echo "Working tree:"
git status --short

echo "============================================================"
