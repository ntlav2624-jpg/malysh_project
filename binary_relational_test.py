#!/usr/bin/env python3

import json
from collections import defaultdict, deque
from copy import deepcopy
from dataclasses import dataclass, asdict
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

WORD_BITS = 4
WORD_MASK = (1 << WORD_BITS) - 1

OUT = Path(
    "experiments/binary_relational"
)

OUT.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# INSTRUCTION SET
# ============================================================

PROGRAM = {
    # Both executions first create exactly the same
    # visible register snapshot R=3.
    0: ("LOAD", 3),

    # Hidden branch depends on FLAG.
    1: ("JZ", 4),

    # FLAG=1 path.
    2: ("ADD", 5),
    3: ("JMP", 5),

    # FLAG=0 path.
    4: ("XOR", 6),

    # Rejoin.
    5: ("STORE", 0),

    # Continue from shared control point.
    6: ("HALT", 0),
}


# ============================================================
# BINARY MACHINE
# ============================================================

@dataclass
class MachineState:
    run_id: str
    step: int
    pc: int
    register: int
    flag: int
    memory: list
    halted: bool


def word(value):
    return int(value) & WORD_MASK


def bits(value):
    return format(
        word(value),
        "0%db" % WORD_BITS,
    )


def visible_snapshot(state):
    """
    Deliberately incomplete observer.

    It sees only the 4-bit general register.
    """

    return {
        "register": state.register,
        "register_bits": bits(
            state.register
        ),
    }


def full_binary_snapshot(state):
    """
    Complete state needed by this toy machine's
    deterministic transition function.
    """

    return {
        "pc": state.pc,
        "register": state.register,
        "register_bits": bits(
            state.register
        ),
        "flag": state.flag,
        "memory": list(
            state.memory
        ),
        "halted": state.halted,
    }


def fetch_instruction(state):
    if state.halted:
        return ("HALT", 0)

    if state.pc not in PROGRAM:
        raise RuntimeError(
            "Invalid PC: %d"
            % state.pc
        )

    return PROGRAM[state.pc]


def execute_one(state):
    before = deepcopy(state)

    opcode, operand = fetch_instruction(
        state
    )

    after = deepcopy(state)
    after.step += 1

    writes = []
    reads = []
    control = []

    if opcode == "LOAD":
        after.register = word(
            operand
        )
        after.pc += 1

        writes.append(
            "register"
        )

    elif opcode == "ADD":
        reads.append(
            "register"
        )

        old = after.register

        after.register = word(
            after.register
            + operand
        )

        after.flag = int(
            old + operand > WORD_MASK
        )

        after.pc += 1

        writes.extend([
            "register",
            "flag",
        ])

    elif opcode == "XOR":
        reads.append(
            "register"
        )

        after.register = word(
            after.register
            ^ operand
        )

        after.pc += 1

        writes.append(
            "register"
        )

    elif opcode == "STORE":
        reads.append(
            "register"
        )

        after.memory[
            operand
        ] = after.register

        after.pc += 1

        writes.append(
            "memory[%d]"
            % operand
        )

    elif opcode == "JZ":
        reads.append(
            "flag"
        )

        if after.flag == 0:
            after.pc = operand

            control.append(
                "branch-taken"
            )
        else:
            after.pc += 1

            control.append(
                "branch-not-taken"
            )

    elif opcode == "JMP":
        after.pc = operand

        control.append(
            "jump"
        )

    elif opcode == "HALT":
        after.halted = True

        control.append(
            "halt"
        )

    else:
        raise RuntimeError(
            "Unknown opcode: %s"
            % opcode
        )

    transition = {
        "source_state": (
            state_key(before)
        ),

        "target_state": (
            state_key(after)
        ),

        "opcode": opcode,
        "operand": operand,

        "reads": reads,
        "writes": writes,
        "control": control,

        "register_delta": (
            after.register
            - before.register
        ),

        "pc_delta": (
            after.pc
            - before.pc
        ),

        "visible_before": (
            visible_snapshot(before)
        ),

        "visible_after": (
            visible_snapshot(after)
        ),
    }

    return after, transition


# ============================================================
# RELATIONAL REPRESENTATION
# ============================================================

def state_key(state):
    return (
        state.pc,
        state.register,
        state.flag,
        tuple(state.memory),
        state.halted,
    )


