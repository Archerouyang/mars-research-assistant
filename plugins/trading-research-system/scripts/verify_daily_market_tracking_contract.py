#!/usr/bin/env python3
"""Verify Daily Market Tracking user-facing guidance contract."""

import sys

from contract_suite import PluginPaths
from contract_verifier import ContractSpec, FileContract, run_contract


PATHS = PluginPaths.from_script(__file__)

FILES = {
    "skill": PATHS.skills / "daily-market-tracking" / "SKILL.md",
    "template": PATHS.templates / "daily-market-tracking.md",
}

REQUIRED = {
    "skill": [
        "运行状态",
        "可执行下一步",
        "盘前快速更新",
        "正式盘中扫描",
        "待复核",
        "修复观察",
        "初始化今日运行包",
        "生成盘中观察清单",
        "导入 KVN snapshot",
        "跳过 KVN",
        "继续盘前快速更新",
        "as of",
        "数据时间戳",
        "internal slug",
    ],
    "template": [
        "## 运行状态",
        "## 可执行下一步",
        "盘前快速更新",
        "正式盘中扫描",
        "待复核",
        "修复观察",
        "初始化今日运行包",
        "生成盘中观察清单",
        "导入 KVN snapshot",
        "跳过 KVN",
        "继续盘前快速更新",
        "as of",
        "数据时间戳",
        "只列 2-4 个动作",
    ],
}

FORBIDDEN = {
    "skill": [
        "premarket_quick_update /",
        "needs_review /",
        "repair-watch /",
    ],
    "template": [
        "premarket_quick_update /",
        "needs_review /",
        "repair-watch /",
    ],
}

SPEC = ContractSpec(
    name="daily market tracking guidance",
    success_message="daily market tracking contract ok",
    failure_header="daily market tracking contract failed:",
    files={
        key: FileContract(
            path=path,
            required_terms=REQUIRED[key],
            forbidden_terms=FORBIDDEN.get(key, []),
            forbidden_label="untranslated user-facing status",
        )
        for key, path in FILES.items()
    },
)


def main() -> int:
    return run_contract(SPEC)


if __name__ == "__main__":
    sys.exit(main())
