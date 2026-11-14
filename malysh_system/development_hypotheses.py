"""
Development hypothesis exchange for ONE Malysh.

The organ preserves Malysh's independent hypothesis before external review.

Contract:

    Malysh proposes
        -> immutable hypothesis record
        -> external review
        -> proposed experiment
        -> result becomes experience

This module never:

* modifies canonical source code;
* executes a proposed experiment;
* grants decision authority to Malysh or the reviewer;
* treats an external review as final truth.

Storage is append-only JSONL with a SHA-256 hash chain.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
import json
import uuid


SCHEMA = "malysh.development-hypothesis.v1"
REVIEW_SCHEMA = "malysh.external-hypothesis-review.v1"
SUBJECT = "Malysh"

REQUIRED_BRANCHES = (
    "primary",
    "possible",
    "negative",
    "unresolved",
)

ALLOWED_REVIEW_STATES = {
    "supported",
    "partially_supported",
    "possible",
    "contradicted",
    "insufficient_evidence",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _digest(value: Any) -> str:
    return sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_mapping(
    name: str,
    value: Any,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(
            f"{name} must be a mapping"
        )

    return deepcopy(dict(value))


def _require_nonempty_text(
    name: str,
    value: Any,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{name} must be text"
        )

    cleaned = value.strip()

    if not cleaned:
        raise ValueError(
            f"{name} must not be empty"
        )

    return cleaned


def _read_last_hash(path: Path) -> str | None:
    if not path.exists():
        return None

    last_hash = None

    with path.open(
        "r",
        encoding="utf-8",
    ) as source:
        for line_number, line in enumerate(
            source,
            1,
        ):
            stripped = line.strip()

            if not stripped:
                continue

            try:
                event = json.loads(stripped)
            except json.JSONDecodeError as error:
                raise ValueError(
                    "damaged hypothesis WAL line "
                    f"{line_number}: {error}"
                ) from error

            last_hash = event.get("event_hash")

    return last_hash


def _append_event(
    path: Path,
    event_type: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    previous_hash = _read_last_hash(path)

    event = {
        "event_schema":
            "malysh.hypothesis-wal-event.v1",

        "event_type":
            event_type,

        "timestamp":
            _utc_now(),

        "previous_hash":
            previous_hash,

        "payload":
            deepcopy(dict(payload)),
    }

    event["event_hash"] = _digest(event)

    with path.open(
        "a",
        encoding="utf-8",
    ) as target:
        target.write(
            json.dumps(
                event,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )

        target.flush()

    return deepcopy(event)


@dataclass(frozen=True)
class HypothesisRecord:
    schema: str
    hypothesis_id: str
    subject: str
    created_at: str
    claim: str
    rationale: list[str]
    branches: dict[str, Any]
    evidence: list[dict[str, Any]]
    proposed_experiment: dict[str, Any]
    invariants: list[str]
    provenance: dict[str, Any]
    state: str
    decision_authority: bool
    state_commit: bool
    automatic_execution: bool
    record_hash: str

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(asdict(self))


def build_hypothesis(
    *,
    claim: str,
    rationale: list[str],
    primary: Mapping[str, Any],
    possible: Mapping[str, Any],
    negative: Mapping[str, Any],
    unresolved: Mapping[str, Any],
    evidence: list[Mapping[str, Any]],
    proposed_experiment: Mapping[str, Any],
    invariants: list[str],
    provenance: Mapping[str, Any],
    hypothesis_id: str | None = None,
) -> HypothesisRecord:
    clean_claim = _require_nonempty_text(
        "claim",
        claim,
    )

    if not isinstance(rationale, list):
        raise TypeError(
            "rationale must be a list"
        )

    clean_rationale = [
        _require_nonempty_text(
            "rationale item",
            item,
        )
        for item in rationale
    ]

    if not clean_rationale:
        raise ValueError(
            "rationale must not be empty"
        )

    if not isinstance(evidence, list):
        raise TypeError(
            "evidence must be a list"
        )

    clean_evidence = [
        _require_mapping(
            "evidence item",
            item,
        )
        for item in evidence
    ]

    if not isinstance(invariants, list):
        raise TypeError(
            "invariants must be a list"
        )

    clean_invariants = [
        _require_nonempty_text(
            "invariant",
            item,
        )
        for item in invariants
    ]

    if not clean_invariants:
        raise ValueError(
            "at least one invariant is required"
        )

    branches = {
        "primary":
            _require_mapping(
                "primary",
                primary,
            ),

        "possible":
            _require_mapping(
                "possible",
                possible,
            ),

        "negative":
            _require_mapping(
                "negative",
                negative,
            ),

        "unresolved":
            _require_mapping(
                "unresolved",
                unresolved,
            ),
    }

    record_without_hash = {
        "schema":
            SCHEMA,

        "hypothesis_id":
            (
                hypothesis_id
                or
                str(uuid.uuid4())
            ),

        "subject":
            SUBJECT,

        "created_at":
            _utc_now(),

        "claim":
            clean_claim,

        "rationale":
            clean_rationale,

        "branches":
            branches,

        "evidence":
            clean_evidence,

        "proposed_experiment":
            _require_mapping(
                "proposed_experiment",
                proposed_experiment,
            ),

        "invariants":
            clean_invariants,

        "provenance":
            _require_mapping(
                "provenance",
                provenance,
            ),

        "state":
            "pending_external_review",

        "decision_authority":
            False,

        "state_commit":
            False,

        "automatic_execution":
            False,
    }

    return HypothesisRecord(
        **record_without_hash,
        record_hash=_digest(
            record_without_hash
        ),
    )


def validate_hypothesis(
    record: Mapping[str, Any],
) -> dict[str, bool]:
    value = _require_mapping(
        "record",
        record,
    )

    branches = value.get(
        "branches",
        {},
    )

    checks = {
        "correct_schema":
            value.get("schema")
            ==
            SCHEMA,

        "one_subject":
            value.get("subject")
            ==
            SUBJECT,

        "claim_present":
            isinstance(
                value.get("claim"),
                str,
            )
            and
            bool(
                value.get(
                    "claim",
                    "",
                ).strip()
            ),

        "all_branches_present":
            isinstance(branches, Mapping)
            and
            all(
                name in branches
                for name in REQUIRED_BRANCHES
            ),

        "pending_review":
            value.get("state")
            ==
            "pending_external_review",

        "no_decision_authority":
            value.get(
                "decision_authority"
            )
            is False,

        "no_state_commit":
            value.get(
                "state_commit"
            )
            is False,

        "no_automatic_execution":
            value.get(
                "automatic_execution"
            )
            is False,

        "experiment_present":
            isinstance(
                value.get(
                    "proposed_experiment"
                ),
                Mapping,
            ),

        "invariants_present":
            isinstance(
                value.get("invariants"),
                list,
            )
            and
            bool(
                value.get("invariants")
            ),
    }

    provided_hash = value.get(
        "record_hash"
    )

    hash_source = deepcopy(value)
    hash_source.pop(
        "record_hash",
        None,
    )

    checks["hash_valid"] = (
        isinstance(
            provided_hash,
            str,
        )
        and
        provided_hash
        ==
        _digest(hash_source)
    )

    return checks


def publish_hypothesis(
    record: HypothesisRecord,
    storage_root: str | Path,
) -> dict[str, Any]:
    root = Path(storage_root)
    payload = record.to_dict()
    checks = validate_hypothesis(payload)

    if not all(checks.values()):
        failed = [
            name
            for name, passed
            in checks.items()
            if not passed
        ]

        raise ValueError(
            "hypothesis invariant failed: "
            + ", ".join(failed)
        )

    hypotheses = (
        root
        / "hypotheses"
    )

    hypotheses.mkdir(
        parents=True,
        exist_ok=True,
    )

    hypothesis_path = (
        hypotheses
        /
        f"{record.hypothesis_id}.json"
    )

    if hypothesis_path.exists():
        raise FileExistsError(
            "hypothesis already published: "
            f"{record.hypothesis_id}"
        )

    hypothesis_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    event = _append_event(
        root / "hypothesis.wal.jsonl",
        "hypothesis_published",
        payload,
    )

    return {
        "schema":
            "malysh.hypothesis-publication.v1",

        "status":
            "published",

        "hypothesis_id":
            record.hypothesis_id,

        "hypothesis_path":
            str(hypothesis_path),

        "wal_event_hash":
            event["event_hash"],

        "invariant_ok":
            True,

        "decision_authority":
            False,

        "state_commit":
            False,

        "automatic_execution":
            False,
    }


def build_external_review(
    *,
    hypothesis: Mapping[str, Any],
    reviewer: str,
    assessment: str,
    reasoning: list[str],
    supported_points: list[str],
    challenged_points: list[str],
    required_tests: list[str],
    reviewer_hypothesis: Mapping[str, Any],
) -> dict[str, Any]:
    original = _require_mapping(
        "hypothesis",
        hypothesis,
    )

    checks = validate_hypothesis(original)

    if not all(checks.values()):
        raise ValueError(
            "cannot review invalid hypothesis"
        )

    clean_assessment = _require_nonempty_text(
        "assessment",
        assessment,
    )

    if clean_assessment not in ALLOWED_REVIEW_STATES:
        raise ValueError(
            "unsupported assessment: "
            f"{clean_assessment}"
        )

    review = {
        "schema":
            REVIEW_SCHEMA,

        "review_id":
            str(uuid.uuid4()),

        "hypothesis_id":
            original["hypothesis_id"],

        "reviewed_at":
            _utc_now(),

        "reviewer":
            _require_nonempty_text(
                "reviewer",
                reviewer,
            ),

        "assessment":
            clean_assessment,

        "reasoning": [
            _require_nonempty_text(
                "reasoning item",
                item,
            )
            for item in reasoning
        ],

        "supported_points": [
            _require_nonempty_text(
                "supported point",
                item,
            )
            for item in supported_points
        ],

        "challenged_points": [
            _require_nonempty_text(
                "challenged point",
                item,
            )
            for item in challenged_points
        ],

        "required_tests": [
            _require_nonempty_text(
                "required test",
                item,
            )
            for item in required_tests
        ],

        "reviewer_hypothesis":
            _require_mapping(
                "reviewer_hypothesis",
                reviewer_hypothesis,
            ),

        "final_truth":
            False,

        "decision_authority":
            False,

        "state_commit":
            False,

        "automatic_execution":
            False,
    }

    review["review_hash"] = _digest(
        review
    )

    return review


def publish_external_review(
    review: Mapping[str, Any],
    storage_root: str | Path,
) -> dict[str, Any]:
    value = _require_mapping(
        "review",
        review,
    )

    if value.get("schema") != REVIEW_SCHEMA:
        raise ValueError(
            "invalid review schema"
        )

    if value.get("assessment") not in ALLOWED_REVIEW_STATES:
        raise ValueError(
            "invalid review assessment"
        )

    if value.get("decision_authority") is not False:
        raise ValueError(
            "reviewer must not have decision authority"
        )

    if value.get("state_commit") is not False:
        raise ValueError(
            "review must not commit state"
        )

    root = Path(storage_root)

    review_dir = (
        root
        /
        "reviews"
        /
        value["hypothesis_id"]
    )

    review_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    review_path = (
        review_dir
        /
        f"{value['review_id']}.json"
    )

    review_path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    event = _append_event(
        root / "hypothesis.wal.jsonl",
        "external_review_published",
        value,
    )

    return {
        "schema":
            "malysh.external-review-publication.v1",

        "status":
            "published",

        "review_path":
            str(review_path),

        "wal_event_hash":
            event["event_hash"],

        "invariant_ok":
            True,

        "decision_authority":
            False,

        "state_commit":
            False,
    }


def create_review_packet(
    hypothesis: Mapping[str, Any],
) -> str:
    value = _require_mapping(
        "hypothesis",
        hypothesis,
    )

    checks = validate_hypothesis(value)

    if not all(checks.values()):
        raise ValueError(
            "cannot export invalid hypothesis"
        )

    return (
        "MALYSH HYPOTHESIS REVIEW PACKET\n"
        "================================\n"
        f"Hypothesis ID: {value['hypothesis_id']}\n"
        f"Subject: {value['subject']}\n"
        f"Claim: {value['claim']}\n\n"
        "The hypothesis below is Malysh's independent proposal.\n"
        "Review it critically. Do not treat either Malysh's claim\n"
        "or the review as final truth. Propose functional tests.\n\n"
        + json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


def inspect_storage(
    storage_root: str | Path,
) -> dict[str, Any]:
    root = Path(storage_root)

    hypotheses = list(
        (root / "hypotheses").glob(
            "*.json"
        )
    ) if (root / "hypotheses").exists() else []

    reviews = list(
        (root / "reviews").glob(
            "*/*.json"
        )
    ) if (root / "reviews").exists() else []

    wal = root / "hypothesis.wal.jsonl"

    events = 0

    if wal.exists():
        with wal.open(
            "r",
            encoding="utf-8",
        ) as source:
            events = sum(
                1
                for line in source
                if line.strip()
            )

    return {
        "schema":
            "malysh.hypothesis-storage-inspection.v1",

        "hypotheses":
            len(hypotheses),

        "reviews":
            len(reviews),

        "wal_events":
            events,

        "canonical_core_modified":
            False,

        "automatic_execution":
            False,
    }
