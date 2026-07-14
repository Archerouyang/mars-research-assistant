#!/usr/bin/env python3
"""Validate the repository-backed Codex plugin distribution contract."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


MARKETPLACE_PATH = Path(".agents/plugins/marketplace.json")
README_MARKETPLACE_COMMAND = (
    "codex plugin marketplace add Archerouyang/dailytrades --ref master"
)
README_MARKETPLACE_LIST_COMMAND = "codex plugin marketplace list"
README_MARKETPLACE_UPGRADE_COMMAND = "codex plugin marketplace upgrade dailytrades"
MISLEADING_SYNC_CLAIMS = (
    "同账号登录会自动同步用户状态",
    "account login automatically syncs user state",
)
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
PUBLIC_PLUGIN_FILES = {
    Path(".codex-plugin/plugin.json"),
    Path("README.md"),
}
PUBLIC_PLUGIN_DIRS = {"assets", "scripts", "skills"}
FIXTURE_FILE_SUFFIXES = {".csv", ".json", ".md"}
TEMPLATE_FILE_SUFFIXES = {".csv", ".md", ".toml"}
FIXTURE_RUNTIME_ROOT_FILES = {"market-plan.md", "trading-profile.md"}
FIXTURE_RUNTIME_DAILY_FILES = {
    "broker_executions.csv",
    "broker_orders.csv",
    "intraday-watchlist.csv",
    "portfolio_snapshot.csv",
    "position-daily-report.md",
    "reviews.md",
    "trade-plans.csv",
}
DATE_COMPONENT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FIXTURE_RUNTIME_RE = re.compile(r"^active-market-plan-\d{4}-\d{2}-\d{2}$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*```([A-Za-z0-9_-]*)\s*$")
ORDERED_LABEL_RE = re.compile(r"^\s*\d+\.\s+\*\*([^*]+)\*\*")


class ContractError(ValueError):
    """Raised when the repository distribution contract is invalid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def read_json(path: Path, label: str) -> dict[str, Any]:
    require(path.is_file(), f"{label} missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label} is not valid JSON: {path}: {exc}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object: {path}")
    return value


