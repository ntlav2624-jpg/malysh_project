#!/usr/bin/env python3

import contextlib
import io
import json
import runpy
from pathlib import Path

import numpy as np


# ============================================================
# LOAD VERIFIED MODEL
# ============================================================

BASE = Path("point_genesis_test.py")

if not BASE.exists():
    raise SystemExit(
        "STOP: point_genesis_test.py not found"
    )

with contextlib.redirect_stdout(io.StringIO()):
    model = runpy.run_path(str(BASE))


COORDS = model["COORDS"]
NODE_COUNT = model["NODE_COUNT"]

POINTS = model["POINTS"]

FULL = model["FULL"]

COORD_TO_NODE = model[
    "COORD_TO_NODE"
]

transfer_step = model[
    "transfer_step"
]


# ============================================================
# PARAMETERS
# ============================================================

STEPS = 40

# Important:
# use the same effective support tolerance
# consistently on both sides of the law.
EPS = 1e-15

OUT = Path(
    "experiments/cloud_front_law"
)


# ============================================================
# FLOW VECTOR
# ============================================================

def flow_vector(rho):
    p = FULL["p"]
    q = FULL["q"]
    k = FULL["k"]

    triad_mean = (
        rho[p]
        + rho[q]
        + rho[k]
    ) / 3.0

    delta = (
        np.bincount(
            p,
            weights=(
                triad_mean
                - rho[p]
            ),
            minlength=NODE_COUNT,
        )

        + np.bincount(
            q,
            weights=(
                triad_mean
                - rho[q]
            ),
            minlength=NODE_COUNT,
        )

        + np.bincount(
            k,
            weights=(
                triad_mean
                - rho[k]
            ),
            minlength=NODE_COUNT,
        )
    )

    return delta


# ============================================================
# ACTIVE SET / FRONT
# ============================================================

def active_mask(rho):
    return rho > EPS


def front_mask(rho, J):
    """
    An inactive coordinate belongs to the
    forward front if the present flow points
    into that coordinate.

        rho_i <= EPS
        J_i   > EPS

    The same coordinate is an outward
    forbidden coordinate for -J.
    """

    return (
        (rho <= EPS)
        & (J > EPS)
    )


def reverse_outward_mask(rho, J):
    """
    For -J:

        (-J)_i < -EPS

    at a boundary state rho_i <= EPS.
    """

    return (
        (rho <= EPS)
        & ((-J) < -EPS)
    )


# ============================================================
# EXACT SET COMPARISON
# ============================================================

def indices(mask):
    return set(
        np.where(mask)[0].tolist()
    )


def coordinate_list(index_set):
    return [
        COORDS[index]
        .astype(int)
        .tolist()

        for index in sorted(
            index_set
        )
    ]


# ============================================================
# ONE POINT
# ============================================================

