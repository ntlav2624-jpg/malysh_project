#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import ast
import importlib
import json
import os
from pathlib import Path
import py_compile
import re
import subprocess
import sys
import tempfile
import time
import traceback


ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT / "runtime" / "unified_health"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = time.strftime("%Y%m%d_%H%M%S")
JSON_REPORT = REPORT_DIR / f"malysh_health_{TIMESTAMP}.json"
TEXT_REPORT = REPORT_DIR / f"malysh_health_{TIMESTAMP}.log"

TIMEOUT = 20

BACKUP_PATTERNS = (
    ".bak",
    ".before",
    ".backup",
    ".corrupted",
)

EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    ".malysh_branch_audit",
    "runtime",
}

INSTALLER_PREFIXES = (
    "install_",
    "fix_",
    "build_",
    "extract_",
    "diagnose_",
    "trace_",
    "inspect_",
    "flush_",
    "certify_",
)

REQUIRED_SYSTEM_MODULES = (
    "malysh_system.registry",
    "malysh_system.genome",
    "malysh_system.capability_router",
    "malysh_system.executor",
    "malysh_system.routed_executor",
    "malysh_system.transaction",
    "malysh_system.orchestrator",
    "malysh_system.supervisor",
    "malysh_system.dual_mind",
    "malysh_system.human_layer",
    "malysh_system.observers",
    "malysh_system.cross_layer_observer",
    "malysh_system.legacy_memory",
    "malysh_system.experience",
    "malysh_system.workflow_recall",
    "malysh_system.passport_memory",
    "malysh_system.certification",
    "malysh_system.inventory",
    "malysh_system.integration_queue",
    "malysh_system.completion_plan",
    "malysh_system.protocols",
    "malysh_system.brain",
)

REQUIRED_FILES = (
    "n7_interface.py",
    "run_pipeline.py",
    "run_reflected_pipeline.py",
    "malysh_cuneiform_engine.py",
    "core/malysh_master_engine.py",
    "core/malysh_firmware_compiler.py",
    "core/malysh_toroidal_geometry.py",
    "config/malysh.json",
    "config/organs.json",
    "config/adapters.json",
    "malysh_system/genome_registry.json",
    "malysh_system/organ_inventory.json",
    "malysh_system/infrastructure_registry.json",
    "malysh_system/knowledge_registry.json",
    "malysh_system/library_registry.json",
    "malysh_system/workflow_experience_registry.json",
)

SEARCH_LAYERS = {
    "kmbp": (
        r"\bKMBP\b",
        r"\bКМБП\b",
        r"\bkmbp\b",
        r"\bкмбп\b",
    ),
    "glyphs": (
        r"glyph",
        r"глиф",
        r"cuneiform",
        r"клинопис",
        r"tablet",
    ),
    "legacy_567": (
        r"567",
        r"N7",
        r"R5",
        r"R6",
    ),
    "chirality": (
        r"chirality",
        r"chiral",
        r"хираль",
    ),
    "state83": (
        r"state83",
        r"STATE83",
        r"№83",
    ),
    "human_layer": (
        r"Human Layer",
        r"human_layer",
        r"possible",
        r"возможно",
    ),
    "omni": (
        r"\bOmni\b",
        r"\bOMNI\b",
        r"\bОмни\b",
    ),
    "swarm": (
        r"\bswarm\b",
        r"\bрой\b",
        r"\bРой\b",
    ),
}


