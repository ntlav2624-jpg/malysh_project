
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional
import hashlib
import json
import math


TAU = 2.0 * math.pi
EPS = 1e-12


def mean(values):
    return sum(values) / len(values) if values else 0.0


def sign(value, eps=1e-12):
    if value > eps:
        return 1
    if value < -eps:
        return -1
    return 0


def stable(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )


def digest(value):
    return hashlib.sha256(
        stable(value).encode("utf-8")
    ).hexdigest()


@dataclass
class TemporalState:
    time: float
    outer_phase: list
    outer_frequency: list
    inner_phase: float
    inner_frequency: float


@dataclass
class SmallZeroState:
    projection: float
    internal_energy: float
    distinguishability: float
    phase: float
    frequency: float
    orientation: tuple
    status: str
    precision: float


@dataclass
class ZeroSymbol:
    symbol_id: str
    projection: float
    frequency: float
    phase: float
    chirality: int
    temporal_direction: int
    polarity: int
    geometry_signature: str
    history_signature: str


class ReflectionWAL:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def append(self, event, payload):
        record = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "event": event,
            "payload": payload,
        }

        with self.path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                stable(record) + "\n"
            )

    def tail(self, limit=64):
        if not self.path.exists():
            return []

        lines = self.path.read_text(
            encoding="utf-8"
        ).splitlines()[-limit:]

        result = []

        for line in lines:
            try:
                result.append(
                    json.loads(line)
                )
            except Exception:
                pass

        return result


