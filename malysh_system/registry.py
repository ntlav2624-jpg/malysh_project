from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "malysh_system" / "organ_inventory.json"


def load_organs() -> list:
    if not INVENTORY.exists():
        return []

    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    organs = []

    for module in data.get("modules", []):
        if not module.get("syntax_ok", False):
            continue

        path = module["path"]

        # Служебные файлы мозга не считаем вычислительными органами.
        if path.startswith("malysh_system/"):
            continue

        organs.append(
            {
                "name": path,
                "category": module.get("category", "unclassified"),
                "path": path,
                "has_main": module.get("has_main", False),
                "classes": module.get("classes", []),
                "functions": module.get("functions", []),
            }
        )

    return organs
