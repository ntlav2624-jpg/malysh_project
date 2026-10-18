#!/usr/bin/env python3

from pathlib import Path
import ast
import json

ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    "runtime",
    ".venv",
    "venv",
}

UTILITY_PREFIXES = (
    "test_",
    "fix_",
    "check_",
    "plot_",
    "visualize_",
    "install_",
)

ORGAN_HINTS = {
    "navier": "physics.navier",
    "plasma": "physics.plasma",
    "turbulence": "physics.turbulence",
    "vortex": "physics.vortex",
    "phase": "geometry.phase",
    "toroid": "geometry.toroidal",
    "geometry": "geometry",
    "topolog": "geometry.topology",
    "q4": "logic.q4",
    "firmware": "logic.firmware",
    "resonance": "resonance",
    "chaos": "dynamics.chaos",
    "bony": "math.bony",
    "apsu": "engine.apsu",
    "cuneiform": "analysis.cuneiform",
    "memory": "memory",
    "forecast": "prediction",
    "predict": "prediction",
    "adaptive": "adaptation",
    "engine": "engine",
}


def category_for(path: Path) -> str:
    name = path.name.lower()

    for key, category in ORGAN_HINTS.items():
        if key in name:
            return category

    if name.startswith(UTILITY_PREFIXES):
        return "utility"

    if name.startswith("run_"):
        return "launcher"

    return "unclassified"


def inspect_python(path: Path) -> dict:
    rel = path.relative_to(ROOT)

    record = {
        "path": str(rel),
        "category": category_for(path),
        "classes": [],
        "functions": [],
        "imports": [],
        "has_main": False,
        "syntax_ok": True,
        "error": None,
    }

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                record["classes"].append(node.name)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                record["functions"].append(node.name)

            elif isinstance(node, ast.Import):
                record["imports"].extend(
                    alias.name for alias in node.names
                )

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    record["imports"].append(node.module)

            elif isinstance(node, ast.If):
                try:
                    expression = ast.unparse(node.test)
                    if "__name__" in expression and "__main__" in expression:
                        record["has_main"] = True
                except Exception:
                    pass

    except Exception as exc:
        record["syntax_ok"] = False
        record["error"] = f"{type(exc).__name__}: {exc}"

    record["classes"] = sorted(set(record["classes"]))
    record["functions"] = sorted(set(record["functions"]))
    record["imports"] = sorted(set(record["imports"]))

    return record


def main() -> None:
    modules = []

    for path in sorted(ROOT.rglob("*.py")):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue

        modules.append(inspect_python(path))

    groups = {}

    for module in modules:
        groups.setdefault(module["category"], []).append(module["path"])

    report = {
        "schema_version": 1,
        "root": str(ROOT),
        "python_modules": len(modules),
        "syntax_valid": sum(1 for m in modules if m["syntax_ok"]),
        "syntax_invalid": sum(1 for m in modules if not m["syntax_ok"]),
        "categories": {
            key: sorted(value)
            for key, value in sorted(groups.items())
        },
        "modules": modules,
    }

    output = ROOT / "malysh_system" / "organ_inventory.json"

    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 68)
    print("МАЛЫШ: ИНВЕНТАРИЗАЦИЯ ОРГАНИЗМА")
    print("=" * 68)
    print(f"Python-модулей : {report['python_modules']}")
    print(f"Синтаксис OK   : {report['syntax_valid']}")
    print(f"С ошибками     : {report['syntax_invalid']}")
    print()

    for category, paths in report["categories"].items():
        print(f"{category:24} {len(paths):4}")

    print()
    print("Карта сохранена:")
    print("malysh_system/organ_inventory.json")
    print("=" * 68)


if __name__ == "__main__":
    main()
