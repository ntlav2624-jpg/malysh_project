#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MALYSH PHOTON-1E6C

Исследовательский эксперимент.

Known Physics:
    стандартный фотон в вакууме:
        v = c
        m0 = 0
        E = h*f
        p = E/c
        E^2 - p^2*c^2 = 0

Hypothesis Branch:
    формально исследуем beta > 1 вплоть до 1 000 000.

Цель не "доказать сверхсветовой фотон", а определить:
1. какой инвариант первым ломается;
2. можно ли сохранить E и p вещественными;
3. можно ли сохранить null-интервал;
4. можно ли сохранить E = pc;
5. что придётся изменить, чтобы beta > 1 имело смысл;
6. существуют ли новые математические паттерны.

Результаты гипотез не объявляются установленной физикой.
"""

from __future__ import annotations

import json
import math
import hashlib

from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# КОНСТАНТЫ
# ============================================================

C = 299_792_458.0
H = 6.626_070_15e-34
HBAR = H / (2.0 * math.pi)

ROOT = Path.home() / "malysh_project"

OUT = (
    ROOT
    / "experiments"
    / "photon_1e6c"
)

OUT.mkdir(
    parents=True,
    exist_ok=True,
)

REPORT = (
    OUT
    / "report.json"
)

AUDIT = (
    OUT
    / "audit.jsonl"
)


# ============================================================
# ИСХОДНЫЙ ФОТОН
#
# Используем частоту как параметр.
# 5e14 Hz примерно соответствует
# оптическому масштабу.
# ============================================================

FREQUENCY_HZ = 5.0e14

E0 = H * FREQUENCY_HZ

P0 = E0 / C


# ============================================================
# ТОЧКИ ЭКСПЕРИМЕНТА
# ============================================================

BETAS = [
    1.0,
    1.000001,
    1.01,
    1.1,
    2.0,
    10.0,
    100.0,
    1_000.0,
    10_000.0,
    100_000.0,
    1_000_000.0,
]


# ============================================================
# СЛУЖЕБНЫЕ
# ============================================================

def now():

    return datetime.now(
        timezone.utc
    ).isoformat()


def audit(
    kind,
    data,
):

    with AUDIT.open(
        "a",
        encoding="utf-8",
    ) as file:

        file.write(

            json.dumps(
                {
                    "utc": now(),
                    "kind": kind,
                    **data,
                },
                ensure_ascii=False,
            )

            + "\n"
        )


# ============================================================
# STANDARD PHOTON
# ============================================================

def standard_photon():

    velocity = C

    energy = E0

    momentum = P0

    # Для безмассового фотона

    invariant = (
        energy**2
        - (momentum * C)**2
    )

    interval_factor = (
        1.0
        - velocity**2 / C**2
    )

    return {

        "beta":
            1.0,

        "velocity_m_s":
            velocity,

        "status":
            "standard_photon",

        "worldline":
            "null",

        "rest_mass":
            0.0,

        "frequency_Hz":
            FREQUENCY_HZ,

        "energy_J":
            energy,

        "momentum_kg_m_s":
            momentum,

        "E_over_pc":
            (
                energy
                / (momentum * C)
            ),

        "energy_momentum_invariant":
            invariant,

        "interval_factor":
            interval_factor,

        "standard_physics":
            True,
    }


# ============================================================
# ФОРМАЛЬНЫЙ beta > 1
# ============================================================

def hypothetical_state(
    beta,
):

    velocity = (
        beta * C
    )

    # --------------------------------------------------------
    # ГИПОТЕЗА A
    #
    # Сохраняем энергию исходного фотона.
    # Принудительно определяем:
    #
    # p = E/v
    #
    # Это НЕ стандартное фотонное соотношение.
    # --------------------------------------------------------

    energy_A = E0

    momentum_A = (
        energy_A
        / velocity
    )

    invariant_A = (

        energy_A**2

        - (
            momentum_A
            * C
        )**2
    )

    effective_m2_A = (
        invariant_A
        / C**4
    )

    # --------------------------------------------------------
    # Проверяем исходное фотонное E = pc
    # --------------------------------------------------------

    photon_relation_A = (

        energy_A
        / (
            momentum_A
            * C
        )
    )

    # При p = E/v получаем
    # E/(pc) = v/c = beta.

    # --------------------------------------------------------
    # ГИПОТЕЗА B
    #
    # Сохраняем фотонное E = pc.
    #
    # Тогда p = E/c независимо от beta.
    #
    # Проверяем, согласуется ли это
    # одновременно с E = pv.
    # --------------------------------------------------------

    energy_B = E0

    momentum_B = (
        energy_B
        / C
    )

    invariant_B = (

        energy_B**2

        - (
            momentum_B
            * C
        )**2
    )

    transport_energy_B = (
        momentum_B
        * velocity
    )

    mismatch_B = (

        transport_energy_B
        / energy_B
    )

    # --------------------------------------------------------
    # GEOMETRY
    # --------------------------------------------------------

    interval_factor = (
        1.0
        - beta**2
    )

    spacelike_scale = (
        math.sqrt(
            beta**2 - 1.0
        )
    )

    reciprocal_scale = (
        1.0
        / spacelike_scale
    )

    reciprocal_identity = (

        spacelike_scale

        * reciprocal_scale
    )

    return {

        "beta":
            beta,

        "velocity_m_s":
            velocity,

        "status":
            "hypothesis_only",

        "standard_physics":
            False,

        "worldline_if_interpreted_as_velocity":
            "spacelike",

        "interval_factor":
            interval_factor,

        # ----------------------------------------------------
        # HYPOTHESIS A
        # ----------------------------------------------------

        "hypothesis_A_keep_E_and_use_p_E_over_v": {

            "energy_J":
                energy_A,

            "momentum":
                momentum_A,

            "E_over_pc":
                photon_relation_A,

            "invariant":
                invariant_A,

            "effective_mass_squared":
                effective_m2_A,

            "photon_E_equals_pc_preserved":
                abs(
                    photon_relation_A - 1.0
                ) < 1e-12,
        },

        # ----------------------------------------------------
        # HYPOTHESIS B
        # ----------------------------------------------------

        "hypothesis_B_keep_E_equals_pc": {

            "energy_J":
                energy_B,

            "momentum":
                momentum_B,

            "invariant":
                invariant_B,

            "E_equals_pc":
                True,

            "pv_over_E":
                mismatch_B,

            "transport_relation_preserved":
                abs(
                    mismatch_B - 1.0
                ) < 1e-12,
        },

        # ----------------------------------------------------
        # MATHEMATICAL SCALES
        # ----------------------------------------------------

        "spacelike_scale":
            spacelike_scale,

        "reciprocal_spacelike_scale":
            reciprocal_scale,

        "scale_product":
            reciprocal_identity,

        "physical_status":
            "unresolved_not_established",
    }


# ============================================================
# O3
#
# Геометрия
# ============================================================

def observer_O3(
    state,
):

    beta = state[
        "beta"
    ]

    if beta == 1.0:

        return {

            "observer":
                "O3",

            "geometry":
                "null",

            "causal_status":
                "standard_photon",
        }

    return {

        "observer":
            "O3",

        "geometry":
            "spacelike",

        "causal_status":
            "not_standard_photon_kinematics",
    }


# ============================================================
# O4
#
# Энергия / импульс / фотонный инвариант
# ============================================================

def observer_O4(
    state,
):

    if state[
        "beta"
    ] == 1.0:

        return {

            "observer":
                "O4",

            "E_equals_pc":
                True,

            "mass_shell":
                "massless",

            "internal_clock":
                "not_defined_as_massive_rest_clock",
        }

    A = state[
        "hypothesis_A_keep_E_and_use_p_E_over_v"
    ]

    B = state[
        "hypothesis_B_keep_E_equals_pc"
    ]

    return {

        "observer":
            "O4",

        "hypothesis_A_E_pc_preserved":
            A[
                "photon_E_equals_pc_preserved"
            ],

        "hypothesis_B_transport_preserved":
            B[
                "transport_relation_preserved"
            ],

        "simultaneously_preserved":
            (
                A[
                    "photon_E_equals_pc_preserved"
                ]
                and
                B[
                    "transport_relation_preserved"
                ]
            ),
    }


# ============================================================
# O5
#
# Логика сохранения
# ============================================================

def observer_O5(
    state,
):

    beta = state[
        "beta"
    ]

    if beta == 1.0:

        return {

            "observer":
                "O5",

            "known_photon_definition":
                "consistent",
        }

    return {

        "observer":
            "O5",

        "known_photon_definition":
            "not_preserved",

        "reason":
            (
                "beta > 1 cannot preserve all tested "
                "standard photon relations simultaneously"
            ),
    }


# ============================================================
# O345
# ============================================================

def observer_O345(
    state,
    o3,
    o4,
    o5,
):

    beta = state[
        "beta"
    ]

    if beta == 1.0:

        consensus = (
            "standard_photon"
        )

    else:

        if o4[
            "simultaneously_preserved"
        ]:

            consensus = (
                "candidate_consistent_extension"
            )

        else:

            consensus = (
                "requires_changed_physics"
            )

    return {

        "observer":
            "O345",

        "consensus":
            consensus,

        "geometry":
            o3,

        "energy_momentum":
            o4,

        "definition_check":
            o5,
    }


# ============================================================
# HUMAN LAYER
# ============================================================

def human_layer(
    beta,
):

    if beta == 1.0:

        return {

            "primary":
                (
                    "standard photon travels at c"
                ),

            "possible":
                (
                    "energy may change through frequency "
                    "without changing vacuum speed"
                ),

            "negative":
                (
                    "no need for superluminal hypothesis"
                ),

            "unresolved":
                None,
        }

    return {

        "primary":
            (
                "beta > 1 is not a standard photon state"
            ),

        "possible":
            (
                "a new object or modified dispersion "
                "relation could be hypothesized"
            ),

        "negative":
            (
                "do not call the mathematical continuation "
                "an experimentally established photon"
            ),

        "unresolved":
            (
                "whether any consistent new physics "
                "can realize the proposed state"
            ),
    }


# ============================================================
# SELF TEST
# ============================================================

def selftest():

    photon = standard_photon()

    assert (
        photon[
            "worldline"
        ]
        == "null"
    )

    assert abs(
        photon[
            "E_over_pc"
        ]
        - 1.0
    ) < 1e-12

    assert abs(
        photon[
            "energy_momentum_invariant"
        ]
    ) < 1e-40

    state = hypothetical_state(
        2.0
    )

    assert abs(

        state[
            "spacelike_scale"
        ]

        * state[
            "reciprocal_spacelike_scale"
        ]

        - 1.0

    ) < 1e-12


# ============================================================
# MAIN
# ============================================================

def main():

    selftest()

    results = []

    # --------------------------------------------------------
    # STANDARD PHOTON
    # --------------------------------------------------------

    standard = (
        standard_photon()
    )

    o3 = observer_O3(
        standard
    )

    o4 = observer_O4(
        standard
    )

    o5 = observer_O5(
        standard
    )

    o345 = observer_O345(
        standard,
        o3,
        o4,
        o5,
    )

    standard[
        "O3"
    ] = o3

    standard[
        "O4"
    ] = o4

    standard[
        "O5"
    ] = o5

    standard[
        "O345"
    ] = o345

    standard[
        "human_layer"
    ] = human_layer(
        1.0
    )

    results.append(
        standard
    )

    # --------------------------------------------------------
    # HYPOTHETICAL > c STATES
    # --------------------------------------------------------

    for beta in BETAS:

        if beta == 1.0:
            continue

        state = hypothetical_state(
            beta
        )

        o3 = observer_O3(
            state
        )

        o4 = observer_O4(
            state
        )

        o5 = observer_O5(
            state
        )

        o345 = observer_O345(
            state,
            o3,
            o4,
            o5,
        )

        state[
            "O3"
        ] = o3

        state[
            "O4"
        ] = o4

        state[
            "O5"
        ] = o5

        state[
            "O345"
        ] = o345

        state[
            "human_layer"
        ] = human_layer(
            beta
        )

        results.append(
            state
        )

        audit(
            "hypothesis_step",
            {
                "beta":
                    beta,

                "consensus":
                    o345[
                        "consensus"
                    ],
            },
        )

    # --------------------------------------------------------
    # ПАТТЕРНЫ
    # --------------------------------------------------------

    patterns = {

        "standard_photon": {

            "v":
                "c",

            "E":
                "h*f",

            "p":
                "E/c",

            "mass_shell":
                "E^2-p^2*c^2=0",
        },

        "discovered_superluminal_pattern": {

            "chi":
                "1/sqrt(beta^2-1)",

            "xi":
                "sqrt(beta^2-1)",

            "identity":
                "chi*xi=1",

            "physical_status":
                "mathematical_only",
        },

        "conflict_pattern": {

            "statement":
                (
                    "For beta>1, keeping p=E/v "
                    "breaks E=pc; keeping E=pc "
                    "breaks E=pv."
                ),

            "interpretation":
                (
                    "At least one standard relation "
                    "must be modified."
                ),

            "physical_status":
                "hypothesis_not_established",
        },
    }

    report = {

        "schema":
            "malysh.photon1e6c.v1",

        "created_utc":
            now(),

        "input_frequency_Hz":
            FREQUENCY_HZ,

        "input_energy_J":
            E0,

        "input_momentum":
            P0,

        "maximum_beta":
            1_000_000.0,

        "formal_maximum_velocity_m_s":
            1_000_000.0 * C,

        "results":
            results,

        "patterns":
            patterns,
    }

    REPORT.write_text(

        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),

        encoding="utf-8",
    )

    audit(
        "experiment_complete",
        {
            "schema":
                report[
                    "schema"
                ],

            "states":
                len(results),

            "maximum_beta":
                1_000_000.0,
        },
    )

    # --------------------------------------------------------
    # PRINT
    # --------------------------------------------------------

    print()
    print(
        "MALYSH PHOTON-1E6C"
    )

    print(
        "==================="
    )

    print(
        "SELFTEST OK"
    )

    print()

    for state in results:

        beta = state[
            "beta"
        ]

        consensus = state[
            "O345"
        ][
            "consensus"
        ]

        print(
            f"beta={beta:>12g} "
            f"v={state['velocity_m_s']:.6e} m/s "
            f"O345={consensus}"
        )

        if beta > 1.0:

            A = state[
                "hypothesis_A_keep_E_and_use_p_E_over_v"
            ]

            B = state[
                "hypothesis_B_keep_E_equals_pc"
            ]

            print(
                "  "
                f"A: E/(pc)={A['E_over_pc']:.6g} "
                f"mass2={A['effective_mass_squared']:.6e}"
            )

            print(
                "  "
                f"B: pv/E={B['pv_over_E']:.6g}"
            )

            print(
                "  "
                f"chi={state['reciprocal_spacelike_scale']:.6g} "
                f"xi={state['spacelike_scale']:.6g} "
                f"product={state['scale_product']:.12g}"
            )

    print()

    print(
        "MAX FORMAL SPEED:"
    )

    print(
        1_000_000.0 * C,
        "m/s"
    )

    print()

    print(
        "KNOWN PHYSICS RESULT:"
    )

    print(
        "photon remains at c in vacuum"
    )

    print()

    print(
        "HYPOTHESIS RESULT:"
    )

    print(
        "beta > 1 requires changing at least "
        "one standard photon relation"
    )

    print()

    print(
        "REPORT:",
        REPORT
    )


if __name__ == "__main__":
    main()