def relational_state(
    state,
    transition=None,
    history=None,
):
    opcode, operand = (
        fetch_instruction(state)
    )

    allowed_next = []

    if not state.halted:
        simulated, _ = execute_one(
            deepcopy(state)
        )

        allowed_next.append({
            "pc": simulated.pc,
            "register": (
                simulated.register
            ),
            "flag": simulated.flag,
            "halted": simulated.halted,
        })

    if transition is None:
        flow = {
            "opcode": opcode,
            "operand": operand,
            "register_delta": None,
            "pc_delta": None,
        }
    else:
        flow = {
            "opcode": transition[
                "opcode"
            ],
            "operand": transition[
                "operand"
            ],
            "register_delta": (
                transition[
                    "register_delta"
                ]
            ),
            "pc_delta": transition[
                "pc_delta"
            ],
        }

    return {
        # K: current admissible machine state.
        "K_state": {
            "pc": state.pc,
            "register": state.register,
            "flag": state.flag,
            "memory": list(
                state.memory
            ),
            "halted": state.halted,
        },

        # R: relation selected by current instruction.
        "R_relation": {
            "opcode": opcode,
            "operand": operand,
        },

        # W: sign and magnitude of immediate effects.
        "W_effect": {
            "register_direction": (
                0
                if transition is None
                else (
                    1
                    if transition[
                        "register_delta"
                    ] > 0
                    else -1
                    if transition[
                        "register_delta"
                    ] < 0
                    else 0
                )
            ),

            "control_direction": (
                0
                if transition is None
                else (
                    1
                    if transition[
                        "pc_delta"
                    ] > 0
                    else -1
                    if transition[
                        "pc_delta"
                    ] < 0
                    else 0
                )
            ),
        },

        # J: actual current flow.
        "J_flow": flow,

        # A: active machine components.
        "A_active": [
            "pc",
            "register",
            "flag",
            "memory",
            "decoder",
        ],

        # F: immediate next-state frontier.
        "F_frontier": allowed_next,

        # rho: simple attention/activity distribution.
        "rho_activity": {
            "control": (
                0.40
            ),
            "register": (
                0.30
            ),
            "flag": (
                0.20
            ),
            "memory": (
                0.10
            ),
        },

        # Phi: execution history.
        "Phi_history_length": (
            0
            if history is None
            else len(history)
        ),

        # O: multiple simultaneous observers.
        "O_observers": {
            "visible": (
                visible_snapshot(state)
            ),
            "full_binary": (
                full_binary_snapshot(
                    state
                )
            ),
            "next_instruction": {
                "opcode": opcode,
                "operand": operand,
            },
        },
    }


# ============================================================
# RUN MACHINE
# ============================================================

def run_machine(
    run_id,
    initial_flag,
):
    state = MachineState(
        run_id=run_id,
        step=0,
        pc=0,
        register=0,
        flag=initial_flag,
        memory=[0, 0, 0, 0],
        halted=False,
    )

    states = [
        deepcopy(state)
    ]

    transitions = []
    relational = [
        relational_state(
            state,
            history=[],
        )
    ]

    while (
        not state.halted
        and len(transitions) < 20
    ):
        next_state, transition = (
            execute_one(state)
        )

        transitions.append(
            transition
        )

        state = next_state

        states.append(
            deepcopy(state)
        )

        relational.append(
            relational_state(
                state,
                transition=transition,
                history=transitions,
            )
        )

    return {
        "run_id": run_id,
        "initial_flag": initial_flag,
        "states": [
            asdict(item)
            for item in states
        ],
        "transitions": transitions,
        "relational": relational,
    }


# ============================================================
# COMPARISON
# ============================================================

run_a = run_machine(
    "A_FLAG_1",
    initial_flag=1,
)

run_b = run_machine(
    "B_FLAG_0",
    initial_flag=0,
)


def comparable_pairs(run_a, run_b):
    pairs = []

    for index_a, state_a_dict in enumerate(
        run_a["states"]
    ):
        state_a = MachineState(
            **state_a_dict
        )

        for index_b, state_b_dict in enumerate(
            run_b["states"]
        ):
            state_b = MachineState(
                **state_b_dict
            )

            if (
                visible_snapshot(state_a)
                ==
                visible_snapshot(state_b)
            ):
                pairs.append({
                    "index_a": index_a,
                    "index_b": index_b,
                    "visible": (
                        visible_snapshot(
                            state_a
                        )
                    ),
                    "full_equal": (
                        full_binary_snapshot(
                            state_a
                        )
                        ==
                        full_binary_snapshot(
                            state_b
                        )
                    ),
                })

    return pairs


pairs = comparable_pairs(
    run_a,
    run_b,
)


# Find the intended collision:
# same visible register after LOAD,
# but different hidden FLAG.
collision_a = MachineState(
    **run_a["states"][1]
)

collision_b = MachineState(
    **run_b["states"][1]
)

same_visible = (
    visible_snapshot(collision_a)
    ==
    visible_snapshot(collision_b)
)

