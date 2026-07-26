#!/usr/bin/env python3
"""Offline, public-surface verification for the Mars Skills collection."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "mars-skills.json"
SKILLS_PATH = ROOT / "skills"
PRIVATE_PATH = re.compile(
    r"/(?:Users|home)/[^/\s]+(?:/|$)|[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s]+(?:[\\/]|$)"
)
SECRET_ASSIGNMENT = re.compile(
    r"(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"]?\S+",
    re.IGNORECASE,
)
LEGACY_TERMS = ("long" + "bridge", "mars" + "-research-assistant")
POLICY_BLOCK = re.compile(r"```mars-skill-policy\n(?P<payload>\{.*?\})\n```", re.DOTALL)
RELEASE_SKILL_IDS = frozenset(
    {
        "ask-mars",
        "market-catalysts-brief",
        "market-snapshot",
        "instrument-research",
        "price-action",
        "drive-writeback",
    }
)
DATA_EVIDENCE_MARKERS = {
    "market-catalysts-brief": frozenset(
        {"研究时间：", "- 来源：", "- 来源时间："}
    ),
    "market-snapshot": frozenset({"来源：", "as_of："}),
    "instrument-research": frozenset({"来源：", "as_of："}),
    "price-action": frozenset({"来源：", "as_of："}),
}


def _fail(message: str) -> None:
    raise SystemExit(f"Mars Skills verification failed: {message}")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"invalid JSON: {path.relative_to(ROOT)} ({error})")
    if not isinstance(parsed, dict):
        _fail(f"JSON object required: {path.relative_to(ROOT)}")
    return parsed


def _skill_directories() -> dict[str, Path]:
    if not SKILLS_PATH.is_dir():
        _fail("skills directory is missing")
    return {
        path.name: path
        for path in SKILLS_PATH.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }


def _manifest_skills() -> dict[str, dict[str, Any]]:
    manifest = _read_json(MANIFEST_PATH)
    if manifest.get("schema_version") != 1:
        _fail("unsupported collection manifest schema")
    if not isinstance(manifest.get("collection"), str) or not manifest["collection"].strip():
        _fail("collection manifest requires a collection name")
    rows = manifest.get("skills")
    if not isinstance(rows, list) or not rows:
        _fail("collection manifest requires at least one Skill")
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            _fail("collection manifest Skill must be an object")
        identifier = row.get("id")
        display_name = row.get("display_name")
        if not isinstance(identifier, str) or not identifier.strip():
            _fail("collection manifest Skill requires an id")
        if not isinstance(display_name, str) or not display_name.strip():
            _fail(f"collection manifest Skill requires a display name: {identifier}")
        if identifier in indexed:
            _fail(f"duplicate collection Skill: {identifier}")
        indexed[identifier] = row
    return indexed


def _verify_skill_contract(identifier: str, directory: Path) -> None:
    skill_text = (directory / "SKILL.md").read_text(encoding="utf-8")
    if f"name: {identifier}" not in skill_text:
        _fail(f"Skill front matter name mismatch: {identifier}")

    agent_text = (directory / "agents" / "openai.yaml")
    if not agent_text.is_file():
        _fail(f"agent metadata missing: {identifier}")
    if "display_name:" not in agent_text.read_text(encoding="utf-8"):
        _fail(f"agent metadata display name missing: {identifier}")

    if "`capability.json`" not in skill_text:
        _fail(f"Skill does not consume its capability contract: {identifier}")

    contract = _read_json(directory / "capability.json")
    if contract.get("schema_version") != 1 or contract.get("skill") != identifier:
        _fail(f"acceptance contract identity mismatch: {identifier}")
    if not isinstance(contract.get("delivery"), str) or not contract["delivery"].strip():
        _fail(f"acceptance contract delivery missing: {identifier}")
    response_fields = contract.get("response_fields")
    if not isinstance(response_fields, list) or not all(
        isinstance(field, str) and field.strip() for field in response_fields
    ):
        _fail(f"acceptance contract response fields invalid: {identifier}")
    forbidden = contract.get("forbidden_effects")
    if not isinstance(forbidden, list) or not all(
        isinstance(effect, str) and effect.strip() for effect in forbidden
    ):
        _fail(f"acceptance contract forbidden effects invalid: {identifier}")
    policy_matches = POLICY_BLOCK.findall(skill_text)
    if len(policy_matches) != 1:
        _fail(f"Skill policy missing or ambiguous: {identifier}")
    try:
        policy = json.loads(policy_matches[0])
    except json.JSONDecodeError as error:
        _fail(f"Skill policy invalid JSON: {identifier} ({error})")
    expected_policy = {
        "delivery": contract["delivery"],
        "forbidden_effects": forbidden,
    }
    if policy != expected_policy:
        _fail(f"Skill policy contradicts capability contract: {identifier}")
    scenarios = contract.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        _fail(f"acceptance contract scenarios missing: {identifier}")
    for scenario in scenarios:
        if not isinstance(scenario, dict) or not isinstance(scenario.get("request"), str):
            _fail(f"acceptance scenario request invalid: {identifier}")
        if not isinstance(scenario.get("expected"), dict) or not scenario["expected"]:
            _fail(f"acceptance scenario expected outcome invalid: {identifier}")
        missing = set(response_fields) - set(scenario["expected"])
        if missing:
            _fail(
                f"acceptance scenario expected outcome missing fields: {identifier} "
                f"({', '.join(sorted(missing))})"
            )

    if identifier == "ask-mars":
        expected_forbidden = {"research", "market_data", "drive_write"}
        if contract.get("delivery") != "recommendation" or set(forbidden) != expected_forbidden:
            _fail("Ask Mars must remain recommendation-only")
        if response_fields != ["recommended_skills", "first_step", "minimum_input"]:
            _fail("Ask Mars response fields changed")
        first = scenarios[0]["expected"]
        if first.get("first_step") != "市场催化剂简报":
            _fail("Ask Mars compound-request first step changed")
        if first.get("sequence") != ["市场催化剂简报", "标的研究"]:
            _fail("Ask Mars compound-request sequence changed")
    _verify_required_contract_values(contract)
    _verify_fixture_scenarios(
        identifier, contract["scenarios"], contract.get("fixture_validation")
    )


def _fixture_path(path_value: object, context: str) -> Path:
    if not isinstance(path_value, str) or not path_value.strip():
        _fail(f"{context} fixture path missing")
    fixture_path = (ROOT / path_value).resolve()
    if not fixture_path.is_relative_to(ROOT.resolve()):
        _fail(f"{context} fixture is outside the repository: {path_value}")
    if not fixture_path.is_file():
        _fail(f"{context} fixture missing: {path_value}")
    return fixture_path


def _verify_required_contract_values(contract: dict[str, Any]) -> None:
    required = contract.get("required_contract")
    if required is None:
        return
    if not isinstance(required, dict) or not required:
        _fail("required contract values must be a non-empty object")
    for field, expected in required.items():
        if contract.get(field) != expected:
            _fail(f"required contract value changed: {field.replace('_', ' ')}")


def _verify_fixture_scenarios(
    identifier: str, scenarios: list[dict[str, Any]], validation: object
) -> None:
    fixture_scenarios = [scenario for scenario in scenarios if "fixture" in scenario]
    if not fixture_scenarios:
        if validation is not None:
            _fail("fixture validation has no fixture scenarios")
        return
    if not isinstance(validation, dict):
        _fail("fixture scenarios require fixture validation")
    renderer = _fixture_path(validation.get("renderer"), "fixture renderer")
    artifact_name = validation.get("artifact")
    markers = validation.get("required_markers")
    if not isinstance(artifact_name, str) or Path(artifact_name).name != artifact_name:
        _fail("fixture validation artifact must be a filename")
    if not isinstance(markers, list) or not all(
        isinstance(marker, str) and marker for marker in markers
    ):
        _fail("fixture validation requires rendered evidence markers")
    evidence_markers = DATA_EVIDENCE_MARKERS.get(identifier, frozenset())
    missing_evidence_markers = evidence_markers - set(markers)
    if missing_evidence_markers:
        _fail(
            f"evidence markers missing: {identifier} "
            f"({', '.join(sorted(missing_evidence_markers))})"
        )
    for scenario in fixture_scenarios:
        fixture = _fixture_path(scenario.get("fixture"), "fixture")
        with tempfile.TemporaryDirectory(prefix="mars-skills-fixture-") as temporary:
            output = Path(temporary) / artifact_name
            result = subprocess.run(
                [
                    sys.executable,
                    str(renderer),
                    "--input",
                    str(fixture),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                _fail(f"fixture render failed: {result.stderr.strip()}")
            if not output.is_file():
                _fail("fixture renderer did not create its artifact")
            rendered = output.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in rendered:
                _fail(f"fixture missing rendered evidence: {marker}")


def _public_candidates() -> list[Path]:
    tracked = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if tracked.returncode == 0:
        return sorted(ROOT / entry for entry in tracked.stdout.decode().split("\0") if entry)
    excluded = {".git", ".scratch", ".venv", ".mypy_cache", ".ruff_cache", "__pycache__"}
    return sorted(
        path
        for path in ROOT.rglob("*")
        if (path.is_file() or path.is_symlink())
        and not any(part in excluded for part in path.relative_to(ROOT).parts)
    )


def _public_text_files() -> list[tuple[Path, str]]:
    text_files: list[tuple[Path, str]] = []
    for path in _public_candidates():
        if path.is_symlink():
            _fail(f"symbolic link in public surface: {path.relative_to(ROOT)}")
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as error:
            _fail(f"unreadable public file: {path.relative_to(ROOT)} ({error})")
        text_files.append((path, text))
    return text_files


def _verify_public_surface() -> None:
    for path, text in _public_text_files():
        if PRIVATE_PATH.search(text):
            _fail(f"private absolute path: {path.relative_to(ROOT)}")
        if SECRET_ASSIGNMENT.search(text):
            _fail(f"possible credential assignment: {path.relative_to(ROOT)}")
        lowered = text.lower()
        if any(term in lowered for term in LEGACY_TERMS):
            _fail(f"retired public reference: {path.relative_to(ROOT)}")
    for skill_directory in _skill_directories().values():
        for prohibited in (".env", "auth.json", "credentials.json"):
            if any(path.name == prohibited for path in skill_directory.rglob("*")):
                _fail(f"private configuration in Skill: {skill_directory.name}")


def _file_bytes(root: Path) -> dict[Path, bytes]:
    return {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _verify_isolated_copies(skill_directories: dict[str, Path]) -> None:
    with tempfile.TemporaryDirectory(prefix="mars-skills-verify-") as temporary:
        temporary_root = Path(temporary)
        for identifier, source in skill_directories.items():
            destination = temporary_root / "agents" / "skills" / identifier
            result = subprocess.run(
                [
                    "bash",
                    str(ROOT / "scripts" / "install-mars-skill.sh"),
                    "--skill",
                    identifier,
                    "--target",
                    str(destination.parent),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                _fail(f"isolated install failed: {identifier} ({result.stderr.strip()})")
            if _file_bytes(source) != _file_bytes(destination):
                _fail(f"isolated copy differs: {identifier}")


def main() -> int:
    manifest_skills = _manifest_skills()
    if set(manifest_skills) != RELEASE_SKILL_IDS:
        _fail("six release Skills are required")
    skill_directories = _skill_directories()
    if set(manifest_skills) != set(skill_directories):
        _fail("collection manifest and discovered Skills differ")
    for identifier, directory in skill_directories.items():
        _verify_skill_contract(identifier, directory)
    _verify_public_surface()
    _verify_isolated_copies(skill_directories)
    print(f"Mars Skills contract ok: {', '.join(sorted(skill_directories))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
