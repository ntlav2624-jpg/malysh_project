from copy import deepcopy

from malysh_system.thinking_cycle import (
    run_thinking_cycle,
)
from malysh_system.unified_mind import MindState


def test_joint_choice_inside_one_malysh(tmp_path):
    result = run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        o345_n=59,
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
    )

    joint = result["joint_choice"]

    assert result["subject"] == "Malysh"
    assert joint["status"] == "ok"
    assert joint["data"]["invariant_ok"] is True

    assert set(joint["data"]["candidates"]) == {
        "main",
        "possible",
    }

    assert "JointChoice" in result["mind"]["reflections"]
    assert all(result["invariants"].values())


def test_disagreement_is_deferred(tmp_path):
    result = run_thinking_cycle(
        data=[6, 14, 26, 30, 19, 5],
        o345_n=59,
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
    )

    joint = result["joint_choice"]["data"]

    assert joint["debate_state"] == "DISAGREEMENT"
    assert joint["deliberation"]["state"] == "DEFERRED"

    assert (
        joint["deliberation"]["selected_for_reasoning"]
        is None
    )

    assert joint["deliberation"]["winner"] is None

    assert (
        joint["deliberation"]["execution_authorized"]
        is False
    )


def test_both_branches_survive(tmp_path):
    old_result = {
        "old_engine": True
    }

    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=17,
        old_result=old_result,
        unresolved={
            "status": "hypothesis",
            "text": "возможно",
            "revisable": True,
        },
        root=tmp_path,
    )

    candidates = (
        result["joint_choice"]
        ["data"]
        ["candidates"]
    )

    assert (
        candidates["main"]["result"]
        ==
        old_result
    )

    assert candidates["main"]["may_be_wrong"] is True
    assert candidates["possible"]["may_be_wrong"] is True
    assert candidates["possible"]["revisable"] is True


def test_joint_choice_cannot_mutate_thought(tmp_path):
    mind = MindState()

    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=47,
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
        mind=mind,
    )

    canonical = deepcopy(
        result["o345"]["canonical"]
    )

    joint = result["joint_choice"]["data"]

    assert mind.canonical == canonical
    assert result["mind"]["canonical"] == canonical

    assert joint["affects_main_answer"] is False
    assert joint["affects_possible_branch"] is False
    assert joint["affects_execution"] is False


def test_evidence_is_not_voting(tmp_path):
    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        o345_n=17,
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
    )

    joint = result["joint_choice"]["data"]

    assert joint["support"]

    assert all(
        item["vote_weight"] is None
        for item in joint["support"]
    )

    assert (
        joint["deliberation"]["majority_vote_used"]
        is False
    )

    assert (
        joint["deliberation"]["vote_count_used"]
        is False
    )


def test_joint_choice_has_no_transaction_power(tmp_path):
    result = run_thinking_cycle(
        data=[1, 2, 3, 4],
        old_result={"historical": True},
        unresolved="возможно",
        root=tmp_path,
    )

    joint = result["joint_choice"]["data"]

    assert joint["decision_authority"] is False
    assert joint["automatic_execution"] is False
    assert joint["state_write"] is False
    assert joint["state_commit"] is False
    assert joint["canonical_write"] is False
    assert joint["transaction_commit"] is False

    assert (
        joint["deliberation"]["transaction_authorized"]
        is False
    )