same_full_state = (
    full_binary_snapshot(collision_a)
    ==
    full_binary_snapshot(collision_b)
)

next_a, next_transition_a = (
    execute_one(
        deepcopy(collision_a)
    )
)

next_b, next_transition_b = (
    execute_one(
        deepcopy(collision_b)
    )
)

same_next_visible = (
    visible_snapshot(next_a)
    ==
    visible_snapshot(next_b)
)

same_next_full = (
    full_binary_snapshot(next_a)
    ==
    full_binary_snapshot(next_b)
)


# The branch instruction itself changes only PC.
# Execute one additional instruction on each path.
future_a, future_transition_a = (
    execute_one(
        deepcopy(next_a)
    )
)

future_b, future_transition_b = (
    execute_one(
        deepcopy(next_b)
    )
)

same_future_visible = (
    visible_snapshot(future_a)
    ==
    visible_snapshot(future_b)
)


# ============================================================
# REACHABILITY / FRONT
# ============================================================

def abstract_successors(state_key_value):
    pc, register, flag, memory, halted = (
        state_key_value
    )

    state = MachineState(
        run_id="abstract",
        step=0,
        pc=pc,
        register=register,
        flag=flag,
        memory=list(memory),
        halted=halted,
    )

    if state.halted:
        return []

    next_state, _ = execute_one(
        state
    )

    return [
        state_key(next_state)
    ]


def reachable_front(initial_state, depth):
    visited = {
        state_key(initial_state)
    }

    frontier = {
        state_key(initial_state)
    }

    rows = []

    for level in range(depth):
        next_frontier = set()

        for item in frontier:
            for successor in (
                abstract_successors(item)
            ):
                if successor not in visited:
                    next_frontier.add(
                        successor
                    )

        rows.append({
            "level": level,
            "visited_before": len(
                visited
            ),
            "frontier_before": len(
                frontier
            ),
            "born": len(
                next_frontier
            ),
            "visited_after": (
                len(visited)
                + len(next_frontier)
            ),
        })

        visited.update(
            next_frontier
        )

        frontier = next_frontier

        if not frontier:
            break

    return {
        "visited_count": len(
            visited
        ),
        "levels": rows,
    }


reachability_a = reachable_front(
    MachineState(
        run_id="A",
        step=0,
        pc=0,
        register=0,
        flag=1,
        memory=[0, 0, 0, 0],
        halted=False,
    ),
    depth=10,
)

reachability_b = reachable_front(
    MachineState(
        run_id="B",
        step=0,
        pc=0,
        register=0,
        flag=0,
        memory=[0, 0, 0, 0],
        halted=False,
    ),
    depth=10,
)


# ============================================================
# OUTPUT
# ============================================================

print("=" * 94)
print(
    "BINARY SNAPSHOT VS "
    "RELATIONAL-DYNAMIC STATE"
)
print("=" * 94)

print()
print(
    "Program:"
)

for address in sorted(PROGRAM):
    opcode, operand = PROGRAM[
        address
    ]

    print(
        "%d: %-5s %d"
        % (
            address,
            opcode,
            operand,
        )
    )


print()
print("=" * 94)
print("TRACE A: initial FLAG=1")
print("=" * 94)

for state in run_a["states"]:
    print(
        "step=%d pc=%d R=%2d [%s] "
        "FLAG=%d M0=%d halted=%s"
        % (
            state["step"],
            state["pc"],
            state["register"],
            bits(
                state["register"]
            ),
            state["flag"],
            state["memory"][0],
            state["halted"],
        )
    )


print()
print("=" * 94)
print("TRACE B: initial FLAG=0")
print("=" * 94)

for state in run_b["states"]:
    print(
        "step=%d pc=%d R=%2d [%s] "
        "FLAG=%d M0=%d halted=%s"
        % (
            state["step"],
            state["pc"],
            state["register"],
            bits(
                state["register"]
            ),
            state["flag"],
            state["memory"][0],
            state["halted"],
        )
    )


print()
print("=" * 94)
print("CONTROLLED COLLISION")
print("=" * 94)

print(
    "same visible register :",
    same_visible,
)

print(
    "same full state       :",
    same_full_state,
)

print(
    "visible A             :",
    visible_snapshot(
        collision_a
    ),
)

print(
    "visible B             :",
    visible_snapshot(
        collision_b
    ),
)

print(
    "hidden A              :",
    {
        "pc": collision_a.pc,
        "flag": collision_a.flag,
    },
)

print(
    "hidden B              :",
    {
        "pc": collision_b.pc,
        "flag": collision_b.flag,
    },
)

print()
print(
    "after branch:"
)

