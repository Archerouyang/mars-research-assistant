#!/usr/bin/env python3
"""Verify the command-first portable Agent Skill distribution."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys


REPO = Path(__file__).resolve().parents[1]
SKILL_NAME = "trading-research-system"
PORTABLE = REPO / "skills" / SKILL_NAME
INSTALL_COMMAND = (
    "npx skills@latest add Archerouyang/dailytrades "
    "--skill trading-research-system -g"
)
PRIVATE_FILE_NAMES = {
    "auth.json",
    "credentials.json",
    ".env",
}
PRIVATE_PATH_RE = re.compile(r"/Users/[^/]+/(?:Documents|Library)/")
PUBLIC_ROOT_FILES = {
    Path("LICENSE"),
    Path("SKILL.md"),
    Path("agents/openai.yaml"),
}
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
VENDOR_FILES = {
    Path("assets/vendor/echarts-6.1.0/LICENSE"),
    Path("assets/vendor/echarts-6.1.0/echarts.min.js"),
    Path("assets/vendor/lightweight-charts-5.2.0/LICENSE"),
    Path(
        "assets/vendor/lightweight-charts-5.2.0/"
        "lightweight-charts.standalone.production.js"
    ),
}
DATE_COMPONENT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FIXTURE_RUNTIME_RE = re.compile(r"^active-market-plan-\d{4}-\d{2}-\d{2}$")


class ContractError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regular_files(root: Path) -> dict[Path, Path]:
    return {
        path.relative_to(root): path
        for path in root.rglob("*")
        if (
            path.is_file()
            and not path.is_symlink()
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        )
    }


def is_allowed_portable_path(relative: Path) -> bool:
    if relative in PUBLIC_ROOT_FILES or relative in VENDOR_FILES:
        return True

    parts = relative.parts
    if len(parts) == 2 and parts[0] == "references":
        return relative.suffix in {".md", ".json"}
    if len(parts) == 2 and parts[0] == "scripts":
        return relative.suffix in {".py", ".mjs"}
    if parts[:2] == ("assets", "templates"):
        return len(parts) == 3 and relative.suffix in TEMPLATE_FILE_SUFFIXES
    if relative == Path("assets/fixtures/README.md"):
        return True
    if parts[:3] in {
        ("assets", "fixtures", "input"),
        ("assets", "fixtures", "expected"),
    }:
        return len(parts) == 4 and relative.suffix in FIXTURE_FILE_SUFFIXES
    if parts[:3] != ("assets", "fixtures", "runtime") or len(parts) < 5:
        return False
    if FIXTURE_RUNTIME_RE.fullmatch(parts[3]) is None:
        return False
    if len(parts) == 5:
        return parts[4] in FIXTURE_RUNTIME_ROOT_FILES
    if len(parts) == 6 and parts[4] == "updates":
        return relative.suffix == ".md" and DATE_COMPONENT_RE.fullmatch(relative.stem) is not None
    if len(parts) == 7 and parts[4] == "daily":
        return (
            DATE_COMPONENT_RE.fullmatch(parts[5]) is not None
            and parts[6] in FIXTURE_RUNTIME_DAILY_FILES
        )
    return False


def validate_skill() -> None:
    skills_root = REPO / "skills"
    discovered = sorted(
        path.parent.name for path in skills_root.glob("*/SKILL.md") if path.is_file()
    )
    require(
        discovered == [SKILL_NAME],
        f"root skills discovery must expose exactly {SKILL_NAME}: {discovered}",
    )
    require((PORTABLE / "SKILL.md").is_file(), "portable SKILL.md missing")
    require((PORTABLE / "agents" / "openai.yaml").is_file(), "portable agents/openai.yaml missing")
    require((PORTABLE / "references").is_dir(), "portable references missing")
    require((PORTABLE / "scripts").is_dir(), "portable scripts missing")
    require((PORTABLE / "assets").is_dir(), "portable assets missing")
    require((PORTABLE / "LICENSE").is_file(), "portable MIT license missing")
    require(
        digest(REPO / "LICENSE") == digest(PORTABLE / "LICENSE"),
        "portable Skill license drift",
    )

    skill_text = (PORTABLE / "SKILL.md").read_text(encoding="utf-8")
    require("name: trading-research-system" in skill_text, "portable skill name drift")
    require("Start today's trading research." in skill_text, "English first-run prompt missing")
    require("开始今日交易研究" in skill_text, "Chinese first-run prompt missing")
    require("blank first-run setup" in skill_text, "blank first-run setup behavior missing")
    require("No order creation" in skill_text, "no-order safety boundary missing")

    nested_skills = sorted(
        path.relative_to(PORTABLE) for path in PORTABLE.rglob("SKILL.md")
    )
    require(nested_skills == [Path("SKILL.md")], f"partial focused skills exposed: {nested_skills}")
    require(not any(path.is_symlink() for path in PORTABLE.rglob("*")), "portable skill contains symlink")

    for relative, path in regular_files(PORTABLE).items():
        require(
            is_allowed_portable_path(relative),
            f"unsupported portable Skill path: {relative}",
        )
        require(path.name not in PRIVATE_FILE_NAMES, f"private runtime-shaped file bundled: {path}")
        if path.suffix.lower() in {".md", ".json", ".toml", ".csv", ".py", ".mjs", ".yaml", ".yml"}:
            text = path.read_text(encoding="utf-8")
            require(
                PRIVATE_PATH_RE.search(text) is None,
                f"private absolute path bundled: {path}",
            )

    fixture_readme = PORTABLE / "assets" / "fixtures" / "README.md"
    require(fixture_readme.is_file(), "synthetic fixture disclosure missing")
    require(
        "synthetic" in fixture_readme.read_text(encoding="utf-8").lower(),
        "fixture disclosure must label all fixtures synthetic",
    )
    for template in (PORTABLE / "assets" / "templates").glob("*.csv"):
        populated = [line for line in template.read_text(encoding="utf-8").splitlines() if line.strip()]
        require(len(populated) == 1, f"public CSV template must be header-only: {template}")


def validate_readme_command() -> None:
    for readme in (REPO / "README.md", REPO / "README.zh-CN.md"):
        text = readme.read_text(encoding="utf-8")
        require(text.count(INSTALL_COMMAND) == 1, f"{readme.name} install command must appear exactly once")


def validate_isolated_smoke() -> None:
    smoke = REPO / "scripts" / "smoke-portable-skill-install.sh"
    require(smoke.is_file(), "isolated install smoke script missing")
    text = smoke.read_text(encoding="utf-8")
    for term in (
        'HOME="$SMOKE_ROOT/home"',
        'CODEX_HOME="$SMOKE_ROOT/codex"',
        'CLAUDE_CONFIG_DIR="$SMOKE_ROOT/claude"',
        'XDG_CONFIG_HOME="$SMOKE_ROOT/xdg"',
        "npx --yes skills@latest add",
        "--list",
        "--skill trading-research-system",
        "--agent codex claude-code",
        "diff -qr",
    ):
        require(term in text, f"isolated install smoke missing {term!r}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO)
    return parser.parse_args()


def main() -> int:
    global REPO, PORTABLE
    args = parse_args()
    REPO = args.repo_root.resolve()
    PORTABLE = REPO / "skills" / SKILL_NAME
    try:
        validate_skill()
        validate_readme_command()
        validate_isolated_smoke()
    except (ContractError, OSError) as exc:
        print(f"portable distribution contract failed: {exc}", file=sys.stderr)
        return 1
    print("portable distribution contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
