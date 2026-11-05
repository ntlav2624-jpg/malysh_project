import json
from pathlib import Path
import subprocess
import sys


ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

RUNNER = (
    ROOT
    / "scripts"
    / "run_all_contours.py"
)


def run_runner(
    tmp_path,
    sequence="6,14,26,30,19,5",
    o345_n="59",
):
    output = (
        tmp_path
        / "runtime.json"
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--sequence",
            sequence,
            "--o345-n",
            o345_n,
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    return (
        completed,
        output,
    )


def test_all_contours_operational(tmp_path):
    completed, output = run_runner(
        tmp_path
    )

    assert completed.returncode == 0, (
        completed.stdout
        + "\n"
        + completed.stderr
    )

    assert output.is_file()

    record = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert (
        record["schema"]
        ==
        "malysh.operational-run.v1"
    )

    assert record["subject"] == "Malysh"

    assert record["verification"]["ok"] is True

    assert all(
        record["verification"][
            "organ_checks"
        ].values()
    )

    assert all(
        record["verification"][
            "safety_checks"
        ].values()
    )

    assert all(
        record["verification"][
            "cycle_invariants"
        ].values()
    )


def test_every_required_organ_is_reported(tmp_path):
    completed, output = run_runner(
        tmp_path
    )

    assert completed.returncode == 0

    record = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert set(record["organs"]) == {
        "O345",
        "O3",
        "O4",
        "O5",
        "KMBP",
        "FullReflections",
        "HumanLayer",
        "Swarm",
        "Omni",
        "InterLayer",
        "JointChoice",
    }

    assert all(
        status == "ok"
        for status in
        record["organs"].values()
    )


def test_joint_choice_remains_non_executing(tmp_path):
    completed, output = run_runner(
        tmp_path
    )

    assert completed.returncode == 0

    record = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    joint = record["joint_choice"]

    assert joint["winner"] is None

    assert (
        joint["execution_authorized"]
        is False
    )

    assert (
        joint["transaction_authorized"]
        is False
    )


def test_custom_inputs_are_preserved(tmp_path):
    completed, output = run_runner(
        tmp_path,
        sequence="1,2,3,4",
        o345_n="17",
    )

    assert completed.returncode == 0

    record = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert record["input"] == [
        1,
        2,
        3,
        4,
    ]

    assert record["o345_n"] == 17


def test_runtime_record_has_result_digest(tmp_path):
    completed, output = run_runner(
        tmp_path
    )

    assert completed.returncode == 0

    record = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    digest = record["result_digest"]

    assert isinstance(digest, str)
    assert len(digest) == 64

    int(digest, 16)
