#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MALYSH BULLET-100C v3

Исследовательский эксперимент:

1. Досветовая ветвь использует специальную относительность.
2. При beta >= 1 известная массивная кинематика останавливается.
3. Сверхсветовые выражения рассматриваются только как гипотезы.
4. Проверяются внешние взаимодействия и внутренние счётчики.
5. O3/O4/O5 формируют независимые наблюдения.
6. O345 сопоставляет их.
7. Human Layer сохраняет primary/possible/negative/unresolved.
8. Новые формулы проходят безопасную математическую проверку.
9. Старые результаты архивируются внешним установочным блоком.

Только стандартная библиотека Python.
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

ROOT = Path.home() / "malysh_project"
OUT = ROOT / "experiments" / "bullet_100c"

REPORT = OUT / "report.json"
FORMULAS = OUT / "learned_formulas.jsonl"
AUDIT = OUT / "audit.jsonl"

OUT.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# ОБЪЕКТ И СРЕДА
# ============================================================

@dataclass
class Bullet:

    mass_kg: float = 0.008
    length_m: float = 0.015
    diameter_m: float = 0.009
    temperature_K: float = 293.15


@dataclass
class Medium:

    name: str = "thin_hydrogen_test"
    density_m3: float = 1e6
    cross_section_m2: float = 1e-20
    particle_mass_kg: float = PROTON_MASS


BULLET = Bullet()
MEDIUM = Medium()


# ============================================================
# ВНУТРЕННИЕ СЧЁТЧИКИ
#
# Это исследовательские характерные масштабы.
# Они пока не являются точной моделью конкретного материала.
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


# ============================================================
# СЛУЖЕБНЫЕ ФУНКЦИИ
# ============================================================

def now():

    return datetime.now(
        timezone.utc
    ).isoformat()


def audit(
    kind,
    data,
):

    record = {

        "utc": now(),

        "kind": kind,

        **data,
    }

    with AUDIT.open(
        "a",
        encoding="utf-8",
    ) as f:

        f.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )


