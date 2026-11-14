#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MALYSH BULLET-100C v4
Карта устойчивости внутренних счётчиков.

Вычисляются три независимых параметра:

Omega = Gamma * tau
    Число внешних событий за один внутренний такт.

Q = deposited_energy_per_event / binding_energy
    Сила одного события относительно масштаба связи.

D = Omega * Q
    Накопленная энергетическая нагрузка за один внутренний такт.

Важно:
- известная физика используется только при beta < 1;
- beta >= 1 исследуется лишь как математическая гипотеза;
- доля deposited_fraction является сценарием, а не известной константой;
- атомные и ядерные пороги являются масштабами модели;
- результаты не заменяют Geant4 или точную модель материала.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import operator

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# КОНСТАНТЫ
# ============================================================

C = 299_792_458.0
QE = 1.602_176_634e-19
PROTON_MASS = 1.672_621_925_95e-27

PROTON_REST_ENERGY_EV = (
    PROTON_MASS * C * C / QE
)

ROOT = Path.home() / "malysh_project"
OUT = ROOT / "experiments" / "bullet_100c"

REPORT = OUT / "report_v4.json"
MAP_FILE = OUT / "stability_map_v4.jsonl"
FORMULAS = OUT / "learned_formulas_v4.jsonl"
AUDIT = OUT / "audit_v4.jsonl"

OUT.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================

@dataclass
class Bullet:

    mass_kg: float = 0.008
    length_m: float = 0.015
    diameter_m: float = 0.009
    temperature_K: float = 293.15


@dataclass
class Medium:

    particle: str = "proton"
    particle_mass_kg: float = PROTON_MASS
    cross_section_m2: float = 1e-20


BULLET = Bullet()
MEDIUM = Medium()


# ============================================================
# ВНУТРЕННИЕ МАСШТАБЫ
#
# Это исследовательские оценки.
# Они не являются точной моделью конкретного сорта стали.
# ============================================================

CLOCKS = {

    "electronic": {
        "tau_s": 1e-16,
        "binding_eV": 10.0,
    },

    "atomic": {
        "tau_s": 1e-15,
        "binding_eV": 10.0,
    },

    "lattice": {
        "tau_s": 1e-12,
        "binding_eV": 3.0,
    },

    "thermal_local": {
        "tau_s": 1e-9,
        "binding_eV": 0.025,
    },

    "nuclear": {
        "tau_s": 1e-22,
        "binding_eV": 1e6,
    },
}


# Сценарии доли энергии одного столкновения,
# реально оставшейся в рассматриваемой внутренней подсистеме.

DEPOSITION_SCENARIOS = {

    "very_weak":
        1e-12,

    "weak":
        1e-9,

    "moderate":
        1e-6,

    "strong":
        1e-3,

    "upper_bound":
        1.0,
}


# Скорости строгой физической ветви.

BETAS = [

    0.0,
    0.1,
    0.5,
    0.9,
    0.99,
    0.999,
    0.9999,
    0.99999,
    0.999999,
]


# Плотности среды, м^-3.

DENSITIES = [

    1e0,
    1e6,
    1e12,
    1e18,
    1e24,
    1e30,
]


# Математическая сверхсветовая ветвь.

SUPERLUMINAL_BETAS = [

    1.01,
    1.1,
    2.0,
    10.0,
    100.0,
]


# ============================================================
# СЛУЖЕБНЫЕ ФУНКЦИИ
# ============================================================

def now():

    return datetime.now(
        timezone.utc
    ).isoformat()


def write_audit(
    kind,
    payload,
):

    record = {

        "utc":
            now(),

        "kind":
            kind,

        **payload,
    }

    with AUDIT.open(
        "a",
        encoding="utf-8",
    ) as file:

        file.write(

            json.dumps(
                record,
                ensure_ascii=False,
            )

            + "\n"
        )


def finite_or_none(
    value,
):

    if not math.isfinite(value):
        return None

    return value


# ============================================================
# БЕЗОПАСНЫЙ АНАЛИЗ ФОРМУЛ
# ============================================================

BINARY_OPERATORS = {

    ast.Add:
        operator.add,

    ast.Sub:
        operator.sub,

    ast.Mult:
        operator.mul,

    ast.Div:
        operator.truediv,

    ast.Pow:
        operator.pow,
}


FUNCTIONS = {

    "sqrt":
        math.sqrt,

    "abs":
        abs,

    "log":
        math.log,

    "exp":
        math.exp,
}


