#!/usr/bin/env python3
"""Verify bilingual newcomer README facts and reproducible synthetic gallery."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import zlib


REPO = Path(__file__).resolve().parents[1]
INSTALL_COMMAND = (
    "npx skills@latest add Archerouyang/dailytrades "
    "--skill trading-research-system -g"
)
VERSION = "0.1.1"
GALLERY = REPO / "docs" / "assets" / "readme"


class ContractError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def headings(text: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"^##\s+(.+)$", text, re.MULTILINE)]


def png_rgb_pixels(path: Path) -> tuple[int, int, bytes]:
    data = path.read_bytes()
    require(data.startswith(b"\x89PNG\r\n\x1a\n"), "PA browser screenshot is not a PNG")
    offset = 8
    width = height = 0
    compressed = bytearray()
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        chunk = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, depth, color_type = struct.unpack(">IIBB", chunk[:10])
            require(depth == 8 and color_type == 2, "PA PNG must be 8-bit RGB")
        elif kind == b"IDAT":
            compressed.extend(chunk)
        elif kind == b"IEND":
            break

    require((width, height) == (1200, 840), "PA browser screenshot dimensions drift")
    raw = zlib.decompress(bytes(compressed))
    stride = width * 3
    require(len(raw) == height * (stride + 1), "PA PNG scanline data is malformed")
    output = bytearray(height * stride)
    previous = bytearray(stride)
    for row in range(height):
        start = row * (stride + 1)
        filter_type = raw[start]
        scanline = bytearray(raw[start + 1 : start + 1 + stride])
        reconstructed = bytearray(stride)
        for index, value in enumerate(scanline):
            left = reconstructed[index - 3] if index >= 3 else 0
            above = previous[index]
            upper_left = previous[index - 3] if index >= 3 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            elif filter_type == 4:
                estimate = left + above - upper_left
                distances = (
                    abs(estimate - left),
                    abs(estimate - above),
                    abs(estimate - upper_left),
                )
                predictor = (left, above, upper_left)[distances.index(min(distances))]
            else:
                raise ContractError(f"unsupported PA PNG filter: {filter_type}")
            reconstructed[index] = (value + predictor) & 0xFF
        output[row * stride : (row + 1) * stride] = reconstructed
        previous = reconstructed
    return width, height, bytes(output)


def validate_png_pixels(path: Path) -> None:
    width, height, pixels = png_rgb_pixels(path)
    count = width * height
    colors = zip(pixels[0::3], pixels[1::3], pixels[2::3])
    black = white = chromatic = 0
    for red, green, blue in colors:
        black += red < 20 and green < 20 and blue < 20
        white += red > 245 and green > 245 and blue > 245
        chromatic += max(red, green, blue) - min(red, green, blue) > 30
    require(black / count < 0.05, "PA browser screenshot contains a blank/black canvas")
    require(white / count > 0.45, "PA browser screenshot lacks the expected light canvas")
    require(chromatic / count > 0.005, "PA browser screenshot lacks rendered chart state")


def validate_pa_html_contract(html: str, *, label: str) -> None:
    require("5.2.0" in html, f"{label} must use Lightweight Charts v5.2.0")
    require("TradingView" in html, f"{label} attribution missing")
    require("Synthetic fixture" in html, f"{label} synthetic label missing")


def validate_readme(path: Path, *, chinese: bool) -> None:
    text = path.read_text(encoding="utf-8")
    line_count = len(text.splitlines())
    if chinese:
        require(line_count <= 180, f"{path.name} must not exceed 180 lines")
    else:
        require(
            150 <= line_count <= 180,
            f"{path.name} must contain 150-180 lines; found {line_count}",
        )
    expected_order = (
        ["30 秒安装", "首次使用", "合成输出示例", "工作流", "能力与数据来源", "Public Skill / Private Runtime", "可选 Native Plugins", "故障排查与详细文档"]
        if chinese
        else ["Install in 30 Seconds", "First Run", "Synthetic Output Gallery", "Workflow", "Capabilities and Sources", "Public Skill / Private Runtime", "Optional Native Plugins", "Troubleshooting and Detailed Docs"]
    )
    actual = headings(text)
    positions = []
    for heading in expected_order:
        require(heading in actual, f"{path.name} missing section: {heading}")
        positions.append(actual.index(heading))
    require(positions == sorted(positions), f"{path.name} newcomer section order drift")
    require(text.count(INSTALL_COMMAND) == 1, f"{path.name} install command drift")
    prompt = "开始今日交易研究" if chinese else "Start today's trading research."
    require(prompt in text, f"{path.name} first-run prompt missing")
    require(f"Version: `{VERSION}`" in text or f"版本：`{VERSION}`" in text, f"{path.name} version missing")
    require("No order actions" in text, f"{path.name} no-order boundary missing")
    require("synthetic" in text.lower() or "合成" in text, f"{path.name} synthetic disclosure missing")
    require("Codex" in text and "Claude Code" in text, f"{path.name} native wrapper facts missing")
    require("flowchart TD" in text, f"{path.name} workflow must be top-down Mermaid")
    for filename in ("macro-regime-panel.svg", "price-action-panel.png", "position-risk-panel.svg"):
        require(f"docs/assets/readme/{filename}" in text, f"{path.name} missing gallery asset {filename}")


def validate_fresh_browser_capture(generator: Path, browser_path: str | None) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        rebuilt = Path(tmp) / "browser-gallery"
        require(not rebuilt.exists(), "fresh browser output directory must start empty")
        command = [
            sys.executable,
            str(generator),
            "--output-dir",
            str(rebuilt),
            "--browser-mode",
            "required",
        ]
        if browser_path:
            command.extend(("--browser-path", browser_path))
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
        )
        require(
            result.returncode == 0,
            f"required browser capture failed: {result.stderr or result.stdout}",
        )

        html_path = rebuilt / "price-action-panel.html"
        png_path = rebuilt / "price-action-panel.png"
        require(html_path.is_file(), "fresh browser run did not generate PA HTML")
        require(png_path.is_file(), "fresh browser run did not generate PA PNG")
        html = html_path.read_text(encoding="utf-8")
        validate_pa_html_contract(html, label="fresh PA HTML")
        require(png_path.stat().st_size > 10_000, "fresh PA browser screenshot appears blank")
        validate_png_pixels(png_path)


def validate_gallery(
    *,
    require_browser_capture: bool = False,
    browser_path: str | None = None,
) -> None:
    expected = (
        "macro-regime-panel.svg",
        "price-action-panel.html",
        "position-risk-panel.svg",
    )
    for filename in expected:
        path = GALLERY / filename
        require(path.is_file(), f"gallery artifact missing: {path}")
        require(path.stat().st_size > 1_000, f"gallery artifact unexpectedly empty: {path}")
    html = (GALLERY / "price-action-panel.html").read_text(encoding="utf-8")
    validate_pa_html_contract(html, label="PA HTML")
    require((REPO / "THIRD_PARTY_NOTICES.md").is_file(), "third-party notice missing")
    notices = (REPO / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    require("Apache-2.0" in notices and "TradingView" in notices, "TradingView Apache notice missing")
    for filename in (
        "macro-regime-panel.svg",
        "price-action-panel.html",
        "price-action-panel-fallback.svg",
        "position-risk-panel.svg",
    ):
        text = (GALLERY / filename).read_text(encoding="utf-8")
        for forbidden in ("#6f42c1", "#0969da", "#fb8500"):
            require(
                forbidden not in text,
                f"README visual violates the neutral/status/attention palette: {filename}",
            )
    generator = REPO / "scripts" / "generate_readme_gallery.py"
    require(generator.is_file(), "README gallery generator missing")

    with tempfile.TemporaryDirectory() as tmp:
        rebuilt = Path(tmp) / "readme-gallery"
        result = subprocess.run(
            [
                sys.executable,
                str(generator),
                "--output-dir",
                str(rebuilt),
                "--browser-mode",
                "none",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        require(result.returncode == 0, result.stderr or result.stdout)
        for filename in (
            "macro-regime-panel.svg",
            "price-action-panel.html",
            "price-action-panel-fallback.svg",
            "position-risk-panel.svg",
        ):
            require(
                (rebuilt / filename).read_bytes() == (GALLERY / filename).read_bytes(),
                f"gallery artifact drift; rebuild it with generate_readme_gallery.py: {filename}",
            )

    if require_browser_capture:
        validate_fresh_browser_capture(generator, browser_path)
    else:
        png_path = GALLERY / "price-action-panel.png"
        require(png_path.is_file(), f"gallery artifact missing: {png_path}")
        require(png_path.stat().st_size > 10_000, "PA browser screenshot appears blank")
        validate_png_pixels(png_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-browser-capture",
        action="store_true",
        help="regenerate the gallery in a fresh directory and require a browser PA capture",
    )
    parser.add_argument(
        "--browser-path",
        help="explicit Chrome/Chromium executable for the required browser capture",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        validate_readme(REPO / "README.md", chinese=False)
        validate_readme(REPO / "README.zh-CN.md", chinese=True)
        validate_gallery(
            require_browser_capture=args.require_browser_capture,
            browser_path=args.browser_path,
        )
    except (ContractError, OSError) as exc:
        print(f"README gallery contract failed: {exc}", file=sys.stderr)
        return 1
    if args.require_browser_capture:
        print("fresh browser capture verified")
    print("README gallery contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
