import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path.home() / "malysh_project"
EXP = ROOT / "experiments/ns_acoustic_external"
RUN = Path(__file__).resolve().parent

SOURCE_RUNS = sorted(
    EXP.glob("runs/flux_time_*")
)

if not SOURCE_RUNS:
    raise SystemExit(
        "[FAIL] Не найден flux_time_*"
    )

SOURCE_RUN = SOURCE_RUNS[-1]
SOURCE_JSON = SOURCE_RUN / "ns3d_flux_time.json"

RESULT_FILE = RUN / "acoustic_alphabet_test.json"
HASH_FILE = RUN / "acoustic_alphabet_test.sha256"


def load_json(path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def vector(snapshot, field):
    return np.asarray(
        snapshot[field],
        dtype=np.float64,
    )


def relative_error(predicted, actual):
    return float(
        np.linalg.norm(predicted - actual)
        / (
            np.linalg.norm(actual)
            + 1e-30
        )
    )


def peak_shell(values):
    return int(
        np.argmax(np.abs(values))
    )


def linear_symbol(s_previous, s_current):
    """
    Прежняя линейная гипотеза:

        S_next = S_current + Delta S
    """

    delta = s_current - s_previous

    return s_current + delta


def damped_symbol(
    s_previous,
    s_current,
    coefficient=0.75,
):
    delta = s_current - s_previous

    return (
        s_current
        + coefficient * delta
    )


def alphabet_symbol(
    s_old,
    s_previous,
    s_current,
):
    """
    Алфавитная композиция:

        Delta_1 = S_current - S_previous
        Delta_0 = S_previous - S_old
        Delta_2 = Delta_1 - Delta_0

        S_next =
            S_current
            + Delta_1
            + Delta_2

    Эквивалентно:

        S_next =
            3*S_current
            - 3*S_previous
            + S_old

    Здесь S, Delta_1 и Delta_2 рассматриваются
    как собственные символы композиционного алфавита.
    """

    delta_previous = (
        s_previous - s_old
    )

    delta_current = (
        s_current - s_previous
    )

    delta_change = (
        delta_current
        - delta_previous
    )

    return (
        s_current
        + delta_current
        + delta_change
    )


def zero_identity_test(values):
    zero = np.zeros_like(values)

    left = values + zero
    right = zero + values

    return {
        "left_error": float(
            np.linalg.norm(left - values)
        ),

        "right_error": float(
            np.linalg.norm(right - values)
        ),

        "pass": bool(
            np.array_equal(left, values)
            and np.array_equal(
                right,
                values,
            )
        ),
    }


def additive_associativity_test(a, b, c):
    left = (a + b) + c
    right = a + (b + c)

    error = float(
        np.linalg.norm(left - right)
    )

    return {
        "error": error,
        "pass": bool(error < 1e-14),
    }


def decomposition_test(
    old,
    previous,
    current,
):
    delta_previous = previous - old
    delta_current = current - previous

    delta_change = (
        delta_current
        - delta_previous
    )

    direct = (
        3.0 * current
        - 3.0 * previous
        + old
    )

    composed = (
        current
        + delta_current
        + delta_change
    )

    error = float(
        np.linalg.norm(
            direct - composed
        )
    )

    return {
        "error": error,
        "pass": bool(error < 1e-14),
    }


packet = load_json(SOURCE_JSON)
snapshots = packet["spectral_snapshots"]

if len(snapshots) < 5:
    raise SystemExit(
        "[FAIL] Недостаточно снимков"
    )


methods = {
    "A_LINEAR": linear_symbol,
    "A_DAMPED": damped_symbol,
    "B_ACOUSTIC_ALPHABET": alphabet_symbol,
}

records = []

for target_index in range(
    3,
    len(snapshots),
):
    old = snapshots[target_index - 3]
    previous = snapshots[
        target_index - 2
    ]
    current = snapshots[
        target_index - 1
    ]
    actual = snapshots[target_index]

    old_flux = vector(
        old,
        "cumulative_flux",
    )

    previous_flux = vector(
        previous,
        "cumulative_flux",
    )

    current_flux = vector(
        current,
        "cumulative_flux",
    )

    actual_flux = vector(
        actual,
        "cumulative_flux",
    )

    old_energy = vector(
        old,
        "energy_spectrum",
    )

    previous_energy = vector(
        previous,
        "energy_spectrum",
    )

    current_energy = vector(
        current,
        "energy_spectrum",
    )

    actual_energy = vector(
        actual,
        "energy_spectrum",
    )

    predictions = {
        "A_LINEAR": {
            "flux": linear_symbol(
                previous_flux,
                current_flux,
            ),

            "energy": linear_symbol(
                previous_energy,
                current_energy,
            ),
        },

        "A_DAMPED": {
            "flux": damped_symbol(
                previous_flux,
                current_flux,
            ),

            "energy": damped_symbol(
                previous_energy,
                current_energy,
            ),
        },

        "B_ACOUSTIC_ALPHABET": {
            "flux": alphabet_symbol(
                old_flux,
                previous_flux,
                current_flux,
            ),

            "energy": alphabet_symbol(
                old_energy,
                previous_energy,
                current_energy,
            ),
        },
    }

    test_record = {
        "target_step":
            int(actual["step"]),

        "target_time":
            float(actual["time"]),

        "methods": {},
    }

    for name, prediction in (
        predictions.items()
    ):
        predicted_energy = np.maximum(
            0.0,
            prediction["energy"],
        )

        test_record["methods"][name] = {
            "flux_relative_error":
                relative_error(
                    prediction["flux"],
                    actual_flux,
                ),

            "energy_relative_error":
                relative_error(
                    predicted_energy,
                    actual_energy,
                ),

            "flux_peak_shell_error":
                abs(
                    peak_shell(
                        prediction["flux"]
                    )
                    - int(
                        actual[
                            "flux_peak_shell"
                        ]
                    )
                ),

            "finite":
                bool(
                    np.all(
                        np.isfinite(
                            prediction["flux"]
                        )
                    )
                    and np.all(
                        np.isfinite(
                            predicted_energy
                        )
                    )
                ),
        }

    test_record["alphabet_invariants"] = {
        "zero_flux":
            zero_identity_test(
                current_flux
            ),

        "zero_energy":
            zero_identity_test(
                current_energy
            ),

        "associativity_flux":
            additive_associativity_test(
                old_flux,
                previous_flux,
                current_flux,
            ),

        "decomposition_flux":
            decomposition_test(
                old_flux,
                previous_flux,
                current_flux,
            ),

        "decomposition_energy":
            decomposition_test(
                old_energy,
                previous_energy,
                current_energy,
            ),
    }

    records.append(test_record)


summary = {}

for method in methods:
    flux_errors = [
        record["methods"][method][
            "flux_relative_error"
        ]
        for record in records
    ]

    energy_errors = [
        record["methods"][method][
            "energy_relative_error"
        ]
        for record in records
    ]

    peak_errors = [
        record["methods"][method][
            "flux_peak_shell_error"
        ]
        for record in records
    ]

    finite = all(
        record["methods"][method][
            "finite"
        ]
        for record in records
    )

    summary[method] = {
        "test_count":
            len(records),

        "mean_flux_error":
            float(np.mean(flux_errors)),

        "median_flux_error":
            float(np.median(flux_errors)),

        "max_flux_error":
            float(np.max(flux_errors)),

        "mean_energy_error":
            float(np.mean(energy_errors)),

        "mean_peak_shell_error":
            float(np.mean(peak_errors)),

        "finite_pass":
            finite,

        "wins_by_flux_error":
            0,
    }


for record in records:
    winner = min(
        methods,
        key=lambda name:
            record["methods"][name][
                "flux_relative_error"
            ],
    )

    summary[winner][
        "wins_by_flux_error"
    ] += 1


all_invariants_pass = all(
    all([
        record[
            "alphabet_invariants"
        ]["zero_flux"]["pass"],

        record[
            "alphabet_invariants"
        ]["zero_energy"]["pass"],

        record[
            "alphabet_invariants"
        ]["associativity_flux"][
            "pass"
        ],

        record[
            "alphabet_invariants"
        ]["decomposition_flux"][
            "pass"
        ],

        record[
            "alphabet_invariants"
        ]["decomposition_energy"][
            "pass"
        ],
    ])
    for record in records
)


linear_error = summary[
    "A_LINEAR"
]["mean_flux_error"]

alphabet_error = summary[
    "B_ACOUSTIC_ALPHABET"
]["mean_flux_error"]

improvement_fraction = (
    (linear_error - alphabet_error)
    / (linear_error + 1e-30)
)

alphabet_wins = summary[
    "B_ACOUSTIC_ALPHABET"
]["wins_by_flux_error"]

test_count = len(records)

# Заранее определённый критерий.
# Не требуется побеждать на каждом шаге.
recommend_add = bool(
    all_invariants_pass

    and summary[
        "B_ACOUSTIC_ALPHABET"
    ]["finite_pass"]

    and improvement_fraction >= 0.10

    and alphabet_wins
        >= math.ceil(test_count / 2)

    and summary[
        "B_ACOUSTIC_ALPHABET"
    ]["mean_energy_error"]
        <= 1.25
        * summary[
            "A_LINEAR"
        ]["mean_energy_error"]
)


result = {
    "schema":
        "malysh.acoustic-alphabet-ab-test.v1",

    "source":
        str(SOURCE_JSON),

    "principle_under_test": {
        "number_composition":
            "S_a plus S_b produces S_(a+b)",

        "spectral_composition":
            "S_p plus S_q produces S_(p+q)",

        "weighted_interaction":
            "T(k|p,q) gives direction and strength",

        "zero_identity":
            "S_0 plus S_n equals S_n",

        "temporal_alphabet":
            (
                "S_next = S_current "
                "plus Delta_1 "
                "plus Delta_2"
            ),

        "decision_authority":
            False,

        "role":
            "independent observer and predictor candidate",
    },

    "method_definitions": {
        "A_LINEAR":
            "S_next = 2*S_current - S_previous",

        "A_DAMPED":
            (
                "S_next = S_current "
                "+ 0.75*(S_current-S_previous)"
            ),

        "B_ACOUSTIC_ALPHABET":
            (
                "S_next = 3*S_current "
                "- 3*S_previous + S_old"
            ),
    },

    "predeclared_recommendation_rule": {
        "all_invariants_pass":
            True,

        "minimum_flux_improvement":
            0.10,

        "minimum_win_fraction":
            0.50,

        "maximum_energy_error_ratio":
            1.25,
    },

    "records":
        records,

    "summary":
        summary,

    "comparison": {
        "linear_mean_flux_error":
            linear_error,

        "alphabet_mean_flux_error":
            alphabet_error,

        "alphabet_improvement_fraction":
            float(improvement_fraction),

        "alphabet_win_count":
            alphabet_wins,

        "test_count":
            test_count,

        "all_invariants_pass":
            all_invariants_pass,
    },

    "recommendation": {
        "add_principle_as_observer":
            recommend_add,

        "do_not_replace_existing_logic":
            True,

        "decision_authority":
            False,

        "automatic_core_integration":
            False,

        "next_action": (
            "If recommended, create an isolated "
            "AcousticAlphabetObserver and test it "
            "on a new frozen future step."
            if recommend_add
            else
            "Keep as external hypothesis and collect "
            "more independent trajectories."
        ),
    },
}


canonical = json.dumps(
    result,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")

digest = hashlib.sha256(
    canonical
).hexdigest()

RESULT_FILE.write_bytes(canonical)

HASH_FILE.write_text(
    digest
    + "  "
    + RESULT_FILE.name
    + "\n",
    encoding="utf-8",
)


print("============================================================")
print(" A/B TEST: ACOUSTIC ALPHABET PRINCIPLE")
print("============================================================")
print("Source:", SOURCE_JSON)
print("Walk-forward tests:", test_count)
print()

for method, values in summary.items():
    print(method)

    print(
        "  mean flux error:",
        f'{values["mean_flux_error"]:.12e}',
    )

    print(
        "  mean energy error:",
        f'{values["mean_energy_error"]:.12e}',
    )

    print(
        "  mean peak error:",
        f'{values["mean_peak_shell_error"]:.6f}',
    )

    print(
        "  wins:",
        values["wins_by_flux_error"],
        "/",
        test_count,
    )

print()
print(
    "Alphabet improvement vs linear:",
    f"{100.0 * improvement_fraction:.6f}%",
)

print(
    "All algebraic invariants pass:",
    all_invariants_pass,
)

print()
print(
    "RECOMMEND ADD AS OBSERVER:",
    recommend_add,
)

print(
    "RECOMMEND REPLACE OLD LOGIC:",
    False,
)

print(
    "DECISION AUTHORITY:",
    False,
)

print()
print("SHA256:", digest)
print("Result:", RESULT_FILE)
print("Hash:", HASH_FILE)