def require_string(mapping: dict[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    require(isinstance(value, str) and bool(value.strip()), f"{label}.{key} is required")
    return value


def is_public_asset_path(relative: Path, path: Path) -> bool:
    parts = relative.parts
    if relative == Path("assets"):
        return path.is_dir()
    if parts[:2] == ("assets", "templates"):
        if len(parts) == 2:
            return path.is_dir()
        return (
            len(parts) == 3
            and path.is_file()
            and path.suffix in TEMPLATE_FILE_SUFFIXES
        )
    if parts[:2] != ("assets", "fixtures"):
        return False
    if len(parts) == 2:
        return path.is_dir()
    if len(parts) == 3:
        if path.is_file():
            return path.name == "README.md"
        return path.is_dir() and parts[2] in {"input", "expected", "runtime"}
    fixture_group = parts[2]
    if fixture_group in {"input", "expected"}:
        return (
            len(parts) == 4
            and path.is_file()
            and path.suffix in FIXTURE_FILE_SUFFIXES
        )
    if fixture_group != "runtime":
        return False
    if len(parts) == 4:
        return path.is_dir() and FIXTURE_RUNTIME_RE.fullmatch(parts[3]) is not None
    if FIXTURE_RUNTIME_RE.fullmatch(parts[3]) is None:
        return False
    if len(parts) == 5:
        return (
            path.is_file() and path.name in FIXTURE_RUNTIME_ROOT_FILES
        ) or (
            path.is_dir() and parts[4] in {"daily", "updates"}
        )
    if len(parts) == 6 and parts[4] == "daily":
        return path.is_dir() and DATE_COMPONENT_RE.fullmatch(parts[5]) is not None
    if len(parts) == 6 and parts[4] == "updates":
        return (
            path.is_file()
            and path.suffix == ".md"
            and DATE_COMPONENT_RE.fullmatch(path.stem) is not None
        )
    if len(parts) == 7 and parts[4] == "daily":
        return (
            DATE_COMPONENT_RE.fullmatch(parts[5]) is not None
            and path.is_file()
            and path.name in FIXTURE_RUNTIME_DAILY_FILES
        )
    return False


def normalize_markdown_label(value: str) -> str:
    value = re.sub(r"[`*_]", "", value)
    return " ".join(value.strip().split()).casefold()


def markdown_headings(text: str) -> list[tuple[int, str, int]]:
    headings: list[tuple[int, str, int]] = []
    in_fence = False
    for index, line in enumerate(text.splitlines()):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if match:
            headings.append(
                (len(match.group(1)), normalize_markdown_label(match.group(2)), index)
            )
    return headings


def markdown_section(text: str, level: int, title: str, label: str) -> str:
    lines = text.splitlines()
    expected = normalize_markdown_label(title)
    headings = markdown_headings(text)
    for heading_index, (candidate_level, candidate_title, start) in enumerate(headings):
        if candidate_level != level or candidate_title != expected:
            continue
        end = len(lines)
        for next_level, _next_title, next_start in headings[heading_index + 1 :]:
            if next_level <= level:
                end = next_start
                break
        return "\n".join(lines[start + 1 : end])
    raise ContractError(f"{label} missing required level-{level} section: {title}")


def fenced_blocks(text: str, language: str) -> list[str]:
    lines = text.splitlines()
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        match = FENCE_RE.match(lines[index])
        if not match:
            index += 1
            continue
        block_language = match.group(1).casefold()
        index += 1
        content: list[str] = []
        while index < len(lines) and not FENCE_RE.match(lines[index]):
            content.append(lines[index])
            index += 1
        if block_language == language.casefold():
            blocks.append("\n".join(content))
        index += 1
    return blocks


def require_fenced_command(section: str, command: str, label: str) -> None:
    command_lines = {
        line.strip()
        for block in fenced_blocks(section, "bash")
        for line in block.splitlines()
        if line.strip()
    }
    require(command in command_lines, f"{label} missing fenced bash command: {command}")


def require_mermaid_flow(section: str, label: str) -> None:
    blocks = fenced_blocks(section, "mermaid")
    require(blocks, f"{label} missing Mermaid flow")
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        require(
            bool(lines) and re.fullmatch(r"flowchart\s+(?:TB|TD|BT|RL|LR)", lines[0]) is not None,
            f"{label} must start with flowchart and a supported direction",
        )
        require(
            any("-->" in line for line in lines[1:]),
            f"{label} must contain at least one directed edge",
        )
        require(
            sum(line.startswith("subgraph ") for line in lines)
            == sum(line == "end" for line in lines),
            f"{label} has unbalanced subgraph blocks",
        )


def ordered_step_labels(section: str) -> list[str]:
    labels: list[str] = []
    for line in section.splitlines():
        match = ORDERED_LABEL_RE.match(line)
        if match:
            labels.append(normalize_markdown_label(match.group(1)))
    return labels


def table_first_cells(section: str) -> list[str]:
    cells: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        columns = [column.strip() for column in stripped.strip("|").split("|")]
        if not columns or all(re.fullmatch(r":?-{3,}:?", column) for column in columns):
            continue
        cells.append(normalize_markdown_label(columns[0]))
    return cells


def require_table_rows(section: str, rows: tuple[str, ...], label: str) -> None:
    first_cells = table_first_cells(section)
    for row in rows:
        require(
            normalize_markdown_label(row) in first_cells,
            f"{label} missing required table row: {row}",
        )


def validate_package_markdown_contract(plugin_root: Path) -> None:
    fixture_readme = plugin_root / "assets" / "fixtures" / "README.md"
    require(fixture_readme.is_file(), f"fixture disclosure missing: {fixture_readme}")
    fixture_text = fixture_readme.read_text(encoding="utf-8")
    markdown_section(
        fixture_text,
        1,
        "Synthetic, Sanitized Fixtures",
        "fixture README",
    )
    require_table_rows(
        fixture_text,
        ("input", "expected", "runtime"),
        "fixture README",
    )

    template_readme = plugin_root / "assets" / "templates" / "README.md"
    require(template_readme.is_file(), f"blank template disclosure missing: {template_readme}")
    template_text = template_readme.read_text(encoding="utf-8")
    markdown_section(template_text, 1, "Blank Public Templates", "template README")
    require_table_rows(
        template_text,
        ("CSV", "Markdown/TOML"),
        "template README",
    )

    plugin_readme_path = plugin_root / "README.md"
    require(plugin_readme_path.is_file(), f"plugin README missing: {plugin_readme_path}")
    plugin_readme = plugin_readme_path.read_text(encoding="utf-8")
    boundary = markdown_section(
        plugin_readme,
        2,
        "Public plugin / private user state boundary",
        "plugin README",
    )
    require_table_rows(
        boundary,
        ("Public plugin", "Private user state"),
        "plugin README public/private boundary",
    )
    markdown_section(plugin_readme, 2, "Local Records", "plugin README")


def validate_repository_readme(readme: str, plugin_name: str) -> None:
    headings = markdown_headings(readme)
    level_two = [(title, line) for level, title, line in headings if level == 2]
    install_title = normalize_markdown_label("安装与升级")
    core_title = normalize_markdown_label("核心闭环")
    require(level_two, "README must contain level-2 sections")
    require(
        level_two[0][0] == install_title,
        "README installation section must be the first level-2 section",
    )
    require(
        any(title == core_title for title, _line in level_two),
        "README missing required level-2 section: 核心闭环",
    )

    installation = markdown_section(readme, 2, "安装与升级", "README")
    first_install = markdown_section(installation, 3, "首次安装", "README installation")
    expected_first_steps = tuple(
        normalize_markdown_label(value)
        for value in (
            "安装前提",
            "添加 marketplace",
            "验证 marketplace",
            "安装 plugin",
            "新开 task 并测试",
            "初始化 private runtime",
        )
    )
    require(
        tuple(ordered_step_labels(first_install)) == expected_first_steps,
        "README first-install ordered steps are incomplete or out of order",
    )
    require_fenced_command(first_install, README_MARKETPLACE_COMMAND, "README first install")
    require_fenced_command(
        first_install,
        README_MARKETPLACE_LIST_COMMAND,
        "README first install",
    )
    require(
        f"`{plugin_name}`" in first_install,
        f"README first install must name plugin `{plugin_name}`",
    )
    require(
        "/plugins" in first_install and "Plugins" in first_install,
        "README first install must cover /plugins and desktop Plugins",
    )
    require(
        fenced_blocks(first_install, "text"),
        "README first install must provide a fenced first-test prompt",
    )
    require(
        "https://developers.openai.com/codex/cli/" in first_install
        and "https://developers.openai.com/codex/app/" in first_install,
        "README prerequisites must link official Codex CLI and desktop docs",
    )
    require_mermaid_flow(first_install, "README installation Mermaid")

    upgrade = markdown_section(installation, 3, "升级", "README installation")
    expected_upgrade_steps = tuple(
        normalize_markdown_label(value)
        for value in ("确认 marketplace", "刷新 marketplace", "更新 plugin", "新开 task")
    )
    require(
        tuple(ordered_step_labels(upgrade)) == expected_upgrade_steps,
        "README upgrade ordered steps are incomplete or out of order",
    )
    require_fenced_command(upgrade, README_MARKETPLACE_UPGRADE_COMMAND, "README upgrade")

    troubleshooting = markdown_section(
        installation,
        3,
        "故障排查",
        "README installation",
    )
    require(
        len(table_first_cells(troubleshooting)) >= 3,
        "README troubleshooting must contain a header and at least two cases",
    )

    boundary = markdown_section(
        readme,
        2,
        "Public plugin / Private user state",
        "README",
    )
    require_table_rows(
        boundary,
        ("Public plugin（公开能力）", "Private user state（私有用户状态）"),
        "README public/private boundary",
    )
    require_mermaid_flow(boundary, "README public/private Mermaid")
    require(
        len(fenced_blocks(readme, "mermaid")) >= 2,
        "README must contain installation and public/private Mermaid diagrams",
    )
    require(
        not any(claim in readme for claim in MISLEADING_SYNC_CLAIMS),
        "README must not claim that account login syncs user state",
    )


def validate_public_package_paths(plugin_root: Path) -> None:
    for path in sorted(plugin_root.rglob("*")):
        relative = path.relative_to(plugin_root)
        if "__pycache__" in relative.parts or path.suffix == ".pyc" or path.name == ".DS_Store":
            raise ContractError(
                f"plugin package contains generated/cache artifact: {relative}"
            )
        if path.is_symlink():
            raise ContractError(f"plugin package must not contain symlink: {relative}")
        if relative.parts[0] == "scripts":
            if path.is_dir() and relative == Path("scripts"):
                continue
            if (
                path.is_file()
                and len(relative.parts) == 2
                and path.suffix == ".py"
            ):
                continue
            raise ContractError(
                "plugin scripts allow only top-level Python files: "
                f"{relative}"
            )
        if relative.parts[0] == "skills":
            valid_skill_path = (
                path.is_dir()
                and (
                    relative == Path("skills")
                    or len(relative.parts) == 2
                    or (
                        len(relative.parts) == 3
                        and relative.parts[2] == "references"
                    )
                )
            ) or (
                path.is_file()
                and (
                    (len(relative.parts) == 3 and path.name == "SKILL.md")
                    or (
                        len(relative.parts) == 4
                        and relative.parts[2] == "references"
                        and path.suffix == ".md"
                    )
                )
            )
            if valid_skill_path:
                continue
            raise ContractError(
                "plugin skills allow only SKILL.md and Markdown references: "
                f"{relative}"
            )
        if relative.parts[0] == "assets":
            if is_public_asset_path(relative, path):
                continue
            raise ContractError(
                f"plugin assets path is not in the public allowlist: {relative}"
            )
        if path.is_dir():
            if relative == Path(".codex-plugin"):
                continue
            raise ContractError(f"plugin package contains non-public path: {relative}")
        if not path.is_file():
            raise ContractError(f"plugin package contains unsupported entry: {relative}")
        if relative in PUBLIC_PLUGIN_FILES:
            continue
        if relative.parts[0] not in PUBLIC_PLUGIN_DIRS:
            raise ContractError(f"plugin package contains non-public path: {relative}")

    skills_root = plugin_root / "skills"
    if skills_root.is_dir():
        for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            require(
                (skill_dir / "SKILL.md").is_file(),
                f"plugin skill missing SKILL.md: {skill_dir.name}",
            )

    for template in sorted((plugin_root / "assets" / "templates").glob("*.csv")):
        rows = [line for line in template.read_text(encoding="utf-8").splitlines() if line.strip()]
        require(
            len(rows) == 1,
            f"public CSV template must be header-only: {template.name}",
        )

    validate_package_markdown_contract(plugin_root)


def validate(repo_root: Path) -> tuple[str, str]:
    repo_root = repo_root.resolve()
    marketplace_path = repo_root / MARKETPLACE_PATH
    marketplace = read_json(marketplace_path, "root marketplace")

    require_string(marketplace, "name", "marketplace")
    marketplace_interface = marketplace.get("interface")
    require(isinstance(marketplace_interface, dict), "marketplace.interface is required")
    marketplace_display_name = require_string(
        marketplace_interface, "displayName", "marketplace.interface"
    )

    plugins = marketplace.get("plugins")
    require(
        isinstance(plugins, list) and len(plugins) == 1,
        "marketplace.plugins must contain exactly one plugin",
    )
    entry = plugins[0]
    require(isinstance(entry, dict), "marketplace.plugins[0] must be an object")
    plugin_name = require_string(entry, "name", "marketplace.plugins[0]")
    require(
        "version" not in entry,
        "marketplace plugin entry must not duplicate manifest version",
    )

    source = entry.get("source")
    require(isinstance(source, dict), "marketplace plugin source is required")
    require(
        source.get("source") == "local",
        "marketplace plugin source.source must be local",
    )
    source_path = require_string(source, "path", "marketplace.plugins[0].source")
    require(
        source_path == f"./plugins/{plugin_name}",
        f"marketplace source.path must be ./plugins/{plugin_name}",
    )
    plugin_root = (repo_root / source_path).resolve()
    require(
        os.path.commonpath((str(repo_root), str(plugin_root))) == str(repo_root),
        "marketplace source.path escapes repository root",
    )
    require(
        plugin_root.is_dir(),
        f"marketplace plugin source does not exist: {source_path}",
    )
    nested_marketplaces = sorted(
        path.relative_to(repo_root)
        for path in repo_root.glob("**/.agents/plugins/marketplace.json")
        if path.resolve() != marketplace_path.resolve()
    )
    require(
        not nested_marketplaces,
        "nested marketplace files conflict with the root distribution source: "
        + ", ".join(str(path) for path in nested_marketplaces),
    )
    validate_public_package_paths(plugin_root)

    policy = entry.get("policy")
    require(isinstance(policy, dict), "marketplace plugin policy is required")
    require(
        policy.get("installation")
        in {"NOT_AVAILABLE", "AVAILABLE", "INSTALLED_BY_DEFAULT"},
        "marketplace policy.installation is invalid",
    )
    require(
        policy.get("authentication") in {"ON_INSTALL", "ON_USE"},
        "marketplace policy.authentication is invalid",
    )
    category = require_string(entry, "category", "marketplace.plugins[0]")

    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    manifest = read_json(manifest_path, "plugin manifest")
    manifest_name = require_string(manifest, "name", "plugin manifest")
    require(manifest_name == plugin_name, "marketplace and plugin manifest names differ")
    require(plugin_root.name == manifest_name, "plugin directory and manifest names differ")
    version = require_string(manifest, "version", "plugin manifest")
    require(
        SEMVER_RE.fullmatch(version) is not None,
        f"plugin manifest version is not strict SemVer: {version}",
    )
    require_string(manifest, "description", "plugin manifest")
    author = manifest.get("author")
    require(isinstance(author, dict), "plugin manifest.author is required")
    require_string(author, "name", "plugin manifest.author")
    manifest_interface = manifest.get("interface")
    require(isinstance(manifest_interface, dict), "plugin manifest.interface is required")
    for field in (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
    ):
        require_string(manifest_interface, field, "plugin manifest.interface")
    capabilities = manifest_interface.get("capabilities")
    require(
        isinstance(capabilities, list)
        and bool(capabilities)
        and all(isinstance(item, str) and item for item in capabilities),
        "plugin manifest.interface.capabilities must contain strings",
    )
    default_prompt = manifest_interface.get("defaultPrompt")
    require(
        isinstance(default_prompt, list)
        and 1 <= len(default_prompt) <= 3
        and all(isinstance(item, str) and bool(item.strip()) for item in default_prompt),
        "plugin manifest.interface.defaultPrompt is required and must contain 1-3 strings",
    )
    require(
        marketplace_display_name == manifest_interface["displayName"],
        "marketplace and plugin manifest display names differ",
    )
    require(
        category == manifest_interface["category"],
        "marketplace and plugin categories differ",
    )

    readme_path = repo_root / "README.md"
    require(readme_path.is_file(), f"README missing: {readme_path}")
    readme = readme_path.read_text(encoding="utf-8")
    validate_repository_readme(readme, plugin_name)
    return plugin_name, version


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the verifier's repository)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        plugin_name, version = validate(args.repo_root)
    except (ContractError, OSError) as exc:
        print(f"error: plugin distribution contract failed: {exc}", file=sys.stderr)
        return 1
    print(f"Plugin distribution contract ok: {plugin_name} {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
