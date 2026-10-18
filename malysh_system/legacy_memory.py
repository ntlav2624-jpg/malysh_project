from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent

REGISTRY_PATH = (
    ROOT
    / "malysh_system"
    / "knowledge_registry.json"
)

TEXT_SUFFIXES = {
    ".py",
    ".json",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".csv",
    ".log",
    ".sh",
}

EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
}

MANDATORY_MEMORIES = {
    "logic_567": {
        "title": "Логика 567",
        "aliases": [
            "567",
            "logic 567",
            "logic_567",
            "логика 567",
        ],
        "kind": "legacy_logic",
    },
    "kmbp": {
        "title": "КМБП",
        "aliases": [
            "кмбп",
            "kmbp",
        ],
        "kind": "legacy_logic",
    },
    "malysh_swarm": {
        "title": "Малыш Рой",
        "aliases": [
            "малыш рой",
            "рой",
            "swarm",
            "malysh swarm",
        ],
        "kind": "collective_logic",
    },
    "omni": {
        "title": "Омни",
        "aliases": [
            "омни",
            "omni",
        ],
        "kind": "legacy_logic",
    },
    "resonance_o7": {
        "title": "Резонанс O7",
        "aliases": [
            "resonance_o7",
            "resonance o7",
            "резонанс o7",
            "operator_7",
            "оператор 7",
        ],
        "kind": "computational_logic",
    },
    "n7_geometry": {
        "title": "Геометрия N7",
        "aliases": [
            "n7",
            "n7_nodes",
            "n7_indices",
            "compute_n7_nodes",
        ],
        "kind": "geometric_logic",
    },
    "adaptive_o7": {
        "title": "Адаптивный O7",
        "aliases": [
            "adaptive_o7",
            "adaptive operator",
            "adaptive_operator_7",
            "адаптивный o7",
        ],
        "kind": "adaptive_logic",
    },
    "reflected_trajectory": {
        "title": "Отражённая траектория",
        "aliases": [
            "reflected",
            "reflection",
            "отражен",
            "отражён",
            "bounded_trajectory",
        ],
        "kind": "geometric_logic",
    },
    "human_possible": {
        "title": "Human Layer: Возможно",
        "aliases": [
            "human layer",
            "human_layer",
            "возможно",
            "reconsideration_possible",
        ],
        "kind": "cognitive_logic",
    },
    "dual_mind": {
        "title": "Двойной разум",
        "aliases": [
            "dual mind",
            "dual_mind",
            "сознание",
            "подсознание",
            "совместный",
        ],
        "kind": "cognitive_logic",
    },
    "passport_memory": {
        "title": "Паспортная память",
        "aliases": [
            "passport",
            "паспорт",
            "memory_vault",
            "deep_history",
        ],
        "kind": "memory_logic",
    },
    "quaternary_logic": {
        "title": "Четверичная логика",
        "aliases": [
            "quaternary",
            "четверич",
            "четверичная",
            "четверичную",
            "четверичной",
            "четверичное",
            "четверичный",
            "четверичные",
            "pam4",
            "pam-4",
            "base-4",
            "base4",
        ],
        "kind": "computational_logic",
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_text(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None

    if b"\x00" in raw:
        return None

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode(
            "utf-8",
            errors="replace",
        )


def relative(path: Path) -> str:
    return str(
        path.relative_to(ROOT)
    )



def repository_files():
    """
    Возвращает независимые источники знаний.

    Сам движок памяти и создаваемые им индексы
    не могут доказывать существование старой логики.
    """
    excluded_files = {
        "malysh_system/legacy_memory.py",
        "malysh_system/knowledge_registry.json",
        "malysh_system/legacy_implant_scan.json",
    }

    paths = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        if any(
            part in EXCLUDED_PARTS
            for part in path.parts
        ):
            continue

        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue

        rel = str(
            path.relative_to(ROOT)
        )

        if rel in excluded_files:
            continue

        paths.append(path)

    return sorted(paths)

def ast_knowledge(
    path: Path,
    text: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "classes": [],
        "functions": [],
        "constants": [],
        "strings": [],
        "parse_error": None,
    }

    if path.suffix != ".py":
        return result

    try:
        tree = ast.parse(
            text,
            filename=str(path),
        )
    except SyntaxError as error:
        result["parse_error"] = (
            f"{error.msg}:{error.lineno}"
        )
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            result["classes"].append(node.name)

        elif isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            result["functions"].append(node.name)

        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id.isupper():
                        result["constants"].append(
                            target.id
                        )

        elif isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                value = node.value.strip()

                if 3 <= len(value) <= 160:
                    result["strings"].append(
                        value
                    )

    for key in (
        "classes",
        "functions",
        "constants",
        "strings",
    ):
        result[key] = sorted(
            set(result[key])
        )

    return result



def alias_pattern(alias):
    """
    Строит границы термина.

    Это не позволяет слову "рой" совпасть
    с фрагментом слова "настройка".
    """
    escaped = re.escape(
        alias.lower()
    )

    return re.compile(
        r"(?<![0-9a-zа-яё_])"
        + escaped
        + r"(?![0-9a-zа-яё_])",
        flags=re.IGNORECASE,
    )


def aliases_in_text(text, aliases):
    lowered = text.lower()

    return sorted(
        {
            alias
            for alias in aliases
            if alias_pattern(alias).search(
                lowered
            )
        }
    )

def current_evidence(
    files: list[Path],
) -> tuple[
    dict[str, list[dict[str, Any]]],
    list[dict[str, Any]],
]:
    memory_hits: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    file_index = []

    for path in files:
        text = safe_text(path)

        if text is None:
            continue

        rel = relative(path)
        analysis = ast_knowledge(
            path,
            text,
        )

        entry = {
            "path": rel,
            "sha256": sha256_bytes(
                text.encode("utf-8")
            ),
            "size": len(text.encode("utf-8")),
            "classes": analysis["classes"],
            "functions": analysis["functions"],
            "constants": analysis["constants"],
            "parse_error": analysis["parse_error"],
        }

        file_index.append(entry)

        searchable_parts = [
            text,
            rel,
            " ".join(analysis["classes"]),
            " ".join(analysis["functions"]),
            " ".join(analysis["constants"]),
            " ".join(analysis["strings"]),
        ]

        searchable = "\n".join(
            searchable_parts
        )

        lines = text.splitlines()

        for memory_id, definition in (
            MANDATORY_MEMORIES.items()
        ):
            matches = aliases_in_text(
                searchable,
                definition["aliases"],
            )

            if not matches:
                continue

            excerpts = []

            for number, line in enumerate(
                lines,
                start=1,
            ):
                lowered_line = line.lower()

                if any(
                    alias.lower()
                    in lowered_line
                    for alias in matches
                ):
                    excerpts.append(
                        {
                            "line": number,
                            "text": line.strip()[:240],
                        }
                    )

                if len(excerpts) >= 5:
                    break

            memory_hits[memory_id].append(
                {
                    "source": "working_tree",
                    "path": rel,
                    "aliases": matches,
                    "excerpts": excerpts,
                }
            )

    return memory_hits, file_index



def git_history_evidence(
    memory_id,
    aliases,
):
    """
    Ищет независимые исторические свидетельства.

    Короткие и неоднозначные aliases исключаются.
    Новый legacy_memory.py не учитывается.
    """
    evidence = []
    seen = set()

    safe_aliases = []

    for alias in aliases:
        normalized = alias.strip()

        if len(normalized) < 4:
            continue

        if normalized.lower() in {
            "logic",
            "memory",
            "логика",
            "память",
        }:
            continue

        safe_aliases.append(normalized)

    for alias in safe_aliases:
        process = subprocess.run(
            [
                "git",
                "log",
                "--all",
                "--format=%H",
                "-S",
                alias,
                "--",
                ".",
                ":(exclude)malysh_system/legacy_memory.py",
                ":(exclude)malysh_system/knowledge_registry.json",
                ":(exclude)malysh_system/legacy_implant_scan.json",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        commits = [
            line.strip()
            for line in process.stdout.splitlines()
            if line.strip()
        ][:10]

        for commit in commits:
            key = (
                memory_id,
                alias.lower(),
                commit,
            )

            if key in seen:
                continue

            seen.add(key)

            metadata = subprocess.run(
                [
                    "git",
                    "show",
                    "-s",
                    "--format=%H%x09%s",
                    commit,
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
            ).stdout.strip()

            evidence.append(
                {
                    "source": "git_history",
                    "alias": alias,
                    "commit": commit,
                    "commit_summary": metadata,
                }
            )

    return evidence

def passport_evidence() -> dict[str, Any]:
    vault = ROOT / "memory_vault"

    passports = sorted(
        vault.glob("passport_*.json")
    ) if vault.exists() else []

    modes = set()
    sources = set()
    classes = set()

    for path in passports:
        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            continue

        mode = data.get("mode")
        source = data.get("source")
        signal_class = data.get(
            "signal_class"
        )

        if mode:
            modes.add(str(mode))

        if source:
            sources.add(str(source))

        if signal_class:
            classes.add(
                str(signal_class)
            )

    return {
        "passport_count": len(passports),
        "modes": sorted(modes),
        "sources": sorted(sources),
        "signal_classes": sorted(classes),
    }


def build_registry() -> dict[str, Any]:
    files = repository_files()

    hits, file_index = current_evidence(
        files
    )

    memories = []

    for memory_id, definition in (
        MANDATORY_MEMORIES.items()
    ):
        working_evidence = hits.get(
            memory_id,
            [],
        )

        history_evidence = (
            git_history_evidence(
                memory_id,
                definition["aliases"],
            )
        )

        if working_evidence:
            status = "recovered"
        elif history_evidence:
            status = "historical"
        else:
            status = "named_unresolved"

        memories.append(
            {
                "id": memory_id,
                "title": definition["title"],
                "kind": definition["kind"],
                "aliases": definition["aliases"],
                "status": status,
                "recallable": True,
                "meaning_invented": False,
                "working_tree_evidence": (
                    working_evidence
                ),
                "git_history_evidence": (
                    history_evidence
                ),
            }
        )

    return {
        "schema_version": 1,
        "system": (
            "Malysh Total Legacy Memory"
        ),
        "policy": {
            "unknown_is_not_deleted": True,
            "meaning_must_not_be_invented": True,
            "named_memory_is_recallable": True,
            "state_write": False,
            "state_commit": False,
        },
        "summary": {
            "memory_count": len(memories),
            "recovered": sum(
                item["status"] == "recovered"
                for item in memories
            ),
            "historical": sum(
                item["status"] == "historical"
                for item in memories
            ),
            "named_unresolved": sum(
                item["status"]
                == "named_unresolved"
                for item in memories
            ),
            "indexed_files": len(file_index),
        },
        "memories": memories,
        "passport_memory": (
            passport_evidence()
        ),
        "file_index": file_index,
    }


def save_registry(
    registry: dict[str, Any],
) -> None:
    REGISTRY_PATH.write_text(
        json.dumps(
            registry,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        registry = build_registry()
        save_registry(registry)
        return registry

    return json.loads(
        REGISTRY_PATH.read_text(
            encoding="utf-8"
        )
    )



def query_tokens(text):
    stopwords = {
        "вспомни",
        "вспомнить",
        "помни",
        "память",
        "логика",
        "логику",
        "логики",
        "малыш",
        "что",
        "было",
        "все",
        "всё",
        "про",
        "это",
        "как",
        "для",
        "and",
        "the",
        "logic",
        "remember",
        "recall",
    }

    return {
        token
        for token in re.findall(
            r"[0-9a-zа-яё_-]+",
            text.lower(),
        )
        if len(token) >= 2
        and token not in stopwords
    }


def recall(
    text,
    limit=12,
):
    """
    Возвращает только связанные с запросом воспоминания.

    Количество файлов или исторических свидетельств
    не создаёт релевантность само по себе.
    """
    registry = load_registry()
    lowered_query = text.lower()
    tokens = query_tokens(text)

    ranked = []

    for memory in registry["memories"]:
        aliases = [
            str(alias)
            for alias in memory["aliases"]
        ]

        exact_aliases = sorted(
            {
                alias
                for alias in aliases
                if alias_pattern(alias).search(
                    lowered_query
                )
            }
        )

        title_match = bool(
            alias_pattern(
                memory["title"]
            ).search(lowered_query)
        )

        id_match = bool(
            alias_pattern(
                memory["id"]
            ).search(lowered_query)
        )

        searchable = " ".join(
            [
                memory["id"],
                memory["title"],
                memory["kind"],
                *aliases,
            ]
        ).lower()

        matched_tokens = sorted(
            {
                token
                for token in tokens
                if alias_pattern(token).search(
                    searchable
                )
            }
        )

        if not (
            exact_aliases
            or title_match
            or id_match
            or matched_tokens
        ):
            continue

        score = 0

        score += (
            20
            * len(exact_aliases)
        )

        score += (
            8
            * len(matched_tokens)
        )

        if title_match:
            score += 20

        if id_match:
            score += 20

        if memory["status"] == "recovered":
            score += 3

        elif memory["status"] == "historical":
            score += 2

        working_paths = sorted(
            {
                item["path"]
                for item in memory[
                    "working_tree_evidence"
                ]
            }
        )

        ranked.append(
            {
                "id": memory["id"],
                "title": memory["title"],
                "kind": memory["kind"],
                "status": memory["status"],
                "score": score,
                "matched_tokens": matched_tokens,
                "matched_aliases": exact_aliases,
                "paths": working_paths,
                "meaning_invented": False,
            }
        )

    ranked.sort(
        key=lambda item: (
            -item["score"],
            item["title"],
        )
    )

    return {
        "query": text,
        "mode": "legacy_recall",
        "results": ranked[:limit],
        "possible": not bool(ranked),
        "state_write": False,
        "state_commit": False,
    }

def print_registry(
    registry: dict[str, Any],
) -> None:
    print("=" * 76)
    print("МАЛЫШ: ПАМЯТЬ ВСЕХ ЛОГИК")
    print("=" * 76)

    summary = registry["summary"]

    print(
        "Indexed files   :",
        summary["indexed_files"],
    )

    print(
        "Memories        :",
        summary["memory_count"],
    )

    print(
        "Recovered       :",
        summary["recovered"],
    )

    print(
        "Historical      :",
        summary["historical"],
    )

    print(
        "Named unresolved:",
        summary["named_unresolved"],
    )

    print("-" * 76)

    for memory in registry["memories"]:
        print(
            f"[{memory['status']:<16}] "
            f"{memory['title']}"
        )

        paths = sorted(
            {
                item["path"]
                for item in memory[
                    "working_tree_evidence"
                ]
            }
        )

        if paths:
            print(
                "  files:",
                ", ".join(paths[:8]),
            )

        history = memory[
            "git_history_evidence"
        ]

        if history:
            print(
                "  git history:",
                len(history),
            )

        if memory["status"] == (
            "named_unresolved"
        ):
            print(
                "  note: имя сохранено, "
                "значение не выдумано"
            )

    passports = registry[
        "passport_memory"
    ]

    print("-" * 76)

    print(
        "Passports:",
        passports["passport_count"],
    )

    print(
        "Modes    :",
        ", ".join(passports["modes"])
        or "-",
    )

    print("=" * 76)


def print_recall(
    result: dict[str, Any],
) -> None:
    print("=" * 76)
    print("МАЛЫШ: ВСПОМИНАЕТ")
    print("=" * 76)

    print("Запрос:", result["query"])

    if not result["results"]:
        print(
            "Точное воспоминание не найдено."
        )
        print(
            "ВОЗМОЖНО: знание существует, "
            "но ещё не связано с источником."
        )

    for index, item in enumerate(
        result["results"],
        start=1,
    ):
        print()
        print(
            f"{index}. {item['title']}"
        )
        print(
            "   status:",
            item["status"],
        )
        print(
            "   kind  :",
            item["kind"],
        )
        print(
            "   score :",
            item["score"],
        )

        if item["paths"]:
            print(
                "   files :",
                ", ".join(item["paths"]),
            )

        if item["status"] == (
            "named_unresolved"
        ):
            print(
                "   meaning: не выдумано; "
                "источник ещё ищется"
            )

    print()
    print("STATE_WRITE : False")
    print("STATE_COMMIT: False")
    print("=" * 76)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="malysh-legacy-memory",
    )

    parser.add_argument(
        "query",
        nargs="?",
    )

    parser.add_argument(
        "--rebuild",
        action="store_true",
    )

    args = parser.parse_args()

    if args.rebuild:
        registry = build_registry()
        save_registry(registry)
    else:
        registry = load_registry()

    if args.query:
        print_recall(
            recall(args.query)
        )
    else:
        print_registry(registry)


if __name__ == "__main__":
    main()
