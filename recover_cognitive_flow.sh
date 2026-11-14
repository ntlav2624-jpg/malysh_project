#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/malysh_project"
cd "$ROOT"

MODULE="malysh_system/cognitive_flow.py"
INTEGRATION="malysh_system/cognitive_flow_integration.py"
TEST="tests/test_cognitive_flow.py"
CONFIG="config/cognitive_flow.json"

EXPECTED_TAG="pre-cognitive-flow-20261110_013919"
EXPECTED_BEFORE="744cfcb14a1fefa569808dbbaa099beb45625ac5"

echo "============================================================"
echo "MALYSH: RECOVER COGNITIVE FLOW INSTALLATION"
echo "============================================================"

git rev-parse --is-inside-work-tree >/dev/null

CURRENT_HEAD="$(git rev-parse HEAD)"

if [ "$CURRENT_HEAD" != "$EXPECTED_BEFORE" ]; then
    echo "STOP: HEAD changed after the failed installation."
    echo "Expected: $EXPECTED_BEFORE"
    echo "Actual  : $CURRENT_HEAD"
    echo "No files changed."
    exit 1
fi

if ! git rev-parse "$EXPECTED_TAG" >/dev/null 2>&1; then
    echo "STOP: safety tag not found: $EXPECTED_TAG"
    echo "No files changed."
    exit 1
fi

if [ -n "$(git diff --cached --name-only)" ]; then
    echo "STOP: Git index already contains staged files:"
    git diff --cached --name-only
    echo "No files changed."
    exit 1
fi

for file in \
    "$MODULE" \
    "$INTEGRATION" \
    "$TEST" \
    "$CONFIG"
do
    if [ ! -f "$file" ]; then
        echo "STOP: expected generated file not found: $file"
        exit 1
    fi
done

echo "[PASS] HEAD unchanged"
echo "[PASS] safety tag exists"
echo "[PASS] generated files exist"
echo "[PASS] Git index is empty"

# ------------------------------------------------------------
# 1. BACK UP THE GENERATED BUT BROKEN MODULE
# ------------------------------------------------------------

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="runtime/cognitive_flow/cognitive_flow.broken.${STAMP}.py"

mkdir -p runtime/cognitive_flow

cp "$MODULE" "$BACKUP"

echo "[PASS] broken generated module archived:"
echo "       $BACKUP"

# ------------------------------------------------------------
# 2. REPAIR ONLY THE BROKEN _frontier FUNCTION
# ------------------------------------------------------------

python - "$MODULE" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

pattern = re.compile(
    r'''
    ^[ ]{4}def[ ]+_frontier$$self$$[^\n]*\n
    (?P<body>
        (?:
            ^[ ]{8,}.*\n
            |
            ^[ \t]*\n
        )*
    )
    (?=^[ ]{4}def[ ]+_propagate_attention\()
    ''',
    re.MULTILINE | re.VERBOSE,
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

new_text, count = pattern.subn(
    replacement,
    text,
    count=1,
)

if count != 1:
    print(
        "STOP: could not identify exactly one "
        "broken _frontier function",
        file=sys.stderr,
    )

    print(
        "Matches found:",
        count,
        file=sys.stderr,
    )

    sys.exit(1)

path.write_text(
    new_text,
    encoding="utf-8",
)

print("[PASS] repaired _frontier function")
PY

# ------------------------------------------------------------
# 3. SHOW THE REPAIRED REGION
# ------------------------------------------------------------

echo
echo "=== REPAIRED REGION ==="

python - "$MODULE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
lines = path.read_text(
    encoding="utf-8"
).splitlines()

start = None

for index, line in enumerate(lines):
    if line.startswith(
        "    def _frontier("
    ):
        start = index
        break

if start is None:
    raise SystemExit(
        "STOP: repaired function not found"
    )

end = min(
    len(lines),
    start + 24,
)

for number in range(start, end):
    print(
        "%5d  %s"
        % (
            number + 1,
            lines[number],
        )
    )
PY

# ------------------------------------------------------------
# 4. CHECK FOR THE KNOWN CORRUPTED TOKEN
# ------------------------------------------------------------

if grep -n \
    'setfrontier' \
    "$MODULE"
then
    echo "STOP: corrupted token still exists."
    exit 1
fi

echo "[PASS] corrupted token absent"

# ------------------------------------------------------------
# 5. PYTHON AND JSON VALIDATION
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
# 6. FUNCTIONAL TESTS
# ------------------------------------------------------------

PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
python "$TEST"

echo "[PASS] functional tests"

# ------------------------------------------------------------
# 7. DIRECT SMOKE TEST
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
    content="real input",
    kind=ThoughtKind.OBSERVATION,
    source="perception",
    confidence=1.0,
    initial_attention=1.0,
    active=True,
)

