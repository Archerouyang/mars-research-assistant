#!/usr/bin/env python3
"""Verify the Issue #75 RUT and VIX3M completed-close source maps."""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = (
    "equity.rut_close",
    "volatility.vix3m_close",
)
EXPECTED_CASE_IDS = {
    "cboe-rut-completed-close",
    "cboe-vix3m-completed-close",
    "same-day-row-is-not-completed",
    "proxies-cannot-satisfy-required-fields",
    "search-snippet-is-discovery-only",
    "configured-broker-is-not-auto-switched",
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
EXPECTED_PRODUCTION_AVAILABILITY = {
    "status": "not_claimed_by_source_contract",
    "reason": (
        "Public discovery and direct opening prove source identity and response "
        "shape, not future reachability, freshness, entitlement, or production "
        "authorization."
    ),
    "runtime_requirements": [
        "fresh HTTPS retrieval from the exact mapped URL",
        "exact expected columns and one selected completed-date row",
        "applicable Cboe entitlement and internal-use rights",
        "source attribution and no raw-payload persistence or redistribution",
    ],
}
EXPECTED_FORBIDDEN_SUBSTITUTES = {
    "equity.rut_close": ["IWM"],
    "volatility.vix3m_close": ["VIXM", "VIXY", "UVXY", "SVXY"],
}
FIELD_CONTRACTS = {
    "equity.rut_close": {
        "endpoint": (
            "https://cdn.cboe.com/api/global/us_indices/daily_prices/"
            "RUT_History.csv"
        ),
        "columns": ["DATE", "RUT"],
        "value_path": ["records", "$last", "RUT"],
        "date_path": ["records", "$last", "DATE"],
        "unit": "index_points",
        "fixture_case": "cboe-rut-completed-close",
        "evidence": {
            "lseg-russell-2000-definition",
            "cboe-rut-product-identity",
            "cboe-rut-daily-csv",
            "cboe-index-licensing",
        },
    },
    "volatility.vix3m_close": {
        "endpoint": (
            "https://cdn.cboe.com/api/global/us_indices/daily_prices/"
            "VIX3M_History.csv"
        ),
        "columns": ["DATE", "OPEN", "HIGH", "LOW", "CLOSE"],
        "value_path": ["records", "$last", "CLOSE"],
        "date_path": ["records", "$last", "DATE"],
        "unit": "volatility_index_points",
        "fixture_case": "cboe-vix3m-completed-close",
        "evidence": {
            "cboe-vix3m-definition",
            "cboe-vix3m-methodology",
            "cboe-vix3m-daily-csv",
            "cboe-index-licensing",
        },
    },
}
EXPECTED_EVIDENCE_URLS = {
    "lseg-russell-2000-definition": (
        "https://www.lseg.com/en/ftse-russell/indices/russell-2000-index"
    ),
    "cboe-rut-product-identity": (
        "https://www.cboe.com/tradable-products/product-list"
    ),
    "cboe-rut-daily-csv": FIELD_CONTRACTS["equity.rut_close"]["endpoint"],
    "cboe-vix3m-definition": (
        "https://www.cboe.com/tradable-products/vix/term-structure"
    ),
    "cboe-vix3m-methodology": (
        "https://cdn.cboe.com/api/global/us_indices/governance/"
        "Volatility_Index_Methodology_Selected_SPX_Target_Expected_"
        "Volatility_Term_Indices.pdf"
    ),
    "cboe-vix3m-daily-csv": FIELD_CONTRACTS["volatility.vix3m_close"][
        "endpoint"
    ],
    "cboe-index-licensing": "https://www.cboe.com/data/global-indices-feed/",
}
REQUIRED_MAP_KEYS = {
    "field_id",
    "contract_status",
    "runtime_availability",
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


class VerificationError(ValueError):
    pass


def parse_args() -> argparse.Namespace:
    skill_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Verify Issue #75 exact RUT and VIX3M source maps."
    )
    parser.add_argument(
        "--map",
        type=Path,
        default=(
            skill_root
            / "references"
            / "issue-75-completed-market-source-contracts.json"
        ),
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=(
            skill_root
            / "assets"
            / "fixtures"
            / "input"
            / "issue-75-source-contract-golden.json"
        ),
    )
    parser.add_argument(
        "--expected-result",
        choices=("complete", "blocked"),
        help="Return success only when the observed source-map result matches.",
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


def assert_equal(actual: Any, expected: Any, context: str) -> None:
    if actual != expected:
        raise VerificationError(
            f"{context}: expected {expected!r}, received {actual!r}"
        )


def get_path(payload: Any, path: list[str]) -> Any:
    value = payload
    for segment in path:
        if segment == "$last":
            if not isinstance(value, list) or not value:
                raise VerificationError(f"path {path!r} expected a non-empty list")
            value = value[-1]
        else:
            if not isinstance(value, dict) or segment not in value:
                raise VerificationError(
                    f"path {path!r} missing segment {segment!r}"
                )
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
        raise VerificationError(f"{context}: timestamp must include a UTC offset")
    return parsed


def verify_source_evidence(contract: dict[str, Any]) -> set[str]:
    evidence = contract.get("source_evidence")
    if not isinstance(evidence, list):
        raise VerificationError("source_evidence must be a list")
    by_id = {
        item.get("id"): item
        for item in evidence
        if isinstance(item, dict) and item.get("id")
    }
    assert_equal(set(by_id), set(EXPECTED_EVIDENCE_URLS), "source evidence ids")
    for evidence_id, expected_url in EXPECTED_EVIDENCE_URLS.items():
        item = by_id[evidence_id]
        assert_equal(item.get("url"), expected_url, f"{evidence_id} url")
        if item.get("discovery") not in {
            "public_web_search",
            "public_web_search_then_direct_open",
        }:
            raise VerificationError(f"{evidence_id}: source was not web-discovered")
        assert_equal(item.get("opened_at"), "2026-07-23", f"{evidence_id} opened")
        if not item.get("authority") or not item.get("supports"):
            raise VerificationError(f"{evidence_id}: incomplete source evidence")
        if "snippet" in str(item.get("discovery")).lower():
            raise VerificationError(f"{evidence_id}: search snippet used as evidence")
    return set(by_id)


def verify_provider_gaps(contract: dict[str, Any]) -> None:
    gaps = contract.get("observed_provider_gaps")
    if not isinstance(gaps, list):
        raise VerificationError("observed_provider_gaps must be a list")
    by_provider = {
        item.get("provider"): item
        for item in gaps
        if isinstance(item, dict) and item.get("provider")
    }
    assert_equal(set(by_provider), {"Longbridge", "IBKR"}, "provider gap set")
    assert_equal(
        by_provider["Longbridge"].get("status"),
        "unsupported",
        "Longbridge gap status",
    )
    assert_equal(
        by_provider["IBKR"].get("status"),
        "not_selected_for_this_public_fallback",
        "IBKR gap status",
    )
    for provider, gap in by_provider.items():
        assert_equal(gap.get("fields"), list(REQUIRED_FIELDS), f"{provider} fields")
        boundary = str(gap.get("boundary", "")).lower()
        if provider == "IBKR" and "never switches" not in boundary:
            raise VerificationError("IBKR gap must prohibit broker switching")


def verify_field_map(
    field_map: dict[str, Any],
    cases_by_id: dict[str, dict[str, Any]],
    evidence_ids: set[str],
) -> dict[str, Any] | None:
    field_id = field_map.get("field_id")
    if field_id not in FIELD_CONTRACTS:
        raise VerificationError(f"unexpected field map: {field_id!r}")
    missing = REQUIRED_MAP_KEYS - field_map.keys()
    if missing:
        raise VerificationError(
            f"{field_id}: missing map keys {', '.join(sorted(missing))}"
        )

    expected = FIELD_CONTRACTS[field_id]
    status = field_map.get("contract_status")
    if status == "blocked":
        blocker = field_map.get("blocker")
        if not isinstance(blocker, dict):
            raise VerificationError(f"{field_id}: blocked map missing blocker")
        for key in ("code", "reason", "required_to_close"):
            if not blocker.get(key):
                raise VerificationError(f"{field_id}: blocker missing {key}")
        assert_equal(
            field_map.get("runtime_availability"),
            "disabled",
            f"{field_id} blocked runtime",
        )
        return {"field_id": field_id, **blocker}
    assert_equal(status, "closed", f"{field_id} contract status")
    assert_equal(
        field_map.get("runtime_availability"),
        "requires_fresh_authorized_read",
        f"{field_id} runtime availability",
    )
    assert_equal(
        field_map.get("provider_id"),
        "cboe_daily_index_history",
        f"{field_id} provider",
    )

    retrieval = field_map.get("retrieval", {})
    assert_equal(retrieval.get("method"), "HTTPS GET CSV", f"{field_id} method")
    assert_equal(
        retrieval.get("endpoint"),
        expected["endpoint"],
        f"{field_id} endpoint",
    )
    assert_equal(
        retrieval.get("non_sensitive_parameters"), {}, f"{field_id} parameters"
    )
    assert_equal(retrieval.get("response_format"), "csv", f"{field_id} format")

    paths = field_map.get("raw_field_paths", {})
    assert_equal(paths.get("value"), expected["value_path"], f"{field_id} value path")
    assert_equal(
        paths.get("data_as_of"), expected["date_path"], f"{field_id} date path"
    )
    normalization = field_map.get("normalization", {})
    assert_equal(
        normalization.get("required_columns"),
        expected["columns"],
        f"{field_id} columns",
    )
    assert_equal(field_map.get("unit"), expected["unit"], f"{field_id} unit")
    assert_equal(
        field_map.get("fixture_cases"),
        [expected["fixture_case"]],
        f"{field_id} fixture cases",
    )
    if expected["fixture_case"] not in cases_by_id:
        raise VerificationError(f"{field_id}: declared fixture is missing")
    assert_equal(
        set(field_map.get("evidence", [])),
        expected["evidence"],
        f"{field_id} evidence",
    )
    if not set(field_map.get("evidence", [])) <= evidence_ids:
        raise VerificationError(f"{field_id}: unknown evidence reference")
    for key in ("completed_market_semantics", "freshness", "allowed_use"):
        if not field_map.get(key):
            raise VerificationError(f"{field_id}: missing {key}")

    expected_guards = [
        {"path": ["source_url"], "equals": expected["endpoint"]},
        {"path": ["columns"], "equals": expected["columns"]},
    ]
    assert_equal(
        field_map.get("identity_guards"),
        expected_guards,
        f"{field_id} identity guards",
    )
    return None


def verify_map_shape(
    contract: dict[str, Any], cases_by_id: dict[str, dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    assert_equal(contract.get("schema_version"), "2.0", "map schema")
    assert_equal(contract.get("contract_version"), "issue-75-v4", "map version")
    assert_equal(contract.get("issue"), 75, "map issue")
    assert_equal(contract.get("parent_issue"), 74, "map parent issue")
    assert_equal(contract.get("scope"), list(REQUIRED_FIELDS), "map scope")
    assert_equal(contract.get("safety"), EXPECTED_SAFETY, "map safety")
    assert_equal(
        contract.get("production_availability"),
        EXPECTED_PRODUCTION_AVAILABILITY,
        "production availability boundary",
    )
    assert_equal(
        contract.get("forbidden_substitutes"),
        EXPECTED_FORBIDDEN_SUBSTITUTES,
        "forbidden substitutes",
    )
    evidence_ids = verify_source_evidence(contract)
    verify_provider_gaps(contract)

    field_maps = contract.get("field_maps")
    if not isinstance(field_maps, list):
        raise VerificationError("field_maps must be a list")
    maps_by_id: dict[str, dict[str, Any]] = {}
    blockers: list[dict[str, Any]] = []
    for field_map in field_maps:
        if not isinstance(field_map, dict):
            raise VerificationError("each field map must be an object")
        field_id = field_map.get("field_id")
        if field_id in maps_by_id:
            raise VerificationError(f"duplicate field map: {field_id}")
        maps_by_id[field_id] = field_map
        blocker = verify_field_map(field_map, cases_by_id, evidence_ids)
        if blocker:
            blockers.append(blocker)
    assert_equal(set(maps_by_id), set(REQUIRED_FIELDS), "required field map set")
    return maps_by_id, blockers


def verify_mapped_field(
    case: dict[str, Any], field_map: dict[str, Any]
) -> None:
    field_id = case.get("field_id")
    expected_contract = FIELD_CONTRACTS[field_id]
    assert_equal(case.get("provider_id"), field_map.get("provider_id"), case["id"])
    payload = case.get("payload")
    if not isinstance(payload, dict):
        raise VerificationError(f"{case['id']}: payload must be an object")
    for guard in field_map["identity_guards"]:
        assert_equal(
            get_path(payload, guard["path"]),
            guard["equals"],
            f"{case['id']} identity guard",
        )

    rows = payload.get("records")
    if not isinstance(rows, list) or not rows:
        raise VerificationError(f"{case['id']}: records must be non-empty")
    value = float(get_path(payload, expected_contract["value_path"]))
    if not math.isfinite(value):
        raise VerificationError(f"{case['id']}: value must be finite")
    data_as_of = normalize_date(get_path(payload, expected_contract["date_path"]))
    matching_dates = [
        normalize_date(row["DATE"])
        for row in rows
        if isinstance(row, dict) and "DATE" in row
    ].count(data_as_of)
    if matching_dates != 1:
        raise VerificationError(
            f"{case['id']}: completed date must occur exactly once"
        )

    expected = case.get("expected", {})
    assert_equal(expected.get("status"), "available", f"{case['id']} status")
    assert_equal(value, expected.get("value"), f"{case['id']} value")
    assert_equal(data_as_of, expected.get("data_as_of"), f"{case['id']} date")
    assert_equal(field_map.get("unit"), expected.get("unit"), f"{case['id']} unit")
    retrieved_at = parse_timestamp(case["retrieved_at"], case["id"])
    if retrieved_at.date() <= date.fromisoformat(data_as_of):
        raise VerificationError(f"{case['id']}: completed close not proven")


def verify_timing_rejection(case: dict[str, Any]) -> None:
    retrieved_at = parse_timestamp(case["retrieved_at"], case["id"])
    data_as_of = date.fromisoformat(case["candidate"]["data_as_of"])
    reason = (
        "completed_close_not_proven"
        if retrieved_at.date() <= data_as_of
        else "unexpectedly_completed"
    )
    assert_equal(reason, case["expected"]["reason"], case["id"])
    assert_equal(case["expected"]["status"], "unsupported", f"{case['id']} status")


def verify_substitutes(
    case: dict[str, Any], forbidden: dict[str, list[str]]
) -> None:
    observed: dict[str, list[str]] = {field_id: [] for field_id in REQUIRED_FIELDS}
    for candidate in case.get("candidates", []):
        field_id = candidate.get("field_id")
        symbol = candidate.get("symbol")
        if field_id not in observed or symbol not in forbidden[field_id]:
            raise VerificationError(
                f"{case['id']}: unexpected substitute {field_id}:{symbol}"
            )
        observed[field_id].append(symbol)
    for symbols in observed.values():
        symbols.sort()
    expected = {field_id: sorted(symbols) for field_id, symbols in forbidden.items()}
    assert_equal(observed, expected, f"{case['id']} substitute set")
    assert_equal(case["expected"]["status"], "unsupported", f"{case['id']} status")
    assert_equal(
        case["expected"]["reason"],
        "substitute_instrument_forbidden",
        case["id"],
    )


def verify_source_rejection(case: dict[str, Any]) -> None:
    source_kind = case.get("candidate", {}).get("source_kind")
    reason = (
        "source_not_opened_and_verified"
        if source_kind == "search_result_snippet"
        else "unexpected_source_kind"
    )
    assert_equal(reason, case["expected"]["reason"], case["id"])
    assert_equal(case["expected"]["status"], "unsupported", f"{case['id']} status")


def verify_broker_switch(case: dict[str, Any]) -> None:
    if case.get("configured_broker") == case.get("candidate_broker"):
        raise VerificationError(f"{case['id']}: fixture does not switch brokers")
    assert_equal(case["expected"]["status"], "unsupported", f"{case['id']} status")
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
    assert_equal(fixture.get("schema_version"), "2.0", "fixture schema")
    assert_equal(fixture.get("issue"), 75, "fixture issue")
    assert_equal(
        fixture.get("fixture_class"),
        "public_safe_synthetic_golden",
        "fixture class",
    )
    notice = str(fixture.get("notice", "")).lower()
    if "synthetic" not in notice or "not licensed market data" not in notice:
        raise VerificationError("fixture notice must disclose synthetic data")

    passed: list[str] = []
    for case in fixture["cases"]:
        kind = case.get("kind")
        if kind == "mapped_field":
            verify_mapped_field(case, maps_by_id[case["field_id"]])
        elif kind == "timing_rejection":
            verify_timing_rejection(case)
        elif kind == "substitute_rejections":
            verify_substitutes(case, forbidden)
        elif kind == "source_rejection":
            verify_source_rejection(case)
        elif kind == "broker_switch_rejection":
            verify_broker_switch(case)
        else:
            raise VerificationError(
                f"{case.get('id', '<unknown>')}: unknown case kind {kind!r}"
            )
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
            if isinstance(case, dict) and case.get("id")
        }
        if len(cases_by_id) != len(cases):
            raise VerificationError("fixture case ids must be present and unique")
        assert_equal(set(cases_by_id), EXPECTED_CASE_IDS, "fixture case set")

        maps_by_id, blockers = verify_map_shape(contract, cases_by_id)
        passed = verify_cases(
            fixture,
            maps_by_id,
            contract.get("forbidden_substitutes", {}),
        )
    except (KeyError, TypeError, ValueError) as exc:
        print(f"VERIFIER FAIL: {exc}")
        return 2

    for case_id in passed:
        print(f"CASE PASS: {case_id}")
    observed = "blocked" if blockers else "complete"
    if blockers:
        for blocker in blockers:
            print(
                "SOURCE BLOCKER: "
                f"{blocker['field_id']} [{blocker['code']}] {blocker['reason']}"
            )
        print(
            f"SOURCE MAP FAIL: {len(blockers)} retained mapping(s) remain blocked"
        )
    else:
        print(
            "SOURCE MAP PASS: exact RUT and VIX3M mappings are closed; "
            "runtime production availability is not claimed"
        )

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
