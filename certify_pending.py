import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path.cwd()

queue = json.loads(
    (ROOT / "malysh_system/integration_queue.json")
    .read_text(encoding="utf-8")
)

candidates = [
    x for x in queue["queue"]
    if x["strategy"] == "certify_process_adapter"
]

results = []

for item in candidates:
    path = ROOT / item["path"]

    record = {
        "id": item["id"],
        "path": item["path"],
        "category": item["category"],
        "status": "pending",
    }

    if not path.exists():
        record["status"] = "missing"
        results.append(record)
        continue

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["MPLBACKEND"] = "Agg"
    env["MALYSH_CERTIFICATION"] = "1"

    started = time.monotonic()

    try:
        with tempfile.TemporaryDirectory(
            prefix="malysh_mass_cert_"
        ) as tmp:
            p = subprocess.run(
                [sys.executable, str(path)],
                cwd=tmp,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
                check=False,
            )

        output = p.stdout or ""

        record["return_code"] = p.returncode
        record["duration_seconds"] = round(
            time.monotonic() - started, 6
        )
        record["output_tail"] = output[-1200:]
        record["status"] = (
            "passed"
            if p.returncode == 0
            else "quarantined"
        )

    except subprocess.TimeoutExpired:
        record["status"] = "timeout"
        record["return_code"] = None
        record["duration_seconds"] = round(
            time.monotonic() - started, 6
        )

    except Exception as error:
        record["status"] = "exception"
        record["error"] = (
            f"{type(error).__name__}: {error}"
        )

    results.append(record)

summary = {
    "total": len(results),
    "passed": sum(
        x["status"] == "passed"
        for x in results
    ),
    "quarantined": sum(
        x["status"] == "quarantined"
        for x in results
    ),
    "timeout": sum(
        x["status"] == "timeout"
        for x in results
    ),
    "exception": sum(
        x["status"] == "exception"
        for x in results
    ),
    "missing": sum(
        x["status"] == "missing"
        for x in results
    ),
}

report = {
    "schema_version": 1,
    "mode": "isolated_mass_certification",
    "central_state_modified": False,
    "summary": summary,
    "results": results,
}

out = ROOT / "runtime/process_certification.json"
out.parent.mkdir(parents=True, exist_ok=True)

out.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print("=" * 72)
print("МАЛЫШ: МАССОВАЯ СЕРТИФИКАЦИЯ")
print("=" * 72)

for key, value in summary.items():
    print(f"{key:12}: {value}")

print("-" * 72)

for item in results:
    print(
        f"[{item['status'].upper():11}] "
        f"{item['path']}"
    )

print("=" * 72)