states = (
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

for state_id, kind in states:
    controller.add_state(
        state_id=state_id,
        content=state_id,
        kind=kind,
        source="smoke",
        confidence=0.8,
    )

relations = (
    (
        "r-primary",
        "primary",
        RelationKind.SUPPORTS,
        1,
    ),
    (
        "r-possible",
        "possible",
        RelationKind.SUGGESTS,
        1,
    ),
    (
        "r-negative",
        "negative",
        RelationKind.CONTRADICTS,
        -1,
    ),
    (
        "r-unresolved",
        "unresolved",
        RelationKind.REQUIRES,
        0,
    ),
)

for relation_id, target, kind, sign in relations:
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
assert not result.execution_allowed

attention_sum = sum(
    result.attention.values()
)

assert abs(
    attention_sum - 1.0
) < 1e-12

assert all(
    value >= 0.0
    for value in result.attention.values()
)

negative_relations = [
    relation
    for relation in controller.relations
    if relation.sign < 0
]

assert len(negative_relations) == 1
assert "negative" in controller.states

print(
    "[PASS] input -> relation -> flow -> four branches"
)

print(
    "[PASS] primary   :",
    result.primary.selected_id,
)

print(
    "[PASS] possible  :",
    result.possible.selected_id,
)

print(
    "[PASS] negative  :",
    result.negative.selected_id,
)

print(
    "[PASS] unresolved:",
    result.unresolved.selected_id,
)

print(
    "[PASS] attention :",
    attention_sum,
)

print(
    "[PASS] WAL       :",
    len(controller.wal),
)
PY

echo "[PASS] direct smoke test"

# ------------------------------------------------------------
# 8. STAGE EXACTLY THE FOUR ARCHITECTURE FILES
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
    echo "STOP: staged set is not exact."
    echo
    echo "EXPECTED:"
    printf '%s\n' "$EXPECTED"
    echo
    echo "ACTUAL:"
    printf '%s\n' "$ACTUAL"
    echo
    echo "Commit was not created."
    exit 1
fi

echo "[PASS] exact staged file set"

# ------------------------------------------------------------
# 9. COMMIT
# ------------------------------------------------------------

git commit \
    -m "architecture: add cognitive flow controller"

AFTER="$(git rev-parse HEAD)"

echo "[PASS] commit created: $AFTER"

# ------------------------------------------------------------
# 10. VERIFY EXACT COMMIT CONTENT
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
    echo "STOP: commit contains unexpected files."
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

echo "[PASS] post-commit functional tests"

# ------------------------------------------------------------
# 12. FINAL REPORT
# ------------------------------------------------------------

echo
echo "============================================================"
echo "COGNITIVE FLOW RECOVERED AND INSTALLED"
echo "============================================================"
echo "Root       : $ROOT"
echo "Branch     : $(git branch --show-current)"
echo "Before     : $EXPECTED_BEFORE"
echo "Safety tag : $EXPECTED_TAG"
echo "Commit     : $AFTER"
echo "Broken copy: $BACKUP"
echo
echo "Core:"
echo "K -> R -> W -> J -> A/rho -> Phi -> O"
echo
echo "Branches:"
echo "primary + possible + negative + unresolved"
echo
echo "[PASS] one unified Malysh"
echo "[PASS] negative branch preserved"
echo "[PASS] normalized nonnegative attention"
echo "[PASS] append-only WAL"
echo "[PASS] observer separated from execution"
echo "[PASS] legacy not overwritten"
echo "[PASS] exact Git commit"
echo "============================================================"

echo
echo "Working tree:"
git status --short