def test_point(
    name,
    coordinate,
):
    rho = np.zeros(
        NODE_COUNT,
        dtype=float,
    )

    rho[
        COORD_TO_NODE[
            coordinate
        ]
    ] = 1.0

    rows = []

    exact_law_count = 0
    exact_set_count = 0

    print()
    print("=" * 104)
    print(
        name,
        coordinate,
    )
    print("=" * 104)

    print(
        "%-4s %-8s %-8s %-8s %-8s "
        "%-8s %-10s %-10s %-10s"
        % (
            "n",
            "|A_n|",
            "front",
            "out(-J)",
            "|A+1|",
            "growth",
            "law",
            "set-law",
            "leak",
        )
    )

    for n in range(STEPS):
        J = flow_vector(
            rho
        )

        A_now_mask = active_mask(
            rho
        )

        F_mask = front_mask(
            rho,
            J,
        )

        R_mask = reverse_outward_mask(
            rho,
            J,
        )

        rho_next = transfer_step(
            rho,
            FULL,
        )

        A_next_mask = active_mask(
            rho_next
        )

        A_now = indices(
            A_now_mask
        )

        A_next = indices(
            A_next_mask
        )

        F = indices(
            F_mask
        )

        reverse_outward = indices(
            R_mask
        )

        # Newly active nodes.
        born = (
            A_next - A_now
        )

        # Nodes that disappeared from active support.
        died = (
            A_now - A_next
        )

        # Front predicted but not actually activated.
        predicted_not_born = (
            F - born
        )

        # Born without being in predicted front.
        born_not_predicted = (
            born - F
        )

        growth = (
            len(A_next)
            - len(A_now)
        )

        scalar_law = (
            growth == len(F)
        )

        set_law = (
            born == F
        )

        reverse_equivalence = (
            F == reverse_outward
        )

        monotone_support = (
            len(died) == 0
        )

        if scalar_law:
            exact_law_count += 1

        if set_law:
            exact_set_count += 1

        leak_count = (
            len(predicted_not_born)
            + len(born_not_predicted)
            + len(died)
        )

        print(
            "%-4d %-8d %-8d %-8d %-8d "
            "%-8d %-10s %-10s %-10d"
            % (
                n,
                len(A_now),
                len(F),
                len(reverse_outward),
                len(A_next),
                growth,

                "PASS"
                if scalar_law
                else "FAIL",

                "PASS"
                if set_law
                else "FAIL",

                leak_count,
            )
        )

        rows.append({
            "step": n,

            "active_now": len(
                A_now
            ),

            "front_size": len(F),

            "reverse_outward_size": len(
                reverse_outward
            ),

            "active_next": len(
                A_next
            ),

            "support_growth": growth,

            "scalar_law_pass": (
                scalar_law
            ),

            "set_law_pass": (
                set_law
            ),

            "reverse_front_equivalence": (
                reverse_equivalence
            ),

            "monotone_support": (
                monotone_support
            ),

            "born_size": len(
                born
            ),

            "died_size": len(
                died
            ),

            "predicted_not_born_size": len(
                predicted_not_born
            ),

            "born_not_predicted_size": len(
                born_not_predicted
            ),

            "born_coordinates": (
                coordinate_list(
                    born
                )
            ),

            "predicted_not_born": (
                coordinate_list(
                    predicted_not_born
                )
            ),

            "born_not_predicted": (
                coordinate_list(
                    born_not_predicted
                )
            ),

            "died_coordinates": (
                coordinate_list(
                    died
                )
            ),

            "sum_J": float(
                J.sum()
            ),

            "norm_J": float(
                np.linalg.norm(J)
            ),

            "mass_now": float(
                rho.sum()
            ),

            "mass_next": float(
                rho_next.sum()
            ),

            "minimum_next": float(
                rho_next.min()
            ),
        })

        rho = rho_next


    # Final support
    final_support = int(
        active_mask(rho).sum()
    )

    first_full_support = None

    for row in rows:
        if (
            row["active_next"]
            == NODE_COUNT
        ):
            first_full_support = (
                row["step"] + 1
            )
            break

    print()
    print(
        "scalar law passes : %d/%d"
        % (
            exact_law_count,
            STEPS,
        )
    )

    print(
        "exact set passes  : %d/%d"
        % (
            exact_set_count,
            STEPS,
        )
    )

    print(
        "first full support:",
        first_full_support,
    )

    return {
        "name": name,

        "coordinate": [
            int(value)
            for value in coordinate
        ],

        "scalar_law_passes": (
            exact_law_count
        ),

        "set_law_passes": (
            exact_set_count
        ),

        "tested_steps": STEPS,

        "first_full_support": (
            first_full_support
        ),

        "final_support": (
            final_support
        ),

        "steps": rows,
    }


# ============================================================
# ALL POINTS
# ============================================================

print("=" * 104)
print("CLOUD FRONT LAW")
print("=" * 104)

print()

print(
    "Scalar hypothesis:"
)

print(
    "|A(n+1)| - |A(n)| = |F(n)|"
)

print()

print(
    "Stronger set hypothesis:"
)

print(
    "A(n+1) \\ A(n) = F(n)"
)

print()

print(
    "Negative observer:"
)

print(
    "F(n) = outward boundary set of -J"
)

print()

print(
    "EPS = %.3e"
    % EPS
)

results = []

for name, coordinate in (
    POINTS.items()
):
    results.append(
        test_point(
            name,
            coordinate,
        )
    )


# ============================================================
# CROSS ANALYSIS
# ============================================================

