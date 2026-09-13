#!/usr/bin/env python3
"""Fail the skill-repo mistakes that have already shipped once.

Run with ``python3 check.py``. It reads only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILLS = (
    "setup-standin",
    "standin-openclaw",
    "standin-hermes-agent",
    "expose-standin",
)

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
NAME = re.compile(r"^name:\s*(\S+)\s*$", re.MULTILINE)
REL_LINK = re.compile(r"\]\((\.\.?/[^)\s#]+)\)")
DASHES = {"—": "em dash", "–": "en dash"}
SECRET_IN_CHAT = re.compile(r"Receive the secret in chat")
LEAKS = (
    r"\bkubernetes\b",
    r"\baks\b",
    r"\bprisma\b",
    r"\bpostgresql\b",
    r"\bcrawl4ai\b",
    r"standin-media-bridge",
    r"emptyDir",
)
HERMES_INTERNALS = re.compile(r"no HTTP hop|no second service", re.IGNORECASE)


def fail(path: Path, msg: str) -> str:
    return f"{path.relative_to(ROOT)}: {msg}"


def skill_files() -> list[Path]:
    missing = [name for name in SKILLS if not (ROOT / name / "SKILL.md").is_file()]
    extra = sorted(
        p.parent.name
        for p in ROOT.glob("*/SKILL.md")
        if p.parent.name not in SKILLS
    )
    problems: list[str] = []
    if missing:
        problems.append(fail(ROOT, f"missing skill directories: {', '.join(missing)}"))
    if extra:
        problems.append(fail(ROOT, f"unexpected skill directories: {', '.join(extra)}"))
    return problems


def check_skill(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []
    fm = FRONTMATTER.match(text)
    if not fm:
        return [fail(path, "missing YAML frontmatter")]
    name_m = NAME.search(fm.group(1))
    if not name_m:
        problems.append(fail(path, "frontmatter has no name"))
    else:
        name = name_m.group(1)
        if name != path.parent.name:
            problems.append(
                fail(path, f"name {name!r} does not match directory {path.parent.name!r}")
            )
    if "description:" not in fm.group(1):
        problems.append(fail(path, "frontmatter has no description"))
    for ch, label in DASHES.items():
        if ch in text:
            problems.append(fail(path, f"contains a forbidden {label}"))
    if SECRET_IN_CHAT.search(text):
        problems.append(fail(path, "tells the agent to take a live secret in chat"))
    for pat in LEAKS:
        if re.search(pat, text, re.IGNORECASE):
            problems.append(fail(path, f"leaks internal wording matching {pat}"))
    if path.parent.name == "standin-hermes-agent" and HERMES_INTERNALS.search(text):
        problems.append(fail(path, "Hermes skill still describes internal hops"))
    if path.parent.name == "standin-openclaw":
        if '"standin-msteams"' not in text:
            problems.append(fail(path, "OpenClaw skill must keep plugin id standin-msteams"))
        if "OpenClaw consult" not in text or "managed" not in text.lower():
            problems.append(fail(path, "OpenClaw recap must require consult and managed chat"))
    if path.parent.name == "standin-hermes-agent" and "msteams_bridge" not in text:
        problems.append(fail(path, "Hermes skill must keep entry point msteams_bridge"))
    if path.parent.name == "setup-standin":
        if "knowledge base" not in text.lower():
            problems.append(fail(path, "setup must mention the knowledge base"))
        if "Receive the secret in chat" in text:
            problems.append(fail(path, "setup still asks for the secret in chat"))
    for rel in REL_LINK.findall(text):
        target = (path.parent / rel).resolve()
        if not target.exists():
            problems.append(fail(path, f"broken relative link {rel}"))
    return problems


def check_readme(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []
    for name in SKILLS:
        if f"./{name}" not in text and f"`{name}`" not in text:
            problems.append(fail(path, f"does not mention skill {name}"))
    if "Compatible with" not in text:
        problems.append(fail(path, "must not claim verified support for every listed harness"))
    for ch, label in DASHES.items():
        if ch in text:
            problems.append(fail(path, f"contains a forbidden {label}"))
    return problems


def main() -> int:
    problems = skill_files()
    for name in SKILLS:
        skill = ROOT / name / "SKILL.md"
        if skill.is_file():
            problems.extend(check_skill(skill))
    readme = ROOT / "README.md"
    if readme.is_file():
        problems.extend(check_readme(readme))
    else:
        problems.append(fail(ROOT, "missing README.md"))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print(f"ok: {len(SKILLS)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
