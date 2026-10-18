from __future__ import annotations

import ast
import hashlib
import json
import os
import py_compile
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "runtime" / "certification"
REPORT_PATH = REPORT_DIR / "latest.json"

CANDIDATES = [
    {
        "id": "toroidal_geometry",
        "path": "core/malysh_toroidal_geometry.py",
        "category": "geometry.toroidal",
    },
    {
        "id": "firmware_compiler",
        "path": "core/malysh_firmware_compiler.py",
        "category": "logic.firmware",
    },
    {
        "id": "chaos_handler",
        "path": "malysh_chaos.py",
        "category": "dynamics.chaos",
    },
    {
        "id": "chaos_bypass",
        "path": "malysh_chaos_bypass.py",
        "category": "dynamics.chaos",
    },
    {
        "id": "bony_paraproduct",
        "path": "malysh_bony_paraproduct_engine.py",
        "category": "math.bony",
    },
    {
        "id": "weighted_bony",
        "path": "malysh_weighted_bony_closure.py",
        "category": "math.bony",
    },
    {
        "id": "navier_continuum",
        "path": "malysh_navier_continuum_closure.py",
        "category": "physics.navier",
    },
    {
        "id": "navier_dynamic",
        "path": "malysh_navier_dynamic.py",
        "category": "physics.navier",
    },
    {
        "id": "navier_spectral",
        "path": "malysh_navier_spectral.py",
        "category": "physics.navier",
    },
    {
        "id": "plasma_vortex",
        "path": "malysh_plasma_vortex.py",
        "category": "physics.plasma",
    },
    {
        "id": "astrophysical_turbulence",
        "path": "astrophysical_turbulence.py",
        "category": "physics.turbulence",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(65536),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def inspect_source(path: Path) -> dict[str, Any]:
    source = path.read_text(
        encoding="utf-8",
        errors="replace",
    )
    tree = ast.parse(source)

    classes = sorted(
        {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        }
    )

    functions = sorted(
        {
            node.name
            for node in ast.walk(tree)
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
        }
    )

    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(
                alias.name
                for alias in node.names
            )

        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
        ):
            imports.append(node.module)

    return {
        "classes": classes,
        "functions": functions,
        "imports": sorted(set(imports)),
    }


def smoke_test(
    path: Path,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    environment["MPLBACKEND"] = "Agg"
    environment["MALYSH_CERTIFICATION"] = "1"

    started = time.monotonic()

    try:
        with tempfile.TemporaryDirectory(
            prefix="malysh_cert_"
        ) as temporary_directory:
            process = subprocess.run(
                [
                    sys.executable,
                    str(path),
                ],
                cwd=temporary_directory,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout_seconds,
                check=False,
            )

        output = process.stdout or ""

        return {
            "status": (
                "passed"
                if process.returncode == 0
                else "failed"
            ),
            "return_code": process.returncode,
            "duration_seconds": round(
                time.monotonic() - started,
                6,
            ),
            "output_tail": output[-1500:],
            "error": None,
        }

    except subprocess.TimeoutExpired as error:
        output = error.stdout or ""

        if isinstance(output, bytes):
            output = output.decode(
                "utf-8",
                errors="replace",
            )

        return {
            "status": "timeout",
            "return_code": None,
            "duration_seconds": round(
                time.monotonic() - started,
                6,
            ),
            "output_tail": str(output)[-1500:],
            "error": (
                f"Тайм-аут {timeout_seconds} секунд"
            ),
        }

    except Exception as error:
        return {
            "status": "exception",
            "return_code": None,
            "duration_seconds": round(
                time.monotonic() - started,
                6,
            ),
            "output_tail": "",
            "error": (
                f"{type(error).__name__}: {error}"
            ),
        }


def certify(candidate: dict[str, str]) -> dict[str, Any]:
    path = ROOT / candidate["path"]

    record: dict[str, Any] = {
        **candidate,
        "exists": path.exists(),
        "sha256": None,
        "syntax": "not_checked",
        "static": {},
        "smoke": {
            "status": "not_run",
        },
        "decision": "rejected",
    }

    if not path.exists():
        record["decision_reason"] = (
            "Файл отсутствует"
        )
        return record

    record["sha256"] = file_hash(path)

    try:
        py_compile.compile(
            str(path),
            doraise=True,
        )
        record["syntax"] = "passed"
        record["static"] = inspect_source(path)

    except Exception as error:
        record["syntax"] = "failed"
        record["decision_reason"] = (
            f"Ошибка синтаксиса: {error}"
        )
        return record

    record["smoke"] = smoke_test(path)

    if record["smoke"]["status"] == "passed":
        record["decision"] = "candidate"
        record["decision_reason"] = (
            "Статика и изолированный запуск успешны"
        )
    else:
        record["decision"] = "quarantined"
        record["decision_reason"] = (
            "Изолированный запуск не прошёл"
        )

    return record


def main() -> None:
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    records = [
        certify(candidate)
        for candidate in CANDIDATES
    ]

    summary = {
        "total": len(records),
        "candidates": sum(
            item["decision"] == "candidate"
            for item in records
        ),
        "quarantined": sum(
            item["decision"] == "quarantined"
            for item in records
        ),
        "rejected": sum(
            item["decision"] == "rejected"
            for item in records
        ),
    }

    report = {
        "schema_version": 1,
        "created_at": utc_now(),
        "mode": "isolated_certification",
        "production_registry_modified": False,
        "summary": summary,
        "organs": records,
    }

    REPORT_PATH.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 72)
    print("МАЛЫШ: СЕРТИФИКАЦИЯ ОРГАНОВ")
    print("=" * 72)
    print(f"Проверено      : {summary['total']}")
    print(f"Кандидатов     : {summary['candidates']}")
    print(f"Карантин       : {summary['quarantined']}")
    print(f"Отклонено      : {summary['rejected']}")
    print("-" * 72)

    for item in records:
        smoke_status = item["smoke"].get(
            "status",
            "not_run",
        )

        print(
            f"[{item['decision'].upper():11}] "
            f"{item['id']:<26} "
            f"syntax={item['syntax']:<7} "
            f"smoke={smoke_status}"
        )

        if item["smoke"].get("error"):
            print(
                f"  Ошибка: "
                f"{item['smoke']['error']}"
            )

    print("-" * 72)
    print(
        "Боевой config/organs.json "
        "НЕ изменялся."
    )
    print(
        "Отчёт: runtime/certification/latest.json"
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