class HealthRegistry:
    def __init__(self):
        self.started = time.time()
        self.records = []
        self.notes = []
        self.inventory = {}
        self.layer_hits = {}

    def add(
        self,
        module,
        check,
        status,
        detail="",
        duration=0.0,
    ):
        item = {
            "module": module,
            "check": check,
            "status": status,
            "detail": str(detail),
            "duration_seconds": round(duration, 6),
        }
        self.records.append(item)

        marker = {
            "PASS": "[PASS]",
            "FAIL": "[FAIL]",
            "WARN": "[WARN]",
            "SKIP": "[SKIP]",
        }.get(status, f"[{status}]")

        print(
            f"{marker:<8} "
            f"{module:<42} "
            f"{check:<20} "
            f"{detail}"
        )

    def summary(self):
        result = {}
        for record in self.records:
            status = record["status"]
            result[status] = result.get(status, 0) + 1
        return result

    def failures(self):
        return [
            record
            for record in self.records
            if record["status"] == "FAIL"
        ]

    def save(self):
        summary = self.summary()

        payload = {
            "schema": "malysh.unified.health.v1",
            "timestamp": TIMESTAMP,
            "root": str(ROOT),
            "elapsed_seconds": round(
                time.time() - self.started,
                6,
            ),
            "summary": summary,
            "inventory": self.inventory,
            "logical_layers": self.layer_hits,
            "notes": self.notes,
            "records": self.records,
            "failures": self.failures(),
        }

        JSON_REPORT.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        lines = [
            "ONE MALYSH UNIFIED HEALTH REPORT",
            "=" * 70,
            f"Timestamp: {TIMESTAMP}",
            f"Root: {ROOT}",
            "",
            "SUMMARY",
            json.dumps(
                summary,
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "FAILURES",
        ]

        failures = self.failures()

        if failures:
            for item in failures:
                lines.append(
                    f"- {item['module']} :: "
                    f"{item['check']} :: "
                    f"{item['detail']}"
                )
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "LOGICAL LAYERS",
                json.dumps(
                    self.layer_hits,
                    ensure_ascii=False,
                    indent=2,
                ),
                "",
                f"JSON report: {JSON_REPORT}",
            ]
        )

        TEXT_REPORT.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )


def active_python_files():
    files = []

    for path in ROOT.rglob("*.py"):
        relative = path.relative_to(ROOT)

        if any(
            part in EXCLUDED_PARTS
            for part in relative.parts
        ):
            continue

        lower_name = path.name.lower()

        if any(
            pattern in lower_name
            for pattern in BACKUP_PATTERNS
        ):
            continue

        files.append(path)

    return sorted(files)


def all_text_files():
    suffixes = {
        ".py",
        ".json",
        ".md",
        ".txt",
        ".sh",
    }

    files = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        relative = path.relative_to(ROOT)

        if any(
            part in EXCLUDED_PARTS
            for part in relative.parts
        ):
            continue

        if path.suffix.lower() in suffixes:
            files.append(path)

    return sorted(files)


def syntax_compile(registry, files):
    print("\n=== PYTHON SYNTAX ===")

    for path in files:
        relative = str(path.relative_to(ROOT))
        start = time.time()

        try:
            py_compile.compile(
                str(path),
                doraise=True,
            )
            registry.add(
                relative,
                "compile",
                "PASS",
                duration=time.time() - start,
            )
        except Exception as exc:
            registry.add(
                relative,
                "compile",
                "FAIL",
                repr(exc),
                time.time() - start,
            )


def json_validation(registry):
    print("\n=== JSON REGISTRIES AND RECORDS ===")

    json_files = sorted(
        path
        for path in ROOT.rglob("*.json")
        if ".git" not in path.parts
    )

    for path in json_files:
        relative = str(path.relative_to(ROOT))
        start = time.time()

        try:
            value = json.loads(
                path.read_text(encoding="utf-8")
            )

            if isinstance(value, dict):
                detail = f"dict keys={len(value)}"
            elif isinstance(value, list):
                detail = f"list items={len(value)}"
            else:
                detail = type(value).__name__

            registry.add(
                relative,
                "json",
                "PASS",
                detail,
                time.time() - start,
            )
        except Exception as exc:
            registry.add(
                relative,
                "json",
                "FAIL",
                repr(exc),
                time.time() - start,
            )


def required_presence(registry):
    print("\n=== REQUIRED UNIFIED COMPONENTS ===")

    for filename in REQUIRED_FILES:
        path = ROOT / filename

        registry.add(
            filename,
            "presence",
            "PASS" if path.exists() else "FAIL",
            "exists" if path.exists() else "missing",
        )


def discover_layers(registry):
    print("\n=== LOGICAL HERITAGE DISCOVERY ===")

    text_files = all_text_files()

    for layer, patterns in SEARCH_LAYERS.items():
        matches = []

        compiled = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in patterns
        ]

        for path in text_files:
            try:
                text = path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            except Exception:
                continue

            if any(regex.search(text) for regex in compiled):
                matches.append(
                    str(path.relative_to(ROOT))
                )

        registry.layer_hits[layer] = matches

        if matches:
            registry.add(
                layer,
                "heritage-discovery",
                "PASS",
                f"files={len(matches)}",
            )
        else:
            registry.add(
                layer,
                "heritage-discovery",
                "WARN",
                "no textual carrier found",
            )


