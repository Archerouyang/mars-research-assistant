#!/usr/bin/env python3
"""Write one representative Macro Board to a caller-owned temporary directory."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Mapping

from macro_fixture import (
    DEFAULT_RESEARCH_AS_OF,
    DEFAULT_XNYS_CALENDAR,
    MACRO_FIELDS,
    complete_raw_macro_values,
)
from stateless_research_run import (
    FieldValue,
    LongbridgeAvailability,
    ResearchRequest,
    run_stateless_research,
)


class FixtureProvider:
    """Return only the requested fields from the synthetic representative fixture."""

    def __init__(self, values: Mapping[str, FieldValue]) -> None:
        self.values = values

    def fetch_many(self, fields: tuple[str, ...]) -> Mapping[str, FieldValue]:
        return {name: self.values[name] for name in fields if name in self.values}


def write_representative_macro_board(output_directory: Path) -> Path:
    """Write a complete fixture Board without creating runtime or saved artifacts."""

    if not output_directory.is_dir():
        raise ValueError("fixture_output_directory_missing")
    output = output_directory / "research-brief.html"
    if output.exists():
        raise FileExistsError("fixture_output_exists")
    result = run_stateless_research(
        ResearchRequest(
            required_fields=MACRO_FIELDS,
            source_choice="portable",
            delivery="macro_regime",
            research_as_of=DEFAULT_RESEARCH_AS_OF,
        ),
        availability=LongbridgeAvailability(cli_present=False, authorized=False),
        providers={"portable": FixtureProvider(complete_raw_macro_values())},
        session_calendar=DEFAULT_XNYS_CALENDAR,
    )
    if result.board_html is None or result.status != "complete":
        raise RuntimeError("representative_macro_fixture_incomplete")
    output.write_text(result.board_html, encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write a representative Macro fixture Board to an existing temporary directory."
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    output = write_representative_macro_board(parser.parse_args().output_dir)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