# ============================================================
# БЕЗОПАСНАЯ МАТЕМАТИКА
#
# Никаких eval, exec, import или доступа к системе.
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

            operation = (
                BINARY_OPERATORS[
                    type(node.op)
                ]
            )

            left = calculate(
                node.left
            )

            right = calculate(
                node.right
            )

            return operation(
                left,
                right,
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
# КЛАССИФИКАЦИЯ НАГРУЗКИ СЧЁТЧИКА
# ============================================================

def classify_counter_load(
    events_per_tick,
):

    if events_per_tick < 0.1:

        return "resolved"

    if events_per_tick < 1.0:

        return "loaded"

    if events_per_tick < 10.0:

        return "overloaded"

    return "continuum_or_unresolved"


# ============================================================
# ИЗВЕСТНАЯ ФИЗИЧЕСКАЯ ВЕТВЬ
# ============================================================

def known_physics(
    beta,
):

    velocity = beta * C

    base = {

        "beta":
            beta,

        "velocity_m_s":
            velocity,

        "branch":
            "known_physics",
    }

    # --------------------------------------------------------
    # СВЕТОВОЙ ПРЕДЕЛ
    # --------------------------------------------------------

    if beta >= 1.0:

        if beta == 1.0:

            status = (
                "massive_object_light_limit"
            )

            worldline = (
                "null_boundary"
            )

        else:

            status = (
                "outside_known_"
                "massive_particle_dynamics"
            )

            worldline = (
                "spacelike"
            )

        return {

            **base,

            "status":
                status,

            "worldline":
                worldline,

            "continued":
                False,
        }

    # --------------------------------------------------------
    # ДОСВЕТОВАЯ ВЕТВЬ
    # --------------------------------------------------------

    gamma = (
        1.0
        / math.sqrt(
            1.0 - beta * beta
        )
    )

    mass = BULLET.mass_kg

    energy = (
        gamma
        * mass
        * C
        * C
    )

    momentum = (
        gamma
        * mass
        * velocity
    )

    proper_time_rate = (
        1.0
        / gamma
    )

    invariant = (
        energy * energy
        - (momentum * C) ** 2
    )

    expected_invariant = (
        mass
        * C
        * C
    ) ** 2

    invariant_relative_error = (

        abs(
            invariant
            - expected_invariant
        )

        / expected_invariant
    )

    # --------------------------------------------------------
    # ЧАСТОТА СТОЛКНОВЕНИЙ
    # ПО СОБСТВЕННОМУ ВРЕМЕНИ ПУЛИ
    # --------------------------------------------------------

    interaction_rate = (

        gamma

        * MEDIUM.density_m3

        * MEDIUM.cross_section_m2

        * velocity
    )

    # --------------------------------------------------------
    # ЭНЕРГИЯ ОДНОЙ ВСТРЕЧНОЙ ЧАСТИЦЫ
    # В СИСТЕМЕ ПУЛИ
    # --------------------------------------------------------

    single_hit_energy_J = (

        (gamma - 1.0)

        * MEDIUM.particle_mass_kg

        * C
        * C
    )

    single_hit_energy_eV = (

        single_hit_energy_J

        / QE
    )

    # --------------------------------------------------------
    # ВНУТРЕННИЕ СЧЁТЧИКИ
    # --------------------------------------------------------

    internal_counters = {}

    for name, configuration in CLOCKS.items():

        tau = configuration[
            "tau_s"
        ]

        binding_eV = configuration[
            "binding_eV"
        ]

        # Число внешних событий
        # за один внутренний такт.

        events_per_tick = (
            interaction_rate
            * tau
        )

        # Приближённый энергетический
        # индекс накопленной нагрузки
        # за один такт.

        damage_index = (

            interaction_rate

            * single_hit_energy_eV

            * tau

            / binding_eV
        )

        internal_counters[
            name
        ] = {

            "tau_s":
                tau,

            "binding_scale_eV":
                binding_eV,

            "external_events_per_tick":
                events_per_tick,

            "load":
                classify_counter_load(
                    events_per_tick
                ),

            "damage_index":
                damage_index,

            "binding_scale_crossed_per_hit":
                (
                    single_hit_energy_eV
                    >= binding_eV
                ),
        }

    return {

        **base,

        "status":
            "valid",

        "worldline":
            "timelike",

        "continued":
            True,

        "gamma":
            gamma,

        "proper_time_rate":
            proper_time_rate,

        "energy_J":
            energy,

        "momentum_kg_m_s":
            momentum,

        "invariant_relative_error":
            invariant_relative_error,

        "interaction_rate_per_proper_s":
            interaction_rate,

        "single_hit_energy_J":
            single_hit_energy_J,

        "single_hit_energy_eV":
            single_hit_energy_eV,

        "internal_counters":
            internal_counters,
    }


# ============================================================
# O3 / O4 / O5 / O345
# ============================================================

def observers(
    result,
):

    beta = result[
        "beta"
    ]

    if beta < 1.0:

        geometry = (
            "timelike"
        )

        causality = (
            "standard"
        )

    elif beta == 1.0:

        geometry = (
            "null"
        )

        causality = (
            "unresolved"
        )

    else:

        geometry = (
            "spacelike"
        )

        causality = (
            "unresolved"
        )

    o3 = {

        "observer":
            "O3",

        "geometry":
            geometry,

        "causality":
            causality,
    }

    if result.get(
        "continued",
        False,
    ):

        counter_values = [

            value[
                "external_events_per_tick"
            ]

            for value
            in result[
                "internal_counters"
            ].values()
        ]

        maximum_load = max(
            counter_values,
            default=0.0,
        )

        o4 = {

            "observer":
                "O4",

            "counter_load_max":
                maximum_load,

            "all_counters_resolve_events":
                maximum_load < 1.0,
        }

        o5 = {

            "observer":
                "O5",

            "medium":
                MEDIUM.name,

            "interaction_rate_per_proper_s":
                result[
                    "interaction_rate_per_proper_s"
                ],

            "single_hit_energy_eV":
                result[
                    "single_hit_energy_eV"
                ],
        }

        if (
            result[
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

    else:

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
                "undefined",
        }

        consensus = (
            "known_model_domain_boundary"
        )

    human_layer = {

        "primary":
            (
                "known physics result"
                if beta < 1.0
                else "known massive branch stops"
            ),

        "possible":
            "test hypotheses separately",

        "negative":
            (
                "do not relabel formal continuation "
                "as established physics"
            ),

        "unresolved":
            "composite matter at or above c",
    }

    return {

        **result,

        "O3":
            o3,

        "O4":
            o4,

        "O5":
            o5,

        "O345":
            consensus,

        "human_layer":
            human_layer,
    }


# ============================================================
# ИССЛЕДОВАНИЕ НОВЫХ ФОРМУЛ
# ============================================================

def discover_formulas():

    specifications = [

        (
            "superluminal_real_scale",

            "1/sqrt(beta**2-1)",

            (
                "Real mathematical scale for beta > 1; "
                "physical meaning unresolved"
            ),
        ),

        (
            "spacelike_scale",

            "sqrt(beta**2-1)",

            (
                "Spacelike mathematical scale; "
                "not ordinary proper time"
            ),
        ),
    ]

    samples = [
        1.01,
        1.1,
        2.0,
        10.0,
        100.0,
    ]

    formulas = []

    for (
        name,
        expression,
        reason,
    ) in specifications:

        tests = []

        for beta in samples:

            try:

                value = safe_math(

                    expression,

                    {
                        "beta": beta
                    },
                )

                tests.append({

                    "beta":
                        beta,

                    "value":
                        value,

                    "valid":
                        True,
                })

            except Exception as error:

                tests.append({

                    "beta":
                        beta,

                    "value":
                        None,

                    "valid":
                        False,

                    "error":
                        str(error),
                })

        if all(
            test["valid"]
            for test in tests
        ):

            status = (
                "candidate_math_valid"
            )

        else:

            status = (
                "hypothesis_failed_math"
            )

        fingerprint = hashlib.sha256(
            expression.encode()
        ).hexdigest()

        formula = {

            "name":
                name,

            "expression":
                expression,

            "reason":
                reason,

            "status":
                status,

            "physical_status":
                "unresolved_not_established",

            "fingerprint":
                fingerprint,

            "tests":
                tests,
        }

        formulas.append(
            formula
        )

        audit(
            "formula_tested",
            {
                "name":
                    name,

                "status":
                    status,
            },
        )

    # --------------------------------------------------------
    # МЕЖФОРМУЛЬНЫЙ ПАТТЕРН
    #
    # chi = 1/sqrt(beta² - 1)
    # xi  = sqrt(beta² - 1)
    #
    # Проверяем chi * xi = 1.
    # --------------------------------------------------------

    pattern_tests = []

    for beta in samples:

        chi = safe_math(

            specifications[0][1],

            {
                "beta": beta
            },
        )

        xi = safe_math(

            specifications[1][1],

            {
                "beta": beta
            },
        )

        product = (
            chi * xi
        )

        pattern_tests.append({

            "beta":
                beta,

            "chi":
                chi,

            "xi":
                xi,

            "chi_times_xi":
                product,

            "error_from_one":
                abs(
                    product - 1.0
                ),
        })

    pattern = {

        "pattern":
            "chi_times_xi_equals_one",

        "status":
            "mathematical_identity_on_test_domain",

        "physical_meaning":
            "unresolved",

        "tests":
            pattern_tests,
    }

    audit(
        "cross_formula_pattern",
        {
            "pattern":
                pattern["pattern"],

            "status":
                pattern["status"],
        },
    )

    return (
        formulas,
        pattern,
    )


# ============================================================
# SELF-TEST
# ============================================================

def selftest():

    result = known_physics(
        0.6
    )

    assert abs(
        result["gamma"]
        - 1.25
    ) < 1e-12

    assert (
        known_physics(
            1.0
        )["continued"]
        is False
    )

    assert (
        known_physics(
            100.0
        )["status"]
        ==
        "outside_known_massive_particle_dynamics"
    )

    formula_value = safe_math(

        "1/sqrt(beta**2-1)",

        {
            "beta": 2.0
        },
    )

    assert abs(
        formula_value
        - 1.0 / math.sqrt(3.0)
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

    speeds = [

        0.0,
        0.1,
        0.5,
        0.9,
        0.99,
        0.999,
        0.9999,
        1.0,
        1.01,
        1.1,
        2.0,
        10.0,
        100.0,
    ]

    results = []

    for beta in speeds:

        result = observers(
            known_physics(
                beta
            )
        )

        results.append(
            result
        )

        audit(
            "simulation_step",
            {
                "beta":
                    beta,

                "status":
                    result["status"],

                "O345":
                    result["O345"],
            },
        )

    (
        formulas,
        pattern,
    ) = discover_formulas()

    report = {

        "schema":
            "malysh.bullet100c.v3",

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

        "counter_model_note":
            (
                "Synthetic characteristic times; "
                "exploratory, not material-specific proof"
            ),

        "results":
            results,

        "discovered_formulas":
            formulas,

        "cross_formula_pattern":
            pattern,
    }

    REPORT.write_text(

        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),

        encoding="utf-8",
    )

    with FORMULAS.open(
        "a",
        encoding="utf-8",
    ) as f:

        for formula in formulas:

            f.write(

                json.dumps(
                    formula,
                    ensure_ascii=False,
                )

                + "\n"
            )

    audit(
        "experiment_complete",
        {
            "schema":
                report["schema"],

            "points":
                len(results),

            "formula_candidates":
                len(formulas),
        },
    )

    print(
        "SELFTEST OK"
    )

    for result in results:

        print(
            f"beta={result['beta']:>7} "
            f"status={result['status']} "
            f"O345={result['O345']}"
        )

        if result.get(
            "continued",
            False,
        ):

            print(
                "  "
                f"gamma={result['gamma']:.9g} "
                f"hit={result['single_hit_energy_eV']:.6g} eV "
                f"rate={result['interaction_rate_per_proper_s']:.6g}"
                "/proper_s"
            )

            counter_text = ", ".join(

                f"{name}:{data['load']}"

                for name, data
                in result[
                    "internal_counters"
                ].items()
            )

            print(
                "  counters:",
                counter_text,
            )

    print(
        "FORMULAS:"
    )

    for formula in formulas:

        print(
            " ",
            formula["name"],
            formula["status"],
        )

    print(
        "PATTERN:",
        pattern["pattern"],
        pattern["status"],
    )

    print(
        "REPORT:",
        REPORT,
    )


if __name__ == "__main__":
    main()