def module_name(path):
    relative = path.relative_to(ROOT)

    if relative.name == "__init__.py":
        return ".".join(relative.parent.parts)

    return ".".join(
        relative.with_suffix("").parts
    )


def import_probe(registry, files):
    print("\n=== ISOLATED IMPORT PROBES ===")

    candidates = []

    for path in files:
        relative = path.relative_to(ROOT)

        if any(
            path.name.startswith(prefix)
            for prefix in INSTALLER_PREFIXES
        ):
            registry.add(
                str(relative),
                "import",
                "SKIP",
                "installer/repair utility",
            )
            continue

        if "archive_experiments" in relative.parts:
            registry.add(
                str(relative),
                "import",
                "SKIP",
                "archived experiment",
            )
            continue

        candidates.append((path, relative))

    for source_path, relative in sorted(
        candidates,
        key=lambda item: str(item[1]),
    ):
        start = time.time()
        relative_text = str(relative)

        # Стандартное имя модуля допустимо только тогда,
        # когда каждый компонент пути является идентификатором Python.
        parts = list(relative.with_suffix("").parts)

        standard_module_name = (
            parts
            and all(part.isidentifier() for part in parts)
        )

        if standard_module_name:
            name = ".".join(parts)

            loader_code = (
                "import importlib; "
                f"importlib.import_module({name!r}); "
                "print('IMPORT_OK')"
            )

            load_mode = f"module:{name}"
        else:
            # Исторические файлы наподобие enki_micro_v3.1.py
            # нельзя передавать в import_module(), потому что точка
            # интерпретируется как разделитель пакета.
            safe_name = re.sub(
                r"[^A-Za-z0-9_]",
                "_",
                source_path.stem,
            )

            if not safe_name:
                safe_name = "malysh_dynamic_module"

            if safe_name[0].isdigit():
                safe_name = "malysh_" + safe_name

            absolute_path = str(source_path.resolve())

            loader_code = (
                "import importlib.util; "
                "import sys; "
                f"path={absolute_path!r}; "
                f"name={safe_name!r}; "
                "spec=importlib.util.spec_from_file_location("
                "name, path"
                "); "
                "assert spec is not None, "
                "'module spec is None'; "
                "assert spec.loader is not None, "
                "'module loader is None'; "
                "module=importlib.util.module_from_spec(spec); "
                "sys.modules[name]=module; "
                "spec.loader.exec_module(module); "
                "print('IMPORT_OK')"
            )

            load_mode = f"file:{safe_name}"

        command = [
            sys.executable,
            "-c",
            loader_code,
        ]

        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=TIMEOUT,
                env={
                    **os.environ,
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )

            output = (
                completed.stdout
                + completed.stderr
            ).strip()

            if completed.returncode == 0:
                detail = f"imported via {load_mode}"

                if output:
                    detail += (
                        "; output="
                        + output[-300:].replace(
                            "\n",
                            " | ",
                        )
                    )

                registry.add(
                    relative_text,
                    "import",
                    "PASS",
                    detail,
                    time.time() - start,
                )
            else:
                registry.add(
                    relative_text,
                    "import",
                    "FAIL",
                    output[-1500:],
                    time.time() - start,
                )

        except subprocess.TimeoutExpired:
            registry.add(
                relative_text,
                "import",
                "FAIL",
                f"timeout>{TIMEOUT}s",
                time.time() - start,
            )
        except Exception as exc:
            registry.add(
                relative_text,
                "import",
                "FAIL",
                repr(exc),
                time.time() - start,
            )


def required_system_imports(registry):
    print("\n=== ONE MALYSH SYSTEM LAYER ===")

    for name in REQUIRED_SYSTEM_MODULES:
        start = time.time()

        try:
            importlib.import_module(name)
            registry.add(
                name,
                "system-import",
                "PASS",
                duration=time.time() - start,
            )
        except Exception:
            registry.add(
                name,
                "system-import",
                "FAIL",
                traceback.format_exc()[-1000:],
                time.time() - start,
            )