def safe_math(
    expression,
    variables,
):

    tree = ast.parse(
        expression,
        mode="eval",
    )

    def calculate(node):

        if isinstance(
            node,
            ast.Expression,
        ):

            return calculate(
                node.body
            )

        if (
            isinstance(node, ast.Constant)
            and isinstance(
                node.value,
                (int, float),
            )
        ):

            return node.value

        if isinstance(
            node,
            ast.Name,
        ):

            if node.id in variables:

                return variables[
                    node.id
                ]

            raise ValueError(
                "unknown_variable:"
                + node.id
            )

        if (
            isinstance(
                node,
                ast.BinOp,
            )
            and type(node.op)
            in BINARY_OPERATORS
        ):

            operation = BINARY_OPERATORS[
                type(node.op)
            ]

            return operation(

                calculate(
                    node.left
                ),

                calculate(
                    node.right
                ),
            )

        if (
            isinstance(
                node,
                ast.UnaryOp,
            )
            and isinstance(
                node.op,
                (
                    ast.UAdd,
                    ast.USub,
                ),
            )
        ):

            value = calculate(
                node.operand
            )

            if isinstance(
                node.op,
                ast.UAdd,
            ):
                return value

            return -value

        if (
            isinstance(
                node,
                ast.Call,
            )
            and isinstance(
                node.func,
                ast.Name,
            )
            and node.func.id
            in FUNCTIONS
            and not node.keywords
        ):

            arguments = [

                calculate(argument)

                for argument
                in node.args
            ]

            return FUNCTIONS[
                node.func.id
            ](*arguments)

        raise ValueError(
            "forbidden_ast:"
            + type(node).__name__
        )

    result = float(
        calculate(tree)
    )

    if not math.isfinite(
        result
    ):

        raise ValueError(
            "non_finite_result"
        )

    return result


# ============================================================
# КЛАССИФИКАЦИЯ РЕЖИМОВ
# ============================================================

def classify_omega(
    omega,
):

    if omega < 0.1:
        return "resolved"

    if omega < 1.0:
        return "loaded"

    if omega < 10.0:
        return "overloaded"

    return "continuum_or_unresolved"


def classify_q(
    q_value,
):

    if q_value < 0.01:
        return "subthreshold"

    if q_value < 1.0:
        return "significant_but_below_binding"

    if q_value < 100.0:
        return "binding_scale_crossed"

    return "strong_single_event"


def classify_d(
    d_value,
):

    if d_value < 0.1:
        return "relaxes_between_events"

    if d_value < 1.0:
        return "accumulation_warning"

    if d_value < 10.0:
        return "accumulation_threshold_crossed"

    return "strong_accumulation"


# ============================================================
# РЕЛЯТИВИСТСКАЯ КИНЕМАТИКА
# ============================================================

def relativistic_state(
    beta,
):

    if beta < 0.0:

        return {
            "beta":
                beta,

            "status":
                "invalid_negative_speed",
        }

    if beta >= 1.0:

        return {

            "beta":
                beta,

            "velocity_m_s":
                beta * C,

            "status":
                (
                    "massive_object_light_limit"
                    if beta == 1.0
                    else
                    "outside_known_massive_particle_dynamics"
                ),

            "continued":
                False,

            "worldline":
                (
                    "null"
                    if beta == 1.0
                    else
                    "spacelike"
                ),
        }

    gamma = (

        1.0

        / math.sqrt(
            1.0 - beta * beta
        )
    )

    velocity = beta * C

    total_energy_J = (

        gamma

        * BULLET.mass_kg

        * C
        * C
    )

    momentum = (

        gamma

        * BULLET.mass_kg

        * velocity
    )

    invariant = (

        total_energy_J**2

        - (momentum * C)**2
    )

    expected_invariant = (

        BULLET.mass_kg

        * C
        * C
    ) ** 2

    invariant_error = (

        abs(
            invariant
            - expected_invariant
        )

        / expected_invariant
    )

    projectile_kinetic_eV = (

        (gamma - 1.0)

        * MEDIUM.particle_mass_kg

        * C
        * C

        / QE
    )

    # Для двух одинаковых частиц:
    # одна движется с gamma, вторая покоится.
    #
    # s = 2 m^2 c^4 (1 + gamma)

    fixed_target_sqrt_s_eV = (

        PROTON_REST_ENERGY_EV

        * math.sqrt(
            2.0 * (1.0 + gamma)
        )
    )

    return {

        "beta":
            beta,

        "velocity_m_s":
            velocity,

        "status":
            "valid",

        "continued":
            True,

        "worldline":
            "timelike",

        "gamma":
            gamma,

        "proper_time_rate":
            1.0 / gamma,

        "total_energy_J":
            total_energy_J,

        "momentum_kg_m_s":
            momentum,

        "invariant_relative_error":
            invariant_error,

        "projectile_kinetic_eV":
            projectile_kinetic_eV,

        "fixed_target_sqrt_s_eV":
            fixed_target_sqrt_s_eV,
    }


