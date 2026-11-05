from copy import deepcopy

from malysh_system.historical_swarm_omni import (
    HistoricalSwarmNode,
    calculate_hmp_layers,
    compute_historical_omni,
    integrate_historical_swarm_omni,
    second_order_resonance,
)
from malysh_system.swarm_omni import (
    integrate_swarm_omni,
)
from malysh_system.unified_mind import MindState


HISTORY = [
    [5, 12, 23, 34, 42, 48],
    [3, 12, 18, 25, 34, 45],
    [5, 11, 23, 30, 42, 49],
]

CANDIDATE = [
    6,
    14,
    21,
    32,
    41,
    49,
]


def build_mind():
    mind = MindState()

    mind.canonical = {
        "a3": 2,
        "b4": 3,
        "c5": 4,
    }

    mind.observe(
        "KMBP",
        {"verified": True},
    )

    mind.observe(
        "FullReflections",
        {"verified": True},
    )

    mind.observe(
        "HumanLayer",
        {"verified": True},
    )

    mind.set_human(
        {
            "logical": {
                "hypothesis": "main",
            },
            "possible": [
                {
                    "hypothesis":
                        "possible",
                }
            ],
        }
    )

    return mind


def test_historical_swarm_transport_contract():
    node = HistoricalSwarmNode(
        "Malysh_Alpha",
        "Scout",
    )

    payload = {
        "state_id":
            "Harmonic_sync",

        "metrics": {
            "expectation": 0.2,
            "variance": 0.05,
            "entropy": 1.5,
        },

        "temperature":
            1.1,
    }

    message = node.send_message(
        "Broadcast",
        "PROPOSAL",
        payload,
    )

    assert message["sender"] == "Malysh_Alpha"
    assert message["receiver"] == "Broadcast"
    assert message["msg_type"] == "PROPOSAL"
    assert message["payload"] == payload


def test_historical_omni_hmp_is_functional():
    H, M, P = calculate_hmp_layers(
        HISTORY,
        49,
    )

    assert set(H) == set(range(1, 50))
    assert set(M) == set(range(1, 50))
    assert set(P) == set(range(1, 50))

    assert abs(sum(H.values()) - 1.0) < 1e-12

    resonance = second_order_resonance(
        CANDIDATE,
        H,
        M,
        P,
    )

    assert isinstance(resonance, float)


def test_historical_omni_is_deterministic():
    mind = build_mind()
    snapshot = mind.snapshot()

    first = compute_historical_omni(
        snapshot,
        HISTORY,
        CANDIDATE,
    )

    second = compute_historical_omni(
        snapshot,
        HISTORY,
        CANDIDATE,
    )

    assert first == second

    assert first["randomness_used"] is False
    assert first["winner"] is None
    assert first["weight_mutation"] is False
    assert first["error_memory_mutation"] is False


def test_current_and_historical_organs_coexist():
    mind = build_mind()

    current_swarm, current_omni = (
        integrate_swarm_omni(
            mind
        )
    )

    current_swarm_copy = deepcopy(
        mind.observations["Swarm"]
    )

    current_omni_copy = deepcopy(
        mind.observations["Omni"]
    )

    historical_swarm, historical_omni = (
        integrate_historical_swarm_omni(
            mind,
            HISTORY,
            CANDIDATE,
        )
    )

    snapshot = mind.snapshot()

    assert current_swarm.status == "ok"
    assert current_omni.status == "ok"

    assert historical_swarm.status == "ok"
    assert historical_omni.status == "ok"

    assert (
        snapshot["observations"]["Swarm"]
        ==
        current_swarm_copy
    )

    assert (
        snapshot["observations"]["Omni"]
        ==
        current_omni_copy
    )

    assert (
        "HistoricalSwarm"
        in snapshot["observations"]
    )

    assert (
        "HistoricalOmni"
        in snapshot["observations"]
    )


def test_historical_organs_cannot_modify_protected_state():
    mind = build_mind()

    integrate_swarm_omni(
        mind
    )

    before = mind.snapshot()

    integrate_historical_swarm_omni(
        mind,
        HISTORY,
        CANDIDATE,
    )

    after = mind.snapshot()

    for field in (
        "subject",
        "canonical",
        "experience",
        "human",
        "main",
        "possible",
    ):
        assert after[field] == before[field]


def test_heritage_provenance_is_explicit():
    mind = build_mind()

    integrate_swarm_omni(
        mind
    )

    swarm, omni = (
        integrate_historical_swarm_omni(
            mind,
            HISTORY,
            CANDIDATE,
        )
    )

    assert (
        swarm.data["heritage"]["identity"]
        ==
        "recovered_source"
    )

    assert (
        omni.data["heritage"]["identity"]
        ==
        "recovered_source"
    )

    assert (
        swarm.data["heritage"]["repository"]
        ==
        "ntlav2624-jpg/malysh"
    )

    assert (
        omni.data["heritage"]["omni_file"]
        ==
        "malysh_omni_daemon.py"
    )
