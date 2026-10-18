from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "memory_vault"


class PassiveObserver:
    observer_id = "unknown"
    category = "observer"

    def observe(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError


class VortexObserver(PassiveObserver):
    observer_id = "vortex_observer"
    category = "observer.vortex"

    def observe(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        resolution = 12

        axis = np.linspace(
            -3.0,
            3.0,
            resolution,
        )

        x, y, z = np.meshgrid(
            axis,
            axis,
            axis,
            indexing="ij",
        )

        alpha = x**2 + y**2 - 1.0
        beta = z + np.sin(x * y)

        dx = x[1, 0, 0] - x[0, 0, 0]

        ga = np.gradient(
            alpha,
            dx,
            dx,
            dx,
            axis=(0, 1, 2),
        )

        gb = np.gradient(
            beta,
            dx,
            dx,
            dx,
            axis=(0, 1, 2),
        )

        ox = ga[1] * gb[2] - ga[2] * gb[1]
        oy = ga[2] * gb[0] - ga[0] * gb[2]
        oz = ga[0] * gb[1] - ga[1] * gb[0]

        magnitude = np.sqrt(
            ox**2 + oy**2 + oz**2
        )

        return {
            "observer": self.observer_id,
            "role": "passive_observer",
            "resolution": resolution,
            "mean_vorticity": float(
                np.mean(magnitude)
            ),
            "max_vorticity": float(
                np.max(magnitude)
            ),
            "state_generation_seen": (
                context.get("generation")
            ),
            "state_write": False,
        }


class PhaseObserver(PassiveObserver):
    observer_id = "phase_observer"
    category = "observer.phase"

    def observe(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        rng = np.random.default_rng(42)

        modes = 100
        steps = 50
        strength = 0.35

        phases = rng.uniform(
            0.0,
            2.0 * math.pi,
            modes,
        )

        means: list[float] = []

        for _ in range(steps):
            means.append(
                float(
                    np.mean(
                        np.abs(
                            np.diff(phases)
                        )
                    )
                )
            )

            new_phases = phases.copy()

            for i in range(
                1,
                modes - 1,
            ):
                delta = strength * (
                    math.sin(
                        phases[i + 1]
                        - phases[i]
                    )
                    + math.sin(
                        phases[i - 1]
                        - phases[i]
                    )
                )

                new_phases[i] += delta

            phases = new_phases

        return {
            "observer": self.observer_id,
            "role": "passive_observer",
            "steps": steps,
            "initial_mean_phase_diff": (
                means[0]
            ),
            "final_mean_phase_diff": (
                means[-1]
            ),
            "resonance_threshold": (
                math.pi / 2.0
            ),
            "state_generation_seen": (
                context.get("generation")
            ),
            "state_write": False,
        }


class VaultObserver(PassiveObserver):
    observer_id = "vault_observer"
    category = "observer.memory"

    def observe(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        files = sorted(
            VAULT.glob(
                "passport_*.json"
            )
        )

        history = []

        for path in files:
            try:
                history.append(
                    json.loads(
                        path.read_text(
                            encoding="utf-8"
                        )
                    )
                )
            except Exception:
                continue

        if not history:
            return {
                "observer": self.observer_id,
                "role": "passive_observer",
                "passport_count": 0,
                "latest": None,
                "state_generation_seen": (
                    context.get("generation")
                ),
                "state_write": False,
            }

        latest = history[-1]

        return {
            "observer": self.observer_id,
            "role": "passive_observer",
            "passport_count": len(history),
            "latest": {
                "generation": latest.get(
                    "generation"
                ),
                "source": latest.get(
                    "source"
                ),
                "mode": latest.get(
                    "mode"
                ),
                "confidence": latest.get(
                    "confidence"
                ),
                "K_metric": latest.get(
                    "K_metric"
                ),
                "energy": latest.get(
                    "energy"
                ),
            },
            "state_generation_seen": (
                context.get("generation")
            ),
            "state_write": False,
        }


def build_observers() -> list:
    return [
        VortexObserver(),
        PhaseObserver(),
        VaultObserver(),
    ]


def observe_all(
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        observer.observe(context)
        for observer in build_observers()
    ]