# ============================================================
# КАРТА OMEGA / Q / D
# ============================================================

def evaluate_regime(
    state,
    density_m3,
    counter_name,
    counter,
    deposition_name,
    deposited_fraction,
):

    beta = state[
        "beta"
    ]

    gamma = state[
        "gamma"
    ]

    velocity = state[
        "velocity_m_s"
    ]

    tau = counter[
        "tau_s"
    ]

    binding_eV = counter[
        "binding_eV"
    ]

    # Частота столкновений по собственному времени
    # движущегося объекта.

    interaction_rate = (

        gamma

        * density_m3

        * MEDIUM.cross_section_m2

        * velocity
    )

    omega = (

        interaction_rate

        * tau
    )

    deposited_energy_eV = (

        deposited_fraction

        * state[
            "projectile_kinetic_eV"
        ]
    )

    q_value = (

        deposited_energy_eV

        / binding_eV
    )

    d_value = (

        omega

        * q_value
    )

    # Критическая плотность Omega = 1.

    denominator_omega = (

        gamma

        * MEDIUM.cross_section_m2

        * velocity

        * tau
    )

    if denominator_omega > 0.0:

        density_for_omega_1 = (

            1.0

            / denominator_omega
        )

    else:

        density_for_omega_1 = None

    # Критическая плотность D = 1.

    denominator_d = (

        denominator_omega

        * q_value
    )

    if denominator_d > 0.0:

        density_for_d_1 = (

            1.0

            / denominator_d
        )

    else:

        density_for_d_1 = None

    return {

        "beta":
            beta,

        "density_m3":
            density_m3,

        "counter":
            counter_name,

        "counter_tau_s":
            tau,

        "binding_scale_eV":
            binding_eV,

        "deposition_scenario":
            deposition_name,

        "deposited_fraction":
            deposited_fraction,

        "interaction_rate_per_proper_s":
            interaction_rate,

        "projectile_kinetic_eV":
            state[
                "projectile_kinetic_eV"
            ],

        "deposited_energy_eV":
            deposited_energy_eV,

        "Omega":
            omega,

        "Omega_regime":
            classify_omega(
                omega
            ),

        "Q":
            q_value,

        "Q_regime":
            classify_q(
                q_value
            ),

        "D":
            d_value,

        "D_regime":
            classify_d(
                d_value
            ),

        "critical_density_Omega_1_m3":
            finite_or_none(
                density_for_omega_1
            )
            if density_for_omega_1 is not None
            else None,

        "critical_density_D_1_m3":
            finite_or_none(
                density_for_d_1
            )
            if density_for_d_1 is not None
            else None,
    }


# ============================================================
# O3 / O4 / O5 / O345
# ============================================================