print(
    "same next visible     :",
    same_next_visible,
)

print(
    "same next full state  :",
    same_next_full,
)

print(
    "next A                :",
    full_binary_snapshot(
        next_a
    ),
)

print(
    "next B                :",
    full_binary_snapshot(
        next_b
    ),
)

print()
print(
    "after one more instruction:"
)

print(
    "future A              :",
    full_binary_snapshot(
        future_a
    ),
)

print(
    "future B              :",
    full_binary_snapshot(
        future_b
    ),
)

print(
    "same future visible   :",
    same_future_visible,
)


print()
print("=" * 94)
print("RELATIONAL INTERPRETATION")
print("=" * 94)

relation_a = relational_state(
    collision_a
)

relation_b = relational_state(
    collision_b
)

print(
    "A relation/flow/front:"
)

print(
    json.dumps(
        {
            "R": relation_a[
                "R_relation"
            ],
            "J": relation_a[
                "J_flow"
            ],
            "F": relation_a[
                "F_frontier"
            ],
        },
        ensure_ascii=False,
        indent=2,
    )
)

print(
    "B relation/flow/front:"
)

print(
    json.dumps(
        {
            "R": relation_b[
                "R_relation"
            ],
            "J": relation_b[
                "J_flow"
            ],
            "F": relation_b[
                "F_frontier"
            ],
        },
        ensure_ascii=False,
        indent=2,
    )
)


# ============================================================
# INVARIANTS
# ============================================================

all_words_valid = True

for run in (run_a, run_b):
    for state in run["states"]:
        if not (
            0
            <= state["register"]
            <= WORD_MASK
        ):
            all_words_valid = False

memory_a_final = (
    run_a["states"][-1][
        "memory"
    ][0]
)

memory_b_final = (
    run_b["states"][-1][
        "memory"
    ][0]
)

final_outputs_differ = (
    memory_a_final
    != memory_b_final
)


print()
print("=" * 94)
print("INVARIANTS")
print("=" * 94)

print(
    "4-bit bounds          :",
    "PASS"
    if all_words_valid
    else "FAIL",
)

print(
    "same visible collision:",
    "PASS"
    if same_visible
    else "FAIL",
)

print(
    "full state differs    :",
    "PASS"
    if not same_full_state
    else "FAIL",
)

print(
    "future visible differs:",
    "PASS"
    if not same_future_visible
    else "FAIL",
)

print(
    "final outputs differ  :",
    "PASS"
    if final_outputs_differ
    else "FAIL",
)

print(
    "M0 A / B              :",
    memory_a_final,
    "/",
    memory_b_final,
)


# ============================================================
# SAVE
# ============================================================

report = {
    "experiment": (
        "Binary snapshot versus "
        "relational-dynamic state"
    ),

    "warning": (
        "The visible binary observer is "
        "deliberately incomplete. A complete "
        "deterministic machine state remains "
        "sufficient to compute the next state. "
        "The experiment tests representational "
        "completeness, not superiority over "
        "binary computation."
    ),

    "word_bits": WORD_BITS,

    "program": {
        str(address): [
            opcode,
            operand,
        ]
        for address, (
            opcode,
            operand,
        ) in PROGRAM.items()
    },

    "run_a": run_a,
    "run_b": run_b,

    "same_visible_pairs": pairs,

    "controlled_collision": {
        "same_visible": same_visible,
        "same_full_state": (
            same_full_state
        ),
        "same_next_visible": (
            same_next_visible
        ),
        "same_next_full": (
            same_next_full
        ),
        "same_future_visible": (
            same_future_visible
        ),
        "collision_a": (
            full_binary_snapshot(
                collision_a
            )
        ),
        "collision_b": (
            full_binary_snapshot(
                collision_b
            )
        ),
        "next_a": (
            full_binary_snapshot(
                next_a
            )
        ),
        "next_b": (
            full_binary_snapshot(
                next_b
            )
        ),
        "future_a": (
            full_binary_snapshot(
                future_a
            )
        ),
        "future_b": (
            full_binary_snapshot(
                future_b
            )
        ),
        "relation_a": relation_a,
        "relation_b": relation_b,
    },

    "reachability": {
        "run_a": reachability_a,
        "run_b": reachability_b,
    },

    "invariants": {
        "all_words_valid": (
            all_words_valid
        ),
        "same_visible_collision": (
            same_visible
        ),
        "full_state_differs": (
            not same_full_state
        ),
        "future_visible_differs": (
            not same_future_visible
        ),
        "final_outputs_differ": (
            final_outputs_differ
        ),
    },
}


output = OUT / (
    "binary_relational.json"
)

output.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)

print()
print("Saved:", output)