def n7_smoke(registry):
    print("\n=== 567 INTERFACE SMOKE TEST ===")
    start = time.time()

    try:
        from run_pipeline import (
            MalyshResonanceEngine as Direct,
        )
        from run_reflected_pipeline import (
            MalyshResonanceEngine as Reflected,
        )

        direct = Direct(
            R6=12.0,
            R5=4.5,
            theta_0=0.5,
            a=0.05,
            k=0.08,
        ).compute_n7_nodes(
            phi_0=0.0,
            d_phi=0.05,
            n_max=400,
        )

        reflected = Reflected(
            R6=12.0,
            R5=4.5,
            theta_0=0.5,
            a=0.08,
            k=0.06,
        ).generate_bounded_trajectory(
            phi_0=0.0,
            d_phi=0.05,
            n_max=350,
        )

        for name, result in (
            ("direct", direct),
            ("reflected", reflected),
        ):
            assert result["n7_indices"], name
            assert result["n7_nodes"], name
            assert (
                result["n7_forward"]
                == "R5->N7->R6"
            )
            assert (
                result["n7_reverse"]
                == "R6->N7->R5"
            )

        registry.add(
            "567",
            "functional",
            "PASS",
            (
                f"direct={direct['n7_mode']}:"
                f"{direct['n7_indices']}; "
                f"reflected={reflected['n7_mode']}:"
                f"{reflected['n7_indices']}"
            ),
            time.time() - start,
        )

    except Exception:
        registry.add(
            "567",
            "functional",
            "FAIL",
            traceback.format_exc()[-1500:],
            time.time() - start,
        )


def glyph_smoke(registry):
    print("\n=== GLYPH / CUNEIFORM SMOKE TEST ===")
    start = time.time()

    try:
        from malysh_cuneiform_engine import (
            MalyshCuneiformEngine567,
        )

        with tempfile.TemporaryDirectory() as temp:
            engine = MalyshCuneiformEngine567(
                data_dir=temp
            )

            source = (
                ROOT / "anunnaki_raw_tablet.txt"
            )

            loaded = engine.load_corpus_from_text(
                str(source)
            )

            assert loaded is True
            assert engine.corpus
            assert engine.sign_frequencies
            assert engine.transition_matrix
            assert engine.attractors

            candidate, tension = engine.restore_gap(
                "an-na",
                "dingir",
            )

            assert candidate
            assert isinstance(tension, float)

            registry.add(
                "glyphs/cuneiform",
                "functional",
                "PASS",
                (
                    f"corpus={len(engine.corpus)}; "
                    f"signs={len(engine.sign_frequencies)}; "
                    f"attractors={len(engine.attractors)}; "
                    f"restored={candidate}; "
                    f"tension={tension:.6f}"
                ),
                time.time() - start,
            )

    except Exception:
        registry.add(
            "glyphs/cuneiform",
            "functional",
            "FAIL",
            traceback.format_exc()[-1500:],
            time.time() - start,
        )


def registry_smoke(registry):
    print("\n=== REGISTRY CROSS-CHECK ===")

    targets = (
        ROOT / "config" / "organs.json",
        ROOT / "config" / "adapters.json",
        ROOT / "malysh_system"
        / "genome_registry.json",
        ROOT / "malysh_system"
        / "organ_inventory.json",
        ROOT / "malysh_system"
        / "infrastructure_registry.json",
    )

    for path in targets:
        relative = str(path.relative_to(ROOT))
        start = time.time()

        try:
            data = json.loads(
                path.read_text(encoding="utf-8")
            )

            text = json.dumps(
                data,
                ensure_ascii=False,
            )

            referenced_python = sorted(
                set(
                    re.findall(
                        r"[A-Za-z0-9_./-]+\.py",
                        text,
                    )
                )
            )

            missing = []

            for reference in referenced_python:
                candidate = ROOT / reference

                if not candidate.exists():
                    missing.append(reference)

            if missing:
                registry.add(
                    relative,
                    "reference-check",
                    "WARN",
                    "missing references: "
                    + ", ".join(missing[:20]),
                    time.time() - start,
                )
            else:
                registry.add(
                    relative,
                    "reference-check",
                    "PASS",
                    (
                        "python references="
                        f"{len(referenced_python)}"
                    ),
                    time.time() - start,
                )

        except Exception:
            registry.add(
                relative,
                "reference-check",
                "FAIL",
                traceback.format_exc()[-1200:],
                time.time() - start,
            )


