from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INVENTORY = (
    ROOT / "malysh_system" / "organ_inventory.json"
)

OUTPUT = (
    ROOT / "malysh_system" / "genome_registry.json"
)

PRODUCTION = ROOT / "config" / "organs.json"
ADAPTERS = ROOT / "config" / "adapters.json"


def load(path: Path) -> dict:
    if not path.exists():
        return {}

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def classify_role(module: dict) -> str:
    path = module["path"]
    name = Path(path).name

    if path.startswith("malysh_system/"):
        return "nervous_system"

    if name.startswith("test_"):
        return "immune_test"

    if name.startswith("plot_"):
        return "visualizer"

    if "visual" in name:
        return "visualizer"

    if name.startswith("run_"):
        return "launcher"

    if "passport" in name:
        return "memory"

    if "history" in name:
        return "memory"

    if module.get("classes"):
        return "organ"

    if module.get("functions"):
        return "functional_organ"

    return "support"


def execution_policy(module: dict, role: str) -> str:
    if role == "nervous_system":
        return "infrastructure"

    if role == "immune_test":
        return "diagnostic"

    if role == "visualizer":
        return "on_demand"

    if role == "memory":
        return "memory_access"

    if module.get("has_main"):
        return "process_candidate"

    if module.get("classes") or module.get("functions"):
        return "adapter_required"

    return "library"


def main() -> None:
    inventory = load(INVENTORY)
    production = load(PRODUCTION)
    adapters = load(ADAPTERS)

    prod_paths = {
        item.get("path")
        for item in production.get("organs", [])
    }

    adapter_paths = {
        item.get("path")
        for item in adapters.get("adapters", [])
    }

    records = []

    for module in inventory.get("modules", []):
        role = classify_role(module)
        path = module["path"]

        if path in prod_paths:
            integration = "production"
        elif path in adapter_paths:
            integration = "adapted"
        elif module.get("syntax_ok"):
            integration = "discovered"
        else:
            integration = "broken"

        records.append({
            "id": path.replace("/", "::"),
            "path": path,
            "category": module.get(
                "category",
                "unclassified",
            ),
            "role": role,
            "execution_policy": execution_policy(
                module,
                role,
            ),
            "integration": integration,
            "syntax_ok": module.get(
                "syntax_ok",
                False,
            ),
            "has_main": module.get(
                "has_main",
                False,
            ),
            "classes": module.get(
                "classes",
                [],
            ),
            "functions": module.get(
                "functions",
                [],
            ),
            "imports": module.get(
                "imports",
                [],
            ),
        })

    summary = {
        "total": len(records),
        "production": sum(
            x["integration"] == "production"
            for x in records
        ),
        "adapted": sum(
            x["integration"] == "adapted"
            for x in records
        ),
        "discovered": sum(
            x["integration"] == "discovered"
            for x in records
        ),
        "broken": sum(
            x["integration"] == "broken"
            for x in records
        ),
    }

    output = {
        "schema_version": 1,
        "system": "Malysh Unified Genome",
        "summary": summary,
        "modules": records,
    }

    OUTPUT.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 68)
    print("МАЛЫШ: ПОЛНЫЙ ГЕНОМ ТЕКУЩЕГО ДЕРЕВА")
    print("=" * 68)

    for key, value in summary.items():
        print(f"{key:12}: {value}")

    print("-" * 68)

    roles = {}

    for record in records:
        roles[record["role"]] = (
            roles.get(record["role"], 0) + 1
        )

    for role in sorted(roles):
        print(
            f"{role:20}: {roles[role]}"
        )

    print("-" * 68)
    print(
        "Registry:",
        OUTPUT.relative_to(ROOT),
    )
    print("=" * 68)


if __name__ == "__main__":
    main()