def build_observers(
    state,
    regimes,
):

    o3 = {

        "observer":
            "O3",

        "worldline":
            state.get(
                "worldline"
            ),

        "causality":
            (
                "standard"
                if state.get(
                    "continued"
                )
                else
                "unresolved"
            ),

        "invariant_relative_error":
            state.get(
                "invariant_relative_error"
            ),
    }

    if not state.get(
        "continued",
        False,
    ):

        o4 = {

            "observer":
                "O4",

            "internal_structure":
                "undefined_under_current_model",
        }

        o5 = {

            "observer":
                "O5",

            "external_interaction":
                "undefined_under_current_model",
        }

        consensus = (
            "known_model_domain_boundary"
        )

    else:

        max_omega = max(
            row["Omega"]
            for row in regimes
        )

        max_q = max(
            row["Q"]
            for row in regimes
        )

        max_d = max(
            row["D"]
            for row in regimes
        )

        overloaded = [

            row

            for row in regimes

            if row["Omega"] >= 1.0
        ]

        single_event_crossings = [

            row

            for row in regimes

            if row["Q"] >= 1.0
        ]

        accumulation_crossings = [

            row

            for row in regimes

            if row["D"] >= 1.0
        ]

        o4 = {

            "observer":
                "O4",

            "maximum_Omega":
                max_omega,

            "maximum_Q":
                max_q,

            "maximum_D":
                max_d,

            "counter_overload_cases":
                len(overloaded),

            "single_event_binding_crossings":
                len(single_event_crossings),

            "accumulation_crossings":
                len(accumulation_crossings),
        }

        o5 = {

            "observer":
                "O5",

            "medium_particle":
                MEDIUM.particle,

            "cross_section_m2":
                MEDIUM.cross_section_m2,

            "tested_density_count":
                len(DENSITIES),

            "tested_deposition_count":
                len(DEPOSITION_SCENARIOS),
        }

        if (
            state[
                "invariant_relative_error"
            ]
            < 1e-9
        ):

            consensus = (
                "known_physics_consistent"
            )

        else:

            consensus = (
                "invariant_failure"
            )

    return {

        "O3":
            o3,

        "O4":
            o4,

        "O5":
            o5,

        "O345":
            consensus,

        "human_layer": {

            "primary":
                (
                    "known relativistic branch"
                    if state.get(
                        "continued"
                    )
                    else
                    "known massive branch stops"
                ),

            "possible":
                (
                    "stability depends separately "
                    "on event rate, deposited energy "
                    "and relaxation time"
                ),

            "negative":
                (
                    "projectile kinetic energy is not "
                    "automatically fully deposited "
                    "into one bond"
                ),

            "unresolved":
                (
                    "exact deposition fractions and "
                    "material-specific cross sections"
                ),
        },
    }


# ============================================================
# СВЕРХСВЕТОВАЯ МАТЕМАТИЧЕСКАЯ ВЕТВЬ
# ============================================================

def investigate_superluminal():

    formulas = [

        {
            "name":
                "chi",

            "expression":
                "1/sqrt(beta**2-1)",
        },

        {
            "name":
                "xi",

            "expression":
                "sqrt(beta**2-1)",
        },
    ]

    results = []

    for beta in SUPERLUMINAL_BETAS:

        chi = safe_math(

            formulas[0][
                "expression"
            ],

            {
                "beta": beta
            },
        )

        xi = safe_math(

            formulas[1][
                "expression"
            ],

            {
                "beta": beta
            },
        )

        results.append({

            "beta":
                beta,

            "chi":
                chi,

            "xi":
                xi,

            "chi_times_xi":
                chi * xi,

            "identity_error":
                abs(
                    chi * xi - 1.0
                ),

            "physical_status":
                "unresolved_not_established",
        })

    for formula in formulas:

        formula[
            "fingerprint"
        ] = hashlib.sha256(

            formula[
                "expression"
            ].encode()

        ).hexdigest()

        formula[
            "status"
        ] = "candidate_math_valid"

    return {

        "formulas":
            formulas,

        "identity":
            "chi_times_xi_equals_one",

        "identity_status":
            "mathematical_identity",

        "physical_status":
            "unresolved_not_established",

        "tests":
            results,
    }


# ============================================================
# SELF-TEST
# ============================================================

