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
README_PUBLIC_PRIVATE_TERMS = (
    "Public plugin（公开能力）",
    "Private user state（私有用户状态）",
    "安装或升级只分发公开 plugin 能力，不复制、打包、提交或同步任何 private user state。",
    "每个用户必须在本机从空白模板独立初始化 private runtime；repo 不会自动恢复个人 profile 或 Active Market Plan。",
    "未来的用户偏好同步必须是独立、私有、显式 opt-in 的能力，不属于本次 public plugin 分发。",
)
MISLEADING_SYNC_CLAIMS = (
    "同账号登录会自动同步用户状态",
    "account login automatically syncs user state",
)
FIXTURE_DISCLOSURE_TERMS = (
    "All files under this directory are synthetic, sanitized test fixtures.",
    "Ticker symbols are examples for contract tests, not a recommendation list, default watchlist, or user profile.",
    "Fixtures must never be populated from private runtime, broker exports, credentials, or research history.",
)
PLUGIN_README_BOUNDARY_TERMS = (
    "Public plugin:",
    "Private user state:",
    "Installation and upgrades distribute public plugin capability only.",
    "initializes a blank private runtime locally",
    "Preference synchronization is not part of this",
)
TEMPLATE_DISCLOSURE_TERMS = (
    "These templates define empty schemas and prompts",
    "They contain no default watchlist, portfolio, setup, trading profile,",
    "Each user initializes a private runtime locally.",
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
PUBLIC_ASSET_DIRS = {"fixtures", "templates"}


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


def validate_public_package_paths(plugin_root: Path) -> None:
    for path in sorted(plugin_root.rglob("*")):
        relative = path.relative_to(plugin_root)
        if "__pycache__" in relative.parts or path.suffix == ".pyc" or path.name == ".DS_Store":
            continue
        if path.is_symlink():
            raise ContractError(f"plugin package must not contain symlink: {relative}")
        if path.is_dir():
            if relative == Path(".codex-plugin"):
                continue
            if relative.parts[0] in {"scripts", "skills"}:
                continue
            if relative.parts[0] == "assets" and (
                len(relative.parts) == 1 or relative.parts[1] in PUBLIC_ASSET_DIRS
            ):
                continue
            raise ContractError(f"plugin package contains non-public path: {relative}")
        if not path.is_file():
            continue
        if relative in PUBLIC_PLUGIN_FILES:
            continue
        if relative.parts[0] not in PUBLIC_PLUGIN_DIRS:
            raise ContractError(f"plugin package contains non-public path: {relative}")
        if relative.parts[0] == "assets" and (
            len(relative.parts) < 2 or relative.parts[1] not in PUBLIC_ASSET_DIRS
        ):
            raise ContractError(f"plugin package contains non-public asset path: {relative}")

    fixture_readme = plugin_root / "assets" / "fixtures" / "README.md"
    require(fixture_readme.is_file(), f"fixture disclosure missing: {fixture_readme}")
    fixture_disclosure = fixture_readme.read_text(encoding="utf-8")
    for term in FIXTURE_DISCLOSURE_TERMS:
        require(term in fixture_disclosure, f"fixture disclosure missing: {term}")

    for template in sorted((plugin_root / "assets" / "templates").glob("*.csv")):
        rows = [line for line in template.read_text(encoding="utf-8").splitlines() if line.strip()]
        require(
            len(rows) == 1,
            f"public CSV template must be header-only: {template.name}",
        )

    template_readme = plugin_root / "assets" / "templates" / "README.md"
    require(template_readme.is_file(), f"blank template disclosure missing: {template_readme}")
    template_disclosure = template_readme.read_text(encoding="utf-8")
    for term in TEMPLATE_DISCLOSURE_TERMS:
        require(term in template_disclosure, f"blank template disclosure missing: {term}")

    for template_name in ("market-plan.md", "trading-profile.md", "weekly-plan.md"):
        template = plugin_root / "assets" / "templates" / template_name
        if template.is_file():
            require(
                "Blank user-owned template; plugin install provides no ticker"
                in template.read_text(encoding="utf-8"),
                f"private runtime template is not explicitly blank: {template_name}",
            )

    plugin_readme = (plugin_root / "README.md").read_text(encoding="utf-8")
    for term in PLUGIN_README_BOUNDARY_TERMS:
        require(
            term in plugin_readme,
            f"plugin README public/private boundary missing: {term}",
        )


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
    require(
        README_MARKETPLACE_COMMAND in readme,
        f"README must contain exact install command: {README_MARKETPLACE_COMMAND}",
    )
    require(
        f"`{plugin_name}`" in readme,
        f"README must name the installable plugin as `{plugin_name}`",
    )
    for term in README_PUBLIC_PRIVATE_TERMS:
        require(term in readme, f"README public/private boundary missing: {term}")
    require(
        not any(claim in readme for claim in MISLEADING_SYNC_CLAIMS),
        "README must not claim that account login syncs user state",
    )
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