class FullReflections:
    """
    Parallel reasoning layer.

    AS_BEFORE:
        preserves original Malysh result.

    AS_NOW:
        executable experimental reasoning:
        - small zero
        - zero alphabet
        - time/frequency/phase separation
        - B3 + 8 lemniscate phase channels
        - clock/code
        - orientation cube
        - possibility branch
        - history/WAL
        - WRITE -> EVOLVE -> READ
        - ablations

    This is a computational model.
    It does not declare the model to be
    established physical law.
    """

    VERSION = "full-reflections.v1"

    def __init__(
        self,
        root=None,
        legacy_hook: Optional[Callable] = None,
    ):
        if root is None:
            root = (
                Path(__file__)
                .resolve()
                .parent
                .parent
            )

        self.root = Path(root)
        self.legacy_hook = legacy_hook

        self.wal = ReflectionWAL(
            self.root
            / "runtime"
            / "reflections"
            / "reflections.wal.jsonl"
        )

    # -------------------------------------------------
    # Basic data field
    # -------------------------------------------------

    def _normalize(self, data):
        values = [
            float(value)
            for value in data
        ]

        if not values:
            raise ValueError(
                "empty input"
            )

        center = mean(values)

        scale = max(
            max(
                abs(value - center)
                for value in values
            ),
            EPS,
        )

        return [
            (value - center) / scale
            for value in values
        ]

    # -------------------------------------------------
    # Eight internal spectral channels
    # -------------------------------------------------

    def _spectrum(self, data):
        values = self._normalize(data)
        n = len(values)

        modes = []

        for k in range(8):

            re = (
                sum(
                    values[j]
                    * math.cos(
                        TAU * k * j / n
                    )
                    for j in range(n)
                )
                / n
            )

            im = (
                -sum(
                    values[j]
                    * math.sin(
                        TAU * k * j / n
                    )
                    for j in range(n)
                )
                / n
            )

            modes.append(
                (
                    math.hypot(re, im),
                    math.atan2(im, re),
                )
            )

        return modes

    # -------------------------------------------------
    # Ball / 8-channel geometric state
    # -------------------------------------------------

    def _geometry(
        self,
        data,
        ablate=None,
    ):
        spectrum = self._spectrum(data)

        spectral_mean = mean(
            [
                amplitude
                for amplitude, _ in spectrum
            ]
        )

        base = (
            0.35
            + 0.08 * spectral_mean
        )

        # CLOCK:
        # monotonic reference component.
        clock = [
            base + j * 0.03125
            for j in range(8)
        ]

        # CODE:
        # non-monotonic relative contribution.
        code = []

        for j in range(8):

            if ablate == "code":
                value = 0.0
            else:
                amplitude, phase = spectrum[j]

                value = (
                    0.06
                    * math.tanh(amplitude)
                    * sign(
                        math.sin(phase)
                        + EPS
                    )
                )

            code.append(value)

        frequencies = []

        for j in range(8):

            clock_value = (
                0.0
                if ablate == "clock"
                else clock[j]
            )

            frequencies.append(
                clock_value + code[j]
            )

        phases = [
            spectrum[j][1] % TAU
            for j in range(8)
        ]

        normalized = self._normalize(data)

        center = (
            mean(normalized),
            mean(
                [
                    math.sin(p)
                    for p in phases
                ]
            ),
            mean(
                [
                    math.cos(p)
                    for p in phases
                ]
            ),
        )

        events = []

        for i in range(8):
            for j in range(i + 1, 8):

                delta = (
                    phases[j]
                    - phases[i]
                ) % TAU

                cos_delta = math.cos(
                    delta
                )

                # Exact lemniscate-style
                # pair relation:
                #
                # r_ij^2 ~ |cos(delta alpha)|
                radius2 = abs(cos_delta)

                central_event = (
                    abs(cos_delta)
                    < 0.075
                )

                sigma_p = sign(
                    math.sin(delta)
                )

                sigma_t = sign(
                    -math.sin(delta)
                    * (
                        frequencies[j]
                        - frequencies[i]
                    )
                )

                sigma_u = sign(
                    center[2]
                )

                events.append(
                    {
                        "pair": [i, j],
                        "radius2": radius2,
                        "central_event":
                            central_event,
                        "orientation": [
                            sigma_p,
                            sigma_t,
                            sigma_u,
                        ],
                    }
                )

        return {
            "space": "B3",
            "radius": 1.0,
            "center": list(center),
            "lemniscates": 8,
            "phases": phases,
            "frequencies": frequencies,
            "clock": clock,
            "code": code,
            "events": events,
        }

    # -------------------------------------------------
    # Small Zero
    # -------------------------------------------------

    def _small_zero(
        self,
        geometry,
        ablate=None,
    ):
        phases = geometry["phases"]
        frequencies = geometry[
            "frequencies"
        ]

        vector = sum(
            complex(
                math.cos(phase),
                math.sin(phase),
            )
            for phase in phases
        ) / 8.0

        projection = abs(vector)

        internal_energy = mean(
            [
                frequency * frequency
                for frequency
                in frequencies
            ]
        )

        distinguishability = (
            internal_energy
            / (projection + 1e-9)
        )

        central_events = [
            event
            for event
            in geometry["events"]
            if event["central_event"]
        ]

        if central_events:
            orientation = tuple(
                central_events[0][
                    "orientation"
                ]
            )
        else:
            orientation = (
                0,
                0,
                sign(
                    geometry[
                        "center"
                    ][2]
                ),
            )

        if ablate == "small_zero":
            status = "ABLATION"

        elif (
            projection < 0.18
            and internal_energy > 1e-6
        ):
            status = "SUPPORTED"

        elif (
            projection < 0.35
            and internal_energy > 1e-6
        ):
            status = "POSSIBLE"

        else:
            status = "NOT_SUPPORTED"

        return SmallZeroState(
            projection=projection,
            internal_energy=
                internal_energy,
            distinguishability=
                distinguishability,
            phase=math.atan2(
                vector.imag,
                vector.real,
            ),
            frequency=mean(
                frequencies
            ),
            orientation=
                orientation,
            status=status,
            precision=1e-9,
        )

    # -------------------------------------------------
    # Alphabet of Small Zeros
    # -------------------------------------------------

    def _alphabet(
        self,
        geometry,
        small_zero,
        history,
    ):
        symbols = []

        history_signature = digest(
            history
        )[:16]

        for event in geometry["events"]:

            if not event[
                "central_event"
            ]:
                continue

            i, j = event["pair"]

            orientation = tuple(
                event["orientation"]
            )

            payload = [
                i,
                j,
                round(
                    geometry[
                        "phases"
                    ][i],
                    8,
                ),
                round(
                    geometry[
                        "phases"
                    ][j],
                    8,
                ),
                orientation,
            ]

            symbol = ZeroSymbol(
                symbol_id=(
                    "Z-"
                    + digest(
                        payload
                    )[:12]
                ),
                projection=
                    small_zero.projection,
                frequency=abs(
                    geometry[
                        "frequencies"
                    ][j]
                    - geometry[
                        "frequencies"
                    ][i]
                ),
                phase=(
                    geometry[
                        "phases"
                    ][j]
                    - geometry[
                        "phases"
                    ][i]
                ) % TAU,
                chirality=
                    orientation[0],
                temporal_direction=
                    orientation[1],
                polarity=
                    orientation[2],
                geometry_signature=
                    digest(
                        payload
                    )[:16],
                history_signature=
                    history_signature,
            )

            symbols.append(
                asdict(symbol)
            )

        if not symbols:

            payload = [
                round(value, 8)
                for value
                in geometry["phases"]
            ]

            symbol = ZeroSymbol(
                symbol_id=(
                    "Z-"
                    + digest(
                        payload
                    )[:12]
                ),
                projection=
                    small_zero.projection,
                frequency=
                    small_zero.frequency,
                phase=
                    small_zero.phase,
                chirality=
                    small_zero
                    .orientation[0],
                temporal_direction=
                    small_zero
                    .orientation[1],
                polarity=
                    small_zero
                    .orientation[2],
                geometry_signature=
                    digest(
                        payload
                    )[:16],
                history_signature=
                    history_signature,
            )

            symbols.append(
                asdict(symbol)
            )

        return symbols

    # -------------------------------------------------
    # Possibility / "possibly" branch
    # -------------------------------------------------

    def _possibility(
        self,
        geometry,
    ):
        classes = sorted(
            {
                tuple(
                    event[
                        "orientation"
                    ]
                )
                for event
                in geometry[
                    "events"
                ]
            }
        )

        realized = (
            list(classes[0])
            if classes
            else [0, 0, 0]
        )

        return {
            "admissible_states": [
                list(value)
                for value in classes
            ],
            "realized_state":
                realized,
            "selection_status":
                "unresolved",
            "candidate_mechanisms": [
                "deterministic",
                "stochastic",
                "chaotic",
                "hidden_variables",
                "insufficient_observations",
            ],
        }

    # -------------------------------------------------
    # WRITE / EVOLVE / READ
    # -------------------------------------------------

    def _decode(
        self,
        geometry,
    ):
        score = sum(
            geometry["code"][j]
            * math.sin(
                geometry[
                    "phases"
                ][j]
            )
            for j in range(8)
        )

        return (
            1
            if score >= 0
            else -1
        )

    def _write_evolve_read(
        self,
        data,
        cycles=10,
        trials=32,
        ablate=None,
    ):
        correct = 0
        records = []

        for trial in range(trials):

            bit = (
                1
                if trial % 2 == 0
                else -1
            )

            geometry = self._geometry(
                data,
                ablate=ablate,
            )

            # WRITE
            for j in range(8):

                pattern = (
                    1
                    if j % 2 == 0
                    else -1
                )

                geometry[
                    "phases"
                ][j] = (
                    geometry[
                        "phases"
                    ][j]
                    + bit
                    * 0.14
                    * pattern
                ) % TAU

            # EVOLVE
            for _ in range(cycles):

                geometry[
                    "phases"
                ] = [
                    (
                        geometry[
                            "phases"
                        ][j]
                        + geometry[
                            "frequencies"
                        ][j]
                    ) % TAU
                    for j in range(8)
                ]

            # READ
            read = self._decode(
                geometry
            )

            if read == bit:
                correct += 1

            records.append(
                {
                    "write": bit,
                    "read": read,
                }
            )

        accuracy = (
            correct / trials
        )

        return {
            "cycles": cycles,
            "trials": trials,
            "accuracy": accuracy,
            "mvp_threshold": 0.65,
            "mvp_pass":
                accuracy > 0.65,
            "records":
                records[:8],
        }

    # -------------------------------------------------
    # Ablation controls
    # -------------------------------------------------

    def _controls(
        self,
        data,
    ):
        result = {}

        for name in (
            "clock",
            "code",
            "small_zero",
            "history",
        ):
            result[name] = (
                self._write_evolve_read(
                    data,
                    ablate=name,
                )
            )

        return result

    # -------------------------------------------------
    # Real legacy hook
    # -------------------------------------------------

    def _legacy(
        self,
        data,
    ):
        if self.legacy_hook is None:
            return {
                "called": False,
                "result": None,
                "error": None,
                "note":
                    "Real 567/KMBP hook not attached yet; "
                    "no decorative replacement was used.",
            }

        try:
            return {
                "called": True,
                "result":
                    self.legacy_hook(
                        data
                    ),
                "error": None,
            }

        except Exception as error:

            return {
                "called": True,
                "result": None,
                "error":
                    (
                        type(error)
                        .__name__
                        + ": "
                        + str(error)
                    ),
            }

    # -------------------------------------------------
    # Main parallel thought
    # -------------------------------------------------

    def think(
        self,
        data,
        old_result,
        unresolved=None,
    ):
        history = self.wal.tail()

        geometry = self._geometry(
            data
        )

        small_zero = (
            self._small_zero(
                geometry
            )
        )

        alphabet = self._alphabet(
            geometry,
            small_zero,
            history,
        )

        temporal = TemporalState(
            time=float(
                len(history)
            ),
            outer_phase=
                geometry[
                    "phases"
                ],
            outer_frequency=
                geometry[
                    "frequencies"
                ],
            inner_phase=
                small_zero.phase,
            inner_frequency=
                small_zero.frequency,
        )

        write_read = (
            self._write_evolve_read(
                data
            )
        )

        controls = (
            self._controls(
                data
            )
        )

        legacy = self._legacy(
            data
        )

        orientation_classes = sorted(
            {
                str(
                    tuple(
                        event[
                            "orientation"
                        ]
                    )
                )
                for event
                in geometry[
                    "events"
                ]
            }
        )

        modern_result = {
            "small_zero":
                asdict(
                    small_zero
                ),

            "zero_alphabet":
                alphabet,

            "temporal_state":
                asdict(
                    temporal
                ),

            "ball_geometry":
                geometry,

            "clock_code": {
                "clock":
                    geometry[
                        "clock"
                    ],
                "code":
                    geometry[
                        "code"
                    ],
                "combined":
                    geometry[
                        "frequencies"
                    ],
            },

            "orientation_cube": {
                "classes":
                    orientation_classes,
                "coordinates": [
                    "chirality_P",
                    "temporal_T",
                    "polarity_U",
                ],
            },

            "possibility":
                self._possibility(
                    geometry
                ),

            "history": {
                "events_seen":
                    len(history),
                "wal_enabled":
                    True,
            },

            "write_evolve_read":
                write_read,

            "controls":
                controls,

            "possible": {
                "status":
                    "POSSIBLE",
                "hypothesis":
                    unresolved,
                "revisable":
                    True,
                "mixed_with_recovered_memory":
                    False,
            },

            "legacy_experience":
                legacy,

            "claims": {
                "physical_proof":
                    False,
                "model_status":
                    "computational_hypothesis",
                "machine_epsilon_is_physics":
                    False,
            },
        }

        code_control = (
            controls[
                "code"
            ][
                "accuracy"
            ]
        )

        if (
            write_read[
                "mvp_pass"
            ]
            and
            code_control
            <
            write_read[
                "accuracy"
            ]
        ):
            selected = "combined"
            reason = (
                "new branch passed "
                "functional test and "
                "code ablation reduced "
                "performance"
            )
        else:
            selected = "as_before"
            reason = (
                "new branch remains "
                "parallel until "
                "functional advantage "
                "is demonstrated"
            )

        # ---------------------------------------------
        # TWO EQUAL VOICES
        # ---------------------------------------------

        voice_a = {
            "name": "VOICE_A_BEFORE",
            "role": "historical_reasoning",
            "rights": "equal",
            "result": old_result,
            "digest": digest(old_result),
        }

        voice_b = {
            "name": "VOICE_B_NOW",
            "role": "experimental_reasoning",
            "rights": "equal",
            "result": modern_result,
            "digest": digest(modern_result),
        }

        # ---------------------------------------------
        # DEBATE
        # ---------------------------------------------

        contradictions = []

        shared_patterns = [
            "both voices receive the same input",
            "both results are preserved",
            "neither voice has permanent priority",
            "neither observer may silently overwrite the other",
        ]

        unresolved_items = []

        tests_needed = []

        # Functional disagreement is preserved,
        # not automatically resolved.

        if write_read["mvp_pass"]:
            contradictions.append(
                "VOICE_B passes WRITE-EVOLVE-READ, "
                "while VOICE_A uses historical criteria."
            )
        else:
            contradictions.append(
                "VOICE_B does not yet pass "
                "WRITE-EVOLVE-READ. "
                "This does NOT grant VOICE_A priority."
            )

            tests_needed.append(
                "Find why WRITE-EVOLVE-READ "
                "is below the MVP threshold "
                "without tuning the answer to the test."
            )

        if legacy.get("called") is False:

            contradictions.append(
                "Real 567/KMBP callable is not yet "
                "attached to VOICE_B."
            )

            tests_needed.append(
                "Attach real legacy 567/KMBP "
                "and verify input -> computation "
                "-> output -> invariant."
            )

        if modern_result.get("possible"):

            unresolved_items.append(
                modern_result[
                    "possible"
                ]
            )

        # ---------------------------------------------
        # DETERMINE ONLY THE STATE OF THE DEBATE
        # NEVER A WINNER
        # ---------------------------------------------

        if (
            stable(old_result)
            ==
            stable(modern_result)
        ):
            debate_state = "AGREEMENT"

        elif contradictions:
            debate_state = "DISAGREEMENT"

        else:
            debate_state = "COMPLEMENTARY"

        # ---------------------------------------------
        # FINAL REFLECTION OBJECT
        # ---------------------------------------------

        result = {
            "schema":
                "malysh.reflections.v2",

            "name":
                "Размышления",

            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "voice_a":
                voice_a,

            "voice_b":
                voice_b,

            "debate": {
                "state":
                    debate_state,

                "equal_rights":
                    True,

                "winner":
                    None,

                "contradictions":
                    contradictions,

                "shared_patterns":
                    shared_patterns,

                "unresolved":
                    unresolved_items,

                "tests_needed":
                    tests_needed,

                "rule":
                    (
                        "DISAGREEMENT is a valid result. "
                        "No voice becomes primary "
                        "because it won previous tests."
                    ),
            },

            # Human Layer:
            # possibilities survive beside logical results.
            "human_layer": {
                "logical_voice":
                    "voice_a",

                "possible_voice":
                    "voice_b",

                "both_preserved":
                    True,

                "possible_may_be_wrong":
                    True,

                "logical_may_be_wrong":
                    True,

                "forced_binary_finality":
                    False,
            },

            # Cross-layer observers can compare results,
            # but cannot directly change execution.
            "cross_layer": {
                "compare":
                    True,

                "search_patterns":
                    True,

                "observer_outputs_separate":
                    True,

                "observer_changes_execution":
                    False,
            },

            # No automatic winner.
            # If an external action eventually requires
            # one concrete choice, it must be decided
            # by functional evidence / invariant,
            # not by permanent authority of A or B.
            "execution_gate": {
                "automatic_winner_forbidden":
                    True,

                "requires_external_invariant":
                    True,

                "requires_functional_test":
                    True,

                "current_decision":
                    None,
            },

            # Backward-compatible views.
            "compatibility": {
                "as_before": {
                    "status":
                        "AS_BEFORE",

                    "result":
                        old_result,

                    "preserved":
                        True,
                },

                "as_now": {
                    "status":
                        "AS_NOW",

                    "result":
                        modern_result,
                },

                "joint_choice": {
                    "selected":
                        None,

                    "reason":
                        (
                            "VOICE_A and VOICE_B "
                            "are equal. "
                            "Their disagreement "
                            "must be preserved."
                        ),
                },
            },
        }

        self.wal.append(
            "REFLECTION",
            {
                "input_digest":
                    digest(data),
                "debate_state":
                    debate_state,
                "mvp_pass":
                    write_read[
                        "mvp_pass"
                    ],
                "small_zero_status":
                    small_zero.status,
            },
        )

        return result