def selftest():

    state = relativistic_state(
        0.6
    )

    assert abs(
        state["gamma"] - 1.25
    ) < 1e-12

    assert (
        state[
            "invariant_relative_error"
        ]
        < 1e-9
    )

    assert (
        relativistic_state(
            1.0
        )[
            "continued"
        ]
        is False
    )

    chi = safe_math(

        "1/sqrt(beta**2-1)",

        {
            "beta": 2.0
        },
    )

    xi = safe_math(

        "sqrt(beta**2-1)",

        {
            "beta": 2.0
        },
    )

    assert abs(
        chi * xi - 1.0
    ) < 1e-12

    try:

        safe_math(

            "__import__('os').system('id')",

            {},
        )

    except Exception:

        pass

    else:

        raise AssertionError(
            "unsafe_AST_accepted"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    selftest()

    states = []
    stability_map = []

    for beta in BETAS:

        state = relativistic_state(
            beta
        )

        local_regimes = []

        for density in DENSITIES:

            for (
                counter_name,
                counter,
            ) in CLOCKS.items():

                for (
                    deposition_name,
                    deposited_fraction,
                ) in DEPOSITION_SCENARIOS.items():

                    row = evaluate_regime(

                        state,
                        density,
                        counter_name,
                        counter,
                        deposition_name,
                        deposited_fraction,
                    )

                    stability_map.append(
                        row
                    )

                    local_regimes.append(
                        row
                    )

        observers = build_observers(
            state,
            local_regimes,
        )

        states.append({

            **state,

            **observers,
        })

    # Добавляем границу и точки > c,
    # но карту обычной материи там не продолжаем.

    for beta in [
        1.0,
        1.01,
        2.0,
        10.0,
        100.0,
    ]:

        state = relativistic_state(
            beta
        )

        observers = build_observers(
            state,
            [],
        )

        states.append({

            **state,

            **observers,
        })

    superluminal = (
        investigate_superluminal()
    )

    # --------------------------------------------------------
    # ПОИСК ПЕРВЫХ ПЕРЕХОДОВ
    # --------------------------------------------------------

    transitions = {

        "Omega_ge_1": [],
        "Q_ge_1": [],
        "D_ge_1": [],
    }

    for row in stability_map:

        if row["Omega"] >= 1.0:

            transitions[
                "Omega_ge_1"
            ].append(row)

        if row["Q"] >= 1.0:

            transitions[
                "Q_ge_1"
            ].append(row)

        if row["D"] >= 1.0:

            transitions[
                "D_ge_1"
            ].append(row)

    summary = {

        "tested_subluminal_speeds":
            len(BETAS),

        "tested_densities":
            len(DENSITIES),

        "tested_counters":
            len(CLOCKS),

        "tested_deposition_scenarios":
            len(DEPOSITION_SCENARIOS),

        "map_points":
            len(stability_map),

        "Omega_crossing_count":
            len(
                transitions[
                    "Omega_ge_1"
                ]
            ),

        "Q_crossing_count":
            len(
                transitions[
                    "Q_ge_1"
                ]
            ),

        "D_crossing_count":
            len(
                transitions[
                    "D_ge_1"
                ]
            ),
    }

    report = {

        "schema":
            "malysh.bullet100c.v4",

        "created_utc":
            now(),

        "bullet":
            asdict(
                BULLET
            ),

        "medium":
            asdict(
                MEDIUM
            ),

        "proton_rest_energy_eV":
            PROTON_REST_ENERGY_EV,

        "model_notice":
            (
                "Exploratory parameter map. "
                "Deposition fractions, binding scales "
                "and cross section are model inputs."
            ),

        "criteria": {

            "Omega":
                "interaction_rate * internal_tau",

            "Q":
                (
                    "deposited_energy_per_event "
                    "/ binding_scale"
                ),

            "D":
                "Omega * Q",
        },

        "summary":
            summary,

        "states":
            states,

        "transitions":
            transitions,

        "superluminal_mathematics":
            superluminal,
    }

    REPORT.write_text(

        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),

        encoding="utf-8",
    )

    with MAP_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        for row in stability_map:

            file.write(

                json.dumps(
                    row,
                    ensure_ascii=False,
                )

                + "\n"
            )

    with FORMULAS.open(
        "w",
        encoding="utf-8",
    ) as file:

        for formula in superluminal[
            "formulas"
        ]:

            file.write(

                json.dumps(
                    formula,
                    ensure_ascii=False,
                )

                + "\n"
            )

    write_audit(
        "experiment_complete",
        {
            "schema":
                report["schema"],

            **summary,
        },
    )

    print()
    print("MALYSH BULLET-100C v4")
    print("======================")
    print("SELFTEST OK")
    print()

    for state in states:

        print(
            f"beta={state['beta']:>9} "
            f"status={state['status']} "
            f"O345={state['O345']}"
        )

        if state.get(
            "continued",
            False,
        ):

            print(
                "  "
                f"gamma={state['gamma']:.8g} "
                f"Kp={state['projectile_kinetic_eV']:.6g} eV "
                f"sqrt(s)={state['fixed_target_sqrt_s_eV']:.6g} eV"
            )

            print(
                "  "
                f"max Omega={state['O4']['maximum_Omega']:.6g} "
                f"max Q={state['O4']['maximum_Q']:.6g} "
                f"max D={state['O4']['maximum_D']:.6g}"
            )

    print()
    print("MAP POINTS:", summary["map_points"])

    print(
        "OMEGA CROSSINGS:",
        summary["Omega_crossing_count"],
    )

    print(
        "Q CROSSINGS:",
        summary["Q_crossing_count"],
    )

    print(
        "D CROSSINGS:",
        summary["D_crossing_count"],
    )

    print()
    print(
        "SUPERLUMINAL PATTERN:",
        superluminal[
            "identity"
        ],
        superluminal[
            "identity_status"
        ],
    )

    print()
    print("REPORT:", REPORT)
    print("MAP:", MAP_FILE)
    print("FORMULAS:", FORMULAS)
    print("AUDIT:", AUDIT)


if __name__ == "__main__":
    main()