def dependency_scan(registry, files):
    print("\n=== LOCAL DEPENDENCY SCAN ===")

    local_modules = {
        module_name(path).split(".")[0]
        for path in files
        if module_name(path)
    }

    local_modules.update(
        path.stem
        for path in ROOT.glob("*.py")
    )

    standard = set(getattr(sys, "stdlib_module_names", ()))

    missing_map = {}

    for path in files:
        relative = str(path.relative_to(ROOT))

        try:
            tree = ast.parse(
                path.read_text(
                    encoding="utf-8",
                    errors="replace",
                ),
                filename=relative,
            )
        except SyntaxError:
            continue

        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(
                    alias.name.split(".")[0]
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(
                        node.module.split(".")[0]
                    )

        unresolved = []

        for dependency in sorted(imports):
            if dependency in standard:
                continue

            if dependency in local_modules:
                continue

            try:
                if (
                    importlib.util.find_spec(dependency)
                    is not None
                ):
                    continue
            except Exception:
                pass

            unresolved.append(dependency)

        if unresolved:
            missing_map[relative] = unresolved
            registry.add(
                relative,
                "dependencies",
                "WARN",
                ", ".join(unresolved),
            )

    if not missing_map:
        registry.add(
            "all-active-python",
            "dependencies",
            "PASS",
            "no unresolved imports",
        )

    registry.inventory[
        "potential_unresolved_dependencies"
    ] = missing_map


def state83_inventory(registry, files):
    print("\n=== STATE83 / CHIRALITY INVENTORY ===")

    selected = []

    for path in files:
        name = path.name.lower()

        if any(
            marker in name
            for marker in (
                "state83",
                "chiral",
                "chirality",
                "expert",
                "v12",
            )
        ):
            selected.append(
                str(path.relative_to(ROOT))
            )

    registry.inventory[
        "state83_chirality_python"
    ] = selected

    registry.add(
        "state83/chirality",
        "inventory",
        "PASS" if selected else "WARN",
        f"active_python_files={len(selected)}",
    )


def top_level_inventory(registry, files):
    categories = {
        "system": [],
        "core": [],
        "legacy": [],
        "state83": [],
        "tools": [],
        "other": [],
    }

    for path in files:
        relative = path.relative_to(ROOT)
        relative_string = str(relative)
        lower = relative_string.lower()

        if relative.parts[0] == "malysh_system":
            category = "system"
        elif relative.parts[0] == "core":
            category = "core"
        elif any(
            word in lower
            for word in (
                "state83",
                "chiral",
                "v12",
                "expert",
            )
        ):
            category = "state83"
        elif any(
            word in lower
            for word in (
                "legacy",
                "cuneiform",
                "glyph",
                "tablet",
                "567",
                "kmbp",
            )
        ):
            category = "legacy"
        elif path.name.startswith(
            INSTALLER_PREFIXES
        ):
            category = "tools"
        else:
            category = "other"

        categories[category].append(
            relative_string
        )

    registry.inventory["python_categories"] = categories

    for category, values in categories.items():
        registry.add(
            category,
            "inventory",
            "PASS",
            f"python_files={len(values)}",
        )


def main():
    os.chdir(ROOT)

    registry = HealthRegistry()
    files = active_python_files()

    registry.inventory["active_python_count"] = len(files)

    print("=" * 78)
    print("ONE MALYSH UNIFIED HEALTH")
    print("=" * 78)
    print("Root:", ROOT)
    print("Python files:", len(files))
    print()

    required_presence(registry)
    top_level_inventory(registry, files)
    discover_layers(registry)
    syntax_compile(registry, files)
    json_validation(registry)
    dependency_scan(registry, files)
    required_system_imports(registry)

    # Общий import-аудит запускается после базовых проверок.
    import_probe(registry, files)

    registry_smoke(registry)
    n7_smoke(registry)
    glyph_smoke(registry)
    state83_inventory(registry, files)

    registry.save()

    print()
    print("=" * 78)
    print("FINAL SUMMARY")
    print("=" * 78)

    summary = registry.summary()

    for status in (
        "PASS",
        "WARN",
        "SKIP",
        "FAIL",
    ):
        print(
            f"{status:<8}: "
            f"{summary.get(status, 0)}"
        )

    print("JSON report:", JSON_REPORT)
    print("Text report:", TEXT_REPORT)

    failures = registry.failures()

    if failures:
        print()
        print("[FAIL] ONE MALYSH HAS RED MODULES")

        for item in failures:
            print(
                " -",
                item["module"],
                "::",
                item["check"],
                "::",
                item["detail"][:300],
            )

        return 1

    print()
    print("[PASS] ONE MALYSH BASE ORGANISM IS HEALTHY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
