from __future__ import annotations

import json
import os

from core.malysh_toroidal_geometry import ToroidalTubeGeometry


def signal_from_environment() -> str:
    text = os.environ.get(
        "MALYSH_COMMAND_TEXT",
        "",
    )

    upper = text.upper()

    for token in upper.replace(",", " ").split():
        compact = "".join(
            char
            for char in token
            if char.isalnum()
        )

        if len(compact) >= 4:
            if any(char.isdigit() for char in compact):
                return compact

    return "6EQUJ5"


def main() -> None:
    signal = signal_from_environment()

    result = ToroidalTubeGeometry(
        signal
    ).compute_geometry()

    metrics = result["toroidal_metrics"]

    summary = {
        "organ": "toroidal_geometry",
        "signature": result["signature"],
        "node_count": len(result["nodes"]),
        "R_major": metrics["R_major"],
        "r_minor": metrics["r_minor"],
        "euclidean_path": metrics["euclidean_path"],
        "resonance_path": metrics["resonance_path"],
    }

    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
