#!/usr/bin/env python3
"""Offline contract, package-budget, and fixture checks for Mars v1.0.2."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from time import perf_counter
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "skills" / "mars-research-assistant"
SKILLS = RUNTIME / "skills"
MANIFEST = RUNTIME / "mars-skills.json"
EXPECTED_SKILLS = {
    "ask-mars",
    "market-catalysts-brief",
    "market-snapshot",
    "instrument-research",
    "deep-equity-research",
    "technical-analysis",
    "drive-writeback",
}
POLICY_BLOCK = re.compile(r"```mars-skill-policy\n(?P<payload>\{.*?\})\n```", re.DOTALL)
MAX_RUNTIME_FILES = 60
MAX_RUNTIME_BYTES = 1 << 20
MAX_FIXTURE_SECONDS = 1.0
PRIVATE_PATH = re.compile(r"/(?:Users|home)/[^/\s]+(?:/|$)")
SECRET_ASSIGNMENT = re.compile(
    r"(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"]?\S+",
    re.IGNORECASE,
)


def _fail(message: str) -> None:
    raise SystemExit(f"Mars Skills verification failed: {message}")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"invalid JSON: {path.relative_to(ROOT)} ({error})")
    if not isinstance(value, dict):
        _fail(f"JSON object required: {path.relative_to(ROOT)}")
    return value


def _runtime_files() -> list[Path]:
    if not RUNTIME.is_dir():
        _fail("runtime package is missing")
    return sorted(path for path in RUNTIME.rglob("*") if path.is_file())


def _verify_runtime_budget() -> None:
    files = _runtime_files()
    size = sum(path.stat().st_size for path in files)
    if len(files) > MAX_RUNTIME_FILES:
        _fail(f"runtime package has {len(files)} files; maximum is {MAX_RUNTIME_FILES}")
    if size > MAX_RUNTIME_BYTES:
        _fail(f"runtime package is {size} bytes; maximum is {MAX_RUNTIME_BYTES}")
    prohibited = {"README.md", "AGENTS.md", "package-files.txt", "install-from-github.sh", "install-mars-skill.sh", "managed_package.py"}
    leaked = [path.relative_to(RUNTIME).as_posix() for path in files if path.name in prohibited]
    if leaked:
        _fail(f"development files leaked into runtime package: {', '.join(leaked)}")
    for path in files:
        relative_parts = path.relative_to(RUNTIME).parts
        if any(part in {"tests", "docs", ".git", ".venv", "__pycache__"} for part in relative_parts):
            _fail(f"development directory leaked into runtime package: {path.relative_to(RUNTIME)}")


def _verify_public_text() -> None:
    for path in [*ROOT.glob("README*"), *ROOT.glob("scripts/*"), *_runtime_files()]:
        if not path.is_file() or path.suffix in {".js", ".png"}:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.name == "uv.lock":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(ROOT)
        if PRIVATE_PATH.search(text):
            _fail(f"private absolute path: {relative}")
        if SECRET_ASSIGNMENT.search(text):
            _fail(f"possible credential assignment: {relative}")
        if "curl" in text.lower():
            _fail(f"curl installer reference remains in public runtime surface: {relative}")


def _verify_root_skill() -> None:
    root_skill = RUNTIME / "SKILL.md"
    text = root_skill.read_text(encoding="utf-8") if root_skill.is_file() else ""
    if "name: mars-research-assistant" not in text:
        _fail("runtime root Skill identity is invalid")
    command_markers = (
        "npx skills add archerthegoat/mars-research-assistant",
        "--skill mars-research-assistant",
        "--agent codex",
        "--global",
        "--copy",
    )
    if any(marker not in text for marker in command_markers):
        _fail("runtime root Skill does not provide the approved npx command")
    for identifier in EXPECTED_SKILLS:
        if f"`skills/{identifier}/SKILL.md`" not in text:
            _fail(f"runtime root Skill does not expose {identifier}")


def _verify_manifest_and_skills() -> None:
    manifest = _read_json(MANIFEST)
    rows = manifest.get("skills")
    if manifest.get("schema_version") != 1 or not isinstance(rows, list):
        _fail("runtime manifest is invalid")
    identifiers = {row.get("id") for row in rows if isinstance(row, dict)}
    if identifiers != EXPECTED_SKILLS or len(rows) != len(EXPECTED_SKILLS):
        _fail("runtime manifest must contain exactly seven expected Skills")
    directories = {path.name for path in SKILLS.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()}
    if directories != EXPECTED_SKILLS:
        _fail("runtime Skill directories and manifest differ")
    for identifier in sorted(EXPECTED_SKILLS):
        directory = SKILLS / identifier
        skill = (directory / "SKILL.md")
        capability_path = directory / "capability.json"
        agent = directory / "agents" / "openai.yaml"
        if not skill.is_file() or not capability_path.is_file() or not agent.is_file():
            _fail(f"runtime Skill is incomplete: {identifier}")
        text = skill.read_text(encoding="utf-8")
        if f"name: {identifier}" not in text or "`capability.json`" not in text:
            _fail(f"runtime Skill metadata is invalid: {identifier}")
        if "tests/" in text:
            _fail(f"runtime Skill refers to development tests: {identifier}")
        capability = _read_json(capability_path)
        if capability.get("schema_version") != 1 or capability.get("skill") != identifier:
            _fail(f"capability identity is invalid: {identifier}")
        delivery = capability.get("delivery")
        forbidden = capability.get("forbidden_effects")
        if not isinstance(delivery, str) or not isinstance(forbidden, list):
            _fail(f"capability delivery boundary is invalid: {identifier}")
        match = POLICY_BLOCK.findall(text)
        if len(match) != 1:
            _fail(f"Skill policy is missing or ambiguous: {identifier}")
        if json.loads(match[0]) != {"delivery": delivery, "forbidden_effects": forbidden}:
            _fail(f"Skill policy and capability contradict: {identifier}")
        if "tests/" in capability_path.read_text(encoding="utf-8"):
            _fail(f"runtime capability refers to development tests: {identifier}")
        if "display_name:" not in agent.read_text(encoding="utf-8"):
            _fail(f"agent metadata is invalid: {identifier}")
    quick = _read_json(SKILLS / "instrument-research" / "capability.json")
    if quick.get("delivery") != "local_markdown_equity_snapshot" or quick.get("issuer_identity_required_before_artifact") is not True:
        _fail("equity snapshot contract is incomplete")
    if quick.get("recent_company_updates", {}).get("window_days") != 30:
        _fail("equity snapshot must keep the 30-day update window")
    deep = _read_json(SKILLS / "deep-equity-research" / "capability.json")
    if len(deep.get("chapters", [])) != 9 or len(deep.get("financial_quality_checks", [])) != 4:
        _fail("deep-equity-research core report contract is incomplete")
    for identifier in EXPECTED_SKILLS - {"technical-analysis"}:
        contract = _read_json(SKILLS / identifier / "capability.json")
        if "local_artifact" not in contract.get("response_fields", []):
            _fail(f"textual Skill must declare a local artifact: {identifier}")


def _render(script: Path, fixture: Path, required_markers: tuple[str, ...]) -> float:
    with tempfile.TemporaryDirectory(prefix="mars-v102-fixture-") as temporary:
        output = Path(temporary) / "mars-research" / "artifact.md"
        started = perf_counter()
        result = subprocess.run(
            [sys.executable, str(script), "--input", str(fixture), "--output", str(output)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        elapsed = perf_counter() - started
        if result.returncode != 0:
            _fail(f"fixture render failed: {script.name}: {result.stderr.strip()}")
        if not output.is_file():
            _fail(f"fixture render did not create an artifact: {script.name}")
        rendered = output.read_text(encoding="utf-8")
        for marker in required_markers:
            if marker not in rendered:
                _fail(f"fixture missing required marker {marker}: {script.name}")
        if elapsed > MAX_FIXTURE_SECONDS:
            _fail(f"fixture render exceeded {MAX_FIXTURE_SECONDS:.1f}s: {script.name} ({elapsed:.3f}s)")
    return elapsed


def _verify_renderers() -> tuple[float, float]:
    snapshot = _render(
        RUNTIME / "scripts" / "render_equity_snapshot.py",
        ROOT / "tests" / "fixtures" / "equity-snapshot-primary.json",
        ("# 个股快览：TEST", "## 关键公开数据", "## 最近 30 天公司相关公告或新闻", "as_of：", "## 数据缺口"),
    )
    deep = _render(
        SKILLS / "deep-equity-research" / "scripts" / "render_deep_equity_research.py",
        ROOT / "tests" / "fixtures" / "deep-equity-research-primary.json",
        ("# 深度个股研究：TEST", "## 1. 研究范围与核心判断", "### 三情景 DCF", "### 反向 DCF", "## 9. 来源、时间戳、假设与数据缺口"),
    )
    return snapshot, deep


def main() -> int:
    _verify_runtime_budget()
    _verify_public_text()
    _verify_root_skill()
    _verify_manifest_and_skills()
    snapshot_seconds, deep_seconds = _verify_renderers()
    files = _runtime_files()
    size = sum(path.stat().st_size for path in files)
    print(
        "Mars Skills v1.0.2 contract ok: "
        f"{len(files)} runtime files, {size} bytes, "
        f"snapshot={snapshot_seconds:.3f}s, deep={deep_seconds:.3f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