all_scalar = True
all_set = True
all_reverse = True
all_monotone = True

failures = []

for point in results:
    for row in point["steps"]:
        if not row[
            "scalar_law_pass"
        ]:
            all_scalar = False

        if not row[
            "set_law_pass"
        ]:
            all_set = False

        if not row[
            "reverse_front_equivalence"
        ]:
            all_reverse = False

        if not row[
            "monotone_support"
        ]:
            all_monotone = False

        if (
            not row["scalar_law_pass"]
            or not row["set_law_pass"]
            or not row[
                "reverse_front_equivalence"
            ]
            or not row[
                "monotone_support"
            ]
        ):
            failures.append({
                "name": point["name"],
                "coordinate": point[
                    "coordinate"
                ],
                "step": row["step"],

                "scalar_law": row[
                    "scalar_law_pass"
                ],

                "set_law": row[
                    "set_law_pass"
                ],

                "reverse_equivalence": (
                    row[
                        "reverse_front_equivalence"
                    ]
                ),

                "monotone_support": (
                    row[
                        "monotone_support"
                    ]
                ),

                "predicted_not_born": (
                    row[
                        "predicted_not_born_size"
                    ]
                ),

                "born_not_predicted": (
                    row[
                        "born_not_predicted_size"
                    ]
                ),

                "died": row[
                    "died_size"
                ],
            })


print()
print("=" * 104)
print("GLOBAL RESULT")
print("=" * 104)

print(
    "scalar front law      :",
    "PASS"
    if all_scalar
    else "FAIL",
)

print(
    "exact set front law   :",
    "PASS"
    if all_set
    else "FAIL",
)

print(
    "front == outward(-J)  :",
    "PASS"
    if all_reverse
    else "FAIL",
)

print(
    "support monotonicity  :",
    "PASS"
    if all_monotone
    else "FAIL",
)

print(
    "failure records       :",
    len(failures),
)


# ============================================================
# VERY IMPORTANT:
# NEGATIVE RESULT IS SAVED, NOT HIDDEN
# ============================================================

if failures:
    print()
    print("=" * 104)
    print(
        "NEGATIVE / COUNTEREXAMPLE CASES"
    )
    print("=" * 104)

    for item in failures[:30]:
        print(item)


# ============================================================
# MASS CHECK
# ============================================================

max_mass_error = 0.0
minimum_state = float("inf")

for point in results:
    for row in point["steps"]:
        max_mass_error = max(
            max_mass_error,

            abs(
                row["mass_now"]
                - 1.0
            ),

            abs(
                row["mass_next"]
                - 1.0
            ),
        )

        minimum_state = min(
            minimum_state,
            row["minimum_next"],
        )


print()
print("=" * 104)
print("INVARIANTS")
print("=" * 104)

print(
    "max mass error = %.18e"
    % max_mass_error
)

print(
    "minimum rho    = %.18e"
    % minimum_state
)


# ============================================================
# SAVE
# ============================================================

report = {
    "experiment": (
        "Cloud front propagation law"
    ),

    "solver_modified": False,

    "hypotheses": {
        "scalar": (
            "|A(n+1)|-|A(n)| = |F(n)|"
        ),

        "set": (
            "A(n+1)\\A(n) = F(n)"
        ),

        "negative_observer": (
            "F(n) equals outward boundary "
            "set detected by -J"
        ),
    },

    "definitions": {
        "active": "rho > EPS",

        "front": (
            "rho <= EPS and J > EPS"
        ),

        "reverse_outward": (
            "rho <= EPS and -J < -EPS"
        ),
    },

    "parameters": {
        "steps": STEPS,
        "EPS": EPS,
        "states": NODE_COUNT,
        "triads": FULL["triads"],
    },

    "global_result": {
        "scalar_law": all_scalar,
        "set_law": all_set,
        "reverse_equivalence": (
            all_reverse
        ),
        "support_monotonicity": (
            all_monotone
        ),
        "failure_count": len(
            failures
        ),
        "max_mass_error": (
            max_mass_error
        ),
        "minimum_state": (
            minimum_state
        ),
    },

    "failures": failures,

    "results": results,
}


output = OUT / (
    "cloud_front_law.json"
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
