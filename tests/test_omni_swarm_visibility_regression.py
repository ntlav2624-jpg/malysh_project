from copy import deepcopy

from malysh_system.unified_mind import MindState
from malysh_system.swarm_omni import (
    run_swarm,
    run_omni,
)


def _baseline_mind():
    mind = MindState()

    mind.canonical = {
        "a3": 2,
        "b4": 3,
        "c5": 4,
    }

    for name in (
        "O3",
        "O4",
        "O5",
        "KMBP",
        "HumanLayer",
    ):
        mind.observe(
            name,
            {
                "organ": name,
                "verified": True,
            },
        )

    return mind


def test_omni_distinguishes_payload_from_published_visibility():
    mind = _baseline_mind()

    baseline = mind.snapshot()
    baseline_before = deepcopy(baseline)

    swarm_result = run_swarm(baseline)

    assert swarm_result.status == "ok"
    assert swarm_result.data["invariant_ok"] is True

    # Direct payload proves that Omni really receives a valid
    # Swarm result.
    omni_without_publication = run_omni(
        baseline,
        swarm_result.data,
    )

    assert omni_without_publication.status == "ok"

    assert (
        omni_without_publication.data["swarm_seen"]
        is True
    )

    assert (
        omni_without_publication.data["swarm_invariant_ok"]
        is True
    )

    # But payload validity and publication in the shared MindState
    # are different facts.  Swarm has not been published here.
    assert (
        "Swarm"
        not in
        omni_without_publication.data["visible_layers"]
    )

    # Now publish exactly the same valid Swarm result.
    published = deepcopy(baseline)

    published.setdefault(
        "observations",
        {},
    )["Swarm"] = deepcopy(
        swarm_result.data
    )

    omni_with_publication = run_omni(
        published,
        swarm_result.data,
    )

    assert omni_with_publication.status == "ok"

    assert (
        "Swarm"
        in
        omni_with_publication.data["visible_layers"]
    )

    # Pure observer functions must not mutate the original snapshot.
    assert baseline == baseline_before
