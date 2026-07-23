#!/usr/bin/env python3
"""Verify Issue #75 source maps against public-safe synthetic golden cases."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "equity.rut_close",
    "volatility.vix3m_close",
    "fx.dxy_close",
    "commodities.xauusd_close",
    "commodities.brent_front_settlement",
    "commodities.brent_contract_code",
    "commodities.brent_roll_state",
}
REQUIRED_MAP_KEYS = {
    "field_id",
    "contract_status",
    "provider_id",
    "retrieval",
    "raw_field_paths",
    "normalization",
    "unit",
    "completed_market_semantics",
    "freshness",
    "allowed_use",
    "identity_guards",
    "fixture_cases",
    "evidence",
}
EXPECTED_SAFETY = {
    "repository_content": "provider_metadata_and_synthetic_fixtures_only",
    "persist_raw_provider_responses_by_default": False,
    "entitlement_required": True,
    "internal_use_rights_required": True,
    "public_redistribution_allowed": False,
    "source_attribution_required": True,
    "automatic_broker_switch_allowed": False,
    "search_snippet_field_evidence_allowed": False,
    "opened_exact_source_required": True,
}
DXY_CANDIDATE_PROVIDER_ID = "marketwatch_dxy_historical_quotes"
DXY_CANDIDATE_ENDPOINT = (
    "https://www.marketwatch.com/investing/index/dxy/download-data"
    "?mod=mw_quote_tab"
)
DXY_REQUIRED_COLUMNS = ["Date", "Open", "High", "Low", "Close"]
DXY_REQUIRED_IDENTITY_TEXT = [
    "DXY U.S.: ICE Futures U.S.",
    "U.S. Dollar Index (DXY)",
    "Historical Quotes",
    "Result Frequency Daily",
    "Historical and current end-of-day data provided by FACTSET",
    "All quotes are in local exchange time",
]


class VerificationError(ValueError):
    pass


class VisibleHTMLTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.visible_text: list[str] = []
        self.tables: list[list[list[tuple[str, str]]]] = []
        self._ignored_depth = 0
        self._table: list[list[tuple[str, str]]] | None = None
        self._row: list[tuple[str, str]] | None = None
        self._cell_tag: str | None = None
        self._cell_parts: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        del attrs
        if tag in {"script", "style"}:
            self._ignored_depth += 1
        elif self._ignored_depth:
            return
        elif tag == "table":
            if self._table is not None:
                raise VerificationError("nested HTML tables are unsupported")
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"th", "td"} and self._row is not None:
            self._cell_tag = tag
            self._cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if tag in {"th", "td"} and self._cell_tag == tag:
            text = " ".join(" ".join(self._cell_parts).split())
            if self._row is None:
                raise VerificationError("HTML cell closed outside a row")
            self._row.append((tag, text))
            self._cell_tag = None
            self._cell_parts = []
        elif tag == "tr" and self._row is not None:
            if self._table is None:
                raise VerificationError("HTML row closed outside a table")
            if self._row:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        text = " ".join(data.split())
        if not text:
            return
        self.visible_text.append(text)
        if self._cell_tag is not None:
            self._cell_parts.append(text)


def parse_args() -> argparse.Namespace:
    skill_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Verify the Issue #75 exact completed-market source contract."
    )
    parser.add_argument(
        "--map",
        type=Path,
        default=skill_root
        / "references"
        / "issue-75-completed-market-source-contracts.json",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=skill_root
        / "assets"
        / "fixtures"
        / "input"
        / "issue-75-source-contract-golden.json",
    )
    parser.add_argument(
        "--expected-result",
        choices=("complete", "blocked"),
        help="Return success only when the observed source-closure result matches.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"{path}: expected a JSON object")
    return value


def get_path(payload: Any, path: list[str]) -> Any:
    value = payload
    for segment in path:
        if segment == "$last":
            if not isinstance(value, list) or not value:
                raise VerificationError(f"path {path!r} expected a non-empty list")
            value = value[-1]
        else:
            if not isinstance(value, dict) or segment not in value:
                raise VerificationError(f"path {path!r} missing segment {segment!r}")
            value = value[segment]
    return value


def normalize_date(value: str) -> str:
    for pattern in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            continue
    raise VerificationError(f"unsupported date format: {value!r}")


def parse_timestamp(value: str, context: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise VerificationError(
            f"{context}: invalid timestamp {value!r}"
        ) from exc
    if parsed.tzinfo is None:
        raise VerificationError(
            f"{context}: timestamp must include a UTC offset"
        )
    return parsed


def assert_equal(actual: Any, expected: Any, context: str) -> None:
    if actual != expected:
        raise VerificationError(
            f"{context}: expected {expected!r}, received {actual!r}"
        )


def verify_map_shape(
    contract: dict[str, Any], cases_by_id: dict[str, dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    assert_equal(contract.get("issue"), 75, "map issue")
    assert_equal(contract.get("parent_issue"), 74, "map parent issue")
    safety = contract.get("safety")
    assert_equal(safety, EXPECTED_SAFETY, "map safety")

    field_maps = contract.get("field_maps")
    if not isinstance(field_maps, list):
        raise VerificationError("map field_maps must be a list")
    maps_by_id: dict[str, dict[str, Any]] = {}
    blockers: list[dict[str, Any]] = []
    for field_map in field_maps:
        if not isinstance(field_map, dict):
            raise VerificationError("each field map must be an object")
        missing_keys = REQUIRED_MAP_KEYS - field_map.keys()
        if missing_keys:
            raise VerificationError(
                f"{field_map.get('field_id', '<unknown>')}: missing keys "
                + ", ".join(sorted(missing_keys))
            )
        field_id = field_map["field_id"]
        if field_id in maps_by_id:
            raise VerificationError(f"duplicate field map: {field_id}")
        maps_by_id[field_id] = field_map

        status = field_map["contract_status"]
        if status == "closed":
            for key in (
                "provider_id",
                "retrieval",
                "raw_field_paths",
                "normalization",
                "completed_market_semantics",
                "freshness",
                "allowed_use",
            ):
                if not field_map.get(key):
                    raise VerificationError(f"{field_id}: closed map missing {key}")
            if not field_map["fixture_cases"]:
                raise VerificationError(f"{field_id}: closed map has no golden case")
            for case_id in field_map["fixture_cases"]:
                if case_id not in cases_by_id:
                    raise VerificationError(
                        f"{field_id}: missing declared fixture case {case_id}"
                    )
        elif status == "blocked":
            blocker = field_map.get("blocker")
            if not isinstance(blocker, dict):
                raise VerificationError(f"{field_id}: blocked map missing blocker")
            for key in ("code", "reason", "required_to_close"):
                if not blocker.get(key):
                    raise VerificationError(
                        f"{field_id}: blocker missing {key}"
                    )
            blockers.append({"field_id": field_id, **blocker})
            if "prohibited" not in field_map["allowed_use"].lower():
                raise VerificationError(
                    f"{field_id}: blocked map must prohibit production use"
                )
        else:
            raise VerificationError(
                f"{field_id}: invalid contract_status {status!r}"
            )

    assert_equal(set(maps_by_id), REQUIRED_FIELDS, "required field map set")
    evidence_ids = {
        item.get("id")
        for item in contract.get("source_evidence", [])
        if isinstance(item, dict)
    }
    for field_id, field_map in maps_by_id.items():
        missing_evidence = set(field_map["evidence"]) - evidence_ids
        if missing_evidence:
            raise VerificationError(
                f"{field_id}: unknown evidence "
                + ", ".join(sorted(missing_evidence))
            )
    return maps_by_id, blockers


def verify_mapped_field(
    case: dict[str, Any], field_map: dict[str, Any]
) -> None:
    assert_equal(case["provider_id"], field_map["provider_id"], case["id"])
    payload = case["payload"]
    for guard in field_map["identity_guards"]:
        actual = get_path(payload, guard["path"])
        assert_equal(actual, guard["equals"], f"{case['id']} identity guard")

    paths = field_map["raw_field_paths"]
    value = float(get_path(payload, paths["value"]))
    data_as_of = normalize_date(get_path(payload, paths["data_as_of"]))
    expected = case["expected"]
    assert_equal(expected["status"], "available", f"{case['id']} status")
    assert_equal(value, expected["value"], f"{case['id']} value")
    assert_equal(data_as_of, expected["data_as_of"], f"{case['id']} date")
    assert_equal(field_map["unit"], expected["unit"], f"{case['id']} unit")

    retrieved_at = parse_timestamp(case["retrieved_at"], case["id"])
    if retrieved_at.date() <= date.fromisoformat(data_as_of):
        raise VerificationError(
            f"{case['id']}: completed daily value was retrieved before its "
            "provider day ended"
        )


def verify_dxy_html_table(
    case: dict[str, Any], field_map: dict[str, Any]
) -> None:
    assert_equal(case["field_id"], "fx.dxy_close", f"{case['id']} field")
    assert_equal(
        case["provider_id"],
        DXY_CANDIDATE_PROVIDER_ID,
        f"{case['id']} provider",
    )
    assert_equal(
        case["provider_id"],
        field_map["provider_id"],
        f"{case['id']} map provider",
    )
    retrieval = field_map["retrieval"]
    assert_equal(
        retrieval["endpoint"],
        DXY_CANDIDATE_ENDPOINT,
        f"{case['id']} endpoint",
    )
    assert_equal(
        retrieval["non_sensitive_parameters"],
        {
            "result_frequency": "Daily",
            "row_date": "$common_completed_date",
        },
        f"{case['id']} retrieval parameters",
    )
    assert_equal(
        retrieval["response_format"],
        "visible HTML table",
        f"{case['id']} response format",
    )
    payload = case["payload"]
    assert_equal(
        payload.get("source_kind"),
        "synthetic_visible_html",
        f"{case['id']} source kind",
    )
    html = payload.get("html")
    if not isinstance(html, str) or not html.strip():
        raise VerificationError(f"{case['id']}: synthetic HTML is missing")

    parser = VisibleHTMLTableParser()
    parser.feed(html)
    parser.close()
    page_text = " ".join(parser.visible_text)
    guard_values = []
    for guard in field_map["identity_guards"]:
        if guard.get("kind") != "visible_text_contains":
            raise VerificationError(
                f"{case['id']}: unsupported DXY identity guard"
            )
        required_text = guard.get("value")
        if not isinstance(required_text, str):
            raise VerificationError(
                f"{case['id']}: DXY identity guard value must be text"
            )
        guard_values.append(required_text)
    assert_equal(
        guard_values,
        DXY_REQUIRED_IDENTITY_TEXT,
        f"{case['id']} identity contract",
    )
    for required_text in DXY_REQUIRED_IDENTITY_TEXT:
        if required_text not in page_text:
            raise VerificationError(
                f"{case['id']}: page identity missing {required_text!r}"
            )

    paths = field_map["raw_field_paths"]
    value_path = paths["value"]
    date_path = paths["data_as_of"]
    assert_equal(
        value_path,
        [
            "visible_document",
            "Historical Quotes",
            "Daily",
            "row[Date=$common_completed_date]",
            "Close",
        ],
        f"{case['id']} value path",
    )
    assert_equal(
        date_path,
        [
            "visible_document",
            "Historical Quotes",
            "Daily",
            "row[Date=$common_completed_date]",
            "Date",
        ],
        f"{case['id']} date path",
    )
    value_column = value_path[-1]
    date_column = date_path[-1]
    required_columns = field_map["normalization"]["required_columns"]
    assert_equal(
        required_columns,
        DXY_REQUIRED_COLUMNS,
        f"{case['id']} required columns",
    )

    matching_tables: list[list[list[tuple[str, str]]]] = []
    for table in parser.tables:
        if not table:
            continue
        header = [text for tag, text in table[0] if tag == "th"]
        if header == required_columns:
            matching_tables.append(table)
    if len(matching_tables) != 1:
        raise VerificationError(
            f"{case['id']}: expected one exact Daily Historical Quotes table, "
            f"received {len(matching_tables)}"
        )

    header = [text for _, text in matching_tables[0][0]]
    if value_column not in header or date_column not in header:
        raise VerificationError(
            f"{case['id']}: required Date/Close columns are absent"
        )
    expected = case["expected"]
    target_date = expected["data_as_of"]
    matching_rows: list[dict[str, str]] = []
    for cells in matching_tables[0][1:]:
        values = [text for _, text in cells]
        if len(values) != len(header):
            raise VerificationError(f"{case['id']}: malformed table row")
        row = dict(zip(header, values))
        if normalize_date(row[date_column]) == target_date:
            matching_rows.append(row)
    if len(matching_rows) != 1:
        raise VerificationError(
            f"{case['id']}: expected one row for completed date {target_date}, "
            f"received {len(matching_rows)}"
        )

    value = float(matching_rows[0][value_column])
    assert_equal(expected["status"], "available", f"{case['id']} status")
    assert_equal(value, expected["value"], f"{case['id']} value")
    assert_equal(field_map["unit"], expected["unit"], f"{case['id']} unit")
    retrieved_at = parse_timestamp(case["retrieved_at"], case["id"])
    if retrieved_at.date() <= date.fromisoformat(target_date):
        raise VerificationError(
            f"{case['id']}: EOD table was retrieved before the completed date ended"
        )


def parse_iso_date(value: str, context: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise VerificationError(f"{context}: invalid date {value!r}") from exc


def select_front_row(
    rows: list[dict[str, Any]],
    expiry_rows: list[dict[str, Any]],
    settlement_date: str,
) -> dict[str, Any]:
    as_of = parse_iso_date(settlement_date, "settlement date")
    eligible = [
        (parse_iso_date(item["LTD"], "LTD"), item["Contract Symbol"])
        for item in expiry_rows
        if parse_iso_date(item["LTD"], "LTD") >= as_of
    ]
    if not eligible:
        raise VerificationError(f"no front contract for {settlement_date}")
    _, front_strip = min(eligible)
    matches = [
        row
        for row in rows
        if row.get("Settlement Price Date") == settlement_date
        and row.get("Strip") == front_strip
        and row.get("Product Name") == "Brent Crude Futures"
        and row.get("Commodity Code") == "BRN"
        and row.get("Contract Type") == "F"
    ]
    if len(matches) != 1:
        raise VerificationError(
            f"expected one front Brent row for {settlement_date}/{front_strip}, "
            f"received {len(matches)}"
        )
    return matches[0]


def get_brent_path(
    payload: dict[str, Any],
    path: list[str],
    current: dict[str, Any],
    previous: dict[str, Any],
) -> Any:
    value: Any = payload
    for segment in path:
        if segment in {"$selected_front", "$current_front"}:
            if not isinstance(value, list) or not any(
                row is current for row in value
            ):
                raise VerificationError(
                    f"path {path!r} did not select from settlement rows"
                )
            value = current
        elif segment == "$previous_front":
            if not isinstance(value, list) or not any(
                row is previous for row in value
            ):
                raise VerificationError(
                    f"path {path!r} did not select from settlement rows"
                )
            value = previous
        elif segment == "$matching_strip":
            if not isinstance(value, list):
                raise VerificationError(
                    f"path {path!r} expected expiry rows before {segment}"
                )
            matches = [
                row
                for row in value
                if row.get("Contract Symbol") == current.get("Strip")
            ]
            if len(matches) != 1:
                raise VerificationError(
                    f"path {path!r} expected one matching expiry row"
                )
            value = matches[0]
        else:
            if not isinstance(value, dict) or segment not in value:
                raise VerificationError(
                    f"path {path!r} missing segment {segment!r}"
                )
            value = value[segment]
    return value


def verify_brent_bundle(
    case: dict[str, Any], maps_by_id: dict[str, dict[str, Any]]
) -> None:
    for field_id in (
        "commodities.brent_front_settlement",
        "commodities.brent_contract_code",
        "commodities.brent_roll_state",
    ):
        assert_equal(
            case["provider_id"],
            maps_by_id[field_id]["provider_id"],
            f"{case['id']} provider",
        )
    payload = case["payload"]
    rows = payload["settlement_rows"]
    expiry_rows = payload["expiry_rows"]
    settlement_dates = sorted({row["Settlement Price Date"] for row in rows})
    if len(settlement_dates) < 2:
        raise VerificationError(f"{case['id']}: roll state requires two dates")
    previous_date, current_date = settlement_dates[-2:]
    previous = select_front_row(rows, expiry_rows, previous_date)
    current = select_front_row(rows, expiry_rows, current_date)
    settlement_map = maps_by_id["commodities.brent_front_settlement"]
    contract_map = maps_by_id["commodities.brent_contract_code"]
    roll_map = maps_by_id["commodities.brent_roll_state"]

    for guard in settlement_map["identity_guards"]:
        for label, row in (("previous", previous), ("current", current)):
            actual = get_path(row, guard["path"])
            assert_equal(
                actual,
                guard["equals"],
                f"{case['id']} {label} identity guard",
            )

    settlement_paths = settlement_map["raw_field_paths"]
    settlement_value = float(
        get_brent_path(
            payload,
            settlement_paths["value"],
            current,
            previous,
        )
    )
    mapped_date = normalize_date(
        get_brent_path(
            payload,
            settlement_paths["data_as_of"],
            current,
            previous,
        )
    )
    settlement_market_id = get_brent_path(
        payload,
        settlement_paths["contract_market_id"],
        current,
        previous,
    )
    expiry_date = normalize_date(
        get_brent_path(
            payload,
            settlement_paths["expiry"],
            current,
            previous,
        )
    )
    expiry_symbol = get_brent_path(
        payload,
        settlement_paths["expiry_contract_symbol"],
        current,
        previous,
    )
    if parse_iso_date(expiry_date, "front expiry") < parse_iso_date(
        mapped_date, "settlement date"
    ):
        raise VerificationError(f"{case['id']}: selected front was already expired")

    contract_paths = contract_map["raw_field_paths"]
    commodity_code = get_brent_path(
        payload,
        contract_paths["commodity_code"],
        current,
        previous,
    )
    strip = get_brent_path(
        payload,
        contract_paths["strip"],
        current,
        previous,
    )
    contract_market_id = get_brent_path(
        payload,
        contract_paths["market_id"],
        current,
        previous,
    )
    assert_equal(
        contract_market_id,
        settlement_market_id,
        f"{case['id']} shared contract identity",
    )
    contract_code = f"{commodity_code}:{strip}"
    assert_equal(
        expiry_symbol,
        strip,
        f"{case['id']} expiry contract symbol",
    )

    roll_paths = roll_map["raw_field_paths"]
    current_market_id = get_brent_path(
        payload,
        roll_paths["current_market_id"],
        current,
        previous,
    )
    previous_market_id = get_brent_path(
        payload,
        roll_paths["previous_market_id"],
        current,
        previous,
    )
    current_strip = get_brent_path(
        payload,
        roll_paths["current_strip"],
        current,
        previous,
    )
    previous_strip = get_brent_path(
        payload,
        roll_paths["previous_strip"],
        current,
        previous,
    )
    same_contract = (
        current_market_id == previous_market_id
        and current_strip == previous_strip
    )
    roll_state = (
        "same_front_contract" if same_contract else "front_contract_changed"
    )
    expected = case["expected"]
    assert_equal(expected["status"], "available", f"{case['id']} status")
    assert_equal(
        settlement_value,
        expected["settlement"],
        f"{case['id']} settlement",
    )
    assert_equal(contract_code, expected["contract_code"], f"{case['id']} code")
    assert_equal(roll_state, expected["roll_state"], f"{case['id']} roll")
    assert_equal(mapped_date, expected["data_as_of"], f"{case['id']} date")
    assert_equal(
        settlement_map["unit"],
        expected["settlement_unit"],
        f"{case['id']} settlement unit",
    )
    assert_equal(
        contract_map["unit"],
        expected["contract_code_unit"],
        f"{case['id']} contract code unit",
    )
    assert_equal(
        roll_map["unit"],
        expected["roll_state_unit"],
        f"{case['id']} roll state unit",
    )

    retrieved_at = parse_timestamp(case["retrieved_at"], case["id"])
    if retrieved_at.date() <= date.fromisoformat(mapped_date):
        raise VerificationError(
            f"{case['id']}: settlement snapshot was retrieved before the "
            "completed settlement day ended"
        )


def verify_rejection(case: dict[str, Any]) -> None:
    candidate = case["candidate"]
    expected = case["expected"]
    if candidate["source_kind"] == "search_result_snippet":
        actual_reason = "source_not_opened_and_verified"
    elif (
        case["field_id"] == "commodities.brent_front_settlement"
        and candidate.get("semantic_type") != "official_settlement"
    ):
        actual_reason = "settlement_semantics_not_proven"
    else:
        raise VerificationError(f"{case['id']}: rejection reason not recognized")
    assert_equal(actual_reason, expected["reason"], case["id"])
    assert_equal(expected["status"], "unsupported", f"{case['id']} status")


def verify_substitutes(
    case: dict[str, Any], forbidden: dict[str, list[str]]
) -> None:
    for candidate in case["candidates"]:
        field_id = candidate["field_id"]
        symbol = candidate["symbol"]
        if symbol not in forbidden.get(field_id, []):
            raise VerificationError(
                f"{case['id']}: {symbol} was not rejected for {field_id}"
            )
    assert_equal(
        case["expected"]["status"],
        "unsupported",
        f"{case['id']} status",
    )
    assert_equal(
        case["expected"]["reason"],
        "substitute_instrument_forbidden",
        case["id"],
    )


def verify_broker_switch(case: dict[str, Any]) -> None:
    if case["configured_broker"] == case["candidate_broker"]:
        raise VerificationError(f"{case['id']}: fixture does not switch brokers")
    assert_equal(
        case["expected"]["status"],
        "unsupported",
        f"{case['id']} status",
    )
    assert_equal(
        case["expected"]["reason"],
        "automatic_broker_switch_forbidden",
        case["id"],
    )


def verify_cases(
    fixture: dict[str, Any],
    maps_by_id: dict[str, dict[str, Any]],
    forbidden: dict[str, list[str]],
) -> list[str]:
    assert_equal(fixture.get("issue"), 75, "fixture issue")
    assert_equal(
        fixture.get("fixture_class"),
        "public_safe_synthetic_golden",
        "fixture class",
    )
    if "synthetic" not in fixture.get("notice", "").lower():
        raise VerificationError("fixture notice must explicitly say synthetic")

    passed: list[str] = []
    for case in fixture["cases"]:
        kind = case["kind"]
        if kind == "mapped_field":
            verify_mapped_field(case, maps_by_id[case["field_id"]])
        elif kind == "html_table_field":
            verify_dxy_html_table(case, maps_by_id[case["field_id"]])
        elif kind == "brent_bundle":
            verify_brent_bundle(case, maps_by_id)
        elif kind == "rejection":
            verify_rejection(case)
        elif kind == "substitute_rejections":
            verify_substitutes(case, forbidden)
        elif kind == "broker_switch_rejection":
            verify_broker_switch(case)
        else:
            raise VerificationError(f"{case['id']}: unknown case kind {kind!r}")
        passed.append(case["id"])
    return passed


def main() -> int:
    args = parse_args()
    try:
        contract = load_json(args.map)
        fixture = load_json(args.fixture)
        cases = fixture.get("cases")
        if not isinstance(cases, list) or not cases:
            raise VerificationError("fixture cases must be a non-empty list")
        cases_by_id = {
            case["id"]: case
            for case in cases
            if isinstance(case, dict) and "id" in case
        }
        if len(cases_by_id) != len(cases):
            raise VerificationError("fixture case ids must be present and unique")

        maps_by_id, blockers = verify_map_shape(contract, cases_by_id)
        passed = verify_cases(
            fixture, maps_by_id, contract.get("forbidden_substitutes", {})
        )
    except (KeyError, TypeError, ValueError) as exc:
        print(f"VERIFIER FAIL: {exc}")
        return 2

    for case_id in passed:
        print(f"CASE PASS: {case_id}")
    if blockers:
        for blocker in blockers:
            print(
                "SOURCE BLOCKER: "
                f"{blocker['field_id']} [{blocker['code']}] {blocker['reason']}"
            )
        observed = "blocked"
        print(
            f"SOURCE CONTRACT FAIL: {len(blockers)} required field mapping(s) "
            "remain blocked"
        )
    else:
        observed = "complete"
        print("SOURCE CONTRACT PASS: all required mappings are closed")

    declared = contract.get("contract_result")
    if declared != observed:
        print(
            f"VERIFIER FAIL: declared contract_result={declared!r}, "
            f"observed={observed!r}"
        )
        return 2
    if args.expected_result:
        if args.expected_result != observed:
            print(
                f"EXPECTED RESULT FAIL: wanted {args.expected_result}, "
                f"observed {observed}"
            )
            return 1
        print(f"EXPECTED RESULT PASS: {observed}")
        return 0
    return 0 if observed == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
